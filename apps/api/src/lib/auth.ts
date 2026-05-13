import jwt from "jsonwebtoken";
import type {
  AppPermission,
  AuthUser,
  LoginResponse,
  RefreshSessionResponse
} from "@mypos/domain";
import { appRepository } from "../data/app-state";
import type { ActionActor } from "../data/types";

interface AccessTokenClaims {
  sub: string;
  username: string;
  displayName: string;
  role: AuthUser["role"];
  branchId: string;
  exp: number;
  iat: number;
}

interface RefreshSessionRecord {
  user: AuthUser;
  permissions: AppPermission[];
  expiresAt: string;
}

export interface VerifiedSession {
  accessToken: string;
  expiresAt: string;
  user: AuthUser;
  permissions: AppPermission[];
}

const accessSecret = process.env.JWT_SECRET;
const refreshSecret = process.env.REFRESH_TOKEN_SECRET;

if (!accessSecret || accessSecret.includes("replace-with")) {
  throw new Error("JWT_SECRET environment variable is required and must not be a placeholder");
}

if (!refreshSecret || refreshSecret.includes("replace-with")) {
  throw new Error("REFRESH_TOKEN_SECRET environment variable is required and must not be a placeholder");
}
const refreshSessions = new Map<string, RefreshSessionRecord>();

setInterval(() => {
  const now = Date.now();
  for (const [tokenId, session] of refreshSessions.entries()) {
    if (new Date(session.expiresAt).getTime() < now) {
      refreshSessions.delete(tokenId);
    }
  }
}, 60 * 60 * 1000);

const toActor = (user: AuthUser): ActionActor => ({
  id: user.id,
  displayName: user.displayName,
  role: user.role
});

const buildAccessToken = (user: AuthUser) =>
  jwt.sign(
    {
      sub: user.id,
      username: user.username,
      displayName: user.displayName,
      role: user.role,
      branchId: user.branchId
    },
    accessSecret,
    { expiresIn: "8h" }
  );

const buildRefreshToken = (user: AuthUser) => {
  const tokenId = crypto.randomUUID();
  const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString();

  const token = jwt.sign(
    {
      sub: user.id,
      jti: tokenId
    },
    refreshSecret,
    { expiresIn: "7d" }
  );

  refreshSessions.set(tokenId, {
    user,
    permissions: appRepository.getPermissions(user.role),
    expiresAt
  });

  return {
    token,
    tokenId,
    expiresAt
  };
};

const issueSession = (user: AuthUser): RefreshSessionResponse => {
  const accessToken = buildAccessToken(user);
  const decoded = jwt.decode(accessToken) as AccessTokenClaims;
  const refreshToken = buildRefreshToken(user);

  return {
    session: {
      accessToken,
      refreshToken: refreshToken.token,
      expiresAt: new Date(decoded.exp * 1000).toISOString(),
      user
    },
    permissions: appRepository.getPermissions(user.role)
  };
};

export const loginWithCredentials = (username: string, pin: string): LoginResponse | null => {
  const user = appRepository.findUserByCredentials(username, pin);

  if (!user) {
    return null;
  }

  user.lastLoginAt = new Date().toISOString();
  const authUser = appRepository.getAuthUser(user);

  if (appRepository.requiresTwoFactor(authUser.role)) {
    const challenge = appRepository.createTwoFactorChallenge(authUser);
    appRepository.recordAuthEvent(toActor(authUser), "auth.challenge_issued", authUser.id);
    return { challenge };
  }

  const session = issueSession(authUser);
  appRepository.recordAuthEvent(toActor(authUser), "auth.login", authUser.id);
  return session;
};

export const verifyTwoFactorSession = (challengeId: string, code: string): LoginResponse | null => {
  const user = appRepository.verifyTwoFactorChallenge(challengeId, code);

  if (!user) {
    return null;
  }

  const session = issueSession(user);
  appRepository.recordAuthEvent(toActor(user), "auth.2fa_verified", user.id);
  return session;
};

export const verifyAccessToken = (token: string): VerifiedSession | null => {
  try {
    const claims = jwt.verify(token, accessSecret) as AccessTokenClaims;
    const userRecord = appRepository.getUserById(claims.sub);

    if (!userRecord) {
      return null;
    }

    const managedUser = appRepository.getManagedUsers().find((user) => user.id === claims.sub);

    if (!managedUser || managedUser.accountStatus !== "ACTIVE") {
      return null;
    }

    if (
      managedUser.forceLogoutAfter &&
      new Date(managedUser.forceLogoutAfter).getTime() > claims.iat * 1000
    ) {
      return null;
    }

    const user = appRepository.getAuthUser(userRecord);

    return {
      accessToken: token,
      expiresAt: new Date(claims.exp * 1000).toISOString(),
      user,
      permissions: appRepository.getPermissions(user.role)
    };
  } catch {
    return null;
  }
};

export const refreshAccessSession = (refreshToken: string): RefreshSessionResponse | null => {
  try {
    const decoded = jwt.verify(refreshToken, refreshSecret) as jwt.JwtPayload;
    const tokenId = decoded.jti;

    if (!tokenId) {
      return null;
    }

    const existing = refreshSessions.get(tokenId);

    if (!existing) {
      return null;
    }

    const managedUser = appRepository.getManagedUsers().find((user) => user.id === existing.user.id);

    if (!managedUser || managedUser.accountStatus !== "ACTIVE") {
      refreshSessions.delete(tokenId);
      return null;
    }

    refreshSessions.delete(tokenId);
    const session = issueSession(existing.user);
    appRepository.recordAuthEvent(toActor(existing.user), "auth.refresh", existing.user.id);
    return session;
  } catch {
    return null;
  }
};

export const revokeRefreshToken = (refreshToken: string) => {
  try {
    const decoded = jwt.verify(refreshToken, refreshSecret) as jwt.JwtPayload;
    const tokenId = decoded.jti;

    if (!tokenId) {
      return false;
    }

    const existing = refreshSessions.get(tokenId);
    refreshSessions.delete(tokenId);

    if (existing) {
      appRepository.recordAuthEvent(toActor(existing.user), "auth.logout", existing.user.id);
    }

    return true;
  } catch {
    return false;
  }
};

export const revokeAllRefreshTokensForUser = (userId: string) => {
  for (const [tokenId, session] of refreshSessions.entries()) {
    if (session.user.id === userId) {
      refreshSessions.delete(tokenId);
    }
  }
};
