#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
cd /opt/buildgate
install -d -m 700 private /var/lib/buildgate/app /var/lib/buildgate/postgres /var/lib/buildgate/caddy
install -d -m 755 /opt/buildgate/public/source

# PostgreSQL drops privileges before traversing the mounted volume root.
# Keep it private, but owned by the image's actual database user.
postgres_uid="$(docker run --rm --entrypoint id postgres:18-alpine -u postgres)"
postgres_gid="$(docker run --rm --entrypoint id postgres:18-alpine -g postgres)"
chown "$postgres_uid:$postgres_gid" /var/lib/buildgate/postgres

# Generate database credentials on the host, never in user data or command logs.
python3 - <<'PY'
import os
import secrets
from pathlib import Path
path = Path('/opt/buildgate/private/runtime.env')
if not path.exists():
    admin = secrets.token_hex(32)
    app = secrets.token_hex(32)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w') as stream:
        stream.write('POSTGRES_PASSWORD=' + admin + '\n')
        stream.write('POSTGRES_DB=buildgate\n')
        stream.write('PGDATA=/var/lib/postgresql/18/docker\n')
        stream.write('DATABASE_ADMIN_URL=postgresql://postgres:' + admin + '@buildgate-db:5432/buildgate\n')
        stream.write('DATABASE_APP_PASSWORD=' + app + '\n')
        stream.write('WEB_ORIGIN=https://buildgate.velox0.com\n')
        stream.write('PORT=8080\n')
        stream.write('OPENROUTER_MODEL=cohere/north-mini-code:free\n')
        stream.write('OPENROUTER_ALLOW_PROVIDER_RETENTION=true\n')
PY

if ! docker network inspect buildgate-private >/dev/null 2>&1; then
  docker network create buildgate-private >/dev/null
fi

if ! docker inspect buildgate-db >/dev/null 2>&1; then
  docker run -d --name buildgate-db --restart unless-stopped \
    --network buildgate-private --memory 512m \
    --env-file /opt/buildgate/private/runtime.env \
    -v /var/lib/buildgate/postgres:/var/lib/postgresql \
    postgres:18-alpine \
    -c max_connections=30 -c shared_buffers=128MB >/dev/null
else
  docker start buildgate-db >/dev/null
fi

ready=false
for _ in $(seq 1 90); do
  if docker exec buildgate-db pg_isready -U postgres -d buildgate >/dev/null 2>&1; then
    ready=true
    break
  fi
  sleep 2
done
if [ "$ready" != true ]; then
  echo 'Database did not become ready.' >&2
  exit 1
fi

# Replacing the app never replaces either private data directory.
if docker inspect buildgate-app >/dev/null 2>&1; then
  docker rm -f buildgate-app >/dev/null
fi
docker run -d --name buildgate-app --restart unless-stopped \
  --network buildgate-private --memory 1100m --memory-swap 1600m \
  --env-file /opt/buildgate/private/runtime.env \
  -v /var/lib/buildgate/app:/app/.local \
  brandgate-hosted:latest >/dev/null

if docker inspect buildgate-proxy >/dev/null 2>&1; then
  docker rm -f buildgate-proxy >/dev/null
fi
docker run -d --name buildgate-proxy --restart unless-stopped \
  --network buildgate-private --memory 128m \
  -p 80:80 -p 443:443 \
  -v /opt/buildgate/deploy/ec2/Caddyfile:/etc/caddy/Caddyfile:ro \
  -v /var/lib/buildgate/caddy:/data \
  -v /opt/buildgate/public:/srv:ro \
  caddy:2-alpine >/dev/null

echo 'BuildGate containers started; verify public TLS, health and account flow.'
