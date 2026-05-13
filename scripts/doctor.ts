import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

type CheckResult = {
  name: string;
  ok: boolean;
  detail: string;
};

function runCommand(command: string, args: string[]) {
  const result = spawnSync(command, args, {
    encoding: "utf8",
    shell: false
  });

  return {
    ok: result.status === 0,
    stdout: result.stdout?.trim() ?? "",
    stderr: result.stderr?.trim() ?? ""
  };
}

function parseEnvFile(filePath: string) {
  const values: Record<string, string> = {};

  if (!existsSync(filePath)) {
    return values;
  }

  const lines = readFileSync(filePath, "utf8").split(/\r?\n/);

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) {
      continue;
    }

    const separatorIndex = trimmed.indexOf("=");
    if (separatorIndex <= 0) {
      continue;
    }

    const key = trimmed.slice(0, separatorIndex).trim();
    const value = trimmed.slice(separatorIndex + 1).trim();
    values[key] = value;
  }

  return values;
}

function isConfigured(value: string | undefined) {
  if (!value) {
    return false;
  }

  return !value.includes("replace-with");
}

async function checkUrl(name: string, url: string): Promise<CheckResult> {
  try {
    const response = await fetch(url);
    return {
      name,
      ok: response.ok,
      detail: `${response.status} ${url}`
    };
  } catch (error) {
    return {
      name,
      ok: false,
      detail: error instanceof Error ? error.message : `unreachable ${url}`
    };
  }
}

async function main() {
  const root = process.cwd();
  const envPath = path.join(root, ".env");
  const env = parseEnvFile(envPath);

  const checks: CheckResult[] = [];

  const nodeVersion = process.version;
  checks.push({
    name: "node",
    ok: true,
    detail: nodeVersion
  });

  const docker = runCommand("powershell", ["-NoProfile", "-Command", "docker --version"]);
  checks.push({
    name: "docker",
    ok: docker.ok,
    detail: docker.ok ? docker.stdout : "Docker not available"
  });

  checks.push({
    name: "env-file",
    ok: existsSync(envPath),
    detail: existsSync(envPath) ? envPath : ".env missing"
  });

  checks.push({
    name: "jwt-secrets",
    ok: isConfigured(env.JWT_SECRET) && isConfigured(env.REFRESH_TOKEN_SECRET),
    detail: isConfigured(env.JWT_SECRET) && isConfigured(env.REFRESH_TOKEN_SECRET) ? "configured" : "placeholder or missing"
  });

  checks.push({
    name: "database-url",
    ok: Boolean(env.DATABASE_URL),
    detail: env.DATABASE_URL || "missing"
  });

  checks.push({
    name: "payment-webhook-secret",
    ok: isConfigured(env.PAYMENT_WEBHOOK_SECRET),
    detail: isConfigured(env.PAYMENT_WEBHOOK_SECRET) ? "configured" : "placeholder or missing"
  });

  const emailProvider = env.RECEIPT_EMAIL_PROVIDER || "INTERNAL_EMAIL_QUEUE";
  const lineProvider = env.RECEIPT_LINE_PROVIDER || "LINE_OA_STUB";
  const printProvider = env.RECEIPT_PRINT_PROVIDER || "LOCAL_PRINTER_STUB";

  checks.push({
    name: "email-provider",
    ok: emailProvider !== "SMTP" || Boolean(env.SMTP_HOST && env.SMTP_FROM),
    detail: emailProvider
  });

  checks.push({
    name: "line-provider",
    ok: lineProvider !== "LINE_OA" || Boolean(env.LINE_CHANNEL_ACCESS_TOKEN),
    detail: lineProvider
  });

  checks.push({
    name: "print-provider",
    ok: printProvider !== "TCP_PRINTER" || Boolean(env.PRINTER_TCP_MAP),
    detail: printProvider
  });

  checks.push(await checkUrl("api-health", "http://127.0.0.1:4000/health"));
  checks.push(await checkUrl("pos-ui", "http://127.0.0.1:5173"));
  checks.push(await checkUrl("kds-ui", "http://127.0.0.1:5174"));
  checks.push(await checkUrl("qr-ui", "http://127.0.0.1:3000"));

  const readyForPilot =
    checks.find((check) => check.name === "env-file")?.ok === true &&
    checks.find((check) => check.name === "jwt-secrets")?.ok === true &&
    checks.find((check) => check.name === "api-health")?.ok === true &&
    checks.find((check) => check.name === "pos-ui")?.ok === true &&
    checks.find((check) => check.name === "kds-ui")?.ok === true &&
    checks.find((check) => check.name === "qr-ui")?.ok === true;

  const warnings = checks.filter((check) => !check.ok && !["api-health", "pos-ui", "kds-ui", "qr-ui", "env-file", "jwt-secrets"].includes(check.name));

  const summary = {
    ok: readyForPilot,
    readyForPilot,
    warnings,
    checks
  };

  console.log(JSON.stringify(summary, null, 2));

  if (!readyForPilot) {
    process.exitCode = 1;
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
