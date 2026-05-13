import "dotenv/config";
import { existsSync } from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

const backupPath = process.argv[2] ? path.resolve(process.cwd(), process.argv[2]) : "";

if (process.argv.includes("--help")) {
  console.log("Usage: npm run db:restore -- backups/mypos-YYYY.sql");
  process.exit(0);
}

if (!process.env.DATABASE_URL?.trim()) {
  console.error("DATABASE_URL is required for db:restore");
  process.exit(1);
}

if (!backupPath || !existsSync(backupPath)) {
  console.error("Usage: npm run db:restore -- backups/mypos-YYYY.sql");
  process.exit(1);
}

const result = spawnSync("psql", [process.env.DATABASE_URL, "--file", backupPath], {
  cwd: process.cwd(),
  stdio: "inherit",
  shell: process.platform === "win32"
});

if (result.status !== 0) {
  console.error(`psql restore failed with exit code ${result.status ?? "unknown"}`);
  process.exit(result.status ?? 1);
}

console.log(
  JSON.stringify(
    {
      ok: true,
      restoredFrom: backupPath
    },
    null,
    2
  )
);
