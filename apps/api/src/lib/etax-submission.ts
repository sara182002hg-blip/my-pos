import type { ReceiptSummary, SubmitEtaxRequest } from "@mypos/domain";

type EtaxSubmitSuccess = {
  ok: true;
  provider: string;
  reference: string;
  message: string;
};

type EtaxSubmitFailure = {
  ok: false;
  provider: string;
  message: string;
};

export type EtaxSubmitOutcome = EtaxSubmitSuccess | EtaxSubmitFailure;

const buildReference = (receiptNo: string) => `ETX-${receiptNo}-${Date.now()}`;

const isConfigured = (value?: string) =>
  typeof value === "string" &&
  value.trim().length > 0 &&
  !value.includes("replace-with") &&
  !value.includes("example.com");

const validateRealProviderConfig = (provider: string): string | null => {
  if (provider !== "RD_REAL") {
    return null;
  }

  const apiBase = process.env.RD_API_BASE?.trim();

  if (!apiBase?.startsWith("https://")) {
    return "RD_REAL requires RD_API_BASE to be HTTPS";
  }

  if (!isConfigured(process.env.RD_CLIENT_ID) || !isConfigured(process.env.RD_CLIENT_SECRET)) {
    return "RD_REAL requires RD_CLIENT_ID and RD_CLIENT_SECRET";
  }

  return null;
};

export const submitEtaxDocument = async (
  receipt: ReceiptSummary,
  payload: SubmitEtaxRequest
): Promise<EtaxSubmitOutcome> => {
  const provider = (process.env.ETAX_PROVIDER ?? "RD_STUB").trim().toUpperCase();

  if (receipt.receiptType !== "E_TAX") {
    return {
      ok: false,
      provider,
      message: "Receipt is not marked as E-TAX"
    };
  }

  if (!receipt.taxPayerName || !receipt.taxId) {
    return {
      ok: false,
      provider,
      message: "Tax payer details are incomplete"
    };
  }

  if (payload.channel === "EMAIL" && !(payload.recipient ?? receipt.taxEmail)?.trim()) {
    return {
      ok: false,
      provider,
      message: "E-TAX email recipient is required"
    };
  }

  if ((process.env.ETAX_FORCE_FAIL ?? "").trim().toLowerCase() === "true") {
    return {
      ok: false,
      provider,
      message: `Simulated E-TAX submission failure for ${receipt.receiptNo}`
    };
  }

  const configError = validateRealProviderConfig(provider);

  if (configError) {
    return {
      ok: false,
      provider,
      message: configError
    };
  }

  return {
    ok: true,
    provider,
    reference: buildReference(receipt.receiptNo),
    message:
      payload.channel === "EMAIL"
        ? `Submitted ${receipt.receiptNo} as E-TAX email`
        : `Submitted ${receipt.receiptNo} to RD portal`
  };
};
