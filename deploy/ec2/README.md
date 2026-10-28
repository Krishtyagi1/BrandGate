# BuildGate EC2 deployment

Requested hostname: `https://buildgate.velox0.com`, with Cloudflare DNS/proxy.

Deployed and publicly smoke-tested on 25 October 2026. Runtime identifiers are in
the ignored `.local/deployment-aws/state.json`. Launch-template default version 6
includes the corrected PostgreSQL ownership setup, tested North Mini image and low-traffic resource profile. Initial cloud-init logged
the ownership failure; the corrected startup was successfully rerun through SSM.

Use one dedicated ARM64 `t4g.micro` in `ap-south-1`, standard CPU credits,
encrypted 30 GiB gp3 EBS and a stable Elastic IP. The app, database and HTTPS proxy
run in separate Docker containers. Only the proxy exposes host ports 80/443;
database and app ports stay private. Manage the host through SSM, without SSH.
Do not change the existing unrelated `main` EC2 instance.

The user approved a USD 20/month hosting budget. Queried AWS component prices
estimate USD 10.47/month at 730 hours for the instance, 30 GiB gp3 and IPv4,
excluding small artifact storage, traffic and taxes. Standard CPU credits avoid
surplus CPU charges. AWS does not enforce this estimate as an automatic hard cap.

The instance role has SSM managed-node access and read access to this deployment's
specific private S3 artifact. No AWS keys or database passwords appear in user
data. Credentials are generated on the host in a root-only file. The app stores
private files and PostgreSQL stores records on encrypted EBS-backed directories.
Preserve the disk on termination; deleting the instance does not stop retained
disk/Elastic IP charges. Explicitly release resources when no longer needed.

`start.sh` runs from `/opt/buildgate`. Before running it, install/start Docker,
load the tested ARM images and place the source-only ZIP at
`/opt/buildgate/public/source/buildgate-source.zip`. Caddy obtains a public TLS
certificate once the hostname resolves to the host. It does not compress/buffer
review streams. Never enable Cloudflare Flexible TLS or expose PostgreSQL/SSH.

Cloudflare record changes are limited to `buildgate`; preserve all other DNS.
Initially use DNS-only for origin certificate verification, then enable the proxy
and restrict HTTP/S origin ingress to Cloudflare's published IPv4 ranges.

The generated environment selects `cohere/north-mini-code:free` with the user-approved
`OPENROUTER_ALLOW_PROVIDER_RETENTION=true`. This keeps no-training and zero-price
routing; provider retention may apply. The new policy requires fresh owner
consent in AI settings. North Mini uses schema-validated function results for
text; it does not support image input. The image contains no provider key.
Supply the key through a private server-side secret when available; never call
unavailable inference a successful AI review. Source inspection, accounts and
draft editing work without live inference. Windows OCR is unavailable on Linux.

This is a single-host prototype, without high availability or a production
identity/retention solution. Back up PostgreSQL and uploads before real use.

## Low-traffic profile — 28 October 2026

The live instance was reduced from 2 GiB to 1 GiB RAM (2 burstable ARM vCPUs),
with 2 GiB swap retained. Container hard limits: app 512 MiB (+512 MiB swap),
PostgreSQL 256 MiB (+256 MiB swap), Caddy 64 MiB (+64 MiB swap). Build images
in CI/off-host rather than on this instance. No autoscaling or commitments.

Fresh public smoke passed HTTPS/login, registration, authenticated organisation
and draft write/read, exact DOCX upload/download and anonymous denial. All three
containers stayed running without OOM; after smoke, host available memory was
422 MiB and swap use 2 MiB. These checks establish a small sequential demo, not
a capacity or concurrent-user guarantee. Original draft/source records remain.
A verified local-on-host database archive precedes resizing; it is not an offsite
backup. The original encrypted 30 GiB disk and Elastic IP were preserved.

Queried Mumbai micro compute rate: USD 0.0056/hour, USD 4.09 at 730 hours.
Combined with previously queried disk/IPv4 rates, base estimate USD 10.47/month,
before traffic, artifact storage and taxes. No automatic hard budget cap. The
512 MiB nano is below the observed combined app/database/host memory footprint.
