"""Deployment boundary checks run without AWS credentials or network access."""

import importlib.util
import io
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request

ROOT = Path(__file__).resolve().parents[2]


class ConfigTests(unittest.TestCase):
    def module(self):
        spec = importlib.util.spec_from_file_location(
            "deploy_production", ROOT / "scripts/deploy-production.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def config(self):
        return {
            "DEPLOY_ENVIRONMENT": "production",
            "AWS_REGION": "ap-south-1",
            "AWS_DEPLOY_ROLE_ARN": "arn:aws:iam::123456789012:role/BuildGateActionsProduction",
            "DEPLOY_INSTANCE_ID": "i-0123456789abcdef0",
            "DEPLOY_BUCKET": "buildgate-test-artifacts",
            "DEPLOY_ORIGIN": "https://buildgate.example.com",
        }

    def test_only_production_and_safe_target_values(self):
        module = self.module()
        self.assertEqual(
            module.validate_config(self.config())["DEPLOY_ENVIRONMENT"], "production"
        )
        for field, value in [
            ("DEPLOY_ENVIRONMENT", "prod"),
            ("AWS_REGION", "us-east-1;id"),
            ("DEPLOY_INSTANCE_ID", "i-fake"),
            ("DEPLOY_BUCKET", "bucket;id"),
            ("DEPLOY_ORIGIN", "http://example.com"),
            ("DEPLOY_ORIGIN", "https://example.com/path"),
            ("AWS_DEPLOY_ROLE_ARN", "*"),
        ]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                module.validate_config({**self.config(), field: value})

    def test_dotenv_is_data_and_never_shell(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env.deploy"
            path.write_text(
                "DEPLOY_ENVIRONMENT=production\nAWS_REGION=$(touch SHOULD_NOT_EXIST)\n"
            )
            data = module.read_env(path)
            self.assertEqual(data["AWS_REGION"], "$(touch SHOULD_NOT_EXIST)")
            self.assertFalse((ROOT / "SHOULD_NOT_EXIST").exists())
            with self.assertRaises(ValueError):
                module.validate_config({**self.config(), **data})


class PublicHealthTests(unittest.TestCase):
    module = ConfigTests.module

    def test_public_check_uses_explicit_agent_and_requires_healthy_json(self):
        module = self.module()

        def open_health(request, timeout):
            self.assertIsInstance(request, Request)
            self.assertEqual(
                request.full_url, "https://buildgate.example.com/api/health"
            )
            self.assertEqual(
                request.get_header("User-agent"), "BuildGate-DeployHealth/1.0"
            )
            self.assertEqual(request.get_header("Accept"), "application/json")
            self.assertEqual(timeout, 10)
            response = io.BytesIO(b'{"status":"ok"}')
            response.status = 200
            return response

        with patch.object(module, "urlopen", side_effect=open_health) as opener:
            module.verify_public_health(
                "https://buildgate.example.com", "synthetic-release"
            )
        self.assertEqual(opener.call_count, 1)

    def test_public_check_reports_http_failure_without_false_success(self):
        module = self.module()
        error = HTTPError(
            "https://buildgate.example.com/api/health", 403, "Forbidden", {}, None
        )
        with (
            patch.object(module, "urlopen", side_effect=error) as opener,
            patch.object(module.time, "sleep"),
            self.assertRaisesRegex(RuntimeError, "Last check: HTTP 403"),
        ):
            module.verify_public_health(
                "https://buildgate.example.com", "synthetic-release"
            )
        self.assertEqual(opener.call_count, 12)

    def test_public_check_rejects_html_and_wrong_status_json(self):
        module = self.module()
        for content in (b"<html>challenge</html>", b'{"status":"error"}', b"[]"):
            with self.subTest(content=content):

                def response(*args, content=content, **kwargs):
                    body = io.BytesIO(content)
                    body.status = 200
                    return body

                with (
                    patch.object(module, "urlopen", side_effect=response),
                    patch.object(module.time, "sleep"),
                    self.assertRaisesRegex(RuntimeError, "public HTTPS failed"),
                ):
                    module.verify_public_health(
                        "https://buildgate.example.com", "synthetic-release"
                    )


class RolloutTests(unittest.TestCase):
    def run_rollout(
        self,
        health_failure=False,
        backup_failure=False,
        lock_failure=False,
        restore_failure=False,
        demo_failure=False,
    ):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            # Isolated external-command substitute records actual rollout decisions.
            fake = root / "docker"
            fake.write_text("""#!/usr/bin/env python3
import json,os,sys
from pathlib import Path
args=sys.argv[1:];log=Path(os.environ['DOCKER_LOG'])
with log.open('a') as f:f.write(json.dumps(args)+'\\n')
if args[0]=='start' and os.environ.get('RESTORE_FAIL')=='1':sys.exit(1)
if args[0]=='exec' and args[1]=='buildgate-db':
 if os.environ.get('BACKUP_FAIL')=='1':sys.exit(1)
 sys.stdout.write('synthetic backup')
if args[0]=='exec' and 'python' in args:
 if os.environ.get('HEALTH_FAIL')=='1' and not Path(os.environ['RESTORED']).exists():sys.exit(1)
if args[:3]==['rename','buildgate-app-previous','buildgate-app']:
 Path(os.environ['RESTORED']).touch()
""")
            fake.chmod(0o755)
            (root / "docker.log").touch()
            lock = root / "flock"
            lock.write_text("#!/bin/sh\nexit ${LOCK_FAIL:-0}\n")
            lock.chmod(0o755)
            (root / "private").mkdir()
            (root / "private/runtime.env").write_text(
                "WEB_ORIGIN=https://example.com\n"
            )
            if demo_failure:
                (root / "private/demo-login-source.json").write_text("{}")
            env = {
                **os.environ,
                "PATH": str(root) + os.pathsep + os.environ["PATH"],
                "DOCKER_LOG": str(root / "docker.log"),
                "RESTORED": str(root / "restored"),
                "HEALTH_FAIL": str(int(health_failure)),
                "BACKUP_FAIL": str(int(backup_failure)),
                "LOCK_FAIL": str(int(lock_failure)),
                "RESTORE_FAIL": str(int(restore_failure)),
            }
            # ROOT argument is explicit and script never touches real /opt in tests.
            result = subprocess.run(
                [
                    "bash",
                    str(ROOT / "deploy/ec2/rollout.sh"),
                    "a" * 40 + "-1",
                    "brandgate-hosted:test",
                    str(root),
                ],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            calls = [
                __import__("json").loads(line)
                for line in (root / "docker.log").read_text().splitlines()
            ]
            return result, calls

    def test_demo_loader_outage_does_not_abort_normal_rollout(self):
        result, calls = self.run_rollout(demo_failure=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(any(c[0] == "run" for c in calls))

    def test_healthy_release_uses_small_limits(self):
        result, calls = self.run_rollout()
        self.assertEqual(result.returncode, 0, result.stderr)
        run = next(c for c in calls if c[0] == "run")
        self.assertIn("512m", run)
        self.assertIn("1024m", run)
        self.assertFalse(any(c[:2] == ["start", "buildgate-app"] for c in calls))

    def test_failed_health_restores_previous_container_and_fails_job(self):
        result, calls = self.run_rollout(health_failure=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(["rename", "buildgate-app-previous", "buildgate-app"], calls)
        self.assertIn(["start", "buildgate-app"], calls)
        self.assertNotIn(
            ["tag", "brandgate-hosted:test", "brandgate-hosted:latest"], calls
        )

    def test_backup_failure_never_stops_current_app(self):
        result, calls = self.run_rollout(backup_failure=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(any(c[0] == "stop" for c in calls))

    def test_concurrent_rollout_is_rejected_before_docker(self):
        result, calls = self.run_rollout(lock_failure=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, [])

    def test_rollback_start_failure_is_reported(self):
        result, _calls = self.run_rollout(health_failure=True, restore_failure=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ROLLBACK FAILED: start", result.stderr)


if __name__ == "__main__":
    unittest.main()
