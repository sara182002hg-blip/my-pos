import "dotenv/config";
import Fastify, { type FastifyError } from "fastify";
import cors from "@fastify/cors";
import rateLimit from "@fastify/rate-limit";
import websocket from "@fastify/websocket";
import { initializeAppState } from "./data/app-state";
import { verifyAccessToken } from "./lib/auth";
import { registerLiveSocket } from "./lib/realtime";
import { registerAuthRoutes } from "./routes/auth";
import { registerCrmRoutes } from "./routes/crm";
import { registerDeliveryRoutes } from "./routes/delivery";
import { registerHrRoutes } from "./routes/hr";
import { registerInventoryRoutes } from "./routes/inventory";
import { registerMenuRoutes } from "./routes/menu";
import { registerOperationRoutes } from "./routes/operations";
import { registerOverviewRoutes } from "./routes/overview";
import { registerPublicRoutes } from "./routes/public";
import { registerSecurityRoutes } from "./routes/security";
import { registerSettingsRoutes } from "./routes/settings";
import { registerStaffRoutes } from "./routes/staff";

const isProduction = process.env.NODE_ENV === "production";

const app = Fastify({
  logger: true,
  trustProxy: true
});

const port = Number(process.env.PORT ?? 4000);

await initializeAppState(app.log);

// CORS: production restricts to CORS_ORIGIN env var; dev allows all
const allowedOrigins = process.env.CORS_ORIGIN
  ? process.env.CORS_ORIGIN.split(",").map((o) => o.trim())
  : ["http://localhost:3000", "http://localhost:5173", "http://localhost:4173"];

await app.register(cors, {
  origin: isProduction ? allowedOrigins : true,
  credentials: true
});

// Global rate limit — per-route overrides (e.g. auth) take precedence
await app.register(rateLimit, {
  global: true,
  max: 300,
  timeWindow: "1 minute",
  keyGenerator: (request) => request.ip,
  errorResponseBuilder: () => ({
    statusCode: 429,
    error: "Too Many Requests",
    message: "Rate limit exceeded. Please slow down."
  })
});

await app.register(websocket);

// Hide internal error details in production
app.setErrorHandler((error: FastifyError, request, reply) => {
  const status = error.statusCode ?? 500;

  if (status >= 500) {
    app.log.error({ err: error, reqId: request.id, url: request.url }, "Unhandled error");
  }

  reply.status(status).send({
    statusCode: status,
    error: error.name ?? "Error",
    message: isProduction && status >= 500 ? "Internal Server Error" : error.message
  });
});

// Graceful shutdown — gives in-flight requests time to complete
const shutdown = (signal: string) => {
  app.log.info({ signal }, "Shutting down");
  app.close().then(() => process.exit(0)).catch((closeErr: unknown) => {
    app.log.error(closeErr, "Error during shutdown");
    process.exit(1);
  });
};

process.on("SIGTERM", () => shutdown("SIGTERM"));
process.on("SIGINT", () => shutdown("SIGINT"));

app.get("/health", {
  config: { rateLimit: { max: 60, timeWindow: "1 minute" } }
}, async () => ({
  status: "ok",
  service: "mypos-api",
  timestamp: new Date().toISOString()
}));

await registerAuthRoutes(app);
await registerOverviewRoutes(app);
await registerCrmRoutes(app);
await registerDeliveryRoutes(app);
await registerHrRoutes(app);
await registerInventoryRoutes(app);
await registerMenuRoutes(app);
await registerOperationRoutes(app);
await registerPublicRoutes(app);
await registerSecurityRoutes(app);
await registerSettingsRoutes(app);
await registerStaffRoutes(app);

app.get("/ws/live", { websocket: true }, (socket, request) => {
  const query = request.query as { token?: string; kds_key?: string };

  // KDS terminals authenticate with a static API key instead of a JWT
  const expectedKdsKey = process.env.KDS_API_KEY;
  if (expectedKdsKey && query.kds_key === expectedKdsKey) {
    registerLiveSocket(socket);
    return;
  }

  const token = query.token ?? request.headers.authorization?.slice("Bearer ".length).trim();
  if (!token || !verifyAccessToken(token)) {
    socket.close(4401, "Unauthorized");
    return;
  }

  registerLiveSocket(socket);
});

app.listen({ host: "0.0.0.0", port }).catch((error) => {
  app.log.error(error);
  process.exit(1);
});
