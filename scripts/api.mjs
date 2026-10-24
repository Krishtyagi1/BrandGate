import { spawn } from "node:child_process";
import { mkdirSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const temporary = resolve(root, ".cache/tmp");
mkdirSync(temporary, { recursive: true });
const env = {
  ...process.env,
  TEMP: temporary,
  TMP: temporary,
  TMPDIR: temporary,
  PYTHONUTF8: "1",
  PYTHONDONTWRITEBYTECODE: "1",
  PYTHONPATH: resolve(root, "services/api"),
  LANGSMITH_TRACING: "false",
  LANGCHAIN_TRACING_V2: "false",
};
const python =
  process.platform === "win32"
    ? ".venv/Scripts/python.exe"
    : ".venv/bin/python";
const child = spawn(
  resolve(root, python),
  ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
  { cwd: root, env, stdio: "inherit" },
);
child.on("exit", (code) => process.exit(code ?? 1));
child.on("error", () => process.exit(1));
process.on("SIGINT", () => child.kill());
process.on("SIGTERM", () => child.kill());
