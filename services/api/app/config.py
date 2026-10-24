import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LOCAL = ROOT / ".local"
LOCAL.mkdir(exist_ok=True)
runtime_file = LOCAL / "runtime.json"
runtime = json.loads(runtime_file.read_text()) if runtime_file.exists() else {}
DATABASE_URL = os.getenv("DATABASE_URL", runtime.get("databaseUrl", ""))
ADMIN_URL = os.getenv("DATABASE_ADMIN_URL", runtime.get("adminUrl", ""))
WEB_ORIGIN = os.getenv("WEB_ORIGIN", "http://127.0.0.1:3000")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
SESSION_SECONDS = 60 * 60 * 12
