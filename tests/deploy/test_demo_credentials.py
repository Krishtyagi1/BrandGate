"""AWS is the only mocked boundary; exercise validation and private file writes."""

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


class DemoCredentialTests(unittest.TestCase):
    def module(self):
        spec = importlib.util.spec_from_file_location(
            "demo_credentials", ROOT / "scripts/load-demo-credentials.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_secure_parameter_is_written_privately_and_atomically(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "demo-login.json"
            value = {
                "email": "demo@example.com",
                "password": "Synthetic fixture password",
                "org_id": "00000000-0000-0000-0000-000000000001",
            }
            result = subprocess.CompletedProcess(
                [],
                0,
                json.dumps(
                    {"Parameter": {"Type": "SecureString", "Value": json.dumps(value)}}
                ),
                "",
            )
            with patch.object(module.subprocess, "run", return_value=result):
                module.load_credentials(
                    "/buildgate/production/demo-login", "ap-south-1", target
                )
            self.assertEqual(json.loads(target.read_text()), value)
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
            self.assertEqual(list(Path(temp).iterdir()), [target])

    def test_bad_parameter_or_aws_outage_removes_cached_secret_without_leaking(self):
        module = self.module()
        for payload in [
            {"Parameter": {"Type": "String", "Value": "private content"}},
            {"Parameter": {"Type": "SecureString", "Value": "private invalid json"}},
            {
                "Parameter": {
                    "Type": "SecureString",
                    "Value": json.dumps(
                        {
                            "email": "demo@example.com",
                            "password": "short",
                            "org_id": "invalid",
                        }
                    ),
                }
            },
            None,
        ]:
            with self.subTest(payload=payload), tempfile.TemporaryDirectory() as temp:
                target = Path(temp) / "demo.json"
                target.write_text("stale secret")
                kwargs = (
                    {
                        "return_value": subprocess.CompletedProcess(
                            [], 0, json.dumps(payload), ""
                        )
                    }
                    if payload is not None
                    else {
                        "side_effect": subprocess.CalledProcessError(
                            1, "aws", stderr="private content"
                        )
                    }
                )
                with (
                    patch.object(module.subprocess, "run", **kwargs),
                    self.assertRaisesRegex(RuntimeError, "Demo credentials could not be loaded") as error,
                ):
                    module.load_credentials(
                        "/buildgate/production/demo-login", "ap-south-1", target
                    )
                self.assertNotIn("private", str(error.exception))
                self.assertFalse(target.exists())
