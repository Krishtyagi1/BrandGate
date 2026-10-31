#!/usr/bin/env bash
# Replace only the app. Database, proxy, private environment and uploads persist.
set -Eeuo pipefail
umask 077
release="${1:?release required}"
image="${2:?image required}"
root="${3:-/opt/buildgate}"
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
[[ "$release" =~ ^[a-f0-9]{40}-[0-9]+(-[0-9]+)?$ ]] || { echo 'Invalid release ID' >&2; exit 2; }
[[ "$image" =~ ^brandgate-hosted:[a-zA-Z0-9_.-]+$ ]] || { echo 'Invalid image tag' >&2; exit 2; }
cd "$root"
[[ -f private/runtime.env ]] || { echo 'Private runtime environment is missing' >&2; exit 2; }
exec 9>private/deploy.lock
flock -n 9 || { echo 'Another host deployment is active' >&2; exit 1; }
if [[ -f private/demo-login-source.json ]]; then
  python3 "$script_dir/load-demo-credentials.py" --source private/demo-login-source.json --output /var/lib/buildgate/app/demo-login.json \
    || echo 'Demo sign-in unavailable; continuing the normal application deployment.' >&2
fi
docker inspect buildgate-app >/dev/null
install -d -m 700 private/backups
backup="private/backups/pre-${release}.dump"
docker exec buildgate-db pg_dump -U postgres -d buildgate -Fc > "$backup"
test -s "$backup"
docker exec -i buildgate-db pg_restore -l < "$backup" >/dev/null
# Previous code is retained; backup is local, not an offsite recovery strategy.
if docker inspect buildgate-app-previous >/dev/null 2>&1; then
  docker rm -f buildgate-app-previous >/dev/null
fi
rollback() {
  trap - ERR
  set +e
  echo 'New app failed; restoring previous app container.' >&2
  if docker inspect buildgate-app-previous >/dev/null 2>&1; then
    docker rm -f buildgate-app >/dev/null 2>&1
    docker rename buildgate-app-previous buildgate-app || { echo 'ROLLBACK FAILED: rename' >&2; exit 1; }
  fi
  docker start buildgate-app >/dev/null || { echo 'ROLLBACK FAILED: start' >&2; exit 1; }
  echo 'Previous container restarted. Inspect health and schema compatibility.' >&2
  exit 1
}
trap rollback ERR
docker stop --time 30 buildgate-app >/dev/null
docker rename buildgate-app buildgate-app-previous
docker run -d --name buildgate-app --restart unless-stopped \
  --network buildgate-private --memory 512m --memory-swap 1024m \
  --label "buildgate.release=$release" --label buildgate.environment=production \
  --env-file "$root/private/runtime.env" \
  -v /var/lib/buildgate/app:/app/.local \
  "$image" >/dev/null
docker exec buildgate-app python -c '
import time
from urllib.request import urlopen
for attempt in range(90):
    try:
        with urlopen("http://127.0.0.1:8080/api/health", timeout=2) as response:
            if response.status == 200:
                break
    except OSError:
        pass
    time.sleep(1)
else:
    raise SystemExit("New app failed health check")
'
docker tag "$image" brandgate-hosted:latest
trap - ERR
printf '%s\n' "$release" > private/current-release
echo "Production release $release passed internal health."
