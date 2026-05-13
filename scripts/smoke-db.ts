import "dotenv/config";
import { spawnSync } from "node:child_process";
import { runPilotSmoke } from "./lib/pilot-smoke-runner.ts";

const runStep = (label: string, command: string, args: string[]) => {
  const result = spawnSync(command, args, {
    cwd: process.cwd(),
    stdio: "inherit",
    shell: true,
    env: process.env
  });

  if (result.status !== 0) {
    throw new Error(`${label} failed with exit code ${result.status ?? "unknown"}`);
  }
};

const main = async () => {
  if (!process.env.DATABASE_URL?.trim()) {
    throw new Error("DATABASE_URL is required for smoke:db");
  }

  runStep("Prisma db push", "npx", ["prisma", "db", "push", "--skip-generate"]);
  runStep("Prisma seed", "npx", ["tsx", "prisma/seed.ts"]);

  const result = await runPilotSmoke();
  console.log(JSON.stringify({ mode: "db", ...result }, null, 2));
};

main().catch((error) => {
  console.error(
    JSON.stringify(
      {
        ok: false,
        message: "Smoke DB script crashed",
        details: String(error)
      },
      null,
      2
    )
  );
  process.exitCode = 1;
});
