import {
  KitchenLineStatus,
  Prisma,
  PrismaClient,
  ReservationStatus,
  TableStatus,
  type OrderSource,
  type OrderStatus,
  type PaymentMethod
} from "@prisma/client";
import type {
  CreateOrderRequest,
  CustomerMember,
  DeliveryPlatformConnection,
  ExceptionRecord,
  IssueTaxInvoiceRequest,
  KitchenQueueCard,
  LeaveRequest,
  MenuItemSummary,
  OrderTicket,
  PaymentSessionSummary,
  ReceiptDispatchAttempt,
  ReceiptSummary,
  RefundReceiptRequest,
  ScheduledShift,
  SecurityPolicy,
  PrintReceiptRequest,
  ShareReceiptRequest,
  SettlePaymentRequest,
  StockItem,
  StockMovement,
  SubmitEtaxRequest,
  SwapShiftRequest,
  TableLayoutPosition,
  UserAccount,
  VoidOrderRequest
} from "@mypos/domain";
import type { ActionActor, AppPersistenceAdapter } from "./types";

const kitchenStatusByAction: Record<string, KitchenLineStatus> = {
  "kitchen.ready": "READY",
  "kitchen.acknowledge": "ACKNOWLEDGED",
  "kitchen.out_of_stock": "OUT_OF_STOCK"
};

const toPrismaDeliveryPlatform = (
  platform: DeliveryPlatformConnection["platform"]
): "GRAB" | "LINE_MAN" | "FOODPANDA" | "ROBINHOOD" | "SHOPEE_FOOD" | "LALAMOVE" => {
  switch (platform) {
    case "GRAB_FOOD":
      return "GRAB";
    case "LINE_MAN":
      return "LINE_MAN";
    case "FOODPANDA":
      return "FOODPANDA";
    case "ROBINHOOD":
      return "ROBINHOOD";
    case "SHOPEE_FOOD":
      return "SHOPEE_FOOD";
    case "LALAMOVE":
      return "LALAMOVE";
    default:
      return "LINE_MAN";
  }
};

type OperationalPrismaClient = PrismaClient & {
  staffNotificationRecord: {
    upsert(
      args: Prisma.StaffNotificationRecordUpsertArgs
    ): Promise<unknown>;
  };
  kitchenChatRecord: {
    upsert(args: Prisma.KitchenChatRecordUpsertArgs): Promise<unknown>;
  };
  deliveryPlatformConnection: {
    upsert(args: object): Promise<unknown>;
  };
  exceptionRecord: {
    upsert(args: object): Promise<unknown>;
  };
  receiptDispatchAttempt: {
    upsert(args: object): Promise<unknown>;
  };
  paymentGatewaySession: {
    upsert(args: object): Promise<unknown>;
  };
};

export class PrismaPersistenceAdapter implements AppPersistenceAdapter {
  constructor(private readonly prisma: PrismaClient) {}

  private get operationalPrisma() {
    return this.prisma as OperationalPrismaClient;
  }

  async persistAuthEvent(actor: ActionActor, action: string, entityId: string) {
    const branchId = await this.resolveBranchId(actor);

    if (!branchId) {
      return;
    }

    if (entityId === actor.id && (action === "auth.login" || action === "auth.challenge_issued")) {
      await this.prisma.appUser.updateMany({
        where: { id: actor.id },
        data: {
          lastLoginAt: new Date()
        }
      });
    }

    await this.writeAuditLog(branchId, actor, action, "AUTH", entityId, {
      source: "api"
    });
  }

  async persistTableStatus(tableId: string, status: TableStatus, actor: ActionActor) {
    const table = await this.prisma.diningTable.findUnique({
      where: { id: tableId },
      select: { id: true, branchId: true }
    });

    if (!table) {
      return;
    }

    await this.prisma.diningTable.update({
      where: { id: table.id },
      data: {
        status
      }
    });

    await this.writeAuditLog(table.branchId, actor, "table.status_change", "TABLE", table.id, {
      status
    });
  }

  async persistQrTableLock(tableId: string, actor: ActionActor) {
    const table = await this.prisma.diningTable.findUnique({
      where: { id: tableId },
      select: { id: true, branchId: true }
    });

    if (!table) {
      return;
    }

    await this.prisma.diningTable.update({
      where: { id: table.id },
      data: {
        status: "LOCKED_BY_QR",
        qrLockedAt: new Date()
      }
    });

    await this.writeAuditLog(table.branchId, actor, "table.qr_lock", "TABLE", table.id, {
      status: "LOCKED_BY_QR"
    });
  }

  async persistTableCheckBillRequested(tableId: string, requestedBy: string, actor: ActionActor) {
    const table = await this.prisma.diningTable.findUnique({
      where: { id: tableId },
      select: { id: true, branchId: true }
    });

    if (!table) {
      return;
    }

    await this.prisma.diningTable.update({
      where: { id: table.id },
      data: {
        status: "PENDING_PAYMENT"
      }
    });

    await this.writeAuditLog(table.branchId, actor, "table.check_bill_requested", "TABLE", table.id, {
      requestedBy
    });
  }

  async persistTableLayout(tableId: string, layout: TableLayoutPosition, actor: ActionActor) {
    const table = await this.prisma.diningTable.findUnique({
      where: { id: tableId },
      select: { id: true, branchId: true }
    });

    if (!table) {
      return;
    }

    const branch = await this.prisma.branch.findUnique({
      where: { id: table.branchId },
      select: { floorplanJson: true }
    });

    const currentFloorplan =
      branch?.floorplanJson && typeof branch.floorplanJson === "object" && !Array.isArray(branch.floorplanJson)
        ? { ...(branch.floorplanJson as Record<string, unknown>) }
        : {};
    const layouts =
      currentFloorplan.layouts && typeof currentFloorplan.layouts === "object" && !Array.isArray(currentFloorplan.layouts)
        ? { ...(currentFloorplan.layouts as Record<string, unknown>) }
        : {};

    layouts[tableId] = layout as unknown as Prisma.InputJsonValue;

    await this.prisma.branch.update({
      where: { id: table.branchId },
      data: {
        floorplanJson: {
          ...currentFloorplan,
          layouts
        } as Prisma.InputJsonValue
      }
    });

    await this.writeAuditLog(table.branchId, actor, "table.layout_update", "TABLE", table.id, {
      x: layout.x,
      y: layout.y
    });
  }

  async persistTableReservation(table: import("@mypos/domain").DiningTable, actor: ActionActor) {
    if (!table.reservation) {
      return;
    }

    const persistedTable = await this.prisma.diningTable.findUnique({
      where: { id: table.id },
      select: { id: true, branchId: true }
    });

    if (!persistedTable) {
      return;
    }

    await this.prisma.reservation.upsert({
      where: { id: table.reservation.id },
      update: {
        customerName: table.reservation.guestName,
        customerPhone: table.reservation.contactPhone ?? "-",
        partySize: table.reservation.partySize,
        reservedAt: new Date(table.reservation.reservedAt),
        status: ReservationStatus.CONFIRMED
      },
      create: {
        id: table.reservation.id,
        branchId: persistedTable.branchId,
        tableId: persistedTable.id,
        customerName: table.reservation.guestName,
        customerPhone: table.reservation.contactPhone ?? "-",
        partySize: table.reservation.partySize,
        reservedAt: new Date(table.reservation.reservedAt),
        status: ReservationStatus.CONFIRMED
      }
    });

    await this.prisma.diningTable.update({
      where: { id: persistedTable.id },
      data: {
        status: "RESERVED"
      }
    });

    await this.writeAuditLog(persistedTable.branchId, actor, "table.reserve", "TABLE", persistedTable.id, {
      guestName: table.reservation.guestName,
      partySize: table.reservation.partySize
    });
  }

  async clearTableReservation(tableId: string, actor: ActionActor) {
    const table = await this.prisma.diningTable.findUnique({
      where: { id: tableId },
      select: { id: true, branchId: true, status: true }
    });

    if (!table) {
      return;
    }

    const reservation = await this.prisma.reservation.findFirst({
      where: {
        tableId,
        status: ReservationStatus.CONFIRMED
      },
      orderBy: {
        reservedAt: "desc"
      }
    });

    if (reservation) {
      await this.prisma.reservation.update({
        where: { id: reservation.id },
        data: {
          status: ReservationStatus.CANCELLED
        }
      });
    }

    if (table.status === "RESERVED") {
      await this.prisma.diningTable.update({
        where: { id: table.id },
        data: {
          status: "AVAILABLE"
        }
      });
    }

    await this.writeAuditLog(table.branchId, actor, "table.reservation_clear", "TABLE", table.id);
  }

  async persistOrderCreated(order: OrderTicket, payload: CreateOrderRequest, actor: ActionActor) {
    const table = await this.prisma.diningTable.findUnique({
      where: { id: payload.tableId },
      select: { id: true, branchId: true }
    });

    if (!table) {
      return;
    }

    const existing = await this.prisma.order.findUnique({
      where: { orderNo: order.id },
      select: { id: true }
    });

    if (existing) {
      return;
    }

    await this.prisma.order.create({
      data: {
        id: order.id,
        branchId: table.branchId,
        tableId: table.id,
        orderNo: order.id,
        source: (payload.source ?? "POS") as OrderSource,
        status: order.status as OrderStatus,
        priority: order.priority,
        guestCount: order.guests,
        subtotalAmount: order.totalAmount,
        discountAmount: 0,
        vatAmount: 0,
        totalAmount: order.totalAmount,
        specialNote: payload.specialNote,
        openedByUserId: actor.id,
        items: {
          create: order.items.map((item) => ({
            id: item.id,
            quantity: item.quantity,
            unitPrice: item.price,
            note: item.note,
            station: item.station,
            lineStatus: "PENDING",
            allergens: item.allergenFlags,
            modifiersJson: item.modifiers as unknown as Prisma.InputJsonValue,
            menuItem: {
              connect: {
                id: item.menuItemId
              }
            }
          }))
        },
        kitchenTickets: {
          create: this.groupKitchenTickets(order).map((ticket) => ({
            id: ticket.id,
            station: ticket.station,
            status: "PENDING"
          }))
        }
      }
    });

    await this.prisma.diningTable.update({
      where: { id: table.id },
      data: {
        status: "SEATED"
      }
    });

    await this.writeAuditLog(table.branchId, actor, "order.create", "ORDER", order.id, {
      tableId: table.id,
      totalAmount: order.totalAmount
    });
  }

  async persistKitchenTicketUpdate(ticket: KitchenQueueCard, action: string, actor: ActionActor) {
    const status = kitchenStatusByAction[action];

    if (!status) {
      return;
    }

    await this.prisma.kitchenTicket.updateMany({
      where: { id: ticket.id },
      data: {
        status,
        startedAt: status === "ACKNOWLEDGED" ? new Date() : undefined,
        finishedAt: status === "READY" ? new Date() : undefined,
        delayReason: status === "OUT_OF_STOCK" ? ticket.note ?? "Out of stock" : undefined
      }
    });

    const branchId = await this.resolveBranchId(actor);

    if (!branchId) {
      return;
    }

    await this.writeAuditLog(branchId, actor, action, "KITCHEN", ticket.id, {
      station: ticket.station,
      tableLabel: ticket.tableLabel
    });
  }

  async persistPaymentSettled(
    order: OrderTicket,
    receipt: ReceiptSummary,
    payload: SettlePaymentRequest,
    actor: ActionActor
  ) {
    const tipAmount = payload.tipAmount ?? receipt.tipAmount ?? 0;
    const chargedAmount = Number((payload.amount + tipAmount).toFixed(2));
    const existingOrder = await this.prisma.order.findUnique({
      where: { orderNo: order.id },
      select: { id: true, branchId: true, tableId: true, memberSettledAt: true }
    });

    if (!existingOrder) {
      return;
    }
    const paymentId = `PAY-${receipt.id}`;
    const existingPayment = await this.prisma.payment.findUnique({
      where: { id: paymentId },
      select: { id: true }
    });
    const existingReceipt = await this.prisma.receipt.findUnique({
      where: { receiptNo: receipt.receiptNo },
      select: { id: true }
    });

    await this.prisma.order.update({
      where: { orderNo: order.id },
      data: {
        status: "PAID",
        closedByUserId: actor.id
      }
    });

    await this.prisma.payment.upsert({
      where: {
        id: paymentId
      },
      update: {
        method: payload.method as PaymentMethod,
        amount: chargedAmount,
        tipAmount,
        referenceNo: receipt.guestLabel ?? null,
        splitGroup: receipt.splitGroupId ?? null,
        paidAt: new Date(receipt.paidAt)
      },
      create: {
        id: paymentId,
        orderId: existingOrder.id,
        method: payload.method as PaymentMethod,
        amount: chargedAmount,
        tipAmount,
        referenceNo: receipt.guestLabel ?? null,
        splitGroup: receipt.splitGroupId ?? null,
        paidAt: new Date(receipt.paidAt)
      }
    });

    await this.prisma.receipt.upsert({
      where: { receiptNo: receipt.receiptNo },
      update: {
        orderId: existingOrder.id,
        splitGroupId: receipt.splitGroupId ?? null,
        splitIndex: receipt.splitIndex ?? null,
        splitCount: receipt.splitCount ?? null,
        guestLabel: receipt.guestLabel ?? null
      } as Prisma.ReceiptUncheckedUpdateInput,
      create: {
        id: receipt.id,
        orderId: existingOrder.id,
        receiptNo: receipt.receiptNo,
        receiptType: receipt.receiptType,
        qrLookupToken: receipt.qrLookupToken,
        splitGroupId: receipt.splitGroupId ?? null,
        splitIndex: receipt.splitIndex ?? null,
        splitCount: receipt.splitCount ?? null,
        guestLabel: receipt.guestLabel ?? null
      } as Prisma.ReceiptUncheckedCreateInput
    });

    if (!existingOrder.memberSettledAt && order.memberId) {
      const existingMember = await this.prisma.customerMember.findUnique({
        where: { id: order.memberId }
      });

      if (existingMember) {
        const earnedPoints = Math.floor(order.totalAmount / 25);
        const mergedFavorites = Array.from(
          new Set([...existingMember.favoriteItems, ...order.items.map((item) => item.name)])
        ).slice(0, 5);
        const nextSpend = Number(existingMember.totalSpend) + order.totalAmount;

        await this.prisma.customerMember.update({
          where: { id: existingMember.id },
          data: {
            pointsBalance: existingMember.pointsBalance + earnedPoints,
            totalSpend: nextSpend,
            lastVisitAt: new Date(),
            favoriteItems: mergedFavorites,
            tier: nextSpend >= 15000 ? "GOLD" : nextSpend >= 5000 ? "SILVER" : "BRONZE"
          }
        });

        await this.prisma.order.update({
          where: { id: existingOrder.id },
          data: {
            memberSettledAt: new Date(receipt.paidAt)
          }
        });

        await this.writeAuditLog(existingOrder.branchId, actor, "member.points_earned", "MEMBER", existingMember.id, {
          earnedPoints,
          orderId: order.id
        });
      }
    }

    if (existingOrder.tableId) {
      await this.prisma.diningTable.update({
        where: { id: existingOrder.tableId },
        data: {
          status: "AVAILABLE",
          qrLockedAt: null
        }
      });
    }

    await this.prisma.kitchenTicket.updateMany({
      where: { orderId: existingOrder.id },
      data: {
        status: "READY",
        finishedAt: new Date(receipt.paidAt)
      }
    });

    if (!existingPayment) {
      await this.writeAuditLog(existingOrder.branchId, actor, "payment.capture", "PAYMENT", order.id, {
        amount: chargedAmount,
        baseAmount: payload.amount,
        tipAmount,
        method: payload.method
      });
    }
    if (!existingReceipt) {
      await this.writeAuditLog(existingOrder.branchId, actor, "receipt.issue", "RECEIPT", receipt.id, {
        receiptNo: receipt.receiptNo,
        tipAmount
      });
    }
  }

  async persistPaymentSession(
    session: PaymentSessionSummary,
    actor: ActionActor,
    audit?: {
      action:
        | "payment.session_create"
        | "payment.session_retry"
        | "payment.session_capture"
        | "payment.session_fail"
        | "payment.session_expire";
      metadata: Record<string, string | number | boolean>;
    }
  ) {
    const existingOrder = await this.prisma.order.findUnique({
      where: { orderNo: session.orderId },
      select: { id: true, branchId: true }
    });

    if (!existingOrder) {
      return;
    }

    await this.operationalPrisma.paymentGatewaySession.upsert({
      where: { id: session.id },
      update: {
        orderId: existingOrder.id,
        tableLabel: session.tableLabel,
        method: session.method as PaymentMethod,
        provider: session.provider,
        amount: session.amount,
        tipAmount: session.tipAmount ?? 0,
        status: session.status,
        reference: session.reference,
        qrPayload: session.qrPayload ?? null,
        checkoutUrl: session.checkoutUrl ?? null,
        failureReason: session.failureReason ?? null,
        createdAt: new Date(session.createdAt),
        expiresAt: new Date(session.expiresAt),
        capturedAt: session.capturedAt ? new Date(session.capturedAt) : null
      },
      create: {
        id: session.id,
        branchId: existingOrder.branchId,
        orderId: existingOrder.id,
        tableLabel: session.tableLabel,
        method: session.method as PaymentMethod,
        provider: session.provider,
        amount: session.amount,
        tipAmount: session.tipAmount ?? 0,
        status: session.status,
        reference: session.reference,
        qrPayload: session.qrPayload ?? null,
        checkoutUrl: session.checkoutUrl ?? null,
        failureReason: session.failureReason ?? null,
        createdAt: new Date(session.createdAt),
        expiresAt: new Date(session.expiresAt),
        capturedAt: session.capturedAt ? new Date(session.capturedAt) : null
      }
    });

    if (audit) {
      await this.writeAuditLog(existingOrder.branchId, actor, audit.action, "PAYMENT", session.orderId, audit.metadata);
    }
  }

  async persistOrderVoided(order: OrderTicket, payload: VoidOrderRequest, actor: ActionActor) {
    const existingOrder = await this.prisma.order.findUnique({
      where: { orderNo: order.id },
      select: { id: true, branchId: true, tableId: true }
    });

    if (!existingOrder) {
      return;
    }

    await this.prisma.order.update({
      where: { orderNo: order.id },
      data: {
        status: "VOIDED",
        specialNote: payload.reason
      }
    });

    if (existingOrder.tableId) {
      await this.prisma.diningTable.update({
        where: { id: existingOrder.tableId },
        data: {
          status: "AVAILABLE",
          qrLockedAt: null
        }
      });
    }

    await this.writeAuditLog(existingOrder.branchId, actor, "order.void", "ORDER", order.id, {
      reason: payload.reason
    });
  }

  async persistReceiptRefunded(
    order: OrderTicket,
    receipt: ReceiptSummary,
    payload: RefundReceiptRequest,
    actor: ActionActor
  ) {
    const existingOrder = await this.prisma.order.findUnique({
      where: { orderNo: order.id },
      select: { id: true, branchId: true }
    });

    if (!existingOrder) {
      return;
    }

    await this.prisma.receipt.updateMany({
      where: {
        id: receipt.id
      },
      data: {
        refundedAt: new Date(),
        refundedAmount: payload.amount ?? receipt.totalAmount,
        refundReason: payload.reason
      } as Prisma.ReceiptUpdateManyMutationInput
    });

    await this.writeAuditLog(existingOrder.branchId, actor, "receipt.refund", "RECEIPT", receipt.id, {
      amount: payload.amount ?? receipt.totalAmount,
      reason: payload.reason
    });
  }

  async persistReceiptShared(
    receipt: ReceiptSummary,
    payload: ShareReceiptRequest,
    actor: ActionActor
  ) {
    const existingReceipt = await this.prisma.receipt.findUnique({
      where: { id: receipt.id },
      select: { id: true, order: { select: { branchId: true } } }
    });

    if (!existingReceipt) {
      return;
    }

    await this.prisma.receipt.update({
      where: { id: receipt.id },
      data: (
        payload.channel === "EMAIL"
          ? {
              email: payload.recipient,
              emailSharedAt: receipt.emailSharedAt ? new Date(receipt.emailSharedAt) : new Date()
            }
          : {
              lineUserId: payload.recipient,
              lineSharedAt: receipt.lineSharedAt ? new Date(receipt.lineSharedAt) : new Date()
            }
      ) as Prisma.ReceiptUpdateInput
    });

    await this.writeAuditLog(existingReceipt.order.branchId, actor, "receipt.share", "RECEIPT", receipt.id, {
      channel: payload.channel,
      recipient: payload.recipient,
      receiptNo: receipt.receiptNo
    });
  }

  async persistReceiptPrinted(
    receipt: ReceiptSummary,
    payload: PrintReceiptRequest,
    actor: ActionActor
  ) {
    const existingReceipt = await this.prisma.receipt.findUnique({
      where: { id: receipt.id },
      select: { id: true, order: { select: { branchId: true } } }
    });

    if (!existingReceipt) {
      return;
    }

    await this.prisma.receipt.update({
      where: { id: receipt.id },
      data: {
        printedAt: receipt.printedAt ? new Date(receipt.printedAt) : new Date(),
        printerName: payload.printerName
      } as Prisma.ReceiptUpdateInput
    });

      await this.writeAuditLog(existingReceipt.order.branchId, actor, "receipt.print", "RECEIPT", receipt.id, {
        printerName: payload.printerName,
        copies: payload.copies ?? 1,
        receiptNo: receipt.receiptNo
      });
    }

  async persistReceiptTaxInvoiceIssued(
    receipt: ReceiptSummary,
    payload: IssueTaxInvoiceRequest,
    actor: ActionActor
  ) {
    const existingReceipt = await this.prisma.receipt.findUnique({
      where: { id: receipt.id },
      select: { id: true, order: { select: { branchId: true } } }
    });

    if (!existingReceipt) {
      return;
    }

    await this.prisma.receipt.update({
      where: { id: receipt.id },
      data: {
        receiptType: payload.receiptType,
        taxPayerName: receipt.taxPayerName ?? payload.taxPayerName,
        taxId: receipt.taxId ?? payload.taxId,
        taxBranchAddress: receipt.taxBranchAddress ?? payload.taxBranchAddress ?? null,
        taxEmail: receipt.taxEmail ?? payload.taxEmail ?? null,
        taxIssuedAt: receipt.taxIssuedAt ? new Date(receipt.taxIssuedAt) : new Date(),
        eTaxStatus: receipt.eTaxStatus ?? null,
        eTaxSubmissionReference: receipt.eTaxSubmissionReference ?? null,
        eTaxSubmittedAt: receipt.eTaxSubmittedAt ? new Date(receipt.eTaxSubmittedAt) : null,
        eTaxError: receipt.eTaxError ?? null
      } as Prisma.ReceiptUpdateInput
    });

    await this.writeAuditLog(
      existingReceipt.order.branchId,
      actor,
      "receipt.tax_invoice_issue",
      "RECEIPT",
      receipt.id,
      {
        receiptNo: receipt.receiptNo,
        receiptType: payload.receiptType,
        taxPayerName: payload.taxPayerName,
        taxId: payload.taxId
      }
    );
  }

  async persistReceiptEtaxSubmitted(
    receipt: ReceiptSummary,
    payload: SubmitEtaxRequest,
    actor: ActionActor
  ) {
    const existingReceipt = await this.prisma.receipt.findUnique({
      where: { id: receipt.id },
      select: { id: true, order: { select: { branchId: true } } }
    });

    if (!existingReceipt) {
      return;
    }

    await this.prisma.receipt.update({
      where: { id: receipt.id },
      data: {
        taxEmail: receipt.taxEmail ?? null,
        eTaxStatus: receipt.eTaxStatus ?? null,
        eTaxSubmissionReference: receipt.eTaxSubmissionReference ?? null,
        eTaxSubmittedAt: receipt.eTaxSubmittedAt ? new Date(receipt.eTaxSubmittedAt) : null,
        eTaxError: receipt.eTaxError ?? null
      } as Prisma.ReceiptUpdateInput
    });

    await this.writeAuditLog(
      existingReceipt.order.branchId,
      actor,
      "receipt.etax_submit",
      "RECEIPT",
      receipt.id,
      {
        receiptNo: receipt.receiptNo,
        channel: payload.channel,
        provider: receipt.eTaxSubmissionReference ? "RD_STUB" : "RD_STUB",
        status: receipt.eTaxStatus ?? "FAILED"
      }
    );
  }

  async persistMemberCreated(member: CustomerMember, actor: ActionActor) {
    const branchId = await this.resolveBranchId(actor);

    if (!branchId) {
      return;
    }

    await this.prisma.customerMember.upsert({
      where: { id: member.id },
      update: {
        fullName: member.fullName,
        phone: member.phone,
        tier: member.tier,
        pointsBalance: member.pointsBalance,
        totalSpend: member.totalSpend,
        lastVisitAt: member.lastVisitAt ? new Date(member.lastVisitAt) : null,
        favoriteItems: member.favoriteItems,
        preferredLanguage: member.preferredLanguage ?? null,
        birthDate: member.birthDate ? new Date(member.birthDate) : null,
        lineUserId: member.lineUserId ?? null
      },
      create: {
        id: member.id,
        branchId,
        fullName: member.fullName,
        phone: member.phone,
        tier: member.tier,
        pointsBalance: member.pointsBalance,
        totalSpend: member.totalSpend,
        lastVisitAt: member.lastVisitAt ? new Date(member.lastVisitAt) : null,
        favoriteItems: member.favoriteItems,
        preferredLanguage: member.preferredLanguage ?? null,
        birthDate: member.birthDate ? new Date(member.birthDate) : null,
        lineUserId: member.lineUserId ?? null
      }
    });

    await this.writeAuditLog(branchId, actor, "member.create", "MEMBER", member.id, {
      fullName: member.fullName
    });
  }

  async persistOrderMemberAssigned(orderId: string, memberId: string, actor: ActionActor) {
    const order = await this.prisma.order.findUnique({
      where: { orderNo: orderId },
      select: { id: true, branchId: true }
    });

    if (!order) {
      return;
    }

    await this.prisma.order.update({
      where: { id: order.id },
      data: {
        memberId
      }
    });

    await this.writeAuditLog(order.branchId, actor, "order.assign_member", "MEMBER", memberId, {
      orderId
    });
  }

  async persistInventoryMovement(item: StockItem, movement: StockMovement, actor: ActionActor) {
    const branchId = await this.resolveBranchId(actor);

    if (!branchId) {
      return;
    }

    await this.prisma.inventoryItem.upsert({
      where: { id: item.id },
      update: {
        name: item.name,
        category: item.category,
        unit: item.unit,
        onHand: item.onHand,
        minLevel: item.minLevel,
        reorderQty: item.reorderQty,
        avgUnitCost: item.avgUnitCost,
        supplierName: item.supplierName ?? null,
        linkedMenuItemIds: item.linkedMenuItems,
        recipeUsageJson: item.recipeUsage ? (item.recipeUsage as unknown as Prisma.InputJsonValue) : Prisma.JsonNull
      },
      create: {
        id: item.id,
        branchId,
        name: item.name,
        category: item.category,
        unit: item.unit,
        onHand: item.onHand,
        minLevel: item.minLevel,
        reorderQty: item.reorderQty,
        avgUnitCost: item.avgUnitCost,
        supplierName: item.supplierName ?? null,
        linkedMenuItemIds: item.linkedMenuItems,
        recipeUsageJson: item.recipeUsage ? (item.recipeUsage as unknown as Prisma.InputJsonValue) : Prisma.JsonNull
      }
    });

    await this.prisma.inventoryMovement.upsert({
      where: { id: movement.id },
      update: {
        branchId,
        itemId: item.id,
        itemName: movement.itemName,
        type: movement.type,
        quantity: movement.quantity,
        unit: movement.unit,
        note: movement.note ?? null,
        actorName: movement.actorName,
        createdAt: new Date(movement.createdAt)
      },
      create: {
        id: movement.id,
        branchId,
        itemId: item.id,
        itemName: movement.itemName,
        type: movement.type,
        quantity: movement.quantity,
        unit: movement.unit,
        note: movement.note ?? null,
        actorName: movement.actorName,
        createdAt: new Date(movement.createdAt)
      }
    });

    await this.writeAuditLog(branchId, actor, "inventory.movement", "ORDER", item.id, {
      type: movement.type,
      quantity: movement.quantity
    });
  }

  async persistScheduledShift(shift: ScheduledShift, actor: ActionActor) {
    const branchId = await this.resolveBranchId(actor);

    if (!branchId) {
      return;
    }

    await this.prisma.shiftPlan.upsert({
      where: { id: shift.id },
      update: {
        branchId,
        userId: shift.userId,
        staffName: shift.staffName,
        role: shift.role,
        shiftDate: new Date(`${shift.shiftDate}T00:00:00.000Z`),
        startTime: shift.startTime,
        endTime: shift.endTime,
        zone: shift.zone,
        status: shift.status,
        assignedByName: shift.assignedByName ?? null,
        note: shift.note ?? null
      },
      create: {
        id: shift.id,
        branchId,
        userId: shift.userId,
        staffName: shift.staffName,
        role: shift.role,
        shiftDate: new Date(`${shift.shiftDate}T00:00:00.000Z`),
        startTime: shift.startTime,
        endTime: shift.endTime,
        zone: shift.zone,
        status: shift.status,
        assignedByName: shift.assignedByName ?? null,
        note: shift.note ?? null
      }
    });

    await this.writeAuditLog(branchId, actor, "hr.schedule_create", "AUTH", shift.id, {
      userId: shift.userId,
      shiftDate: shift.shiftDate
    });
  }

  async persistLeaveRequest(request: LeaveRequest, actor: ActionActor) {
    const branchId = await this.resolveBranchId(actor);

    if (!branchId) {
      return;
    }

    await this.prisma.leaveRequest.upsert({
      where: { id: request.id },
      update: {
        branchId,
        userId: request.userId,
        staffName: request.staffName,
        leaveDate: new Date(`${request.leaveDate}T00:00:00.000Z`),
        leaveType: request.leaveType,
        reason: request.reason,
        status: request.status,
        requestedAt: new Date(request.requestedAt),
        reviewerName: request.reviewerName ?? null,
        reviewedAt: request.reviewedAt ? new Date(request.reviewedAt) : null,
        coverStaffUserId: request.coverStaffUserId ?? null,
        coverStaffName: request.coverStaffName ?? null
      },
      create: {
        id: request.id,
        branchId,
        userId: request.userId,
        staffName: request.staffName,
        leaveDate: new Date(`${request.leaveDate}T00:00:00.000Z`),
        leaveType: request.leaveType,
        reason: request.reason,
        status: request.status,
        requestedAt: new Date(request.requestedAt),
        reviewerName: request.reviewerName ?? null,
        reviewedAt: request.reviewedAt ? new Date(request.reviewedAt) : null,
        coverStaffUserId: request.coverStaffUserId ?? null,
        coverStaffName: request.coverStaffName ?? null
      }
    });

    await this.writeAuditLog(branchId, actor, "hr.leave_request", "AUTH", request.id, {
      leaveDate: request.leaveDate,
      leaveType: request.leaveType
    });
  }

  async persistLeaveReview(request: LeaveRequest, actor: ActionActor) {
    const existing = await this.prisma.leaveRequest.findUnique({
      where: { id: request.id },
      select: { id: true, branchId: true }
    });

    if (!existing) {
      await this.persistLeaveRequest(request, actor);
      return;
    }

    await this.prisma.leaveRequest.update({
      where: { id: request.id },
      data: {
        status: request.status,
        reviewerName: request.reviewerName ?? null,
        reviewedAt: request.reviewedAt ? new Date(request.reviewedAt) : null
      }
    });

    await this.writeAuditLog(existing.branchId, actor, "hr.leave_review", "AUTH", request.id, {
      status: request.status
    });
  }

  async persistSwapRequest(request: SwapShiftRequest, actor: ActionActor) {
    const branchId = await this.resolveBranchId(actor);

    if (!branchId) {
      return;
    }

    await this.prisma.swapShiftRequest.upsert({
      where: { id: request.id },
      update: {
        branchId,
        shiftPlanId: request.shiftId,
        requesterUserId: request.requesterUserId,
        requesterName: request.requesterName,
        targetUserId: request.targetUserId ?? null,
        targetStaffName: request.targetStaffName ?? null,
        shiftDate: new Date(`${request.shiftDate}T00:00:00.000Z`),
        reason: request.reason,
        status: request.status,
        requestedAt: new Date(request.requestedAt),
        reviewerName: request.reviewerName ?? null,
        reviewedAt: request.reviewedAt ? new Date(request.reviewedAt) : null
      },
      create: {
        id: request.id,
        branchId,
        shiftPlanId: request.shiftId,
        requesterUserId: request.requesterUserId,
        requesterName: request.requesterName,
        targetUserId: request.targetUserId ?? null,
        targetStaffName: request.targetStaffName ?? null,
        shiftDate: new Date(`${request.shiftDate}T00:00:00.000Z`),
        reason: request.reason,
        status: request.status,
        requestedAt: new Date(request.requestedAt),
        reviewerName: request.reviewerName ?? null,
        reviewedAt: request.reviewedAt ? new Date(request.reviewedAt) : null
      }
    });

    await this.writeAuditLog(branchId, actor, "hr.swap_request", "AUTH", request.id, {
      shiftId: request.shiftId,
      targetUserId: request.targetUserId ?? ""
    });
  }

  async persistSwapReview(request: SwapShiftRequest, actor: ActionActor) {
    const existing = await this.prisma.swapShiftRequest.findUnique({
      where: { id: request.id },
      select: { id: true, branchId: true }
    });

    if (!existing) {
      await this.persistSwapRequest(request, actor);
      return;
    }

    await this.prisma.swapShiftRequest.update({
      where: { id: request.id },
      data: {
        status: request.status,
        reviewerName: request.reviewerName ?? null,
        reviewedAt: request.reviewedAt ? new Date(request.reviewedAt) : null,
        targetUserId: request.targetUserId ?? null,
        targetStaffName: request.targetStaffName ?? null
      }
    });

    if (request.status === "APPROVED" && request.targetUserId) {
      await this.prisma.shiftPlan.update({
        where: { id: request.shiftId },
        data: {
          userId: request.targetUserId,
          staffName: request.targetStaffName ?? ""
        }
      });
    }

    await this.writeAuditLog(existing.branchId, actor, "hr.swap_review", "AUTH", request.id, {
      status: request.status
    });
  }

  async persistSecurityPolicy(policy: SecurityPolicy, actor: ActionActor) {
    const branchId = await this.resolveBranchId(actor);

    if (!branchId) {
      return;
    }

    await this.prisma.securityConfig.upsert({
      where: { branchId },
      update: {
        adminIpWhitelist: policy.adminIpWhitelist,
        twoFactorRoles: policy.twoFactorRoles,
        receiptTemplateJson: policy.receiptTemplate as unknown as Prisma.InputJsonValue
      },
      create: {
        branchId,
        adminIpWhitelist: policy.adminIpWhitelist,
        twoFactorRoles: policy.twoFactorRoles,
        receiptTemplateJson: policy.receiptTemplate as unknown as Prisma.InputJsonValue
      }
    });

    await this.writeAuditLog(branchId, actor, "security.policy_update", "AUTH", "SECURITY-POLICY", {
      adminIpWhitelist: policy.adminIpWhitelist.join(","),
      twoFactorRoles: policy.twoFactorRoles.join(","),
      receiptBusinessName: policy.receiptTemplate.businessName
    });
  }

  async persistShiftSession(shift: import("@mypos/domain").ShiftSession, actor: ActionActor) {
    const branchId = await this.resolveBranchId(actor);

    if (!branchId || !shift.userId) {
      return;
    }

    await this.prisma.shiftSession.upsert({
      where: { id: shift.id },
      update: {
        startedAt: new Date(shift.checkInAt),
        endedAt: shift.checkOutAt ? new Date(shift.checkOutAt) : null,
        roleLabel: shift.role,
        checkInLat: 13.7563,
        checkInLng: 100.5018,
        checkOutLat: shift.checkOutAt ? 13.7563 : null,
        checkOutLng: shift.checkOutAt ? 100.5018 : null,
        geofenceStatus: shift.geofenceStatus,
        distanceMeters: shift.distanceMeters ?? 0,
        tipAmount: shift.tipAmount,
        ordersHandled: shift.ordersHandled,
        deviceId: shift.deviceId,
        ipAddress: shift.ipAddress ?? "127.0.0.1"
      },
      create: {
        id: shift.id,
        branchId,
        userId: shift.userId,
        startedAt: new Date(shift.checkInAt),
        endedAt: shift.checkOutAt ? new Date(shift.checkOutAt) : null,
        roleLabel: shift.role,
        checkInLat: 13.7563,
        checkInLng: 100.5018,
        checkOutLat: shift.checkOutAt ? 13.7563 : null,
        checkOutLng: shift.checkOutAt ? 100.5018 : null,
        geofenceStatus: shift.geofenceStatus,
        distanceMeters: shift.distanceMeters ?? 0,
        tipAmount: shift.tipAmount,
        ordersHandled: shift.ordersHandled,
        deviceId: shift.deviceId,
        ipAddress: shift.ipAddress ?? "127.0.0.1"
      }
    });

    await this.writeAuditLog(
      branchId,
      actor,
      shift.checkOutAt ? "shift.clock_out" : "shift.clock_in",
      "AUTH",
      shift.id,
      {
        deviceId: shift.deviceId,
        geofenceStatus: shift.geofenceStatus
      }
    );
  }

  async persistStaffNotification(
    notification: import("@mypos/domain").StaffNotification,
    actor?: ActionActor | null
  ) {
    const branchId = actor ? await this.resolveBranchId(actor) : await this.resolveFallbackBranchId();

    if (!branchId) {
      return;
    }

    await this.operationalPrisma.staffNotificationRecord.upsert({
      where: { id: notification.id },
      update: {
        type: notification.type,
        title: notification.title,
        message: notification.message,
        audienceRole: notification.audienceRole,
        audienceUserId: notification.audienceUserId ?? null,
        tableLabel: notification.tableLabel ?? null,
        isRead: notification.read,
        createdAt: new Date(notification.createdAt)
      },
      create: {
        id: notification.id,
        branchId,
        type: notification.type,
        title: notification.title,
        message: notification.message,
        audienceRole: notification.audienceRole,
        audienceUserId: notification.audienceUserId ?? null,
        tableLabel: notification.tableLabel ?? null,
        isRead: notification.read,
        createdAt: new Date(notification.createdAt)
      }
    });

    if (actor && notification.type === "HELP_REQUEST") {
      await this.writeAuditLog(branchId, actor, "staff.request_help", "AUTH", notification.id, {
        tableLabel: notification.tableLabel ?? ""
      });
    }
  }

  async persistChatMessage(message: import("@mypos/domain").KitchenChatMessage, actor: ActionActor) {
    const branchId = await this.resolveBranchId(actor);

    if (!branchId) {
      return;
    }

    await this.operationalPrisma.kitchenChatRecord.upsert({
      where: { id: message.id },
      update: {
        fromName: message.fromName,
        fromRole: message.fromRole,
        target: message.target,
        tableLabel: message.tableLabel ?? null,
        message: message.message,
        createdAt: new Date(message.createdAt)
      },
      create: {
        id: message.id,
        branchId,
        fromName: message.fromName,
        fromRole: message.fromRole,
        target: message.target,
        tableLabel: message.tableLabel ?? null,
        message: message.message,
        createdAt: new Date(message.createdAt)
      }
    });

    await this.writeAuditLog(branchId, actor, "staff.chat_message", "KITCHEN", message.id, {
      target: message.target,
      tableLabel: message.tableLabel ?? ""
    });
  }

  async persistExceptionRecord(record: ExceptionRecord, actor: ActionActor) {
    const branchId = await this.resolveBranchId(actor);

    if (!branchId) {
      return;
    }

    await this.operationalPrisma.exceptionRecord.upsert({
      where: { id: record.id },
      update: {
        kind: record.kind,
        orderId: record.orderId,
        receiptId: record.receiptId ?? null,
        reason: record.reason,
        amount: record.amount ?? null,
        actorName: record.actorName,
        actorRole: record.actorRole,
        createdAt: new Date(record.createdAt)
      },
      create: {
        id: record.id,
        branchId,
        kind: record.kind,
        orderId: record.orderId,
        receiptId: record.receiptId ?? null,
        reason: record.reason,
        amount: record.amount ?? null,
        actorName: record.actorName,
        actorRole: record.actorRole,
        createdAt: new Date(record.createdAt)
      }
    });
  }

  async persistReceiptDispatchAttempt(attempt: ReceiptDispatchAttempt, actor: ActionActor) {
    const branchId = await this.resolveBranchId(actor);

    if (!branchId) {
      return;
    }

    await this.operationalPrisma.receiptDispatchAttempt.upsert({
      where: { id: attempt.id },
      update: {
        receiptId: attempt.receiptId,
        receiptNo: attempt.receiptNo,
        channel: attempt.channel,
        target: attempt.target,
        status: attempt.status,
        provider: attempt.provider,
        message: attempt.message ?? null,
        createdAt: new Date(attempt.createdAt)
      },
      create: {
        id: attempt.id,
        branchId,
        receiptId: attempt.receiptId,
        receiptNo: attempt.receiptNo,
        channel: attempt.channel,
        target: attempt.target,
        status: attempt.status,
        provider: attempt.provider,
        message: attempt.message ?? null,
        createdAt: new Date(attempt.createdAt)
      }
    });
  }

  async persistDeliveryPlatformConnection(
    platform: DeliveryPlatformConnection,
    actor: ActionActor,
    audit?: {
      action: "delivery.platform_toggle" | "delivery.menu_sync";
      metadata: Record<string, string | number | boolean>;
    }
  ) {
    const branchId = await this.resolveBranchId(actor);

    if (!branchId) {
      return;
    }

    await this.operationalPrisma.deliveryPlatformConnection.upsert({
      where: {
        branchId_platform: {
          branchId,
          platform: toPrismaDeliveryPlatform(platform.platform)
        }
      },
      update: {
        displayName: platform.displayName,
        enabled: platform.enabled,
        acceptsOrders: platform.acceptsOrders,
        menuSyncState: platform.menuSyncState,
        lastSyncAt: platform.lastSyncAt ? new Date(platform.lastSyncAt) : null,
        commissionRate: platform.commissionRate
      },
      create: {
        branchId,
        platform: toPrismaDeliveryPlatform(platform.platform),
        displayName: platform.displayName,
        enabled: platform.enabled,
        acceptsOrders: platform.acceptsOrders,
        menuSyncState: platform.menuSyncState,
        lastSyncAt: platform.lastSyncAt ? new Date(platform.lastSyncAt) : null,
        commissionRate: platform.commissionRate
      }
    });

    await this.writeAuditLog(
      branchId,
      actor,
      audit?.action ?? "delivery.platform_config_sync",
      "ORDER",
      platform.platform,
      audit?.metadata ?? {
        enabled: platform.enabled,
        menuSyncState: platform.menuSyncState
      }
    );
  }

  async persistUserAccountCreated(user: UserAccount, actor: ActionActor) {
    const branchId = await this.resolveBranchId(actor);

    if (!branchId) {
      return;
    }

    await this.prisma.appUser.upsert({
      where: { username: user.username },
      update: {
        displayName: user.displayName,
        role: user.role,
        branchId,
        isActive: user.accountStatus === "ACTIVE",
        accountExpires: user.expiresAt ? new Date(user.expiresAt) : null,
        blockedAt: user.blockedAt ? new Date(user.blockedAt) : null,
        forceLogoutAfter: user.forceLogoutAfter ? new Date(user.forceLogoutAfter) : null,
        lastLoginAt: user.lastLoginAt ? new Date(user.lastLoginAt) : null
      },
      create: {
        id: user.id,
        username: user.username,
        displayName: user.displayName,
        role: user.role,
        branchId,
        pinHash: user.pin,
        isActive: (user.accountStatus ?? "ACTIVE") === "ACTIVE",
        accountExpires: user.expiresAt ? new Date(user.expiresAt) : null,
        blockedAt: user.blockedAt ? new Date(user.blockedAt) : null,
        forceLogoutAfter: user.forceLogoutAfter ? new Date(user.forceLogoutAfter) : null,
        lastLoginAt: user.lastLoginAt ? new Date(user.lastLoginAt) : null
      }
    });

    await this.writeAuditLog(branchId, actor, "user.create", "AUTH", user.id, {
      username: user.username,
      role: user.role
    });
  }

  async persistUserAccountUpdated(user: UserAccount, actor: ActionActor) {
    const existing = await this.prisma.appUser.findFirst({
      where: {
        OR: [{ id: user.id }, { username: user.username }]
      },
      select: { id: true }
    });

    if (!existing) {
      await this.persistUserAccountCreated(user, actor);
      return;
    }

    await this.prisma.appUser.update({
      where: { id: existing.id },
      data: {
        displayName: user.displayName,
        role: user.role,
        pinHash: user.pin,
        isActive: (user.accountStatus ?? "ACTIVE") === "ACTIVE",
        accountExpires: user.expiresAt ? new Date(user.expiresAt) : null,
        blockedAt: user.blockedAt ? new Date(user.blockedAt) : null,
        forceLogoutAfter: user.forceLogoutAfter ? new Date(user.forceLogoutAfter) : null,
        lastLoginAt: user.lastLoginAt ? new Date(user.lastLoginAt) : null
      }
    });

    const branchId = await this.resolveBranchId(actor);

    if (!branchId) {
      return;
    }

    await this.writeAuditLog(branchId, actor, "user.update", "AUTH", user.id, {
      username: user.username,
      role: user.role,
      accountStatus: user.accountStatus ?? "ACTIVE"
    });
  }

  async persistUserAccountForcedLogout(user: UserAccount, actor: ActionActor) {
    await this.persistUserAccountUpdated(user, actor);

    const branchId = await this.resolveBranchId(actor);

    if (!branchId) {
      return;
    }

    await this.writeAuditLog(branchId, actor, "user.force_logout", "AUTH", user.id, {
      username: user.username
    });
  }

  async persistMenuItemCreated(menuItem: MenuItemSummary, actor: ActionActor) {
    const branchId = await this.resolveBranchId(actor);

    if (!branchId) {
      return;
    }

    const category = await this.ensureMenuCategory(branchId, menuItem.category);

    await this.prisma.menuItem.upsert({
      where: { id: menuItem.id },
      update: {
        categoryId: category.id,
        name: menuItem.name,
        description: menuItem.description,
        basePrice: menuItem.price,
        happyHourPrice: menuItem.happyHourPrice ?? null,
        imageUrl: menuItem.imageUrl,
        isActive: menuItem.inStock,
        allergenInfo: menuItem.allergenInfo ?? menuItem.tags,
        translationsJson: menuItem.translations
          ? (menuItem.translations as Prisma.InputJsonValue)
          : Prisma.JsonNull,
        station: this.resolveKitchenStation(menuItem)
      },
      create: {
        id: menuItem.id,
        branchId,
        categoryId: category.id,
        name: menuItem.name,
        description: menuItem.description,
        basePrice: menuItem.price,
        happyHourPrice: menuItem.happyHourPrice ?? null,
        imageUrl: menuItem.imageUrl,
        isActive: menuItem.inStock,
        allergenInfo: menuItem.allergenInfo ?? menuItem.tags,
        translationsJson: menuItem.translations
          ? (menuItem.translations as Prisma.InputJsonValue)
          : Prisma.JsonNull,
        station: this.resolveKitchenStation(menuItem)
      }
    });

    await this.syncMenuModifierGroups(menuItem.id, menuItem.modifierGroups);

    await this.writeAuditLog(branchId, actor, "menu.create", "ORDER", menuItem.id, {
      name: menuItem.name,
      price: menuItem.price
    });
  }

  async persistMenuItemUpdated(menuItem: MenuItemSummary, actor: ActionActor) {
    const existingItem = await this.prisma.menuItem.findUnique({
      where: { id: menuItem.id },
      select: { id: true, branchId: true }
    });

    if (!existingItem) {
      await this.persistMenuItemCreated(menuItem, actor);
      return;
    }

    const category = await this.ensureMenuCategory(existingItem.branchId, menuItem.category);

    await this.prisma.menuItem.update({
      where: { id: menuItem.id },
      data: {
        categoryId: category.id,
        name: menuItem.name,
        description: menuItem.description,
        basePrice: menuItem.price,
        happyHourPrice: menuItem.happyHourPrice ?? null,
        imageUrl: menuItem.imageUrl,
        isActive: menuItem.inStock,
        allergenInfo: menuItem.allergenInfo ?? menuItem.tags,
        translationsJson: menuItem.translations
          ? (menuItem.translations as Prisma.InputJsonValue)
          : Prisma.JsonNull,
        station: this.resolveKitchenStation(menuItem)
      }
    });

    await this.syncMenuModifierGroups(menuItem.id, menuItem.modifierGroups);

    await this.writeAuditLog(existingItem.branchId, actor, "menu.update", "ORDER", menuItem.id, {
      price: menuItem.price,
      inStock: menuItem.inStock
    });
  }

  private async syncMenuModifierGroups(
    menuItemId: string,
    modifierGroups: MenuItemSummary["modifierGroups"]
  ) {
    await this.prisma.modifierOption.deleteMany({
      where: {
        modifierGroup: {
          menuItemId
        }
      }
    });

    await this.prisma.modifierGroup.deleteMany({
      where: {
        menuItemId
      }
    });

    for (const group of modifierGroups ?? []) {
      await this.prisma.modifierGroup.create({
        data: {
          id: group.id,
          menuItemId,
          name: group.name,
          minSelect: group.required ? 1 : 0,
          maxSelect: group.multiSelect ? Math.max(group.options.length, 1) : 1,
          options: {
            create: group.options.map((option) => ({
              id: option.id,
              name: option.label,
              extraPrice: option.extraPrice
            }))
          }
        }
      });
    }
  }

  private async resolveBranchId(actor: ActionActor) {
    const user = await this.prisma.appUser.findUnique({
      where: { id: actor.id },
      select: { branchId: true }
    });

    if (user?.branchId) {
      return user.branchId;
    }

    const branch = await this.prisma.branch.findFirst({
      select: { id: true }
    });

    return branch?.id ?? null;
  }

  private async resolveFallbackBranchId() {
    const branch = await this.prisma.branch.findFirst({
      select: { id: true }
    });

    return branch?.id ?? null;
  }

  private async writeAuditLog(
    branchId: string,
    actor: ActionActor,
    action: string,
    entityType: string,
    entityId: string,
    metadata?: Record<string, string | number | boolean>
  ) {
    await this.prisma.auditLog.create({
      data: {
        branchId,
        actorId: actor.id,
        actorRole: actor.role,
        action,
        entityType,
        entityId,
        metadata: metadata ?? {}
      }
    });
  }

  private groupKitchenTickets(order: OrderTicket) {
    const numericOrderId = order.id.replace(/\D+/g, "") || order.id;
    const stations = Array.from(new Set(order.items.map((item) => item.station)));

    return stations.map((station, index) => ({
      id: `K-${numericOrderId}-${index + 1}`,
      station
    }));
  }

  private async ensureMenuCategory(branchId: string, categoryName: string) {
    const existingCategory = await this.prisma.menuCategory.findFirst({
      where: {
        branchId,
        name: categoryName
      }
    });

    if (existingCategory) {
      return existingCategory;
    }

    return this.prisma.menuCategory.create({
      data: {
        branchId,
        name: categoryName
      }
    });
  }

  private resolveKitchenStation(menuItem: MenuItemSummary) {
    if (menuItem.tags.includes("bar") || menuItem.category.toLowerCase().includes("cocktail")) {
      return "BAR";
    }

    return "HOT";
  }
}
