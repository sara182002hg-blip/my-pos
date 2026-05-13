import type { AssignMemberRequest, CreateMemberRequest } from "@mypos/domain";
import type { FastifyInstance } from "fastify";
import { appRepository } from "../data/app-state";
import { asDownloadFilename, toCsv } from "../lib/csv";
import { requireAuth, requirePermission } from "../lib/guards";
import { broadcastSnapshot } from "../lib/realtime";

export const registerCrmRoutes = async (app: FastifyInstance) => {
  app.get("/api/members", async (request, reply) => {
    const session = requireAuth(request, reply);

    if (!session) {
      return { message: "Unauthorized" };
    }

    const canView =
      session.permissions.includes("sales.view_today") ||
      session.permissions.includes("sales.view_all") ||
      session.permissions.includes("payments.capture");

    if (!canView) {
      reply.status(403);
      return { message: "Forbidden" };
    }

    return {
      members: appRepository.getMembers()
    };
  });

  app.get("/api/crm/overview", async (request, reply) => {
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
      overview: appRepository.getCrmOverview()
    };
  });

  app.get("/api/members/export.csv", async (request, reply) => {
    const session = requireAuth(request, reply);

    if (!session) {
      return { message: "Unauthorized" };
    }

    const canView =
      session.permissions.includes("sales.view_today") ||
      session.permissions.includes("sales.view_all") ||
      session.permissions.includes("payments.capture");

    if (!canView) {
      reply.status(403);
      return { message: "Forbidden" };
    }

    const overview = appRepository.getCrmOverview();
    const rows = [
      {
        section: "crm_summary",
        generatedAt: overview.generatedAt,
        totalMembers: overview.totalMembers,
        loyaltyOutstandingPoints: overview.loyaltyOutstandingPoints,
        activeMembersThisMonth: overview.activeMembersThisMonth
      },
      ...appRepository.getMembers().map((member) => ({
        section: "member",
        id: member.id,
        fullName: member.fullName,
        phone: member.phone,
        tier: member.tier,
        pointsBalance: member.pointsBalance,
        totalSpend: member.totalSpend,
        lastVisitAt: member.lastVisitAt ?? "",
        favoriteItems: member.favoriteItems.join("|"),
        preferredLanguage: member.preferredLanguage ?? "",
        birthDate: member.birthDate ?? "",
        lineUserId: member.lineUserId ?? ""
      })),
      ...overview.topMembers.map((member) => ({
        section: "top_member",
        id: member.id,
        fullName: member.fullName,
        tier: member.tier,
        pointsBalance: member.pointsBalance,
        totalSpend: member.totalSpend
      })),
      ...overview.birthdayMembers.map((member) => ({
        section: "birthday_member",
        id: member.id,
        fullName: member.fullName,
        birthDate: member.birthDate ?? "",
        preferredLanguage: member.preferredLanguage ?? ""
      }))
    ];

    reply.header("content-type", "text/csv; charset=utf-8");
    reply.header("content-disposition", `attachment; filename="${asDownloadFilename("crm-members")}"`);
    return toCsv(rows);
  });

  app.post<{ Body: CreateMemberRequest }>("/api/members", async (request, reply) => {
    const session = requirePermission(request, reply, "orders.manage");

    if (!session) {
      return { message: "Forbidden" };
    }

    const member = appRepository.createMember(request.body, {
      id: session.user.id,
      displayName: session.user.displayName,
      role: session.user.role
    });

    return {
      member
    };
  });

  app.post<{ Params: { orderId: string }; Body: AssignMemberRequest }>(
    "/api/orders/:orderId/assign-member",
    async (request, reply) => {
      const session = requirePermission(request, reply, "orders.manage");

      if (!session) {
        return { message: "Forbidden" };
      }

      const result = appRepository.assignMemberToOrder(
        request.params.orderId,
        request.body.memberId,
        {
          id: session.user.id,
          displayName: session.user.displayName,
          role: session.user.role
        }
      );

      if (!result) {
        reply.status(400);
        return { message: "Could not assign member" };
      }

      broadcastSnapshot();

      return result;
    }
  );
};
