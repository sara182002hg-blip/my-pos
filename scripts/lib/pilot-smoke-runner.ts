import Fastify from "fastify";
import { initializeAppState } from "../../apps/api/src/data/app-state.ts";
import { registerAuthRoutes } from "../../apps/api/src/routes/auth.ts";
import { registerOverviewRoutes } from "../../apps/api/src/routes/overview.ts";
import { registerOperationRoutes } from "../../apps/api/src/routes/operations.ts";

export interface PilotSmokeResult {
  ok: true;
  orderId: string;
  receiptNo: string;
  receiptMethod: string;
  sessionStatus: string;
  sessionsTracked: number;
  gatewayPending: number;
  gatewayCaptured: number;
  salesGross: number;
  receiptsIssued: number;
}

export interface ResetDemoSmokeResult {
  ok: true;
  createdOrderId: string;
  ordersBeforeReset: number;
  ordersAfterReset: number;
  receiptsAfterReset: number;
  paymentSessionsAfterReset: number;
}

export const runPilotSmoke = async (): Promise<PilotSmokeResult> => {
  process.env.PAYMENT_WEBHOOK_SECRET = process.env.PAYMENT_WEBHOOK_SECRET || "smoke-secret";

  const app = Fastify();

  try {
    await initializeAppState(app.log);
    await registerAuthRoutes(app);
    await registerOverviewRoutes(app);
    await registerOperationRoutes(app);

    const login = await app.inject({
      method: "POST",
      url: "/api/auth/login",
      payload: { username: "cashier01", pin: "1234" }
    });

    if (login.statusCode !== 200) {
      throw new Error(`Cashier login failed: ${login.body}`);
    }

    const token = login.json().session.accessToken as string;
    const authHeaders = { authorization: `Bearer ${token}` };

    const [tablesResponse, menuResponse] = await Promise.all([
      app.inject({ method: "GET", url: "/api/tables" }),
      app.inject({ method: "GET", url: "/api/menu" })
    ]);

    const table = tablesResponse.json().find((item: { status: string }) => item.status === "AVAILABLE");
    const menuItem = menuResponse.json().find((item: { inStock: boolean }) => item.inStock);

    if (!table || !menuItem) {
      throw new Error(
        JSON.stringify({
          message: "Seed data unavailable for smoke test",
          tableFound: Boolean(table),
          menuFound: Boolean(menuItem)
        })
      );
    }

    const createOrder = await app.inject({
      method: "POST",
      url: "/api/orders",
      headers: authHeaders,
      payload: {
        tableId: table.id,
        guestCount: 2,
        waiterName: "Pilot Smoke",
        priority: "NORMAL",
        source: "POS",
        items: [{ menuItemId: menuItem.id, quantity: 1 }]
      }
    });

    if (createOrder.statusCode !== 200) {
      throw new Error(`Order creation failed: ${createOrder.body}`);
    }

    const order = createOrder.json().order;

    const sessionCreate = await app.inject({
      method: "POST",
      url: `/api/orders/${order.id}/payment-session`,
      headers: authHeaders,
      payload: {
        method: "PROMPTPAY",
        amount: order.totalAmount,
        tipAmount: 20
      }
    });

    if (sessionCreate.statusCode !== 200) {
      throw new Error(`Payment session creation failed: ${sessionCreate.body}`);
    }

    const session = sessionCreate.json().session;

    const webhook = await app.inject({
      method: "POST",
      url: "/api/payment-sessions/webhook",
      headers: { "x-payment-webhook-secret": process.env.PAYMENT_WEBHOOK_SECRET },
      payload: {
        sessionId: session.id,
        provider: session.provider,
        event: "PAID",
        amount: order.totalAmount + 20
      }
    });

    if (webhook.statusCode !== 200) {
      throw new Error(`Gateway webhook capture failed: ${webhook.body}`);
    }

    const receipt = webhook.json().receipt;

    const [receiptsResponse, sessionsResponse, reportResponse] = await Promise.all([
      app.inject({ method: "GET", url: "/api/receipts", headers: authHeaders }),
      app.inject({ method: "GET", url: "/api/payment-sessions", headers: authHeaders }),
      app.inject({ method: "GET", url: "/api/reports/backoffice", headers: authHeaders })
    ]);

    const sessions = sessionsResponse.json().sessions;
    const report = reportResponse.json().report;

    return {
      ok: true,
      orderId: order.id,
      receiptNo: receipt.receiptNo,
      receiptMethod: receipt.paymentMethod,
      sessionStatus: webhook.json().session.status,
      sessionsTracked: sessions.length,
      gatewayPending: report.gatewayOps.pendingCount,
      gatewayCaptured: report.gatewayOps.capturedCount,
      salesGross: report.sales.grossSales,
      receiptsIssued: receiptsResponse.json().receipts.length
    };
  } finally {
    await app.close();
  }
};

export const runResetDemoSmoke = async (): Promise<ResetDemoSmokeResult> => {
  const app = Fastify();

  try {
    await initializeAppState(app.log);
    await registerAuthRoutes(app);
    await registerOverviewRoutes(app);
    await registerOperationRoutes(app);

    const cashierLogin = await app.inject({
      method: "POST",
      url: "/api/auth/login",
      payload: { username: "cashier01", pin: "1234" }
    });

    if (cashierLogin.statusCode !== 200) {
      throw new Error(`Cashier login failed: ${cashierLogin.body}`);
    }

    const cashierToken = cashierLogin.json().session.accessToken as string;
    const cashierHeaders = { authorization: `Bearer ${cashierToken}` };

    const [tablesResponse, menuResponse, ordersBeforeResponse] = await Promise.all([
      app.inject({ method: "GET", url: "/api/tables" }),
      app.inject({ method: "GET", url: "/api/menu" }),
      app.inject({ method: "GET", url: "/api/orders/export.csv", headers: cashierHeaders })
    ]);

    const table = tablesResponse.json().find((item: { status: string }) => item.status === "AVAILABLE");
    const menuItem = menuResponse.json().find((item: { inStock: boolean }) => item.inStock);

    if (!table || !menuItem) {
      throw new Error(
        JSON.stringify({
          message: "Seed data unavailable for reset smoke test",
          tableFound: Boolean(table),
          menuFound: Boolean(menuItem)
        })
      );
    }

    const ordersBeforeReset = ordersBeforeResponse
      .body
      .trim()
      .split("\n")
      .filter((line) => line.trim().length > 0).length - 1;

    const createOrder = await app.inject({
      method: "POST",
      url: "/api/orders",
      headers: cashierHeaders,
      payload: {
        tableId: table.id,
        guestCount: 2,
        waiterName: "Reset Smoke",
        priority: "NORMAL",
        source: "POS",
        items: [{ menuItemId: menuItem.id, quantity: 1 }]
      }
    });

    if (createOrder.statusCode !== 200) {
      throw new Error(`Order creation failed: ${createOrder.body}`);
    }

    const createdOrder = createOrder.json().order;

    const ownerLogin = await app.inject({
      method: "POST",
      url: "/api/auth/login",
      payload: { username: "owner01", pin: "9999" }
    });

    if (ownerLogin.statusCode !== 200) {
      throw new Error(`Owner login challenge failed: ${ownerLogin.body}`);
    }

    const challenge = ownerLogin.json().challenge;

    const ownerVerify = await app.inject({
      method: "POST",
      url: "/api/auth/verify-2fa",
      payload: { challengeId: challenge.challengeId, code: challenge.demoCode }
    });

    if (ownerVerify.statusCode !== 200) {
      throw new Error(`Owner 2FA verification failed: ${ownerVerify.body}`);
    }

    const ownerToken = ownerVerify.json().session.accessToken as string;
    const ownerHeaders = { authorization: `Bearer ${ownerToken}` };

    const resetResponse = await app.inject({
      method: "POST",
      url: "/api/system/reset-demo",
      headers: ownerHeaders
    });

    if (resetResponse.statusCode !== 200) {
      throw new Error(`Reset demo failed: ${resetResponse.body}`);
    }

    const [ordersAfterResponse, receiptsAfterResponse, sessionsAfterResponse] = await Promise.all([
      app.inject({ method: "GET", url: "/api/orders/export.csv", headers: cashierHeaders }),
      app.inject({ method: "GET", url: "/api/receipts", headers: cashierHeaders }),
      app.inject({ method: "GET", url: "/api/payment-sessions", headers: cashierHeaders })
    ]);

    const ordersAfterReset = ordersAfterResponse
      .body
      .trim()
      .split("\n")
      .filter((line) => line.trim().length > 0).length - 1;

    if (ordersAfterReset !== ordersBeforeReset) {
      throw new Error(
        JSON.stringify({
          message: "Reset demo did not restore baseline order count",
          ordersBeforeReset,
          ordersAfterReset
        })
      );
    }

    return {
      ok: true,
      createdOrderId: createdOrder.id,
      ordersBeforeReset,
      ordersAfterReset,
      receiptsAfterReset: receiptsAfterResponse.json().receipts.length,
      paymentSessionsAfterReset: sessionsAfterResponse.json().sessions.length
    };
  } finally {
    await app.close();
  }
};
