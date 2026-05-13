import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { randomBytes } from "node:crypto";
import path from "node:path";

const root = process.cwd();
const envPath = path.join(root, ".env");
const envExamplePath = path.join(root, ".env.example");

if (existsSync(envPath)) {
  console.log(
    JSON.stringify(
      {
        ok: true,
        created: false,
        path: envPath,
        detail: ".env already exists"
      },
      null,
      2
    )
  );
  process.exit(0);
}

const template = readFileSync(envExamplePath, "utf8");

const jwtSecret = randomBytes(64).toString("hex");
const refreshSecret = randomBytes(64).toString("hex");
const webhookSecret = randomBytes(32).toString("hex");

const envFile = template
  .replace("JWT_SECRET=", `JWT_SECRET=${jwtSecret}`)
  .replace("REFRESH_TOKEN_SECRET=", `REFRESH_TOKEN_SECRET=${refreshSecret}`)
  .replace("PAYMENT_WEBHOOK_SECRET=replace-with-payment-webhook-secret", `PAYMENT_WEBHOOK_SECRET=${webhookSecret}`);

writeFileSync(envPath, envFile, "utf8");

console.log(
  JSON.stringify(
    {
      ok: true,
      created: true,
      path: envPath
    },
    null,
    2
  )
);
