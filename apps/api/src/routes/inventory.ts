import type {
  InventoryOverviewResponse,
  RecordStockMovementRequest
} from "@mypos/domain";
import type { FastifyInstance } from "fastify";
import { appRepository } from "../data/app-state";
import { requirePermission } from "../lib/guards";

export const registerInventoryRoutes = async (app: FastifyInstance) => {
  app.get("/api/inventory/overview", async (request, reply) => {
    const session = requirePermission(request, reply, "menu.manage");

    if (!session) {
      return { message: "Forbidden" };
    }

    const response: InventoryOverviewResponse = {
      overview: appRepository.getInventoryOverview()
    };

    return response;
  });

  app.post<{ Body: RecordStockMovementRequest }>("/api/inventory/movements", async (request, reply) => {
    const session = requirePermission(request, reply, "menu.manage");

    if (!session) {
      return { message: "Forbidden" };
    }

    const result = appRepository.recordStockMovement(request.body, {
      id: session.user.id,
      displayName: session.user.displayName,
      role: session.user.role
    });

    if (!result) {
      reply.status(400);
      return { message: "Could not record stock movement" };
    }

    return result;
  });
};
