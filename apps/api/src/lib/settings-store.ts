/**
 * settings-store.ts
 * ──────────────────
 * Singleton key-value store backed by the `StoreSetting` Prisma table.
 * Falls back to process.env when Prisma is not connected (dev/demo mode).
 *
 * Sensitive values (passwords, tokens, secret keys) are stored in DB as-is
 * but returned to the UI masked as "***SET***" so they are never exposed.
 */

import type { StoreSettings } from "@mypos/domain";
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyPrismaClient = any;

// Keys that must be masked when returned to the UI
const SENSITIVE_KEYS = new Set<keyof StoreSettings>([
  "lineChannelAccessToken",
  "smtpPass",
  "omiseSecretKey",
  "twoc2pSecretKey",
  "paymentWebhookSecret",
]);

const MASKED = "***SET***";

// Mapping: StoreSettings field → process.env fallback key
const ENV_FALLBACK: Record<keyof StoreSettings, string | null> = {
  storeName:                "STORE_NAME",
  storeAddress:             "STORE_ADDRESS",
  storeTaxId:               "STORE_TAX_ID",
  storePhone:               "STORE_PHONE",
  promptpayMerchantId:      "PROMPTPAY_MERCHANT_ID",
  promptpayPhone:           "PROMPTPAY_MERCHANT_PHONE",
  lineChannelAccessToken:   "LINE_CHANNEL_ACCESS_TOKEN",
  smtpHost:                 "SMTP_HOST",
  smtpPort:                 "SMTP_PORT",
  smtpUser:                 "SMTP_USER",
  smtpPass:                 "SMTP_PASS",
  smtpFrom:                 "SMTP_FROM",
  cardProvider:             "PAYMENT_CARD_PROVIDER",
  omisePublicKey:           "OMISE_PUBLIC_KEY",
  omiseSecretKey:           "OMISE_SECRET_KEY",
  twoc2pMerchantId:         "TWOC2P_MERCHANT_ID",
  twoc2pSecretKey:          "TWOC2P_SECRET_KEY",
  paymentWebhookSecret:     "PAYMENT_WEBHOOK_SECRET",
  printerTcpMap:            "PRINTER_TCP_MAP",
  printerMode:              "PRINTER_TCP_MODE",
  receiptBusinessName:      null,
  receiptBranchLabel:       null,
  receiptFooterMessage:     null,
  receiptContactLine:       null,
};

class SettingsStore {
  private prisma: AnyPrismaClient | null = null;
  /** branchId → key → rawValue (unmasked) */
  private cache = new Map<string, Map<string, string>>();

  setPrisma(client: AnyPrismaClient) {
    this.prisma = client;
  }

  /** Load all settings for a branch from DB into cache */
  async warmUp(branchId: string) {
    if (!this.prisma) return;
    const rows = await this.prisma.storeSetting.findMany({ where: { branchId } });
    const map = new Map<string, string>();
    for (const row of rows) map.set(row.key, row.value);
    this.cache.set(branchId, map);
  }

  /** Get raw (unmasked) value for a key. Falls back to process.env. */
  getRaw(branchId: string, key: keyof StoreSettings): string {
    const cached = this.cache.get(branchId)?.get(key);
    if (cached !== undefined) return cached;
    const envKey = ENV_FALLBACK[key];
    if (envKey) return process.env[envKey]?.trim() ?? "";
    return "";
  }

  /** Get all settings for a branch, masking sensitive fields */
  async getAll(branchId: string): Promise<StoreSettings> {
    if (this.prisma && !this.cache.has(branchId)) {
      await this.warmUp(branchId);
    }

    const raw = (key: keyof StoreSettings) => this.getRaw(branchId, key);
    const masked = (key: keyof StoreSettings) => {
      const v = raw(key);
      return v ? MASKED : "";
    };

    return {
      storeName:              raw("storeName"),
      storeAddress:           raw("storeAddress"),
      storeTaxId:             raw("storeTaxId"),
      storePhone:             raw("storePhone"),
      promptpayMerchantId:    raw("promptpayMerchantId"),
      promptpayPhone:         raw("promptpayPhone"),
      lineChannelAccessToken: masked("lineChannelAccessToken"),
      smtpHost:               raw("smtpHost"),
      smtpPort:               raw("smtpPort"),
      smtpUser:               raw("smtpUser"),
      smtpPass:               masked("smtpPass"),
      smtpFrom:               raw("smtpFrom"),
      cardProvider:           raw("cardProvider") as StoreSettings["cardProvider"],
      omisePublicKey:         raw("omisePublicKey"),
      omiseSecretKey:         masked("omiseSecretKey"),
      twoc2pMerchantId:       raw("twoc2pMerchantId"),
      twoc2pSecretKey:        masked("twoc2pSecretKey"),
      paymentWebhookSecret:   masked("paymentWebhookSecret"),
      printerTcpMap:          raw("printerTcpMap"),
      printerMode:            (raw("printerMode") || "TEXT") as StoreSettings["printerMode"],
      receiptBusinessName:    raw("receiptBusinessName"),
      receiptBranchLabel:     raw("receiptBranchLabel"),
      receiptFooterMessage:   raw("receiptFooterMessage"),
      receiptContactLine:     raw("receiptContactLine"),
    };
  }

  /** Persist a batch of settings. Skips masked placeholder values (user didn't change them). */
  async setMany(branchId: string, updates: Partial<StoreSettings>) {
    const branchCache = this.cache.get(branchId) ?? new Map<string, string>();

    for (const [rawKey, value] of Object.entries(updates)) {
      const key = rawKey as keyof StoreSettings;
      // Skip if user sent back the mask — means "no change"
      if (value === MASKED) continue;
      if (typeof value !== "string") continue;

      branchCache.set(key, value);

      if (this.prisma) {
        await this.prisma.storeSetting.upsert({
          where: { branchId_key: { branchId, key } },
          create: { branchId, key, value },
          update: { value },
        });
      }
    }

    this.cache.set(branchId, branchCache);
  }

  /** Invalidate cache for a branch (force re-load from DB next request) */
  invalidate(branchId: string) {
    this.cache.delete(branchId);
  }
}

export const settingsStore = new SettingsStore();
