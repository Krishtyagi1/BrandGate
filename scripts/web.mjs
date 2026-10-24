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
  NEXT_TELEMETRY_DISABLED: "1",
  NEXT_DISABLE_SWC_WASM: "1",
};
const command = process.argv[2] || "dev";
await import('./editor-assets.mjs');
const executable =
  command === "typecheck" ? "typescript/bin/tsc" : "next/dist/bin/next";
const args =
  command === "typecheck"
    ? ["--noEmit"]
    : command === "dev" || command === "start"
      ? [command, "--hostname", "127.0.0.1"]
      : [command];
const child = spawn(
  process.execPath,
  [resolve(root, "node_modules", executable), ...args],
  { cwd: resolve(root, "apps/web"), env, stdio: "inherit" },
);
child.on("exit", (code) => process.exit(code ?? 1));
child.on("error", () => process.exit(1));
process.on("SIGINT", () => child.kill());
process.on("SIGTERM", () => child.kill());
