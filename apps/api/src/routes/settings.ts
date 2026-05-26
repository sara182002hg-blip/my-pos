import type { UpdateStoreSettingsRequest } from "@mypos/domain";
import type { FastifyInstance } from "fastify";
import { settingsStore } from "../lib/settings-store";
import { requirePermission } from "../lib/guards";

export const registerSettingsRoutes = async (app: FastifyInstance) => {
  // GET /api/settings — ดึงค่า settings ทั้งหมด (Manager+)
  app.get("/api/settings", async (request, reply) => {
    const session = requirePermission(request, reply, "system.manage");
    if (!session) return;

    const branchId = session.user.branchId;
    const settings = await settingsStore.getAll(branchId);
    return { settings };
  });

  // PUT /api/settings — อัปเดต settings (Manager+)
  app.put<{ Body: UpdateStoreSettingsRequest }>("/api/settings", async (request, reply) => {
    const session = requirePermission(request, reply, "system.manage");
    if (!session) return;

    const branchId = session.user.branchId;
    await settingsStore.setMany(branchId, request.body);

    const settings = await settingsStore.getAll(branchId);
    return { settings };
  });
};
