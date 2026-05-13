import "dotenv/config";
import Fastify from "fastify";
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
import { registerStaffRoutes } from "./routes/staff";

const app = Fastify({
  logger: true
});

const port = Number(process.env.PORT ?? 4000);

await initializeAppState(app.log);

await app.register(cors, {
  origin: true
});

await app.register(rateLimit, {
  global: false
});

await app.register(websocket);

app.get("/health", async () => ({
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
await registerStaffRoutes(app);

app.get("/ws/live", { websocket: true }, (socket, request) => {
  const query = request.query as { token?: string };
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
