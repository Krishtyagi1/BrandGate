# Railway trial deployment

User request: deploy the existing app and return a working public link. Railway
was selected in follow-up. Use trial credits only; never upgrade or purchase.

Reuse the current Next.js/FastAPI/PostgreSQL architecture. One Docker service
exposes Next.js on Railway's PORT; FastAPI listens on loopback behind the existing
same-origin proxy. One private PostgreSQL service owns durable records. A volume
at `/app/.local` retains private uploads. Start with an empty cloud workspace;
never upload local accounts, files, environment files or database data.

The startup script creates a restricted `inkloom_app` login when absent and uses
a separately supplied password. It refuses privileged existing runtime roles.
Only migration setup uses the database owner's connection. Cookies are secure,
WEB_ORIGIN is the exact HTTPS public origin, and only one replica is supported
because review jobs and rate limits currently live in process memory.

Alternatives: Vercel frontend plus external backend needs more independent
services and persistent storage integration. Render supports the same architecture
but free web services cannot retain uploads. Railway trial is the user's choice;
availability depends on account eligibility and remaining credit.

Keep free-only AI and all existing privacy/approval controls. A key is optional
for initial account/source pages; absent AI must remain visibly unavailable.
Do not claim live AI passes until a real request succeeds. Windows OCR remains
unavailable in the Linux container; transcript-based image checks remain.

Verification: startup validation/credential tests, real PostgreSQL bootstrap,
existing 129 backend tests, web build, Docker build when a daemon is available,
and public HTTPS registration/source/draft plus negative permission smoke tests.
Never report the app deployed until an observed public endpoint works.
