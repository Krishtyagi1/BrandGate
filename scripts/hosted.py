"""One public Next.js server, one loopback API; no embedded cloud database."""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

import psycopg

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/api"))

from app.hosting import bootstrap_database, prepare_environment


def main():
    env = prepare_environment(os.environ)
    env.update(
        PYTHONPATH=str(ROOT / "services/api"),
        PYTHONDONTWRITEBYTECODE="1",
        NEXT_TELEMETRY_DISABLED="1",
        LANGSMITH_TRACING="false",
        LANGCHAIN_TRACING_V2="false",
    )
    bootstrap_database(env["DATABASE_ADMIN_URL"], env["DATABASE_APP_PASSWORD"])
    children = []
    stopping = False

    def stop(*_):
        nonlocal stopping
        stopping = True
        for child in children:
            if child.poll() is None:
                child.terminate()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        api = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=ROOT,
            env=env,
        )
        children.append(api)
        deadline = time.monotonic() + 90
        while not stopping:
            if api.poll() is not None:
                raise RuntimeError("API failed during startup.")
            try:
                with urlopen("http://127.0.0.1:8000/api/health", timeout=2) as response:
                    if response.status == 200:
                        break
            except OSError:
                pass
            if time.monotonic() > deadline:
                raise RuntimeError("API startup timed out.")
            time.sleep(0.25)
        if stopping:
            return 0
        web = subprocess.Popen(
            [
                "node", str(ROOT / "node_modules/next/dist/bin/next"), "start",
                "--hostname", "0.0.0.0", "--port", env["PORT"],
            ],
            cwd=ROOT / "apps/web",
            env=env,
        )
        children.append(web)
        while not stopping:
            if any(child.poll() is not None for child in children):
                return 1
            time.sleep(0.25)
        return 0
    finally:
        stop()
        deadline = time.monotonic() + 10
        for child in children:
            try:
                child.wait(timeout=max(0.1, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError, OSError, psycopg.Error, subprocess.SubprocessError) as error:
        # Connection exceptions can contain private connection strings.
        print(f"Hosted startup failed ({type(error).__name__}); check private configuration.", file=sys.stderr)
        raise SystemExit(1) from None
