import type { AppPermission, UserRole } from "@mypos/domain";
import type { FastifyReply, FastifyRequest } from "fastify";
import { appRepository } from "../data/app-state";
import { verifyAccessToken, type VerifiedSession } from "./auth";

export interface KitchenActor {
  id: string;
  displayName: string;
  role: UserRole;
}

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

// Accepts either a valid JWT (orders.manage) or a static KDS_API_KEY header.
// Used for kitchen action routes so KDS terminals don't need a login session.
export const requireKdsOrPermission = (
  request: FastifyRequest,
  reply: FastifyReply,
  permission: AppPermission
): { id: string; displayName: string; role: UserRole } | null => {
  const expectedKey = process.env.KDS_API_KEY;
  const sentKey = request.headers["x-kds-key"];

  if (expectedKey && sentKey === expectedKey) {
    return { id: "kds-terminal", displayName: "KDS Terminal", role: "KITCHEN" };
  }

  const session = requirePermission(request, reply, permission);
  return session
    ? { id: session.user.id, displayName: session.user.displayName, role: session.user.role }
    : null;
};
