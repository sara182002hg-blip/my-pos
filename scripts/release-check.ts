import { spawnSync } from "node:child_process";

type StepResult = {
  name: string;
  ok: boolean;
  exitCode: number | null;
};

function runStep(name: string, command: string, args: string[], allowFailure = false): StepResult {
  const commandArgs = process.platform === "win32" ? ["/d", "/s", "/c", command, ...args] : args;
  const commandName = process.platform === "win32" ? "cmd.exe" : command;
  const result = spawnSync(commandName, commandArgs, {
    cwd: process.cwd(),
    encoding: "utf8"
  });

  const ok = result.status === 0;

  if (result.stdout?.trim()) {
    console.log(result.stdout.trim());
  }

  if (result.stderr?.trim()) {
    console.error(result.stderr.trim());
  }

  if (result.error) {
    console.error(String(result.error));
  }

  if (!ok && !allowFailure) {
    throw new Error(`${name} failed with exit code ${result.status ?? "unknown"}`);
  }

  return {
    name,
    ok,
    exitCode: result.status
  };
}

const main = () => {
  const npmCommand = "npm";
  const steps = [
    runStep("typecheck", npmCommand, ["run", "typecheck"]),
    runStep("build:pos-console", npmCommand, ["run", "build", "--workspace", "@mypos/pos-console"]),
    runStep("build:kds", npmCommand, ["run", "build", "--workspace", "@mypos/kds"]),
    runStep("build:customer-qr", npmCommand, ["run", "build", "--workspace", "@mypos/customer-qr"]),
    runStep("smoke:all", npmCommand, ["run", "smoke:all"]),
    runStep("prod:check", npmCommand, ["run", "prod:check"], true)
  ];

  const hardFailures = steps.filter((step) => !step.ok && step.name !== "prod:check");
  const prodReady = steps.find((step) => step.name === "prod:check")?.ok === true;

  console.log(
    JSON.stringify(
      {
        ok: hardFailures.length === 0,
        readyForPilot: hardFailures.length === 0,
        readyForProduction: prodReady,
        steps
      },
      null,
      2
    )
  );

  if (hardFailures.length > 0) {
    process.exitCode = 1;
  }
};

try {
  main();
} catch (error) {
  console.error(
    JSON.stringify(
      {
        ok: false,
        message: "Release check failed",
        details: String(error)
      },
      null,
      2
    )
  );
  process.exitCode = 1;
}
