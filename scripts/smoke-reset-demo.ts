import "dotenv/config";
import { runResetDemoSmoke } from "./lib/pilot-smoke-runner.ts";

runResetDemoSmoke()
  .then((result) => {
    console.log(JSON.stringify(result, null, 2));
  })
  .catch((error) => {
    console.error(
      JSON.stringify(
        {
          ok: false,
          message: "Smoke reset-demo script crashed",
          details: String(error)
        },
        null,
        2
      )
    );
    process.exitCode = 1;
  });
