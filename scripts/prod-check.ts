import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

type CheckResult = {
  name: string;
  ok: boolean;
  detail: string;
  severity: "blocker" | "warning";
};

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

  return !value.includes("replace-with") && !value.includes("example.com");
}

function areConfigured(values: Array<string | undefined>) {
  return values.every((value) => isConfigured(value));
}

function isHttpsUrl(value: string | undefined) {
  return Boolean(value?.startsWith("https://"));
}

function hasValidPrinterMap(value: string | undefined) {
  if (!isConfigured(value)) {
    return false;
  }

  try {
    const parsed = JSON.parse(value!) as Record<string, { host?: string; port?: number | string }>;
    return Object.values(parsed).some((entry) => entry.host && !Number.isNaN(Number(entry.port ?? 9100)));
  } catch {
    return value!
      .split(",")
      .map((entry) => entry.trim())
      .some((entry) => /^[^=]+=[^:]+:\d{2,5}$/.test(entry));
  }
}

async function main() {
  const root = process.cwd();
  const envArgIndex = process.argv.findIndex((arg) => arg === "--env");
  const envPath = envArgIndex >= 0 && process.argv[envArgIndex + 1]
    ? path.resolve(root, process.argv[envArgIndex + 1])
    : path.join(root, ".env");
  const env = parseEnvFile(envPath);

  const checks: CheckResult[] = [
    {
      name: "env-file",
      ok: existsSync(envPath),
      detail: existsSync(envPath) ? envPath : ".env missing",
      severity: "blocker"
    },
    {
      name: "node-env",
      ok: env.NODE_ENV === "production",
      detail: env.NODE_ENV || "missing",
      severity: "warning"
    },
    {
      name: "database-url",
      ok: isConfigured(env.DATABASE_URL),
      detail: env.DATABASE_URL || "missing",
      severity: "blocker"
    },
    {
      name: "redis-url",
      ok: isConfigured(env.REDIS_URL),
      detail: env.REDIS_URL || "missing",
      severity: "warning"
    },
    {
      name: "jwt-secrets",
      ok: isConfigured(env.JWT_SECRET) && isConfigured(env.REFRESH_TOKEN_SECRET),
      detail:
        isConfigured(env.JWT_SECRET) && isConfigured(env.REFRESH_TOKEN_SECRET)
          ? "configured"
          : "placeholder or missing",
      severity: "blocker"
    },
    {
      name: "payment-webhook-secret",
      ok: isConfigured(env.PAYMENT_WEBHOOK_SECRET),
      detail: isConfigured(env.PAYMENT_WEBHOOK_SECRET) ? "configured" : "placeholder or missing",
      severity: "blocker"
    },
    {
      name: "api-url-https",
      ok: isHttpsUrl(env.VITE_API_BASE_URL) && isConfigured(env.VITE_API_BASE_URL),
      detail: env.VITE_API_BASE_URL || "missing",
      severity: "warning"
    },
    {
      name: "checkout-url-https",
      ok: isHttpsUrl(env.PAYMENT_CHECKOUT_BASE_URL) && isConfigured(env.PAYMENT_CHECKOUT_BASE_URL),
      detail: env.PAYMENT_CHECKOUT_BASE_URL || "missing",
      severity: "warning"
    },
    {
      name: "promptpay-provider",
      ok:
        env.PAYMENT_PROMPTPAY_PROVIDER === "PROMPTPAY_REAL" &&
        areConfigured([env.PROMPTPAY_MERCHANT_ID, env.PROMPTPAY_MERCHANT_PHONE]),
      detail: env.PAYMENT_PROMPTPAY_PROVIDER || "missing",
      severity: "blocker"
    },
    {
      name: "card-provider",
      ok:
        (env.PAYMENT_CARD_PROVIDER === "OMISE_REAL" &&
          areConfigured([env.OMISE_PUBLIC_KEY, env.OMISE_SECRET_KEY])) ||
        (env.PAYMENT_CARD_PROVIDER === "2C2P_REAL" &&
          areConfigured([env.TWOC2P_MERCHANT_ID, env.TWOC2P_SECRET_KEY])),
      detail: env.PAYMENT_CARD_PROVIDER || "missing",
      severity: "blocker"
    },
    {
      name: "email-provider",
      ok:
        env.RECEIPT_EMAIL_PROVIDER === "SMTP" &&
        areConfigured([env.SMTP_HOST, env.SMTP_FROM, env.SMTP_USER, env.SMTP_PASS]),
      detail: env.RECEIPT_EMAIL_PROVIDER || "missing",
      severity: "blocker"
    },
    {
      name: "line-provider",
      ok:
        env.RECEIPT_LINE_PROVIDER === "LINE_OA" &&
        isConfigured(env.LINE_CHANNEL_ACCESS_TOKEN) &&
        isHttpsUrl(env.LINE_API_BASE),
      detail: env.RECEIPT_LINE_PROVIDER || "missing",
      severity: "blocker"
    },
    {
      name: "print-provider",
      ok: env.RECEIPT_PRINT_PROVIDER === "TCP_PRINTER" && hasValidPrinterMap(env.PRINTER_TCP_MAP),
      detail: env.RECEIPT_PRINT_PROVIDER || "missing",
      severity: "warning"
    },
    {
      name: "etax-provider",
      ok:
        env.ETAX_PROVIDER === "RD_REAL" &&
        isHttpsUrl(env.RD_API_BASE) &&
        areConfigured([env.RD_CLIENT_ID, env.RD_CLIENT_SECRET]),
      detail: env.ETAX_PROVIDER || "missing",
      severity: "warning"
    }
  ];

  const blockers = checks.filter((check) => !check.ok && check.severity === "blocker");
  const warnings = checks.filter((check) => !check.ok && check.severity === "warning");

  console.log(
    JSON.stringify(
      {
        ok: blockers.length === 0,
        readyForProduction: blockers.length === 0,
        blockerCount: blockers.length,
        warningCount: warnings.length,
        blockers,
        warnings,
        checks
      },
      null,
      2
    )
  );

  if (blockers.length > 0) {
    process.exitCode = 1;
  }
}

main().catch((error) => {
  console.error(
    JSON.stringify(
      {
        ok: false,
        message: "Production readiness check crashed",
        details: String(error)
      },
      null,
      2
    )
  );
  process.exitCode = 1;
});
