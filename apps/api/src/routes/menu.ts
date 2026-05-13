import type {
  CreateMenuItemRequest,
  UpdateMenuItemRequest
} from "@mypos/domain";
import type { FastifyInstance } from "fastify";
import { appRepository } from "../data/app-state";
import { asDownloadFilename, toCsv } from "../lib/csv";
import { broadcastSnapshot } from "../lib/realtime";
import { requirePermission } from "../lib/guards";

export const registerMenuRoutes = async (app: FastifyInstance) => {
  app.get("/api/menu/export.csv", async (request, reply) => {
    const session = requirePermission(request, reply, "menu.manage");

    if (!session) {
      return { message: "Forbidden" };
    }

    const rows = appRepository.getSnapshot().menu.map((item) => ({
      id: item.id,
      category: item.category,
      name: item.name,
      price: item.price,
      happyHourPrice: item.happyHourPrice ?? "",
      inStock: item.inStock,
      tags: item.tags.join("|"),
      allergenInfo: item.allergenInfo?.join("|") ?? "",
      imageUrl: item.imageUrl,
      description: item.description ?? "",
      translationTh: item.translations?.th?.name ?? "",
      translationEn: item.translations?.en?.name ?? "",
      translationZh: item.translations?.zh?.name ?? "",
      translationJa: item.translations?.ja?.name ?? "",
      modifierGroups: item.modifierGroups?.map((group) => group.name).join("|") ?? ""
    }));

    reply.header("content-type", "text/csv; charset=utf-8");
    reply.header("content-disposition", `attachment; filename="${asDownloadFilename("menu")}"`);
    return toCsv(rows);
  });

  app.post<{ Body: CreateMenuItemRequest }>("/api/menu", async (request, reply) => {
    const session = requirePermission(request, reply, "menu.manage");

    if (!session) {
      return { message: "Forbidden" };
    }

    const menuItem = appRepository.createMenuItem(request.body, {
      id: session.user.id,
      displayName: session.user.displayName,
      role: session.user.role
    });

    broadcastSnapshot();

    return {
      message: "Menu item created",
      menuItem
    };
  });

  app.post<{ Params: { menuItemId: string }; Body: UpdateMenuItemRequest }>(
    "/api/menu/:menuItemId",
    async (request, reply) => {
      const session = requirePermission(request, reply, "menu.manage");

      if (!session) {
        return { message: "Forbidden" };
      }

      const menuItem = appRepository.updateMenuItem(request.params.menuItemId, request.body, {
        id: session.user.id,
        displayName: session.user.displayName,
        role: session.user.role
      });

      if (!menuItem) {
        reply.status(404);
        return { message: "Menu item not found" };
      }

      broadcastSnapshot();

      return {
        message: "Menu item updated",
        menuItem
      };
    }
  );
};
