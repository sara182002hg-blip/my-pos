import { timingSafeEqual } from "node:crypto";
import type {
  CreatePaymentSessionRequest,
  OrderTicket,
  PaymentGatewayProvider,
  PaymentSessionStatus,
  PaymentSessionSummary
} from "@mypos/domain";
import { settingsStore } from "./settings-store";

// branchId is injected via context when available; fall back to well-known demo id
let _activeBranchId = "BR-TH-001";
export const setActiveBranchId = (id: string) => { _activeBranchId = id; };

const getSetting = (key: Parameters<typeof settingsStore.getRaw>[1]) =>
  settingsStore.getRaw(_activeBranchId, key);

const getProviderForMethod = (
  method: CreatePaymentSessionRequest["method"]
): PaymentGatewayProvider => {
  if (method === "PROMPTPAY") {
    const v = getSetting("cardProvider"); // PromptPay always REAL when merchant configured
    const merchantId = getSetting("promptpayMerchantId");
    if (merchantId) return "PROMPTPAY_REAL";
    return ((process.env.PAYMENT_PROMPTPAY_PROVIDER ?? "PROMPTPAY_STUB").trim().toUpperCase() ||
      "PROMPTPAY_STUB") as PaymentGatewayProvider;
  }

  if (method === "CARD") {
    const provider = getSetting("cardProvider") ||
      process.env.PAYMENT_CARD_PROVIDER?.trim().toUpperCase() ||
      "OMISE_STUB";
    return (provider || "OMISE_STUB") as PaymentGatewayProvider;
  }

  if (method === "RABBIT_LINE_PAY") {
    return "RABBIT_LINE_PAY_STUB";
  }

  return "TRUE_MONEY_STUB";
};

const buildReference = (orderId: string, method: CreatePaymentSessionRequest["method"]) =>
  `${method}-${orderId}-${Date.now()}`;

const requireSetting = (key: Parameters<typeof settingsStore.getRaw>[1], label: string) => {
  const value = getSetting(key) || process.env[label]?.trim();
  if (!value || value.includes("replace-with")) {
    throw new Error(`${label} is required — กรุณาตั้งค่าใน Settings ของแอพ`);
  }
  return value;
};

const assertProviderConfig = (
  provider: PaymentGatewayProvider,
  method: CreatePaymentSessionRequest["method"]
) => {
  if (provider === "PROMPTPAY_REAL") {
    requireSetting("promptpayMerchantId", "PROMPTPAY_MERCHANT_ID");
    requireSetting("promptpayPhone", "PROMPTPAY_MERCHANT_PHONE");
    return;
  }

  if (provider === "OMISE_REAL") {
    requireSetting("omisePublicKey", "OMISE_PUBLIC_KEY");
    requireSetting("omiseSecretKey", "OMISE_SECRET_KEY");
    return;
  }

  if (provider === "2C2P_REAL") {
    requireSetting("twoc2pMerchantId", "TWOC2P_MERCHANT_ID");
    requireSetting("twoc2pSecretKey", "TWOC2P_SECRET_KEY");
    return;
  }

  if (method === "CARD" && provider !== "OMISE_STUB" && provider !== "TWOC2P_STUB") {
    throw new Error(`Unsupported card provider: ${provider}`);
  }
};

const normalizeWebhookEvent = (event: string): PaymentSessionStatus | null => {
  const normalized = event.trim().toUpperCase().replace(/[\s-]+/g, "_");

  if (["CAPTURED", "PAID", "SUCCESS", "SUCCEEDED", "COMPLETED"].includes(normalized)) {
    return "CAPTURED";
  }

  if (["FAILED", "FAIL", "DECLINED", "CANCELLED", "CANCELED"].includes(normalized)) {
    return "FAILED";
  }

  if (["EXPIRED", "TIMEOUT", "TIMED_OUT"].includes(normalized)) {
    return "EXPIRED";
  }

  return null;
};

const toSafeBuffer = (value: string) => Buffer.from(value, "utf8");

export const validatePaymentWebhookSecret = (providedSecret?: string | string[]) => {
  const expectedSecret = getSetting("paymentWebhookSecret") || process.env.PAYMENT_WEBHOOK_SECRET?.trim();
  const providedValue = Array.isArray(providedSecret) ? providedSecret[0] : providedSecret;
  const candidate = providedValue?.trim();

  if (!expectedSecret || !candidate) {
    return false;
  }

  const expectedBuffer = toSafeBuffer(expectedSecret);
  const candidateBuffer = toSafeBuffer(candidate);

  if (expectedBuffer.length !== candidateBuffer.length) {
    return false;
  }

  return timingSafeEqual(expectedBuffer, candidateBuffer);
};

export const parsePaymentWebhookPayload = (payload: {
  sessionId?: string;
  reference?: string;
  provider?: PaymentGatewayProvider;
  event?: string;
  amount?: number;
  message?: string;
}) => {
  const sessionId = payload.sessionId?.trim() || undefined;
  const reference = payload.reference?.trim() || undefined;
  const status = payload.event ? normalizeWebhookEvent(payload.event) : null;

  if (!status || (!sessionId && !reference)) {
    return null;
  }

  return {
    sessionId,
    reference,
    provider: payload.provider,
    status,
    amount: payload.amount,
    message: payload.message?.trim() || undefined
  };
};

export const createGatewayPaymentSession = (
  order: OrderTicket,
  payload: CreatePaymentSessionRequest
): PaymentSessionSummary => {
  const provider = getProviderForMethod(payload.method);
  assertProviderConfig(provider, payload.method);
  const createdAt = new Date().toISOString();
  const expiresAt = new Date(Date.now() + 15 * 60 * 1000).toISOString();
  const reference = buildReference(order.id, payload.method);
  const baseSession: PaymentSessionSummary = {
    id: `PS-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
    orderId: order.id,
    tableLabel: order.tableLabel,
    method: payload.method,
    provider,
    amount: Number(payload.amount.toFixed(2)),
    tipAmount: payload.tipAmount ? Number(payload.tipAmount.toFixed(2)) : undefined,
    status: "PENDING",
    reference,
    createdAt,
    expiresAt
  };

  if (payload.method === "PROMPTPAY") {
    const merchantPhone = provider === "PROMPTPAY_REAL"
      ? requireSetting("promptpayPhone", "PROMPTPAY_MERCHANT_PHONE")
      : getSetting("promptpayPhone") || process.env.PROMPTPAY_MERCHANT_PHONE?.trim() || "0812345678";
    return {
      ...baseSession,
      qrPayload: `PROMPTPAY|${merchantPhone}|${payload.amount.toFixed(2)}|${reference}`
    };
  }

  const checkoutBaseUrl = process.env.PAYMENT_CHECKOUT_BASE_URL?.trim() || "https://pay.mypos.local";
  return {
    ...baseSession,
    checkoutUrl: `${checkoutBaseUrl}/checkout/${reference}`
  };
};
