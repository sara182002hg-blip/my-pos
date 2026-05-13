import "dotenv/config";
import { runPilotSmoke } from "./lib/pilot-smoke-runner.ts";

runPilotSmoke()
  .then((result) => {
    console.log(JSON.stringify(result, null, 2));
  })
  .catch((error) => {
    console.error(
      JSON.stringify(
        {
          ok: false,
          message: "Smoke pilot script crashed",
          details: String(error)
        },
        null,
        2
      )
    );
    process.exitCode = 1;
  });
