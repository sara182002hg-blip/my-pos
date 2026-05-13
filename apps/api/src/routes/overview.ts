import type { FastifyInstance } from "fastify";
import { appRepository } from "../data/app-state";
import { requireAuth, requirePermission } from "../lib/guards";
import { asDownloadFilename, toCsv } from "../lib/csv";

export const registerOverviewRoutes = async (app: FastifyInstance) => {
  app.get("/api/overview", async () => appRepository.getSnapshot());
  app.get("/api/orders", async () => appRepository.getSnapshot().orders);
  app.get("/api/tables", async () => appRepository.getSnapshot().tables);
  app.get("/api/menu", async () => appRepository.getSnapshot().menu);
  app.get("/api/shifts", async () => appRepository.getSnapshot().shifts);
  app.get("/api/kitchen", async () => appRepository.getSnapshot().kitchen);

  app.get("/api/receipts", async (request, reply) => {
    const session = requirePermission(request, reply, "payments.capture");

    if (!session) {
      return { message: "Forbidden" };
    }

    return {
      receipts: appRepository.getReceipts()
    };
  });

  app.get("/api/payment-sessions", async (request, reply) => {
    const session = requirePermission(request, reply, "payments.capture");

    if (!session) {
      return { message: "Forbidden" };
    }

    return {
      sessions: appRepository.getPaymentSessions()
    };
  });

  app.get("/api/receipts/dispatch-attempts", async (request, reply) => {
    const session = requirePermission(request, reply, "payments.capture");

    if (!session) {
      return { message: "Forbidden" };
    }

    return {
      attempts: appRepository.getReceiptDispatchAttempts()
    };
  });

  app.get("/api/audit", async (request, reply) => {
    const session = requirePermission(request, reply, "audit.view");

    if (!session) {
      return { message: "Forbidden" };
    }

    return {
      entries: appRepository.getAuditEntries()
    };
  });

  app.get("/api/exceptions", async (request, reply) => {
    const session = requirePermission(request, reply, "receipts.void");

    if (!session) {
      return { message: "Forbidden" };
    }

    return {
      exceptions: appRepository.getExceptions()
    };
  });

  app.get("/api/exceptions/export.csv", async (request, reply) => {
    const session = requirePermission(request, reply, "receipts.void");

    if (!session) {
      return { message: "Forbidden" };
    }

    const rows = appRepository.getExceptions().map((exception) => ({
      id: exception.id,
      kind: exception.kind,
      orderId: exception.orderId,
      receiptId: exception.receiptId ?? "",
      reason: exception.reason,
      amount: exception.amount ?? 0,
      actorName: exception.actorName,
      actorRole: exception.actorRole,
      createdAt: exception.createdAt
    }));

    reply.header("content-type", "text/csv; charset=utf-8");
    reply.header("content-disposition", `attachment; filename="${asDownloadFilename("exceptions")}"`);
    return rows.length
      ? toCsv(rows)
      : "id,kind,orderId,receiptId,reason,amount,actorName,actorRole,createdAt\n";
  });

  app.get("/api/tables/export.csv", async (request, reply) => {
    const session = requireAuth(request, reply);

    if (!session) {
      return { message: "Unauthorized" };
    }

    const canView =
      session.permissions.includes("orders.manage") ||
      session.permissions.includes("sales.view_today") ||
      session.permissions.includes("sales.view_all");

    if (!canView) {
      reply.status(403);
      return { message: "Forbidden" };
    }

    const rows = appRepository.getSnapshot().tables.map((table) => ({
      id: table.id,
      label: table.label,
      zone: table.zone,
      seats: table.seats,
      status: table.status,
      occupiedMinutes: table.occupiedMinutes,
      currentAmount: table.currentAmount,
      qrLocked: table.qrLocked,
      layoutX: table.layout.x,
      layoutY: table.layout.y,
      layoutWidth: table.layout.width,
      layoutHeight: table.layout.height,
      reservationGuestName: table.reservation?.guestName ?? "",
      reservationAt: table.reservation?.reservedAt ?? "",
      reservationPartySize: table.reservation?.partySize ?? "",
      reservationPhone: table.reservation?.contactPhone ?? "",
      reservationNote: table.reservation?.note ?? ""
    }));

    reply.header("content-type", "text/csv; charset=utf-8");
    reply.header("content-disposition", `attachment; filename="${asDownloadFilename("tables")}"`);
    return toCsv(rows);
  });

  app.get("/api/reports/backoffice", async (request, reply) => {
    const session = requireAuth(request, reply);

    if (!session) {
      return { message: "Unauthorized" };
    }

    const canViewSales =
      session.permissions.includes("sales.view_today") ||
      session.permissions.includes("sales.view_all");

    if (!canViewSales) {
      reply.status(403);
      return { message: "Forbidden" };
    }

    return {
      report: appRepository.getBackofficeReport({
        includeHr: session.permissions.includes("hr.view")
      })
    };
  });

  app.get("/api/orders/export.csv", async (request, reply) => {
    const session = requireAuth(request, reply);

    if (!session) {
      return { message: "Unauthorized" };
    }

    const canView =
      session.permissions.includes("orders.manage") ||
      session.permissions.includes("sales.view_today") ||
      session.permissions.includes("sales.view_all");

    if (!canView) {
      reply.status(403);
      return { message: "Forbidden" };
    }

    const rows = appRepository.getSnapshot().orders.flatMap((order) => {
      const orderRow = {
        section: "order",
        id: order.id,
        tableLabel: order.tableLabel,
        waiterName: order.waiterName,
        memberId: order.memberId ?? "",
        memberName: order.memberName ?? "",
        status: order.status,
        priority: order.priority,
        guests: order.guests,
        createdAt: order.createdAt,
        updatedAt: order.updatedAt,
        totalAmount: order.totalAmount
      };

      const itemRows = order.items.map((item) => ({
        section: "order_item",
        orderId: order.id,
        itemId: item.id,
        menuItemId: item.menuItemId,
        name: item.name,
        quantity: item.quantity,
        price: item.price,
        station: item.station,
        status: item.status,
        note: item.note ?? "",
        allergenFlags: item.allergenFlags.join("|"),
        modifiers: item.modifiers.map((modifier) => `${modifier.group}:${modifier.option}`).join("|")
      }));

      return [orderRow, ...itemRows];
    });

    reply.header("content-type", "text/csv; charset=utf-8");
    reply.header("content-disposition", `attachment; filename="${asDownloadFilename("orders")}"`);
    return toCsv(rows);
  });

  app.get("/api/kitchen/export.csv", async (request, reply) => {
    const session = requireAuth(request, reply);

    if (!session) {
      return { message: "Unauthorized" };
    }

    const canView =
      session.permissions.includes("orders.manage") ||
      session.permissions.includes("sales.view_today") ||
      session.permissions.includes("sales.view_all");

    if (!canView) {
      reply.status(403);
      return { message: "Forbidden" };
    }

    const rows = appRepository.getSnapshot().kitchen.map((card) => ({
      id: card.id,
      tableLabel: card.tableLabel,
      ticketNo: card.ticketNo,
      station: card.station,
      priority: card.priority,
      elapsedMinutes: card.elapsedMinutes,
      colorState: card.colorState,
      items: card.items.join(" | "),
      note: card.note ?? ""
    }));

    reply.header("content-type", "text/csv; charset=utf-8");
    reply.header("content-disposition", `attachment; filename="${asDownloadFilename("kitchen")}"`);
    return rows.length
      ? toCsv(rows)
      : "id,tableLabel,ticketNo,station,priority,elapsedMinutes,colorState,items,note\n";
  });

  app.get("/api/reports/backoffice/export.csv", async (request, reply) => {
    const session = requireAuth(request, reply);

    if (!session) {
      return { message: "Unauthorized" };
    }

    const canViewSales =
      session.permissions.includes("sales.view_today") ||
      session.permissions.includes("sales.view_all");

    if (!canViewSales) {
      reply.status(403);
      return { message: "Forbidden" };
    }

    const report = appRepository.getBackofficeReport({
      includeHr: session.permissions.includes("hr.view")
    });

    const rows = [
      {
        section: "sales_summary",
        generatedAt: report.generatedAt,
        grossSales: report.sales.grossSales,
        refundsTotal: report.sales.refundsTotal,
        tipsTotal: report.sales.tipsTotal,
        collectedTotal: report.sales.collectedTotal,
        paidOrders: report.sales.paidOrders,
        voidedOrders: report.sales.voidedOrders,
        openOrders: report.sales.openOrders,
        averageTicket: report.sales.averageTicket,
        openTables: report.sales.openTables,
        pendingPaymentTables: report.sales.pendingPaymentTables
      },
      ...report.hourlySales.map((bucket) => ({
        section: "hourly_sales",
        hour: bucket.hour,
        sales: bucket.sales,
        orders: bucket.orders
      })),
      ...report.paymentMethods.map((method) => ({
        section: "payment_method",
        method: method.method,
        amount: method.amount,
        salesAmount: method.salesAmount,
        tipAmount: method.tipAmount,
        count: method.count
      })),
      ...report.topItems.map((item) => ({
        section: "top_item",
        menuItemId: item.menuItemId,
        name: item.name,
        quantity: item.quantity,
        sales: item.sales
      })),
      ...report.staffPerformance.map((staff) => ({
        section: "staff_performance",
        staffName: staff.staffName,
        role: staff.role,
        ordersHandled: staff.ordersHandled,
        tipAmount: staff.tipAmount,
        hoursWorked: staff.hoursWorked,
        active: staff.active,
        geofenceStatus: staff.geofenceStatus
      })),
      ...report.recentGatewaySessions.map((gatewaySession) => ({
        section: "gateway_session",
        id: gatewaySession.id,
        orderId: gatewaySession.orderId,
        tableLabel: gatewaySession.tableLabel,
        method: gatewaySession.method,
        provider: gatewaySession.provider,
        amount: gatewaySession.amount,
        tipAmount: gatewaySession.tipAmount ?? 0,
        status: gatewaySession.status,
        reference: gatewaySession.reference,
        createdAt: gatewaySession.createdAt,
        expiresAt: gatewaySession.expiresAt,
        capturedAt: gatewaySession.capturedAt ?? "",
        failureReason: gatewaySession.failureReason ?? ""
      })),
      ...report.recentReceiptDispatches.map((attempt) => ({
        section: "receipt_dispatch",
        id: attempt.id,
        receiptId: attempt.receiptId,
        receiptNo: attempt.receiptNo,
        channel: attempt.channel,
        target: attempt.target,
        status: attempt.status,
        provider: attempt.provider,
        message: attempt.message ?? "",
        createdAt: attempt.createdAt
      })),
      {
        section: "receipt_ops",
        totalIssued: report.receiptOps.totalIssued,
        printedCount: report.receiptOps.printedCount,
        emailedCount: report.receiptOps.emailedCount,
        lineSharedCount: report.receiptOps.lineSharedCount,
        pendingShareCount: report.receiptOps.pendingShareCount,
        pendingPrintCount: report.receiptOps.pendingPrintCount,
        taxInvoiceCount: report.receiptOps.taxInvoiceCount,
        eTaxCount: report.receiptOps.eTaxCount,
        pendingETaxSubmissionCount: report.receiptOps.pendingETaxSubmissionCount,
        submittedETaxCount: report.receiptOps.submittedETaxCount
      },
      {
        section: "gateway_ops",
        totalSessions: report.gatewayOps.totalSessions,
        pendingCount: report.gatewayOps.pendingCount,
        capturedCount: report.gatewayOps.capturedCount,
        failedCount: report.gatewayOps.failedCount,
        expiredCount: report.gatewayOps.expiredCount,
        totalAmount: report.gatewayOps.totalAmount,
        pendingAmount: report.gatewayOps.pendingAmount
      },
      {
        section: "audit_summary",
        totalEntries: report.auditSummary.totalEntries,
        voidRefundAlerts: report.auditSummary.voidRefundAlerts,
        refundEvents: report.auditSummary.refundEvents,
        voidEvents: report.auditSummary.voidEvents,
        authEvents: report.auditSummary.authEvents,
        kitchenEvents: report.auditSummary.kitchenEvents
      }
    ];

    reply.header("content-type", "text/csv; charset=utf-8");
    reply.header("content-disposition", `attachment; filename="${asDownloadFilename("backoffice-report")}"`);
    return toCsv(rows);
  });

  app.get("/api/receipts/export.csv", async (request, reply) => {
    const session = requirePermission(request, reply, "payments.capture");

    if (!session) {
      return { message: "Forbidden" };
    }

    const rows = appRepository.getReceipts().map((receipt) => ({
      id: receipt.id,
      orderId: receipt.orderId,
      receiptNo: receipt.receiptNo,
      receiptType: receipt.receiptType,
      status: receipt.status ?? "ISSUED",
      paymentMethod: receipt.paymentMethod,
      totalAmount: receipt.totalAmount,
      tipAmount: receipt.tipAmount ?? 0,
      paidAt: receipt.paidAt,
      guestLabel: receipt.guestLabel ?? "",
      splitIndex: receipt.splitIndex ?? "",
      splitCount: receipt.splitCount ?? "",
      email: receipt.email ?? "",
      lineUserId: receipt.lineUserId ?? "",
      printerName: receipt.printerName ?? "",
      printedAt: receipt.printedAt ?? "",
      emailSharedAt: receipt.emailSharedAt ?? "",
      lineSharedAt: receipt.lineSharedAt ?? "",
      refundedAmount: receipt.refundedAmount ?? 0,
      refundedAt: receipt.refundedAt ?? "",
      refundReason: receipt.refundReason ?? "",
      taxPayerName: receipt.taxPayerName ?? "",
      taxId: receipt.taxId ?? "",
      taxIssuedAt: receipt.taxIssuedAt ?? "",
      eTaxStatus: receipt.eTaxStatus ?? "",
      eTaxSubmissionReference: receipt.eTaxSubmissionReference ?? ""
    }));

    reply.header("content-type", "text/csv; charset=utf-8");
    reply.header("content-disposition", `attachment; filename="${asDownloadFilename("receipts")}"`);
    return toCsv(rows);
  });

  app.get("/api/receipts/dispatch-attempts/export.csv", async (request, reply) => {
    const session = requirePermission(request, reply, "payments.capture");

    if (!session) {
      return { message: "Forbidden" };
    }

    const rows = appRepository.getReceiptDispatchAttempts().map((attempt) => ({
      id: attempt.id,
      receiptId: attempt.receiptId,
      receiptNo: attempt.receiptNo,
      channel: attempt.channel,
      target: attempt.target,
      status: attempt.status,
      provider: attempt.provider,
      message: attempt.message ?? "",
      createdAt: attempt.createdAt
    }));

    reply.header("content-type", "text/csv; charset=utf-8");
    reply.header("content-disposition", `attachment; filename="${asDownloadFilename("receipt-dispatches")}"`);
    return toCsv(rows);
  });

  app.get("/api/payment-sessions/export.csv", async (request, reply) => {
    const session = requirePermission(request, reply, "payments.capture");

    if (!session) {
      return { message: "Forbidden" };
    }

    const rows = appRepository.getPaymentSessions().map((paymentSession) => ({
      id: paymentSession.id,
      orderId: paymentSession.orderId,
      tableLabel: paymentSession.tableLabel,
      method: paymentSession.method,
      provider: paymentSession.provider,
      amount: paymentSession.amount,
      tipAmount: paymentSession.tipAmount ?? 0,
      status: paymentSession.status,
      reference: paymentSession.reference,
      createdAt: paymentSession.createdAt,
      expiresAt: paymentSession.expiresAt,
      capturedAt: paymentSession.capturedAt ?? "",
      failureReason: paymentSession.failureReason ?? ""
    }));

    reply.header("content-type", "text/csv; charset=utf-8");
    reply.header("content-disposition", `attachment; filename="${asDownloadFilename("payment-sessions")}"`);
    return toCsv(rows);
  });

  app.get("/api/audit/export.csv", async (request, reply) => {
    const session = requirePermission(request, reply, "audit.view");

    if (!session) {
      return { message: "Forbidden" };
    }

    const rows = appRepository.getAuditEntries().map((entry) => ({
      id: entry.id,
      actorName: entry.actorName,
      actorRole: entry.actorRole,
      action: entry.action,
      entityType: entry.entityType,
      entityId: entry.entityId,
      createdAt: entry.createdAt,
      metadata: JSON.stringify(entry.metadata ?? {})
    }));

    reply.header("content-type", "text/csv; charset=utf-8");
    reply.header("content-disposition", `attachment; filename="${asDownloadFilename("audit-feed")}"`);
    return toCsv(rows);
  });

  app.get("/api/inventory/export.csv", async (request, reply) => {
    const session = requirePermission(request, reply, "menu.manage");

    if (!session) {
      return { message: "Forbidden" };
    }

    const overview = appRepository.getInventoryOverview();
    const rows = [
      ...overview.items.map((item) => ({
        section: "inventory_item",
        id: item.id,
        name: item.name,
        category: item.category,
        unit: item.unit,
        onHand: item.onHand,
        minLevel: item.minLevel,
        reorderQty: item.reorderQty,
        avgUnitCost: item.avgUnitCost,
        supplierName: item.supplierName ?? "",
        status: item.status,
        linkedMenuItems: item.linkedMenuItems.join("|"),
        lastUpdatedAt: item.lastUpdatedAt
      })),
      ...overview.recentMovements.map((movement) => ({
        section: "stock_movement",
        id: movement.id,
        itemId: movement.itemId,
        itemName: movement.itemName,
        type: movement.type,
        quantity: movement.quantity,
        unit: movement.unit,
        note: movement.note ?? "",
        actorName: movement.actorName,
        createdAt: movement.createdAt
      })),
      ...overview.purchaseSuggestions.map((suggestion) => ({
        section: "purchase_suggestion",
        itemId: suggestion.itemId,
        itemName: suggestion.itemName,
        reorderQty: suggestion.reorderQty,
        unit: suggestion.unit,
        supplierName: suggestion.supplierName ?? ""
      }))
    ];

    reply.header("content-type", "text/csv; charset=utf-8");
    reply.header("content-disposition", `attachment; filename="${asDownloadFilename("inventory")}"`);
    return toCsv(rows);
  });
};
