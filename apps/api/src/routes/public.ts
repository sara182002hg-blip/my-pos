import type {
  PublicCheckBillRequest,
  PublicOrderRequest,
  PublicTableResponse
} from "@mypos/domain";
import type { FastifyInstance } from "fastify";
import { appRepository } from "../data/app-state";
import { broadcastSnapshot } from "../lib/realtime";

export const registerPublicRoutes = async (app: FastifyInstance) => {
  app.get<{ Params: { tableId: string } }>("/api/public/tables/:tableId", async (request, reply) => {
    const session = appRepository.getPublicTableSession(request.params.tableId);

    if (!session) {
      reply.status(404);
      return { message: "Table not found" };
    }

    const response: PublicTableResponse = {
      table: session.table,
      menu: appRepository.getSnapshot().menu.filter((item) => item.inStock),
      orders: session.orders
    };

    return response;
  });

  app.post<{ Params: { tableId: string } }>("/api/public/tables/:tableId/lock", async (request, reply) => {
    const table = appRepository.lockTableForQr(request.params.tableId);

    if (!table) {
      reply.status(404);
      return { message: "Table not found" };
    }

    broadcastSnapshot();
    return { table };
  });

  app.post<{ Params: { tableId: string }; Body: PublicOrderRequest }>(
    "/api/public/tables/:tableId/orders",
    {
      config: {
        rateLimit: {
          max: 5,
          timeWindow: "1 minute",
          errorResponseBuilder: () => ({ message: "Too many orders. Please wait before placing another." })
        }
      }
    },
    async (request, reply) => {
      const order = appRepository.createPublicOrder(request.params.tableId, request.body);

      if (!order) {
        reply.status(400);
        return { message: "Could not create QR order" };
      }

      broadcastSnapshot();
      return { order };
    }
  );

  app.post<{ Params: { tableId: string }; Body: PublicCheckBillRequest }>(
    "/api/public/tables/:tableId/check-bill",
    async (request, reply) => {
      const table = appRepository.requestCheckBill(request.params.tableId, request.body);

      if (!table) {
        reply.status(404);
        return { message: "Table not found" };
      }

      broadcastSnapshot();
      return { table };
    }
  );
};
