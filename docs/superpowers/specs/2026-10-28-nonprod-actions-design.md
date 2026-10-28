> Superseded by the user’s final production-on-`prod` correction. See docs/GITHUB_ACTIONS_PRODUCTION.md. No GitHub environment; repo secrets; native ARM build; prod-branch OIDC; user monitors Actions.

# Non-production GitHub Actions

User requested GitHub Actions deployment, local `.env.deploy` configuration and user-managed GitHub setup, then approved proceeding after reducing the existing demo host to t4g.micro. Treat the existing demo host as nonprod; no new infrastructure or production environment is created.

CI runs on pull requests, pushes to main and reusable invocation: PostgreSQL integration tests, Ruff, typecheck, production build. Manual deployment on main runs the same checks first, builds an ARM64 image off-host, uploads a SHA-addressed private S3 artifact and uses SSM for deployment. Deployment serializes locally and on the host, retains the previous app container, backs up the DB before startup, verifies health and restores the old app on failure. Only expand-compatible schema changes are eligible; container rollback cannot undo a database migration. Runtime key/database credentials remain in the host's root-only environment.

Use OIDC restricted to the chosen repository's nonprod environment and main branch protection; no static AWS access keys. `.env.deploy` is ignored and mode 0600, with non-secret target values and a blank deployment-role ARN. A committed template and setup guide explain manually configuring environment variables/secrets, exact AWS permissions and host artifact-read permissions. No GitHub secrets, IAM trusts or workflows are activated remotely in this task.

Workflow tools validate target configuration before invoking AWS; no dotenv file is sourced as shell. Pin actions to verified commit hashes. No cloud credentials on PR CI. Deployment timeout and rollback failures are reported as failures; cancelled CI must not abandon a host rollout (SSM continues to completion). Smoke tests use synthetic data locally and health over HTTPS; no inference on every CI run.

User steering: no GitHub environment; repository Actions secrets. Exact main-branch immutable OIDC subject replaces environment-bound subject. This is the final deployment contract.
