# Railway trial deployment

Use trial credits only. Do not purchase a plan or upgrade automatically. Railway
trial eligibility, remaining credit and quotas determine whether this can run.
This is deployment preparation until a public HTTPS smoke test is recorded.

## Services

1. Create a new empty project and add PostgreSQL in the same region.
2. Deploy the repository root as a Docker service; Railway detects `Dockerfile`.
   Use its default container command. Set healthcheck path `/api/health`, timeout
   120 seconds, one replica and restart-on-failure with at most three retries in
   service settings. New services cannot use the deprecated `railway.json` format.
3. Attach a private volume at **`/app/.local`** to the app service. Uploads are
   otherwise lost on deployment. Keep one replica; current jobs run in process.
4. Generate a public HTTPS domain for the app, targeting port 8080.

## App variables

| Name | Value |
| --- | --- |
| `DATABASE_ADMIN_URL` | Private reference `${{Postgres.DATABASE_URL}}` (adjust service name) |
| `DATABASE_APP_PASSWORD` | A new random secret retained across app deployments |
| `WEB_ORIGIN` | Exact `https://` app domain, without trailing slash |
| `OPENROUTER_MODEL` | `openrouter/free` |
| `OPENROUTER_API_KEY` | Optional private key; absent means live AI unavailable |
| `PORT` | `8080` |

If `WEB_ORIGIN` is absent, startup uses `https://${RAILWAY_PUBLIC_DOMAIN}`. Secure
cookies are enforced in hosted mode. Do not set `DATABASE_URL` to PostgreSQL's
admin credential: startup derives a separate restricted `inkloom_app` connection.
It creates that login only when absent and rejects privileged existing logins.
Use a fresh project database rather than replacing another application's roles.

Never commit a real password/key or upload `.env`, `.local`, `.cache`, local
accounts or company files. Both source-upload and Docker contexts must exclude
those paths. New cloud data starts empty. Add approved sources through the app.

## Verification

- Build with `docker build -t brandgate-hosted .` when Docker is available.
- `/api/health` and `/login` must respond over the public HTTPS domain.
- Register a synthetic account; create an organisation, confirm rules and save
  a draft. Validate an unauthenticated request is rejected.
- Confirm saved uploads survive an app restart; verify private original download
  still requires organisation membership.
- Live review/rewrite claims require actual eligible free inference. An unavailable
  route or absent key must remain incomplete, never approved.

No local database is migrated automatically. Windows OCR is unavailable in Linux;
verified transcripts remain the fallback. Existing prototype identity, retention
and dependency limits in README still apply. A trial deployment is not a promise
of permanent free hosting or production readiness.

Official references: [Dockerfiles](https://docs.railway.com/builds/dockerfiles),
[volumes](https://docs.railway.com/volumes),
[pricing](https://docs.railway.com/pricing/plans).
