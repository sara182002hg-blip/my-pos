import type {
  LoginRequest,
  RefreshSessionRequest,
  UserRole,
  VerifyTwoFactorRequest
} from "@mypos/domain";
import type { FastifyInstance } from "fastify";
import { appRepository } from "../data/app-state";
import {
  loginWithCredentials,
  refreshAccessSession,
  revokeRefreshToken,
  verifyTwoFactorSession
} from "../lib/auth";
import { requireAuth } from "../lib/guards";

export const registerAuthRoutes = async (app: FastifyInstance) => {
  app.post<{ Body: LoginRequest }>("/api/auth/login", {
    config: {
      rateLimit: {
        max: 10,
        timeWindow: "1 minute",
        errorResponseBuilder: () => ({ message: "Too many login attempts. Please wait a minute." })
      }
    }
  }, async (request, reply) => {
    const session = loginWithCredentials(request.body.username, request.body.pin);

    if (!session) {
      reply.status(401);
      return { message: "Invalid username or PIN" };
    }

    return session;
  });

  app.post<{ Body: VerifyTwoFactorRequest }>("/api/auth/verify-2fa", {
    config: {
      rateLimit: {
        max: 5,
        timeWindow: "1 minute",
        errorResponseBuilder: () => ({ message: "Too many 2FA attempts. Please wait a minute." })
      }
    }
  }, async (request, reply) => {
    const session = verifyTwoFactorSession(request.body.challengeId, request.body.code);

    if (!session) {
      reply.status(401);
      return { message: "Invalid 2FA code" };
    }

    return session;
  });

  app.post<{ Body: RefreshSessionRequest }>("/api/auth/refresh", async (request, reply) => {
    const session = refreshAccessSession(request.body.refreshToken);

    if (!session) {
      reply.status(401);
      return { message: "Invalid refresh token" };
    }

    return session;
  });

  app.post<{ Body: RefreshSessionRequest }>("/api/auth/logout", async (request, reply) => {
    const revoked = revokeRefreshToken(request.body.refreshToken);

    if (!revoked) {
      reply.status(400);
      return { message: "Refresh token not recognized" };
    }

    return { message: "Logged out" };
  });

  app.get("/api/auth/me", async (request, reply) => {
    const session = requireAuth(request, reply);

    if (!session) {
      return { message: "Unauthorized" };
    }

    return {
      session: {
        accessToken: session.accessToken,
        refreshToken: "",
        expiresAt: session.expiresAt,
        user: session.user
      },
      permissions: session.permissions
    };
  });

  app.get<{ Params: { role: UserRole } }>("/api/security/permissions/:role", async (request, reply) => {
    const session = requireAuth(request, reply);

    if (!session) {
      return { message: "Unauthorized" };
    }

    return {
      role: request.params.role,
      permissions: appRepository.getPermissions(request.params.role)
    };
  });
};
