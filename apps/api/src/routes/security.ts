import type {
  CreateUserAccountRequest,
  ManagedUserFeedResponse,
  SecurityPolicyResponse,
  UpdateSecurityPolicyRequest,
  UpdateUserAccountRequest
} from "@mypos/domain";
import type { FastifyInstance } from "fastify";
import { appRepository } from "../data/app-state";
import { revokeAllRefreshTokensForUser } from "../lib/auth";
import { asDownloadFilename, toCsv } from "../lib/csv";
import { requirePermission } from "../lib/guards";

export const registerSecurityRoutes = async (app: FastifyInstance) => {
  app.get("/api/security/policy", async (request, reply) => {
    const session = requirePermission(request, reply, "audit.view");

    if (!session) {
      return { message: "Forbidden" };
    }

    const response: SecurityPolicyResponse = {
      policy: appRepository.getSecurityPolicy()
    };

    return response;
  });

  app.get("/api/security/users", async (request, reply) => {
    const session = requirePermission(request, reply, "audit.view");

    if (!session) {
      return { message: "Forbidden" };
    }

    const response: ManagedUserFeedResponse = {
      users: appRepository.getManagedUsers()
    };

    return response;
  });

  app.get("/api/security/export.csv", async (request, reply) => {
    const session = requirePermission(request, reply, "audit.view");

    if (!session) {
      return { message: "Forbidden" };
    }

    const policy = appRepository.getSecurityPolicy();
    const rows = [
      {
        section: "security_policy",
        adminIpWhitelist: policy.adminIpWhitelist.join("|"),
        twoFactorRoles: policy.twoFactorRoles.join("|"),
        receiptBusinessName: policy.receiptTemplate.businessName,
        receiptBranchLabel: policy.receiptTemplate.branchLabel,
        receiptFooterMessage: policy.receiptTemplate.footerMessage,
        receiptContactLine: policy.receiptTemplate.contactLine ?? "",
        showQrLookupOnPrint: policy.receiptTemplate.showQrLookupOnPrint,
        showTipLine: policy.receiptTemplate.showTipLine
      },
      ...appRepository.getManagedUsers().map((user) => ({
        section: "managed_user",
        id: user.id,
        username: user.username,
        displayName: user.displayName,
        role: user.role,
        branchId: user.branchId,
        accountStatus: user.accountStatus,
        expiresAt: user.expiresAt ?? "",
        blockedAt: user.blockedAt ?? "",
        forceLogoutAfter: user.forceLogoutAfter ?? "",
        lastLoginAt: user.lastLoginAt ?? ""
      }))
    ];

    reply.header("content-type", "text/csv; charset=utf-8");
    reply.header("content-disposition", `attachment; filename="${asDownloadFilename("security")}"`);
    return toCsv(rows);
  });

  app.post<{ Body: CreateUserAccountRequest }>("/api/security/users", async (request, reply) => {
    const session = requirePermission(request, reply, "system.manage");

    if (!session) {
      return { message: "Forbidden" };
    }

    const user = appRepository.createUserAccount(request.body, {
      id: session.user.id,
      displayName: session.user.displayName,
      role: session.user.role
    });

    if (!user) {
      reply.status(400);
      return { message: "Could not create user account" };
    }

    return { user };
  });

  app.post<{ Params: { userId: string }; Body: UpdateUserAccountRequest }>(
    "/api/security/users/:userId",
    async (request, reply) => {
      const session = requirePermission(request, reply, "system.manage");

      if (!session) {
        return { message: "Forbidden" };
      }

      const user = appRepository.updateUserAccount(request.params.userId, request.body, {
        id: session.user.id,
        displayName: session.user.displayName,
        role: session.user.role
      });

      if (!user) {
        reply.status(404);
        return { message: "User not found" };
      }

      if (user.accountStatus !== "ACTIVE") {
        revokeAllRefreshTokensForUser(user.id);
      }

      return { user };
    }
  );

  app.post<{ Params: { userId: string } }>("/api/security/users/:userId/force-logout", async (request, reply) => {
    const session = requirePermission(request, reply, "system.manage");

    if (!session) {
      return { message: "Forbidden" };
    }

    const user = appRepository.forceLogoutUser(request.params.userId, {
      id: session.user.id,
      displayName: session.user.displayName,
      role: session.user.role
    });

    if (!user) {
      reply.status(404);
      return { message: "User not found" };
    }

    revokeAllRefreshTokensForUser(user.id);
    return { user };
  });

  app.post<{ Body: UpdateSecurityPolicyRequest }>("/api/security/policy", async (request, reply) => {
    const session = requirePermission(request, reply, "system.manage");

    if (!session) {
      return { message: "Forbidden" };
    }

    const policy = appRepository.updateSecurityPolicy(request.body, {
      id: session.user.id,
      displayName: session.user.displayName,
      role: session.user.role
    });

    return { policy };
  });
};
