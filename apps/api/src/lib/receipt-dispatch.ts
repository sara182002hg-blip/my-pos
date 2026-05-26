import type {
  PrintReceiptRequest,
  ReceiptSummary,
  ReceiptTemplateSettings,
  ShareReceiptRequest
} from "@mypos/domain";
import net from "node:net";
import nodemailer from "nodemailer";
import { settingsStore } from "./settings-store";

// uses the same active branch as payment-gateway; services share one branch context per process
let _activeBranchId = "BR-TH-001";
export const setReceiptDispatchBranchId = (id: string) => { _activeBranchId = id; };

const getSetting = (key: Parameters<typeof settingsStore.getRaw>[1]) =>
  settingsStore.getRaw(_activeBranchId, key);

type DispatchSuccess = {
  ok: true;
  provider: string;
  message: string;
  target: string;
};

type DispatchFailure = {
  ok: false;
  provider: string;
  message: string;
  target: string;
};

export type ReceiptDispatchOutcome = DispatchSuccess | DispatchFailure;

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/i;
const truthyValues = new Set(["1", "true", "yes", "on"]);
const defaultPrinterPort = 9100;
const esc = 0x1b;
const gs = 0x1d;

const getFailureChannels = () =>
  new Set(
    (process.env.RECEIPT_DISPATCH_FAIL_CHANNELS ?? "")
      .split(",")
      .map((item) => item.trim().toUpperCase())
      .filter(Boolean)
  );

const isTruthy = (value?: string) => truthyValues.has((value ?? "").trim().toLowerCase());

const isConfigured = (value?: string) =>
  typeof value === "string" &&
  value.trim().length > 0 &&
  !value.includes("replace-with") &&
  !value.includes("example.com");

const defaultReceiptTemplate: ReceiptTemplateSettings = {
  businessName: "MyPOS Night Kitchen",
  branchLabel: "Bangkok Riverside Branch",
  footerMessage: "Thank you and see you again.",
  contactLine: "LINE OA: @myposnight · 02-123-4567",
  showQrLookupOnPrint: true,
  showTipLine: true
};

const resolveReceiptTemplate = (template?: ReceiptTemplateSettings) => ({
  ...defaultReceiptTemplate,
  ...template
});

const buildReceiptPrintText = (
  receipt: ReceiptSummary,
  copies: number,
  template?: ReceiptTemplateSettings
) => {
  const activeTemplate = resolveReceiptTemplate(template);

  return [
    activeTemplate.businessName,
    activeTemplate.branchLabel,
    `Receipt: ${receipt.receiptNo}`,
    `Order: ${receipt.orderId}`,
    `Paid at: ${receipt.paidAt}`,
    `Method: ${receipt.paymentMethod}`,
    `Total: ${receipt.totalAmount.toFixed(2)}`,
    activeTemplate.showTipLine && receipt.tipAmount ? `Tip: ${receipt.tipAmount.toFixed(2)}` : undefined,
    `Copies: ${copies}`,
    activeTemplate.showQrLookupOnPrint ? `QR lookup: ${receipt.qrLookupToken}` : undefined,
    activeTemplate.contactLine,
    "".padEnd(32, "-"),
    activeTemplate.footerMessage,
    "\n\n\n"
  ]
    .filter(Boolean)
    .join("\n");
};

const buildReceiptPrintPayload = (
  receipt: ReceiptSummary,
  copies: number,
  template?: ReceiptTemplateSettings
) => {
  const mode = (process.env.PRINTER_TCP_MODE ?? "TEXT").trim().toUpperCase();
  const printableText = buildReceiptPrintText(receipt, copies, template);
  const activeTemplate = resolveReceiptTemplate(template);

  if (mode !== "ESCPOS") {
    return {
      bytes: Buffer.from(printableText, "utf8"),
      mode: "TEXT"
    };
  }

  const lines = printableText.split("\n");
  const chunks: Buffer[] = [
    Buffer.from([esc, 0x40]),
    Buffer.from([esc, 0x61, 0x01]),
    Buffer.from([esc, 0x45, 0x01]),
    Buffer.from(`${activeTemplate.businessName}\n`, "utf8"),
    Buffer.from([esc, 0x45, 0x00]),
    Buffer.from(`${activeTemplate.branchLabel}\n`, "utf8"),
    Buffer.from([esc, 0x61, 0x00])
  ];

  lines.slice(1).forEach((line) => {
    chunks.push(Buffer.from(`${line}\n`, "utf8"));
  });

  chunks.push(Buffer.from([0x0a, 0x0a, 0x0a]));
  chunks.push(Buffer.from([gs, 0x56, 0x41, 0x10]));

  return {
    bytes: Buffer.concat(chunks),
    mode: "ESCPOS"
  };
};

const resolveTcpPrinterTarget = (printerName: string) => {
  const normalized = printerName.trim();

  if (!normalized) {
    return null;
  }

  const directMatch = normalized.match(/^([^:]+):(\d{2,5})$/);

  if (directMatch) {
    return {
      host: directMatch[1],
      port: Number(directMatch[2]),
      targetLabel: normalized
    };
  }

  const rawMap = process.env.PRINTER_TCP_MAP?.trim();

  if (!rawMap) {
    return null;
  }

  try {
    const parsed = JSON.parse(rawMap) as Record<
      string,
      { host?: string; port?: number | string }
    >;
    const config = parsed[normalized];

    if (!config?.host) {
      return null;
    }

    const port = Number(config.port ?? defaultPrinterPort);

    if (Number.isNaN(port)) {
      return null;
    }

    return {
      host: config.host,
      port,
      targetLabel: `${config.host}:${port}`
    };
  } catch {
    const entries = rawMap.split(",").map((entry) => entry.trim()).filter(Boolean);
    const match = entries
      .map((entry) => {
        const [name, target] = entry.split("=");
        const targetMatch = target?.trim().match(/^([^:]+):(\d{2,5})$/);

        if (!name?.trim() || !targetMatch) {
          return null;
        }

        return {
          name: name.trim(),
          host: targetMatch[1],
          port: Number(targetMatch[2])
        };
      })
      .find((entry) => entry?.name === normalized);

    if (!match || Number.isNaN(match.port)) {
      return null;
    }

    return {
      host: match.host,
      port: match.port,
      targetLabel: `${match.host}:${match.port}`
    };
  }
};

const sendEmailViaSmtp = async (
  receipt: ReceiptSummary,
  recipient: string,
  template?: ReceiptTemplateSettings
): Promise<ReceiptDispatchOutcome> => {
  const host = getSetting("smtpHost") || process.env.SMTP_HOST?.trim();
  const port = Number(getSetting("smtpPort") || process.env.SMTP_PORT || "587");
  const user = getSetting("smtpUser") || process.env.SMTP_USER?.trim();
  const pass = getSetting("smtpPass") || process.env.SMTP_PASS || "";
  const from = getSetting("smtpFrom") || process.env.SMTP_FROM?.trim();
  const secure = isTruthy(process.env.SMTP_SECURE);
  const provider = "SMTP";
  const activeTemplate = resolveReceiptTemplate(template);

  if (!isConfigured(host) || !isConfigured(from) || !isConfigured(user) || !isConfigured(pass) || Number.isNaN(port)) {
    return {
      ok: false,
      provider,
      target: recipient,
      message: "SMTP provider selected but SMTP_HOST/SMTP_PORT/SMTP_FROM/SMTP_USER/SMTP_PASS are incomplete"
    };
  }

  const transport = nodemailer.createTransport({
    host,
    port,
    secure,
    auth: { user: user!, pass }
  });

  try {
    await transport.sendMail({
      from,
      to: recipient,
      subject: `${activeTemplate.businessName} Receipt ${receipt.receiptNo}`,
      text: [
        activeTemplate.businessName,
        activeTemplate.branchLabel,
        `Receipt: ${receipt.receiptNo}`,
        `Order: ${receipt.orderId}`,
        `Total: ${receipt.totalAmount.toFixed(2)}`,
        activeTemplate.showTipLine && receipt.tipAmount ? `Tip: ${receipt.tipAmount.toFixed(2)}` : undefined,
        `Paid at: ${receipt.paidAt}`,
        `Payment method: ${receipt.paymentMethod}`,
        activeTemplate.showQrLookupOnPrint ? `QR lookup: ${receipt.qrLookupToken}` : undefined,
        activeTemplate.contactLine,
        activeTemplate.footerMessage
      ]
        .filter(Boolean)
        .join("\n"),
      html: [
        `<h2>${activeTemplate.businessName}</h2>`,
        `<p>${activeTemplate.branchLabel}</p>`,
        `<h3>Receipt ${receipt.receiptNo}</h3>`,
        `<p><strong>Order:</strong> ${receipt.orderId}</p>`,
        `<p><strong>Total:</strong> ${receipt.totalAmount.toFixed(2)}</p>`,
        activeTemplate.showTipLine && receipt.tipAmount
          ? `<p><strong>Tip:</strong> ${receipt.tipAmount.toFixed(2)}</p>`
          : "",
        `<p><strong>Paid at:</strong> ${receipt.paidAt}</p>`,
        `<p><strong>Payment method:</strong> ${receipt.paymentMethod}</p>`,
        activeTemplate.showQrLookupOnPrint
          ? `<p><strong>QR lookup:</strong> ${receipt.qrLookupToken}</p>`
          : "",
        activeTemplate.contactLine ? `<p>${activeTemplate.contactLine}</p>` : "",
        `<p>${activeTemplate.footerMessage}</p>`
      ].join("")
    });

    return {
      ok: true,
      provider,
      target: recipient,
      message: `Sent ${receipt.receiptNo} via SMTP`
    };
  } catch (error) {
    return {
      ok: false,
      provider,
      target: recipient,
      message: error instanceof Error ? error.message : `SMTP send failed for ${receipt.receiptNo}`
    };
  }
};

const sendLineViaApi = async (
  receipt: ReceiptSummary,
  recipient: string,
  template?: ReceiptTemplateSettings
): Promise<ReceiptDispatchOutcome> => {
  const provider = "LINE_OA";
  const accessToken = getSetting("lineChannelAccessToken") || process.env.LINE_CHANNEL_ACCESS_TOKEN?.trim();
  const apiBase = (process.env.LINE_API_BASE ?? "https://api.line.me").trim();
  const activeTemplate = resolveReceiptTemplate(template);

  if (!isConfigured(accessToken)) {
    return {
      ok: false,
      provider,
      target: recipient,
      message: "LINE_OA provider selected but LINE_CHANNEL_ACCESS_TOKEN is missing"
    };
  }

  if (!apiBase.startsWith("https://")) {
    return {
      ok: false,
      provider,
      target: recipient,
      message: "LINE_OA provider selected but LINE_API_BASE must be HTTPS"
    };
  }

  try {
    const response = await fetch(`${apiBase}/v2/bot/message/push`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        to: recipient,
        messages: [
          {
            type: "text",
            text: [
              activeTemplate.businessName,
              activeTemplate.branchLabel,
              `Receipt ${receipt.receiptNo}`,
              `Order ${receipt.orderId}`,
              `Total ${receipt.totalAmount.toFixed(2)}`,
              activeTemplate.showTipLine && receipt.tipAmount ? `Tip ${receipt.tipAmount.toFixed(2)}` : undefined,
              `Paid via ${receipt.paymentMethod}`,
              activeTemplate.showQrLookupOnPrint ? `QR ${receipt.qrLookupToken}` : undefined,
              activeTemplate.contactLine,
              activeTemplate.footerMessage
            ]
              .filter(Boolean)
              .join("\n")
          }
        ]
      })
    });

    if (!response.ok) {
      const body = await response.text();
      return {
        ok: false,
        provider,
        target: recipient,
        message: body || `LINE API returned ${response.status}`
      };
    }

    return {
      ok: true,
      provider,
      target: recipient,
      message: `Sent ${receipt.receiptNo} via LINE OA`
    };
  } catch (error) {
    return {
      ok: false,
      provider,
      target: recipient,
      message: error instanceof Error ? error.message : `LINE send failed for ${receipt.receiptNo}`
    };
  }
};

const sendPrintViaTcp = async (
  receipt: ReceiptSummary,
  payload: PrintReceiptRequest,
  template?: ReceiptTemplateSettings
): Promise<ReceiptDispatchOutcome> => {
  const provider = "TCP_PRINTER";
  const resolved = resolveTcpPrinterTarget(payload.printerName);

  if (!resolved) {
    return {
      ok: false,
      provider,
      target: payload.printerName.trim(),
      message: "TCP printer provider selected but printer target is not resolvable"
    };
  }

  const timeoutMs = Number(process.env.PRINTER_TCP_TIMEOUT_MS ?? "3000");
  const printablePayload = buildReceiptPrintPayload(receipt, payload.copies ?? 1, template);

  return new Promise<ReceiptDispatchOutcome>((resolve) => {
    const socket = new net.Socket();
    let settled = false;

    const finalize = (result: ReceiptDispatchOutcome) => {
      if (settled) {
        return;
      }

      settled = true;
      socket.destroy();
      resolve(result);
    };

    socket.setTimeout(timeoutMs);

    socket.once("connect", () => {
      socket.write(printablePayload.bytes, (error) => {
        if (error) {
          finalize({
            ok: false,
            provider,
            target: resolved.targetLabel,
            message: error.message
          });
          return;
        }

        socket.end();
      });
    });

    socket.once("close", (hadError) => {
      if (settled) {
        return;
      }

      if (hadError) {
        finalize({
          ok: false,
          provider,
          target: resolved.targetLabel,
          message: `TCP printer connection closed with error for ${receipt.receiptNo}`
        });
        return;
      }

      finalize({
        ok: true,
        provider,
        target: resolved.targetLabel,
        message: `Printed ${receipt.receiptNo} via TCP printer (${printablePayload.mode})`
      });
    });

    socket.once("timeout", () => {
      finalize({
        ok: false,
        provider,
        target: resolved.targetLabel,
        message: `TCP printer timeout after ${timeoutMs}ms`
      });
    });

    socket.once("error", (error) => {
      finalize({
        ok: false,
        provider,
        target: resolved.targetLabel,
        message: error.message
      });
    });

    socket.connect(resolved.port, resolved.host);
  });
};

export const dispatchReceiptShare = async (
  receipt: ReceiptSummary,
  payload: ShareReceiptRequest,
  template?: ReceiptTemplateSettings
): Promise<ReceiptDispatchOutcome> => {
  const provider =
    payload.channel === "EMAIL"
      ? process.env.RECEIPT_EMAIL_PROVIDER ?? "INTERNAL_EMAIL_QUEUE"
      : process.env.RECEIPT_LINE_PROVIDER ?? "LINE_OA_STUB";
  const target = payload.recipient.trim();

  if (!target) {
    return {
      ok: false,
      provider,
      target,
      message: "Recipient is required"
    };
  }

  if (payload.channel === "EMAIL" && !emailPattern.test(target)) {
    return {
      ok: false,
      provider,
      target,
      message: "Invalid email format"
    };
  }

  if (payload.channel === "LINE" && target.length < 4) {
    return {
      ok: false,
      provider,
      target,
      message: "LINE user id looks too short"
    };
  }

  if (getFailureChannels().has(payload.channel)) {
    return {
      ok: false,
      provider,
      target,
      message: `Simulated ${payload.channel} dispatch failure for ${receipt.receiptNo}`
    };
  }

  if (payload.channel === "EMAIL" && provider.toUpperCase() === "SMTP") {
    return sendEmailViaSmtp(receipt, target, template);
  }

  if (payload.channel === "LINE" && provider.toUpperCase() === "LINE_OA") {
    return sendLineViaApi(receipt, target, template);
  }

  return {
    ok: true,
    provider,
    target,
    message:
      payload.channel === "EMAIL"
        ? `Queued ${receipt.receiptNo} for email delivery`
        : `Queued ${receipt.receiptNo} for LINE delivery`
  };
};

export const dispatchReceiptPrint = async (
  receipt: ReceiptSummary,
  payload: PrintReceiptRequest,
  template?: ReceiptTemplateSettings
): Promise<ReceiptDispatchOutcome> => {
  const provider = process.env.RECEIPT_PRINT_PROVIDER ?? "LOCAL_PRINTER_STUB";
  const target = payload.printerName.trim();

  if (!target) {
    return {
      ok: false,
      provider,
      target,
      message: "Printer name is required"
    };
  }

  if (/offline|error|fail/i.test(target)) {
    return {
      ok: false,
      provider,
      target,
      message: `Printer ${target} is unavailable`
    };
  }

  if (getFailureChannels().has("PRINT")) {
    return {
      ok: false,
      provider,
      target,
      message: `Simulated PRINT dispatch failure for ${receipt.receiptNo}`
    };
  }

  if (provider.toUpperCase() === "TCP_PRINTER") {
    return sendPrintViaTcp(receipt, payload, template);
  }

  return {
    ok: true,
    provider,
    target,
    message: `Printed ${receipt.receiptNo} to ${target}`
  };
};
