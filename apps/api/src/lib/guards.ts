import type { AppPermission } from "@mypos/domain";
import type { FastifyReply, FastifyRequest } from "fastify";
import { appRepository } from "../data/app-state";
import { verifyAccessToken, type VerifiedSession } from "./auth";

const getBearerToken = (authorization?: string) => {
  if (!authorization?.startsWith("Bearer ")) {
    return null;
  }

  return authorization.slice("Bearer ".length).trim();
};

export const requireAuth = (request: FastifyRequest, reply: FastifyReply): VerifiedSession | null => {
  const token = getBearerToken(request.headers.authorization);

  if (!token) {
    reply.status(401);
    return null;
  }

  const session = verifyAccessToken(token);

  if (!session) {
    reply.status(401);
    return null;
  }

  return session;
};

export const requirePermission = (
  request: FastifyRequest,
  reply: FastifyReply,
  permission: AppPermission
) => {
  const session = requireAuth(request, reply);

  if (!session) {
    return null;
  }

  if (!session.permissions.includes(permission)) {
    reply.status(403);
    return null;
  }

  const sensitivePermissions: AppPermission[] = [
    "audit.view",
    "hr.view",
    "sales.view_all",
    "system.manage"
  ];

  if (
    sensitivePermissions.includes(permission) &&
    (session.user.role === "OWNER" || session.user.role === "MANAGER") &&
    !appRepository.isAdminIpAllowed(request.ip)
  ) {
    reply.status(403);
    return null;
  }

  return session;
};
