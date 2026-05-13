import type {
  CreatePaymentSessionRequest,
  CreateOrderRequest,
  CreateReservationRequest,
  IssueTaxInvoiceRequest,
  PaymentWebhookRequest,
  PrintReceiptRequest,
  RefundReceiptRequest,
  ShareReceiptRequest,
  SettlePaymentRequest,
  SplitPaymentRequest,
  SubmitEtaxRequest,
  UpdateTableLayoutRequest,
  VoidOrderRequest
} from "@mypos/domain";
import type { FastifyInstance } from "fastify";
import { appRepository } from "../data/app-state";
import { dispatchReceiptPrint, dispatchReceiptShare } from "../lib/receipt-dispatch";
import { submitEtaxDocument } from "../lib/etax-submission";
import { parsePaymentWebhookPayload, validatePaymentWebhookSecret } from "../lib/payment-gateway";
import { broadcastSnapshot } from "../lib/realtime";
import { requirePermission } from "../lib/guards";

export const registerOperationRoutes = async (app: FastifyInstance) => {
  const buildActor = (session: NonNullable<ReturnType<typeof requirePermission>>) => ({
    id: session.user.id,
    displayName: session.user.displayName,
    role: session.user.role
  });

  const recordFailedDispatchAttempt = (
    receiptId: string,
    receiptNo: string,
    channel: "EMAIL" | "LINE" | "PRINT",
    target: string,
    provider: string,
    message: string,
    actor: ReturnType<typeof buildActor>
  ) =>
    appRepository.recordReceiptDispatchAttempt(
      {
        id: `RDA-${Date.now()}-${receiptId}-FAIL`,
        receiptId,
        receiptNo,
        channel,
        target,
        status: "FAILED",
        provider,
        message,
        createdAt: new Date().toISOString()
      },
      actor
    );

  app.post<{ Body: CreateOrderRequest }>("/api/orders", async (request, reply) => {
    const session = requirePermission(request, reply, "orders.manage");

    if (!session) {
      return { message: "Forbidden" };
    }

    const order = appRepository.createOrder(request.body, {
      id: session.user.id,
      displayName: session.user.displayName,
      role: session.user.role
    });

    if (!order) {
      reply.status(400);
      return { message: "Could not create order" };
    }

    broadcastSnapshot();

    return {
      message: "Order created",
      order,
      actor: session.user.displayName
    };
  });

  app.post<{ Params: { orderId: string }; Body: SettlePaymentRequest }>(
    "/api/orders/:orderId/pay",
    async (request, reply) => {
      const session = requirePermission(request, reply, "payments.capture");

      if (!session) {
        return { message: "Forbidden" };
      }

      const result = appRepository.settlePayment(
        request.params.orderId,
        request.body,
        {
          id: session.user.id,
          displayName: session.user.displayName,
          role: session.user.role
        }
      );

      if (!result) {
        reply.status(404);
        return { message: "Order not found" };
      }

      broadcastSnapshot();

      return {
        message: "Payment settled",
        ...result,
        actor: session.user.displayName
      };
    }
  );

  app.post<{ Params: { orderId: string }; Body: CreatePaymentSessionRequest }>(
    "/api/orders/:orderId/payment-session",
    async (request, reply) => {
      const session = requirePermission(request, reply, "payments.capture");

      if (!session) {
        return { message: "Forbidden" };
      }

      let result;

      try {
        result = appRepository.createPaymentSession(request.params.orderId, request.body, {
          id: session.user.id,
          displayName: session.user.displayName,
          role: session.user.role
        });
      } catch (error) {
        reply.status(502);
        return {
          message: error instanceof Error ? error.message : "Payment provider configuration failed"
        };
      }

      if (!result) {
        reply.status(400);
        return { message: "Could not create payment session" };
      }

      broadcastSnapshot();

      return {
        message: "Payment session created",
        session: result,
        actor: session.user.displayName
      };
    }
  );

  app.post<{ Params: { sessionId: string } }>(
    "/api/payment-sessions/:sessionId/capture",
    async (request, reply) => {
      const session = requirePermission(request, reply, "payments.capture");

      if (!session) {
        return { message: "Forbidden" };
      }

      const result = appRepository.capturePaymentSession(request.params.sessionId, {
        id: session.user.id,
        displayName: session.user.displayName,
        role: session.user.role
      });

      if (!result) {
        reply.status(400);
        return { message: "Payment session capture failed" };
      }

      broadcastSnapshot();

      return {
        message: "Payment session captured",
        ...result,
        actor: session.user.displayName
      };
    }
  );

  app.post<{ Params: { sessionId: string } }>(
    "/api/payment-sessions/:sessionId/retry",
    async (request, reply) => {
      const session = requirePermission(request, reply, "payments.capture");

      if (!session) {
        return { message: "Forbidden" };
      }

      const result = appRepository.retryPaymentSession(request.params.sessionId, {
        id: session.user.id,
        displayName: session.user.displayName,
        role: session.user.role
      });

      if (!result) {
        reply.status(400);
        return { message: "Payment session retry failed" };
      }

      broadcastSnapshot();

      return {
        message: "Payment session retried",
        ...result,
        actor: session.user.displayName
      };
    }
  );

  app.post<{ Body: PaymentWebhookRequest }>("/api/payment-sessions/webhook", async (request, reply) => {
    if (!validatePaymentWebhookSecret(request.headers["x-payment-webhook-secret"])) {
      reply.status(401);
      return { message: "Invalid payment webhook secret" };
    }

    const payload = parsePaymentWebhookPayload(request.body);

    if (!payload) {
      reply.status(400);
      return { message: "Invalid payment webhook payload" };
    }

    const existingSession = appRepository.getPaymentSessions().find(
      (session) =>
        (payload.sessionId && session.id === payload.sessionId) ||
        (payload.reference && session.reference === payload.reference)
    );

    if (!existingSession) {
      reply.status(404);
      return { message: "Payment session not found" };
    }

    if (payload.provider && payload.provider !== existingSession.provider) {
      reply.status(409);
      return { message: "Payment provider mismatch" };
    }

    if (typeof payload.amount === "number") {
      const expectedAmounts = [
        Number(existingSession.amount.toFixed(2)),
        Number((existingSession.amount + (existingSession.tipAmount ?? 0)).toFixed(2))
      ];

      if (!expectedAmounts.some((value) => Math.abs(value - payload.amount!) < 0.01)) {
        reply.status(409);
        return { message: "Payment amount mismatch" };
      }
    }

    const result = appRepository.processPaymentWebhook(payload, {
      id: "gateway-webhook",
      displayName: "Payment Gateway",
      role: "OWNER"
    });

    if (!result) {
      reply.status(400);
      return { message: "Payment webhook could not be processed" };
    }

    broadcastSnapshot();

    return {
      message: "Payment webhook processed",
      ...result
    };
  });

  app.post<{ Params: { orderId: string }; Body: SplitPaymentRequest }>(
    "/api/orders/:orderId/split-pay",
    async (request, reply) => {
      const session = requirePermission(request, reply, "payments.capture");

      if (!session) {
        return { message: "Forbidden" };
      }

      const result = appRepository.splitSettlePayment(
        request.params.orderId,
        request.body,
        {
          id: session.user.id,
          displayName: session.user.displayName,
          role: session.user.role
        }
      );

      if (!result) {
        reply.status(400);
        return { message: "Split payment failed" };
      }

      broadcastSnapshot();

      return {
        message: "Split payment settled",
        ...result,
        actor: session.user.displayName
      };
    }
  );

  app.post<{ Params: { orderId: string }; Body: VoidOrderRequest }>(
    "/api/orders/:orderId/void",
    async (request, reply) => {
      const session = requirePermission(request, reply, "receipts.void");

      if (!session) {
        return { message: "Forbidden" };
      }

      const result = appRepository.voidOrder(request.params.orderId, request.body, {
        id: session.user.id,
        displayName: session.user.displayName,
        role: session.user.role
      });

      if (!result) {
        reply.status(400);
        return { message: "Order cannot be voided" };
      }

      broadcastSnapshot();

      return {
        message: "Order voided",
        ...result,
        actor: session.user.displayName
      };
    }
  );

  app.post<{ Params: { receiptId: string }; Body: RefundReceiptRequest }>(
    "/api/receipts/:receiptId/refund",
    async (request, reply) => {
      const session = requirePermission(request, reply, "receipts.void");

      if (!session) {
        return { message: "Forbidden" };
      }

      const result = appRepository.refundReceipt(request.params.receiptId, request.body, {
        id: session.user.id,
        displayName: session.user.displayName,
        role: session.user.role
      });

      if (!result) {
        reply.status(400);
        return { message: "Receipt cannot be refunded" };
      }

      broadcastSnapshot();

      return {
        message: "Receipt refunded",
        ...result,
        actor: session.user.displayName
      };
    }
  );

  app.post<{ Params: { receiptId: string }; Body: ShareReceiptRequest }>(
    "/api/receipts/:receiptId/share",
    async (request, reply) => {
      const session = requirePermission(request, reply, "payments.capture");

      if (!session) {
        return { message: "Forbidden" };
      }

      const receipt = appRepository.getReceiptById(request.params.receiptId);

      if (!receipt) {
        reply.status(404);
        return { message: "Receipt not found" };
      }

      const actor = buildActor(session);
      const receiptTemplate = appRepository.getSecurityPolicy().receiptTemplate;
      const outcome = await dispatchReceiptShare(receipt, request.body, receiptTemplate);

      if (!outcome.ok) {
        const attempt = recordFailedDispatchAttempt(
          receipt.id,
          receipt.receiptNo,
          request.body.channel,
          outcome.target,
          outcome.provider,
          outcome.message,
          actor
        );

        broadcastSnapshot();
        reply.status(502);
        return {
          message: "Receipt dispatch failed",
          receipt,
          attempt,
          actor: session.user.displayName
        };
      }

      const result = appRepository.shareReceipt(request.params.receiptId, request.body, actor, {
        provider: outcome.provider,
        message: outcome.message
      });

      if (!result) {
        reply.status(404);
        return { message: "Receipt not found" };
      }

      broadcastSnapshot();

      return {
        message: "Receipt shared",
        ...result,
        actor: session.user.displayName
      };
    }
  );

  app.post<{ Params: { receiptId: string }; Body: PrintReceiptRequest }>(
    "/api/receipts/:receiptId/print",
    async (request, reply) => {
      const session = requirePermission(request, reply, "payments.capture");

      if (!session) {
        return { message: "Forbidden" };
      }

      const receipt = appRepository.getReceiptById(request.params.receiptId);

      if (!receipt) {
        reply.status(404);
        return { message: "Receipt not found" };
      }

      const actor = buildActor(session);
      const receiptTemplate = appRepository.getSecurityPolicy().receiptTemplate;
      const outcome = await dispatchReceiptPrint(receipt, request.body, receiptTemplate);

      if (!outcome.ok) {
        const attempt = recordFailedDispatchAttempt(
          receipt.id,
          receipt.receiptNo,
          "PRINT",
          outcome.target,
          outcome.provider,
          outcome.message,
          actor
        );

        broadcastSnapshot();
        reply.status(502);
        return {
          message: "Receipt print failed",
          receipt,
          attempt,
          actor: session.user.displayName
        };
      }

      const result = appRepository.printReceipt(request.params.receiptId, request.body, actor, {
        provider: outcome.provider,
        message: outcome.message
      });

      if (!result) {
        reply.status(404);
        return { message: "Receipt not found" };
      }

      broadcastSnapshot();

      return {
        message: "Receipt printed",
        ...result,
        actor: session.user.displayName
      };
    }
  );

  app.post<{ Params: { receiptId: string }; Body: IssueTaxInvoiceRequest }>(
    "/api/receipts/:receiptId/tax-invoice",
    async (request, reply) => {
      const session = requirePermission(request, reply, "payments.capture");

      if (!session) {
        return { message: "Forbidden" };
      }

      const result = appRepository.issueTaxInvoice(request.params.receiptId, request.body, {
        id: session.user.id,
        displayName: session.user.displayName,
        role: session.user.role
      });

      if (!result) {
        reply.status(400);
        return { message: "Tax invoice issue failed" };
      }

      broadcastSnapshot();

      return {
        message: "Tax invoice issued",
        ...result,
        actor: session.user.displayName
      };
    }
  );

  app.post<{ Params: { receiptId: string }; Body: SubmitEtaxRequest }>(
    "/api/receipts/:receiptId/e-tax-submit",
    async (request, reply) => {
      const session = requirePermission(request, reply, "payments.capture");

      if (!session) {
        return { message: "Forbidden" };
      }

      const receipt = appRepository.getReceiptById(request.params.receiptId);

      if (!receipt) {
        reply.status(404);
        return { message: "Receipt not found" };
      }

      const outcome = await submitEtaxDocument(receipt, request.body);

      if (!outcome.ok) {
        const result = appRepository.submitEtax(
          request.params.receiptId,
          request.body,
          {
            id: session.user.id,
            displayName: session.user.displayName,
            role: session.user.role
          },
          {
            provider: outcome.provider,
            message: outcome.message,
            failed: true
          }
        );

        broadcastSnapshot();
        reply.status(502);
        return {
          message: "E-Tax submission failed",
          receipt: result?.receipt ?? receipt,
          actor: session.user.displayName
        };
      }

      const result = appRepository.submitEtax(
        request.params.receiptId,
        request.body,
        {
          id: session.user.id,
          displayName: session.user.displayName,
          role: session.user.role
        },
        {
          provider: outcome.provider,
          reference: outcome.reference,
          message: outcome.message
        }
      );

      if (!result) {
        reply.status(400);
        return { message: "E-Tax submission failed" };
      }

      broadcastSnapshot();

      return {
        message: "E-Tax submitted",
        ...result,
        actor: session.user.displayName
      };
    }
  );

  app.post<{ Params: { attemptId: string } }>(
    "/api/receipts/dispatch-attempts/:attemptId/retry",
    async (request, reply) => {
      const session = requirePermission(request, reply, "payments.capture");

      if (!session) {
        return { message: "Forbidden" };
      }

      const priorAttempt = appRepository
        .getReceiptDispatchAttempts()
        .find((attempt) => attempt.id === request.params.attemptId);

      if (!priorAttempt) {
        reply.status(404);
        return { message: "Dispatch attempt not found" };
      }

      if (priorAttempt.status !== "FAILED") {
        reply.status(400);
        return { message: "Only failed dispatch attempts can be retried" };
      }

      const receipt = appRepository.getReceiptById(priorAttempt.receiptId);

      if (!receipt) {
        reply.status(404);
        return { message: "Receipt not found" };
      }

      const actor = buildActor(session);
      const receiptTemplate = appRepository.getSecurityPolicy().receiptTemplate;

      if (priorAttempt.channel === "PRINT") {
        const payload: PrintReceiptRequest = {
          printerName: priorAttempt.target,
          copies: 1
        };
        const outcome = await dispatchReceiptPrint(receipt, payload, receiptTemplate);

        if (!outcome.ok) {
          const attempt = recordFailedDispatchAttempt(
            receipt.id,
            receipt.receiptNo,
            "PRINT",
            outcome.target,
            outcome.provider,
            `Retry failed: ${outcome.message}`,
            actor
          );

          broadcastSnapshot();
          reply.status(502);
          return {
            message: "Receipt print retry failed",
            receipt,
            attempt,
            actor: session.user.displayName
          };
        }

        const result = appRepository.printReceipt(receipt.id, payload, actor, {
          provider: outcome.provider,
          message: outcome.message
        });

        if (!result) {
          reply.status(404);
          return { message: "Receipt not found" };
        }

        broadcastSnapshot();
        return {
          message: "Receipt print retried",
          receipt: result.receipt,
          attempt: appRepository.getReceiptDispatchAttempts()[0],
          actor: session.user.displayName
        };
      }

      const payload: ShareReceiptRequest = {
        channel: priorAttempt.channel,
        recipient: priorAttempt.target
      };
      const outcome = await dispatchReceiptShare(receipt, payload, receiptTemplate);

      if (!outcome.ok) {
        const attempt = recordFailedDispatchAttempt(
          receipt.id,
          receipt.receiptNo,
          payload.channel,
          outcome.target,
          outcome.provider,
          `Retry failed: ${outcome.message}`,
          actor
        );

        broadcastSnapshot();
        reply.status(502);
        return {
          message: "Receipt share retry failed",
          receipt,
          attempt,
          actor: session.user.displayName
        };
      }

      const result = appRepository.shareReceipt(receipt.id, payload, actor, {
        provider: outcome.provider,
        message: outcome.message
      });

      if (!result) {
        reply.status(404);
        return { message: "Receipt not found" };
      }

      broadcastSnapshot();
      return {
        message: "Receipt share retried",
        receipt: result.receipt,
        attempt: appRepository.getReceiptDispatchAttempts()[0],
        actor: session.user.displayName
      };
    }
  );

  app.post<{ Params: { tableId: string }; Body: { status: string } }>(
    "/api/tables/:tableId/status",
    async (request, reply) => {
      const session = requirePermission(request, reply, "orders.manage");

      if (!session) {
        return { message: "Forbidden" };
      }

      const table = appRepository.updateTableStatus(
        request.params.tableId,
        request.body.status as Parameters<typeof appRepository.updateTableStatus>[1],
        {
          id: session.user.id,
          displayName: session.user.displayName,
          role: session.user.role
        }
      );

      if (!table) {
        reply.status(404);
        return { message: "Table not found" };
      }

      broadcastSnapshot();

      return {
        message: "Table status updated",
        table
      };
    }
  );

  app.post<{ Params: { tableId: string }; Body: UpdateTableLayoutRequest }>(
    "/api/tables/:tableId/layout",
    async (request, reply) => {
      const session = requirePermission(request, reply, "orders.manage");

      if (!session) {
        return { message: "Forbidden" };
      }

      const table = appRepository.updateTableLayout(request.params.tableId, request.body, {
        id: session.user.id,
        displayName: session.user.displayName,
        role: session.user.role
      });

      if (!table) {
        reply.status(404);
        return { message: "Table not found" };
      }

      broadcastSnapshot();

      return {
        message: "Table layout updated",
        table
      };
    }
  );

  app.post<{ Params: { tableId: string }; Body: CreateReservationRequest }>(
    "/api/tables/:tableId/reserve",
    async (request, reply) => {
      const session = requirePermission(request, reply, "orders.manage");

      if (!session) {
        return { message: "Forbidden" };
      }

      const table = appRepository.reserveTable(request.params.tableId, request.body, {
        id: session.user.id,
        displayName: session.user.displayName,
        role: session.user.role
      });

      if (!table) {
        reply.status(404);
        return { message: "Table not found" };
      }

      broadcastSnapshot();

      return {
        message: "Table reserved",
        table
      };
    }
  );

  app.post<{ Params: { tableId: string } }>(
    "/api/tables/:tableId/clear-reservation",
    async (request, reply) => {
      const session = requirePermission(request, reply, "orders.manage");

      if (!session) {
        return { message: "Forbidden" };
      }

      const table = appRepository.clearTableReservation(request.params.tableId, {
        id: session.user.id,
        displayName: session.user.displayName,
        role: session.user.role
      });

      if (!table) {
        reply.status(404);
        return { message: "Table not found" };
      }

      broadcastSnapshot();

      return {
        message: "Table reservation cleared",
        table
      };
    }
  );

  app.post("/api/system/reset-demo", async (request, reply) => {
    const session = requirePermission(request, reply, "system.manage");

    if (!session) {
      return { message: "Forbidden" };
    }

    const reset = appRepository.resetDemoState();

    if (!reset) {
      reply.status(409);
      return { message: "Demo reset unavailable while persistence is enabled" };
    }

    broadcastSnapshot();

    return {
      message: "Demo state reset",
      actor: session.user.displayName
    };
  });

  app.post<{ Params: { ticketId: string } }>("/api/kitchen/:ticketId/ready", async (request, reply) => {
    const session = requirePermission(request, reply, "orders.manage");

    if (!session) {
      return { message: "Forbidden" };
    }

    const ticket = appRepository.markKitchenReady(request.params.ticketId, {
      id: session.user.id,
      displayName: session.user.displayName,
      role: session.user.role
    });

    if (!ticket) {
      reply.status(404);
      return { message: "Ticket not found" };
    }

    broadcastSnapshot();
    return { message: "Kitchen ticket marked ready", ticket };
  });

  app.post<{ Params: { ticketId: string } }>("/api/kitchen/:ticketId/acknowledge", async (request, reply) => {
    const session = requirePermission(request, reply, "orders.manage");

    if (!session) {
      return { message: "Forbidden" };
    }

    const ticket = appRepository.acknowledgeKitchenTicket(request.params.ticketId, {
      id: session.user.id,
      displayName: session.user.displayName,
      role: session.user.role
    });

    if (!ticket) {
      reply.status(404);
      return { message: "Ticket not found" };
    }

    broadcastSnapshot();
    return { message: "Kitchen ticket acknowledged", ticket };
  });

  app.post<{ Params: { ticketId: string } }>("/api/kitchen/:ticketId/out-of-stock", async (request, reply) => {
    const session = requirePermission(request, reply, "orders.manage");

    if (!session) {
      return { message: "Forbidden" };
    }

    const ticket = appRepository.markKitchenOutOfStock(request.params.ticketId, {
      id: session.user.id,
      displayName: session.user.displayName,
      role: session.user.role
    });

    if (!ticket) {
      reply.status(404);
      return { message: "Ticket not found" };
    }

    broadcastSnapshot();
    return { message: "Kitchen ticket marked out of stock", ticket };
  });
};
