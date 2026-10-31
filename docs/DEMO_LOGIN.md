# Shared demo sign in

The login button creates a one-hour HttpOnly session for the configured fictional demo account. Demo sessions are limited to one organisation and use effective creator permissions. Visitors can edit/upload fictional documents, comment and explicitly run reviews, rewrites and chat. They cannot change rules, team membership or processing consent; create/join organisations; or perform human approvals. Edits, files and chat are shared with other visitors. Normal password sign in remains unchanged.

## AWS configuration

Store a JSON object with exactly `email`, `password` and `org_id` in an AWS SSM **SecureString**. The account must already exist with an active membership in that organisation. Provision it privately; do not place the value in command-line arguments, source control, screenshots or logs. The production parameter is `/buildgate/production/demo-login` in `ap-south-1`.

Grant the host instance role `ssm:GetParameter` for that exact ARN, following `deploy/github/host-demo-policy.example.json`. The standard SSM service encryption key is used. A customer-managed KMS key additionally needs its own scoped decrypt permission.

The host configuration `/opt/buildgate/private/demo-login-source.json` contains only the parameter path and region:

```json
{"parameter":"/buildgate/production/demo-login","region":"ap-south-1"}
```

The normal startup/rollout runs `scripts/load-demo-credentials.py` on the host. It retrieves and validates the SecureString, then atomically replaces `/var/lib/buildgate/app/demo-login.json` with mode 0600. The app's existing private volume maps this to `/app/.local/demo-login.json`. The app container receives neither AWS credentials nor a new cloud role. The API re-reads this private file for each demo sign in and verifies the password and active membership. Nothing auto-enables processing consent or runs an AI request on login.

AWS reference: [GetParameter decryption flag](https://docs.aws.amazon.com/cli/latest/reference/ssm/get-parameter.html).

## Failure and maintenance

Missing, unreadable, malformed or insecurely permissioned files return a generic unavailable message. Failed AWS retrieval removes the stale cached value; the normal app continues to start/deploy. Never replace an unavailable demo with an unrestricted owner session. Demo entry is rate limited and uses the normal CSRF/origin protections.

To rotate credentials, update the account password and SecureString together, then run the host loader or deploy again. Cached credentials refresh on startup/rollout, not per click. Existing demo sessions last at most one hour; credential removal prevents new sessions and does not revoke existing sessions. Delete their `demo_sessions` records if immediate revocation is needed. Demo tokens never enter the normal `sessions` table, so an older application cannot treat them as owner sessions after a rollback.

For local development, use an ignored mode-0600 file at `.local/demo-login.json`, or set server-only `DEMO_LOGIN_FILE` to another private absolute path. Never use a `NEXT_PUBLIC_` variable. Automated tests use isolated synthetic credentials and offline model doubles; those tests are not live AI quality evidence.
