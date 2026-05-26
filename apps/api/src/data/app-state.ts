import type { FastifyBaseLogger } from "fastify";
import { MemoryAppRepository } from "./memory-repository";
import { PrismaPersistenceAdapter } from "./prisma-persistence";
import { connectPrismaClient, loadStateFromPrisma } from "./prisma-bootstrap";
import { settingsStore } from "../lib/settings-store";

export const appRepository = new MemoryAppRepository();

export const initializeAppState = async (logger?: FastifyBaseLogger) => {
  const prisma = await connectPrismaClient();

  if (!prisma) {
    appRepository.setPersistenceAdapter(null);
    appRepository.resetDemoState();
    logger?.info("App state using in-memory seed data");
    return;
  }

  settingsStore.setPrisma(prisma);
  appRepository.setPersistenceAdapter(new PrismaPersistenceAdapter(prisma));
  const prismaState = await loadStateFromPrisma(prisma);

  if (prismaState) {
    appRepository.hydrate(prismaState);
    logger?.info("App state bootstrapped from Prisma");
    return;
  }

  logger?.info("Prisma connected but bootstrap data unavailable, continuing with in-memory seed data");
};
