import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import pg from "pg";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../..");
const runtime = path.join(root, ".runtime");
const dataDir = path.join(runtime, "postgres");
const logFile = path.join(runtime, "postgres.log");
const binDir = path.join(here, "node_modules", "@embedded-postgres", "windows-x64", "native", "bin");
const initdb = path.join(binDir, "initdb.exe");
const pgCtl = path.join(binDir, "pg_ctl.exe");
const port = Number(process.env.NATIVE_POSTGRES_PORT ?? "55432");
const password = process.env.POSTGRES_PASSWORD;

if (!password) {
  console.error("POSTGRES_PASSWORD must be loaded from .runtime/native.env");
  process.exit(2);
}

fs.mkdirSync(runtime, { recursive: true });

function run(executable, args, allowFailure = false) {
  const result = spawnSync(executable, args, {
    cwd: root,
    stdio: "inherit",
    env: { ...process.env, PGPASSWORD: password },
  });
  if (!allowFailure && result.status !== 0) process.exit(result.status ?? 1);
  return result.status ?? 1;
}

async function ensureDatabase() {
  const client = new pg.Client({ host: "127.0.0.1", port, user: "honeypot", password, database: "postgres" });
  await client.connect();
  const result = await client.query("SELECT 1 FROM pg_database WHERE datname = $1", ["honeypot"]);
  if (result.rowCount === 0) await client.query("CREATE DATABASE honeypot");
  await client.end();
}

const action = process.argv[2];
if (action === "init") {
  if (!fs.existsSync(path.join(dataDir, "PG_VERSION"))) {
    run(initdb, [
      `--pgdata=${dataDir}`,
      "--username=honeypot",
      `--pwfile=${path.join(runtime, "postgres-password")}`,
      "--auth-host=scram-sha-256",
      "--auth-local=trust",
      "--encoding=UTF8",
      "--locale=C",
    ]);
  }
} else if (action === "start") {
  if (!fs.existsSync(path.join(dataDir, "PG_VERSION"))) {
    console.error("PostgreSQL is not initialized. Run scripts/native-infra.ps1 setup first.");
    process.exit(2);
  }
  const status = run(pgCtl, ["status", "-D", dataDir], true);
  if (status !== 0) {
    run(pgCtl, ["start", "-D", dataDir, "-l", logFile, "-w", "-o", `-p ${port} -h 127.0.0.1`]);
  }
  await ensureDatabase();
  console.log(`PostgreSQL is ready on 127.0.0.1:${port}.`);
} else if (action === "stop") {
  const status = run(pgCtl, ["status", "-D", dataDir], true);
  if (status === 0) run(pgCtl, ["stop", "-D", dataDir, "-m", "fast", "-w"]);
} else if (action === "status") {
  process.exitCode = run(pgCtl, ["status", "-D", dataDir], true);
} else {
  console.error("Usage: node postgres.mjs <init|start|stop|status>");
  process.exit(2);
}
