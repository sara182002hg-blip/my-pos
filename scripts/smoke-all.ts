import "dotenv/config";
import { runPilotSmoke, runResetDemoSmoke } from "./lib/pilot-smoke-runner.ts";

const main = async () => {
  const pilot = await runPilotSmoke();
  const resetDemo = await runResetDemoSmoke();

  console.log(
    JSON.stringify(
      {
        ok: true,
        pilot,
        resetDemo
      },
      null,
      2
    )
  );
};

main().catch((error) => {
  console.error(
    JSON.stringify(
      {
        ok: false,
        message: "Smoke all script crashed",
        details: String(error)
      },
      null,
      2
    )
  );
  process.exitCode = 1;
});
