import "dotenv/config";
import { mkdirSync } from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

const backupDir = path.resolve(process.cwd(), "backups");
const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
const outputPath = path.join(backupDir, `mypos-${timestamp}.sql`);

if (process.argv.includes("--help")) {
  console.log("Usage: npm run db:backup");
  process.exit(0);
}

if (!process.env.DATABASE_URL?.trim()) {
  console.error("DATABASE_URL is required for db:backup");
  process.exit(1);
}

mkdirSync(backupDir, { recursive: true });

const result = spawnSync("pg_dump", [process.env.DATABASE_URL, "--file", outputPath, "--no-owner"], {
  cwd: process.cwd(),
  stdio: "inherit",
  shell: process.platform === "win32"
});

if (result.status !== 0) {
  console.error(`pg_dump failed with exit code ${result.status ?? "unknown"}`);
  process.exit(result.status ?? 1);
}

console.log(
  JSON.stringify(
    {
      ok: true,
      outputPath
    },
    null,
    2
  )
);
