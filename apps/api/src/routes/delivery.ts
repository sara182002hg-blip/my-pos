import type {
  DeliveryMenuSyncRequest,
  DeliveryPlatform,
  DeliveryPlatformToggleRequest
} from "@mypos/domain";
import type { FastifyInstance } from "fastify";
import { appRepository } from "../data/app-state";
import { asDownloadFilename, toCsv } from "../lib/csv";
import { requireAuth, requirePermission } from "../lib/guards";

export const registerDeliveryRoutes = async (app: FastifyInstance) => {
  app.get("/api/delivery/overview", async (request, reply) => {
    const session = requireAuth(request, reply);

    if (!session) {
      return { message: "Unauthorized" };
    }

    const canView =
      session.permissions.includes("sales.view_today") ||
      session.permissions.includes("sales.view_all");

    if (!canView) {
      reply.status(403);
      return { message: "Forbidden" };
    }

    return {
      center: appRepository.getDeliveryCenterSnapshot()
    };
  });

  app.get("/api/delivery/export.csv", async (request, reply) => {
    const session = requireAuth(request, reply);

    if (!session) {
      return { message: "Unauthorized" };
    }

    const canView =
      session.permissions.includes("sales.view_today") ||
      session.permissions.includes("sales.view_all");

    if (!canView) {
      reply.status(403);
      return { message: "Forbidden" };
    }

    const center = appRepository.getDeliveryCenterSnapshot();
    const rows = [
      {
        section: "delivery_summary",
        generatedAt: center.generatedAt,
        grossSales: center.summary.grossSales,
        commissionTotal: center.summary.commissionTotal,
        activeOrders: center.summary.activeOrders,
        avgEtaMinutes: center.summary.avgEtaMinutes
      },
      ...center.platforms.map((platform) => ({
        section: "delivery_platform",
        platform: platform.platform,
        displayName: platform.displayName,
        enabled: platform.enabled,
        acceptsOrders: platform.acceptsOrders,
        menuSyncState: platform.menuSyncState,
        lastSyncAt: platform.lastSyncAt ?? "",
        commissionRate: platform.commissionRate
      })),
      ...center.orders.map((order) => ({
        section: "delivery_order",
        id: order.id,
        platform: order.platform,
        externalOrderNo: order.externalOrderNo,
        customerName: order.customerName,
        status: order.status,
        placedAt: order.placedAt,
        etaMinutes: order.etaMinutes,
        totalAmount: order.totalAmount,
        commissionAmount: order.commissionAmount,
        branchStatus: order.branchStatus,
        items: order.items.map((item) => `${item.name} x${item.quantity}`).join(" | ")
      }))
    ];

    reply.header("content-type", "text/csv; charset=utf-8");
    reply.header("content-disposition", `attachment; filename="${asDownloadFilename("delivery-center")}"`);
    return toCsv(rows);
  });

  app.post<{ Params: { platform: DeliveryPlatform }; Body: DeliveryPlatformToggleRequest }>(
    "/api/delivery/platforms/:platform/toggle",
    async (request, reply) => {
      const session = requirePermission(request, reply, "menu.manage");

      if (!session) {
        return { message: "Forbidden" };
      }

      const platform = appRepository.toggleDeliveryPlatform(
        request.params.platform,
        request.body.enabled,
        {
          id: session.user.id,
          displayName: session.user.displayName,
          role: session.user.role
        }
      );

      if (!platform) {
        reply.status(404);
        return { message: "Platform not found" };
      }

      return { platform };
    }
  );

  app.post<{ Params: { platform: DeliveryPlatform }; Body: DeliveryMenuSyncRequest }>(
    "/api/delivery/platforms/:platform/sync-menu",
    async (request, reply) => {
      const session = requirePermission(request, reply, "menu.manage");

      if (!session) {
        return { message: "Forbidden" };
      }

      const platform = appRepository.syncDeliveryPlatformMenu(request.params.platform, {
        id: session.user.id,
        displayName: session.user.displayName,
        role: session.user.role
      });

      if (!platform) {
        reply.status(404);
        return { message: "Platform not found" };
      }

      return {
        platform,
        propagatedOutOfStock: Boolean(request.body.propagateOutOfStock)
      };
    }
  );
};
