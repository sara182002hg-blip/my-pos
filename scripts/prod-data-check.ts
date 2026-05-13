import { PrismaClient } from "@prisma/client";
import { existsSync, readFileSync } from "node:fs";
import net from "node:net";
import path from "node:path";

type CheckResult = {
  name: string;
  ok: boolean;
  detail: string;
};

function parseEnvFile(filePath: string) {
  const values: Record<string, string> = {};

  if (!existsSync(filePath)) {
    return values;
  }

  for (const line of readFileSync(filePath, "utf8").split(/\r?\n/)) {
    const trimmed = line.trim();

    if (!trimmed || trimmed.startsWith("#")) {
      continue;
    }

    const separatorIndex = trimmed.indexOf("=");

    if (separatorIndex <= 0) {
      continue;
    }

    values[trimmed.slice(0, separatorIndex).trim()] = trimmed.slice(separatorIndex + 1).trim();
  }

  return values;
}

function isConfigured(value: string | undefined) {
  return Boolean(value) && !value!.includes("replace-with") && !value!.includes("example.com");
}

async function checkPostgres(databaseUrl: string | undefined): Promise<CheckResult> {
  if (!isConfigured(databaseUrl)) {
    return {
      name: "postgres",
      ok: false,
      detail: "DATABASE_URL is missing or still a placeholder"
    };
  }

  const prisma = new PrismaClient({
    datasources: {
      db: {
        url: databaseUrl
      }
    }
  });

  try {
    await prisma.$queryRaw`SELECT 1`;
    return {
      name: "postgres",
      ok: true,
      detail: "reachable"
    };
  } catch (error) {
    return {
      name: "postgres",
      ok: false,
      detail: error instanceof Error ? error.message : "connection failed"
    };
  } finally {
    await prisma.$disconnect();
  }
}

function checkRedis(redisUrl: string | undefined): Promise<CheckResult> {
  if (!isConfigured(redisUrl)) {
    return Promise.resolve({
      name: "redis",
      ok: false,
      detail: "REDIS_URL is missing or still a placeholder"
    });
  }

  return new Promise((resolve) => {
    const url = new URL(redisUrl!);
    const socket = new net.Socket();
    const port = Number(url.port || "6379");
    const host = url.hostname;

    const finish = (result: CheckResult) => {
      socket.destroy();
      resolve(result);
    };

    socket.setTimeout(3000);
    socket.once("connect", () => {
      finish({
        name: "redis",
        ok: true,
        detail: `${host}:${port} reachable`
      });
    });
    socket.once("timeout", () => {
      finish({
        name: "redis",
        ok: false,
        detail: `${host}:${port} timeout`
      });
    });
    socket.once("error", (error) => {
      finish({
        name: "redis",
        ok: false,
        detail: error.message
      });
    });
    socket.connect(port, host);
  });
}

async function main() {
  const envArgIndex = process.argv.findIndex((arg) => arg === "--env");
  const envPath =
    envArgIndex >= 0 && process.argv[envArgIndex + 1]
      ? path.resolve(process.cwd(), process.argv[envArgIndex + 1])
      : path.resolve(process.cwd(), ".env");
  const env = parseEnvFile(envPath);
  const checks = await Promise.all([checkPostgres(env.DATABASE_URL), checkRedis(env.REDIS_URL)]);
  const ok = checks.every((check) => check.ok);

  console.log(
    JSON.stringify(
      {
        ok,
        envPath,
        checks
      },
      null,
      2
    )
  );

  if (!ok) {
    process.exitCode = 1;
  }
}

main().catch((error) => {
  console.error(
    JSON.stringify(
      {
        ok: false,
        message: "Production data check crashed",
        details: String(error)
      },
      null,
      2
    )
  );
  process.exitCode = 1;
});
