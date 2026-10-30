"""Manual production deployment via CLI; never source dotenv or send runtime secrets."""

import argparse
import base64
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
FIELDS = (
    "DEPLOY_ENVIRONMENT",
    "AWS_REGION",
    "AWS_DEPLOY_ROLE_ARN",
    "DEPLOY_INSTANCE_ID",
    "DEPLOY_BUCKET",
    "DEPLOY_ORIGIN",
)


def read_env(path):
    values = {}
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError("Deployment file must contain NAME=value entries.")
        key, value = line.split("=", 1)
        if key not in FIELDS:
            raise ValueError("Unknown deployment field: " + key)
        if key in values:
            raise ValueError("Duplicate deployment field: " + key)
        values[key] = value.strip().strip("\"'")
    return values


def validate_config(values):
    config = {key: values.get(key, "") for key in FIELDS}
    patterns = {
        "DEPLOY_ENVIRONMENT": r"production",
        "AWS_REGION": r"[a-z]{2}(?:-[a-z]+)+-\d",
        "AWS_DEPLOY_ROLE_ARN": r"arn:aws:iam::\d{12}:role/[A-Za-z0-9+=,.@_/-]+",
        "DEPLOY_INSTANCE_ID": r"i-[a-f0-9]{17}",
        "DEPLOY_BUCKET": r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]",
    }
    for key, pattern in patterns.items():
        if not re.fullmatch(pattern, config[key]):
            raise ValueError("Missing or invalid " + key)
    parsed = urlsplit(config["DEPLOY_ORIGIN"])
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.path
        or parsed.query
        or parsed.fragment
        or parsed.port not in (None, 443)
    ):
        raise ValueError("DEPLOY_ORIGIN must be the exact HTTPS origin.")
    return config


def deploy(config, image, release):
    if not re.fullmatch(r"[a-f0-9]{40}-[0-9]+(?:-[0-9]+)?", release):
        raise ValueError("Release must be commit SHA-run ID[-attempt].")
    if not image.is_file():
        raise ValueError("Image archive is missing.")

    def aws(*args):
        result = subprocess.run(
            ["aws", *args, "--region", config["AWS_REGION"], "--output", "json"],
            capture_output=True,
            text=True,
            timeout=600,
            check=True,
        )
        return json.loads(result.stdout) if result.stdout.strip() else {}

    # OIDC has already established the role in Actions; local runs use configured AWS CLI.
    identity = aws("sts", "get-caller-identity")
    account = config["AWS_DEPLOY_ROLE_ARN"].split(":")[4]
    if identity["Account"] != account:
        raise ValueError("AWS account does not match the configured deployment role.")
    instance = aws(
        "ec2", "describe-instances", "--instance-ids", config["DEPLOY_INSTANCE_ID"]
    )
    host = instance["Reservations"][0]["Instances"][0]
    tags = {item["Key"]: item["Value"] for item in host.get("Tags", [])}
    if tags.get("DeploymentEnvironment") != "production":
        raise ValueError(
            "Target instance must have DeploymentEnvironment=production tag."
        )
    if host["State"]["Name"] != "running" or host["Architecture"] != "arm64":
        raise ValueError("Target must be a running ARM64 instance.")
    with image.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    key = "production/releases/" + release + "/image.tar.gz"
    aws(
        "s3",
        "cp",
        str(image),
        "s3://" + config["DEPLOY_BUCKET"] + "/" + key,
        "--only-show-errors",
    )
    script = base64.b64encode((ROOT / "deploy/ec2/rollout.sh").read_bytes()).decode()
    folder = "/opt/buildgate/releases/" + release
    commands = "\n".join(
        [
            "set -eu",
            "umask 077",
            "install -d -m 700 " + folder,
            "aws s3 cp "
            + shlex.quote("s3://" + config["DEPLOY_BUCKET"] + "/" + key)
            + " "
            + folder
            + "/image.tar.gz --region "
            + shlex.quote(config["AWS_REGION"])
            + " --only-show-errors",
            "echo "
            + shlex.quote(digest + "  " + folder + "/image.tar.gz")
            + " | sha256sum -c -",
            "docker load -i " + folder + "/image.tar.gz",
            "rm " + folder + "/image.tar.gz",
            "printf %s "
            + shlex.quote(script)
            + " | base64 -d > "
            + folder
            + "/rollout.sh",
            "bash "
            + folder
            + "/rollout.sh "
            + release
            + " brandgate-hosted:"
            + release,
        ]
    )
    command = aws(
        "ssm",
        "send-command",
        "--instance-ids",
        config["DEPLOY_INSTANCE_ID"],
        "--document-name",
        "AWS-RunShellScript",
        "--parameters",
        json.dumps({"commands": [commands], "executionTimeout": ["1200"]}),
        "--comment",
        "BuildGate production " + release,
    )["Command"]["CommandId"]
    print("SSM deployment command: " + command, flush=True)
    deadline = time.monotonic() + 1260
    while time.monotonic() < deadline:
        try:
            result = aws(
                "ssm",
                "get-command-invocation",
                "--command-id",
                command,
                "--instance-id",
                config["DEPLOY_INSTANCE_ID"],
            )
        except subprocess.CalledProcessError as error:
            if "InvocationDoesNotExist" in error.stderr:
                time.sleep(5)
                continue
            raise
        status = result["Status"]
        if status == "Success":
            break
        if status not in ("Pending", "InProgress", "Delayed"):
            raise RuntimeError(
                "Host deployment failed ("
                + status
                + "); inspect SSM command "
                + command
            )
        time.sleep(5)
    else:
        raise RuntimeError(
            "SSM wait timed out; host command may still be running: " + command
        )
    verify_public_health(config["DEPLOY_ORIGIN"], release)


def verify_public_health(origin, release):
    request = Request(
        origin + "/api/health",
        headers={
            "User-Agent": "BuildGate-DeployHealth/1.0",
            "Accept": "application/json",
        },
    )
    last_failure = "No response"
    for attempt in range(12):
        try:
            with urlopen(request, timeout=10) as response:
                content = response.read(65537)
                body = json.loads(content) if len(content) <= 65536 else None
                if (
                    response.status == 200
                    and isinstance(body, dict)
                    and body.get("status") == "ok"
                ):
                    print("Production public HTTPS health passed. Release: " + release)
                    return
                last_failure = f"HTTP {response.status}; invalid health payload"
        except HTTPError as error:
            last_failure = f"HTTP {error.code}"
            error.close()
        except (OSError, ValueError) as error:
            last_failure = type(error).__name__
        if attempt < 11:
            time.sleep(5)
    raise RuntimeError(
        "Internal deploy passed but public HTTPS failed. Inspect Cloudflare/origin; no success claimed."
        + " Last check: "
        + last_failure
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--image", type=Path)
    parser.add_argument("--release")
    args = parser.parse_args()
    config = validate_config(read_env(args.env_file) if args.env_file else os.environ)
    if args.check:
        print("Production deployment configuration valid. No AWS changes made.")
        return
    if not args.image or not args.release:
        raise ValueError("--image and --release are required for deployment.")
    deploy(config, args.image, args.release)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, OSError, subprocess.SubprocessError) as error:
        # Never print environment contents, AWS process arguments or runtime secrets.
        print(
            "Deployment failed: "
            + (
                str(error)
                if isinstance(error, (ValueError, RuntimeError))
                else type(error).__name__
            ),
            file=sys.stderr,
        )
        raise SystemExit(1) from None
