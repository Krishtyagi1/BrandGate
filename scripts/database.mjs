import EmbeddedPostgres from "embedded-postgres";
import pg from "pg";
import { randomBytes } from "node:crypto";
import {
  existsSync,
  mkdirSync,
  readFileSync,
  writeFileSync,
  appendFileSync,
} from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

export const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
export async function startDatabase() {
  const temporary = resolve(root, ".cache/tmp");
  mkdirSync(temporary, { recursive: true });
  process.env.TEMP = temporary;
  process.env.TMP = temporary;
  process.env.TMPDIR = temporary;
  const local = resolve(root, ".local");
  mkdirSync(local, { recursive: true });
  const file = resolve(local, "runtime.json");
  let config;
  if (existsSync(file)) config = JSON.parse(readFileSync(file, "utf8"));
  else {
    const adminPassword = randomBytes(24).toString("hex");
    const appPassword = randomBytes(24).toString("hex");
    config = {
      adminPassword,
      appPassword,
      adminUrl: `postgresql://postgres:${adminPassword}@127.0.0.1:54329/inkloom`,
      databaseUrl: `postgresql://inkloom_app:${appPassword}@127.0.0.1:54329/inkloom`,
    };
    writeFileSync(file, JSON.stringify(config), { mode: 0o600 });
  }
  const log = (message) =>
    appendFileSync(resolve(local, "postgres.log"), `${message}\n`);
  const database = new EmbeddedPostgres({
    databaseDir: resolve(local, "postgres"),
    user: "postgres",
    password: config.adminPassword,
    port: 54329,
    persistent: true,
    authMethod: "scram-sha-256",
    postgresFlags: ["-h", "127.0.0.1"],
    onLog: log,
    onError: log,
  });
  if (!existsSync(resolve(local, "postgres/PG_VERSION")))
    await database.initialise();
  await database.start();
  const client = new pg.Client({
    connectionString: config.adminUrl.replace(/\/[^/]+$/, "/postgres"),
  });
  await client.connect();
  if (
    !(await client.query("SELECT 1 FROM pg_roles WHERE rolname='inkloom_app'"))
      .rowCount
  ) {
    await client.query(
      `CREATE ROLE inkloom_app LOGIN PASSWORD '${config.appPassword}' NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS`,
    );
  }
  if (
    !(await client.query("SELECT 1 FROM pg_database WHERE datname='inkloom'"))
      .rowCount
  )
    await client.query("CREATE DATABASE inkloom TEMPLATE template0 ENCODING 'UTF8' LC_COLLATE 'C' LC_CTYPE 'C'");
  await client.end();
  console.log("PostgreSQL ready on 127.0.0.1:54329 (project-local data).");
  return { database, config };
}
if (
  process.argv[1] &&
  resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  const { database } = await startDatabase();
  const stop = async () => {
    await database.stop();
    process.exit(0);
  };
  process.on("SIGINT", stop);
  process.on("SIGTERM", stop);
}
