import { spawn } from "node:child_process";
import { mkdirSync, readFileSync } from "node:fs";
import pg from "pg";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const temporary = resolve(root, ".cache/tmp");
mkdirSync(temporary, { recursive: true });
const config = JSON.parse(
  readFileSync(resolve(root, ".local/runtime.json"), "utf8"),
);
const admin = new pg.Client({
  connectionString: config.adminUrl.replace(/\/[^/]+$/, "/postgres"),
});
await admin.connect();
if (
  !(await admin.query("SELECT 1 FROM pg_database WHERE datname='inkloom_test_utf8'"))
    .rowCount
)
  await admin.query("CREATE DATABASE inkloom_test_utf8 TEMPLATE template0 ENCODING 'UTF8' LC_COLLATE 'C' LC_CTYPE 'C'");
await admin.end();
const env = {
  ...process.env,
  TEMP: temporary,
  TMP: temporary,
  TMPDIR: temporary,
  PYTHONUTF8: "1",
  PYTHONDONTWRITEBYTECODE: "1",
  LANGSMITH_TRACING: "false",
  LANGCHAIN_TRACING_V2: "false",
  PYTHONPATH: resolve(root, "services/api"),
  DATABASE_URL: config.databaseUrl.replace(/\/[^/]+$/, "/inkloom_test_utf8"),
  DATABASE_ADMIN_URL: config.adminUrl.replace(/\/[^/]+$/, "/inkloom_test_utf8"),
};
const python =
  process.platform === "win32"
    ? ".venv/Scripts/python.exe"
    : ".venv/bin/python";
const child = spawn(
  resolve(root, python),
  [
    "-m",
    "pytest",
    "services/api/tests",
    "-q",
    "--tb=short",
    "--basetemp",
    ".cache/pytest-temp",
    "-o",
    "cache_dir=.cache/pytest",
    "--junitxml=.local/test-results/backend.xml",
    ...process.argv.slice(2),
  ],
  { cwd: root, env, stdio: "inherit" },
);
child.on("exit", (code) => process.exit(code ?? 1));
child.on("error", () => process.exit(1));
