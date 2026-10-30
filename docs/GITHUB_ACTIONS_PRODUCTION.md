# GitHub Actions: production deployment

The existing BuildGate t4g.micro instance is the production target. The user explicitly
requested repository Actions secrets and no GitHub environment. The production workflow targets the existing public instance; no extra instance is created. Builds run on the GitHub runner.

## Configured workflow

- `ci.yml`: PR/prod/reusable backend tests, deployment boundary tests, lint,
  typecheck and production build; no cloud/model credentials.
- `deploy-production.yml`: prod-branch push/manual deployment after CI, concurrency group
  `deploy-production`, short-lived AWS OIDC credentials.
- `scripts/deploy-production.py`: account/ARM/production-tag checks, private S3 upload,
  exact SHA-256 verification, SSM deployment wait and public HTTPS verification.
- `deploy/ec2/rollout.sh`: host lock, verified local database archive, app replacement
  and old-container rollback on new-app startup/internal-health failure.

## Secrets and AWS trust

Local ignored `.env.deploy` is mode 0600 and contains the deployment role ARN,
region, instance ID, private bucket and origin. GitHub does not read that local
file automatically. These are configured as repository Actions secrets:
`AWS_REGION`, `AWS_DEPLOY_ROLE_ARN`, `DEPLOY_INSTANCE_ID`, `DEPLOY_BUCKET`,
`DEPLOY_ORIGIN`. No static AWS access key, PAT, OpenRouter key or database password
is required. App secrets remain at `/opt/buildgate/private/runtime.env`.

Validate configuration without deploying:

```sh
python3 scripts/deploy-production.py --env-file .env.deploy --check
```

To import the configuration again after changing it:

```sh
gh secret set --repo Krishtyagi1/BrandGate --env-file .env.deploy
```

`DEPLOY_ENVIRONMENT` is fixed to `production` in workflow code; an imported secret
with that name cannot override it. The committed `.env.deploy.example` contains
placeholders. Real `.env.deploy` is excluded from Git, Docker and source archives.

AWS role `BuildGateActionsProduction` is bound to this repository's actual immutable
OIDC subject ending `:ref:refs/heads/prod`. Other branches/repositories cannot
assume it. The example trust uses name-based subjects; verify the real subject
format before applying it to another repository. Do not wildcard the trust.
The deployment role can upload only under the private bucket's
`production/releases/*`, describe targets and send SSM commands to the one tagged
production instance. The host role has read-only access to that release prefix.
The target must have `DeploymentEnvironment=production`. Existing policies remain.

## Running deployment

Pushing to `prod` starts deployment after CI. Manual dispatch can also be used when GitHub exposes the workflow:

```sh
gh workflow run deploy-production.yml --repo Krishtyagi1/BrandGate --ref prod
```

CI runs first. ARM builds run off-host on a native `ubuntu-24.04-arm` runner for this public repository; no emulation is needed. Images are tagged
`brandgate-hosted:COMMIT_SHA-RUN_ID-ATTEMPT`, uploaded privately, verified and
loaded on the host. Only the app container is replaced; database/proxy, private
environment, records and uploads persist. App cap remains 512 MiB plus bounded
swap. The previous app container is retained for rollback. A brief restart gap
is expected. Inspect the run and SSM command ID after completion.

## Recovery and limits

A local private `pg_dump -Fc` backup is checked with `pg_restore -l` before app
replacement. This is not an independent/offsite backup. Failed new-app startup
or internal health restores the old app and fails the workflow. Rollback failure
also fails the workflow. Public-only HTTPS failure fails the job for inspection;
it does not blindly roll back an internally healthy app for a DNS/Cloudflare issue.

**Container rollback does not reverse database migrations.** Deploy only
expand-compatible migrations; destructive/data-rewriting changes need a separate
reviewed migration/recovery plan. Cancelled GitHub runs may leave SSM running;
inspect the command before rerunning. Host flock rejects concurrent app swaps.
Review unused images, old local database backups and private S3 releases
periodically so the 30 GiB host disk and artifact storage stay bounded.

Local deployment tests run the actual shell control flow against isolated external
command substitutes. They are not evidence of a hosted Actions deployment.
CI never spends model quota. Real AI checks remain separate synthetic tests.

The public health verifier identifies itself as `BuildGate-DeployHealth/1.0`
and requests JSON. A read-only 30 October check reproduced HTTP 403 for Python's
default user agent while the named checker and normal requests received HTTP
200. Failures now include the last HTTP status/error type; HTML challenges and
JSON without `status=ok` still fail. A previously failed run retains its original
commit, so deploy a commit containing the fix rather than expecting its rerun to
pick up local changes.

Official OIDC reference:
https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws
