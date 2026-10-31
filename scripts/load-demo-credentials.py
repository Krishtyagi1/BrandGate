"""Load the exact SSM SecureString on the EC2 host, never in the browser or image."""

import argparse
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from uuid import UUID


def load_credentials(parameter, region, output):
    temporary = None
    try:
        if (
            not isinstance(parameter, str)
            or not parameter.startswith("/")
            or len(parameter) > 2048
        ):
            raise ValueError()
        if not isinstance(region, str) or not re.fullmatch(
            r"[a-z]{2}(?:-[a-z]+)+-[0-9]+", region
        ):
            raise ValueError()
        result = subprocess.run(
            [
                "aws",
                "ssm",
                "get-parameter",
                "--name",
                parameter,
                "--with-decryption",
                "--region",
                region,
                "--output",
                "json",
                "--no-cli-pager",
                "--cli-connect-timeout",
                "5",
                "--cli-read-timeout",
                "10",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        item = json.loads(result.stdout)["Parameter"]
        if item["Type"] != "SecureString":
            raise ValueError()
        value = json.loads(item["Value"])
        if set(value) != {"email", "password", "org_id"}:
            raise ValueError()
        if (
            not isinstance(value["email"], str)
            or "@" not in value["email"]
            or len(value["email"]) > 254
        ):
            raise ValueError()
        if (
            not isinstance(value["password"], str)
            or not 12 <= len(value["password"]) <= 128
        ):
            raise ValueError()
        UUID(value["org_id"])
        content = json.dumps(value)
        if len(content.encode()) > 4096:
            raise ValueError()
        output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with tempfile.NamedTemporaryFile(
            mode="w", dir=output.parent, prefix=".demo-", delete=False
        ) as stream:
            temporary = Path(stream.name)
            os.fchmod(stream.fileno(), 0o600)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, output)
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
        subprocess.SubprocessError,
    ):
        output.unlink(missing_ok=True)
        raise RuntimeError(
            "Demo credentials could not be loaded from AWS; demo entry is disabled."
        ) from None
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        source = json.loads(args.source.read_text())
        load_credentials(source["parameter"], source["region"], args.output)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError):
        args.output.unlink(missing_ok=True)
        raise SystemExit(
            "Demo credentials could not be loaded from AWS; demo entry is disabled."
        ) from None


if __name__ == "__main__":
    main()
