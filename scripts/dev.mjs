import { spawn } from "node:child_process";
import { mkdirSync } from "node:fs";
import { resolve } from "node:path";
import { startDatabase, root } from "./database.mjs";
import './editor-assets.mjs';

mkdirSync(resolve(root, ".cache/tmp"), { recursive: true });
const env = {
  ...process.env,
  TEMP: resolve(root, ".cache/tmp"),
  TMP: resolve(root, ".cache/tmp"),
  NEXT_TELEMETRY_DISABLED: "1",
  PYTHONUTF8: "1",
  PYTHONDONTWRITEBYTECODE: "1",
  TMPDIR: resolve(root, ".cache/tmp"),
  LANGSMITH_TRACING: "false",
  LANGCHAIN_TRACING_V2: "false",
  PYTHONPATH: resolve(root, "services/api"),
  PIP_CACHE_DIR: resolve(root, ".cache/pip"),
  PLAYWRIGHT_BROWSERS_PATH: resolve(root, ".cache/playwright"),
};
const { database, config } = await startDatabase();
env.DATABASE_URL = config.databaseUrl;
env.DATABASE_ADMIN_URL = config.adminUrl;
const python =
  process.platform === "win32"
    ? resolve(root, ".venv/Scripts/python.exe")
    : resolve(root, ".venv/bin/python");
const api = spawn(
  python,
  ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
  { cwd: root, env, stdio: "inherit" },
);
const web = spawn(
  process.execPath,
  [
    resolve(root, "node_modules/next/dist/bin/next"),
    "dev",
    "--hostname",
    "127.0.0.1",
  ],
  { cwd: resolve(root, "apps/web"), env, stdio: "inherit" },
);
let stopping = false;
async function stop(code = 0) {
  if (stopping) return;
  stopping = true;
  api.kill();
  web.kill();
  await database.stop();
  process.exit(code);
}
api.on("exit", (code) => {
  if (!stopping) stop(code ?? 1);
});
web.on("exit", (code) => {
  if (!stopping) stop(code ?? 1);
});
process.on("SIGINT", () => stop());
process.on("SIGTERM", () => stop());
