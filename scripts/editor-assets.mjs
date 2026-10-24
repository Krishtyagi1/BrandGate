import { cpSync, mkdirSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const source = resolve(root, "node_modules/@superdoc/docx-engine/dist");
const target = resolve(root, "apps/web/public/vendor/docx-engine");
mkdirSync(target, { recursive: true });
cpSync(source, target, {
  recursive: true,
  filter: (p) => !p.endsWith(".d.ts"),
});
const manifest = JSON.parse(
  readFileSync(resolve(source, "manifest.json"), "utf8"),
);
mkdirSync(resolve(root, "apps/web/lib"), { recursive: true });
const { writeFileSync } = await import("node:fs");
writeFileSync(
  resolve(root, "apps/web/lib/editor-runtime.json"),
  JSON.stringify({
    documentWorker: "/vendor/docx-engine/" + manifest.domWorkerRelativePath,
  }),
);
console.log("Pinned editor runtime assets copied inside the project.");
