import {
  KitchenLineStatus,
  Prisma,
  PrismaClient,
  type AppUser,
  type AuditLog,
  type Branch,
  type CustomerMember,
  type DiningTable,
  type InventoryItem,
  type InventoryMovement,
  type KitchenChatRecord,
  type LeaveRequest,
  type Reservation,
  type SecurityConfig,
  type ShiftPlan,
  type ShiftSession,
  type StaffNotificationRecord,
  type SwapShiftRequest
} from "@prisma/client";
import type { MutableAppState } from "./types";

type MenuItemWithCategory = Prisma.MenuItemGetPayload<{
  include: {
    category: true;
    modifierGroups: {
      include: {
        options: true;
      };
    };
  };
}>;

type OrderWithRelations = Prisma.OrderGetPayload<{
  include: {
    table: true;
    items: {
      include: {
        menuItem: true;
      };
    };
    kitchenTickets: true;
    payments: {
      orderBy: {
        paidAt: "asc";
      };
    };
    receipts: {
      orderBy: [
        {
          splitIndex: "asc";
        },
        {
          receiptNo: "asc";
        }
      ];
    };
  };
}>;

type DeliveryOrderWithRelations = Prisma.DeliveryOrderGetPayload<{
  include: {
    order: {
      include: {
        items: {
          include: {
            menuItem: true;
          };
        };
      };
    };
  };
}>;

type DeliveryPlatformConfigRecord = {
  platform: "GRAB" | "LINE_MAN" | "FOODPANDA" | "ROBINHOOD" | "SHOPEE_FOOD" | "LALAMOVE";
  displayName: string;
  enabled: boolean;
  acceptsOrders: boolean;
  menuSyncState: string;
  lastSyncAt: Date | null;
  commissionRate: { toNumber: () => number } | number;
};

type PrismaExceptionRecord = {
  id: string;
  kind: string;
  orderId: string;
  receiptId: string | null;
  reason: string;
  amount: { toNumber: () => number } | number | null;
  actorName: string;
  actorRole: string;
  createdAt: Date;
};

type PrismaReceiptDispatchRecord = {
  id: string;
  receiptId: string;
  receiptNo: string;
  channel: string;
  target: string;
  status: string;
  provider: string;
  message: string | null;
  createdAt: Date;
};

type PrismaPaymentGatewaySessionRecord = {
  id: string;
  orderId: string;
  tableLabel: string;
  method: string;
  provider: string;
  amount: { toNumber: () => number } | number;
  tipAmount: { toNumber: () => number } | number;
  status: string;
  reference: string;
  qrPayload: string | null;
  checkoutUrl: string | null;
  failureReason: string | null;
  createdAt: Date;
  expiresAt: Date;
  capturedAt: Date | null;
  order: {
    orderNo: string;
  };
};

type OperationalPrismaClient = PrismaClient & {
  staffNotificationRecord: {
    findMany(
      args: Prisma.StaffNotificationRecordFindManyArgs
    ): Promise<StaffNotificationRecord[]>;
  };
  kitchenChatRecord: {
    findMany(args: Prisma.KitchenChatRecordFindManyArgs): Promise<KitchenChatRecord[]>;
  };
  deliveryPlatformConnection: {
    findMany(args: object): Promise<DeliveryPlatformConfigRecord[]>;
  };
  exceptionRecord: {
    findMany(args: object): Promise<PrismaExceptionRecord[]>;
  };
  receiptDispatchAttempt: {
    findMany(args: object): Promise<PrismaReceiptDispatchRecord[]>;
  };
  paymentGatewaySession: {
    findMany(args: object): Promise<PrismaPaymentGatewaySessionRecord[]>;
  };
};

const toDomainDeliveryPlatform = (
  platform: DeliveryPlatformConfigRecord["platform"]
): MutableAppState["deliveryPlatforms"][number]["platform"] => {
  switch (platform) {
    case "GRAB":
      return "GRAB_FOOD";
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

const toDomainDeliveryStatus = (
  status: "RECEIVED" | "ACCEPTED" | "PREPARING" | "READY_FOR_PICKUP" | "PICKED_UP" | "DELIVERED" | "CANCELLED"
): MutableAppState["deliveryOrders"][number]["status"] => {
  switch (status) {
    case "RECEIVED":
      return "NEW";
    case "ACCEPTED":
      return "ACCEPTED";
    case "PREPARING":
      return "PREPARING";
    case "READY_FOR_PICKUP":
      return "READY_FOR_PICKUP";
    case "PICKED_UP":
      return "OUT_FOR_DELIVERY";
    case "DELIVERED":
      return "COMPLETED";
    case "CANCELLED":
      return "CANCELLED";
    default:
      return "NEW";
  }
};

const toDecimalNumber = (value: { toNumber: () => number } | number | null | undefined) => {
  if (typeof value === "number") {
    return value;
  }

  if (value && typeof value.toNumber === "function") {
    return value.toNumber();
  }

  return 0;
};

const toModifierSelections = (value: Prisma.JsonValue | null | undefined) => {
  if (!value || !Array.isArray(value)) {
    return [];
  }

  return value.flatMap((entry) => {
    if (!entry || typeof entry !== "object" || Array.isArray(entry)) {
      return [];
    }

    const group = "group" in entry && typeof entry.group === "string" ? entry.group : null;
    const option = "option" in entry && typeof entry.option === "string" ? entry.option : null;
    const extraPrice =
      "extraPrice" in entry && typeof entry.extraPrice === "number" ? entry.extraPrice : 0;

    if (!group || !option) {
      return [];
    }

    return [
      {
        group,
        option,
        extraPrice
      }
    ];
  });
};

const toMenuTranslations = (value: Prisma.JsonValue | null | undefined) => {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return undefined;
  }

  const normalized = Object.entries(value).reduce<
    Partial<Record<"th" | "en" | "zh" | "ja", { name: string; category: string; description?: string }>>
  >((accumulator, [language, translation]) => {
    if (
      (language === "th" || language === "en" || language === "zh" || language === "ja") &&
      translation &&
      typeof translation === "object" &&
      !Array.isArray(translation) &&
      "name" in translation &&
      "category" in translation &&
      typeof translation.name === "string" &&
      typeof translation.category === "string"
    ) {
      accumulator[language] = {
        name: translation.name,
        category: translation.category,
        description:
          "description" in translation && typeof translation.description === "string"
            ? translation.description
            : undefined
      };
    }

    return accumulator;
  }, {});

  return Object.keys(normalized).length > 0 ? normalized : undefined;
};

export const connectPrismaClient = async () => {
  if (!process.env.DATABASE_URL) {
    return null;
  }

  const prisma = new PrismaClient();

  try {
    await prisma.$connect();
    return prisma;
  } catch {
    await prisma.$disconnect();
    return null;
  }
};

export const loadStateFromPrisma = async (
  prisma: PrismaClient
): Promise<Partial<MutableAppState> | null> => {
  try {
    const now = Date.now();
    const operationalPrisma = prisma as OperationalPrismaClient;

    const [
      branch,
      securityConfig,
      users,
      tables,
      reservations,
      customers,
      inventoryItems,
      inventoryMovements,
      shiftPlans,
      leaveRequests,
      swapShiftRequests,
      shiftSessions,
      staffNotifications,
      kitchenChats,
      menuItems,
      orders,
      auditLogs,
      receiptDispatchAttempts,
      paymentGatewaySessions
    ]: [
      Pick<Branch, "floorplanJson"> | null,
      SecurityConfig | null,
      AppUser[],
      DiningTable[],
      Reservation[],
      CustomerMember[],
      InventoryItem[],
      InventoryMovement[],
      ShiftPlan[],
      LeaveRequest[],
      SwapShiftRequest[],
      ShiftSession[],
      StaffNotificationRecord[],
      KitchenChatRecord[],
      MenuItemWithCategory[],
      OrderWithRelations[],
      AuditLog[],
      PrismaReceiptDispatchRecord[],
      PrismaPaymentGatewaySessionRecord[]
    ] = await Promise.all([
      prisma.branch.findFirst({
        select: {
          floorplanJson: true
        }
      }),
      prisma.securityConfig.findFirst(),
      prisma.appUser.findMany(),
      prisma.diningTable.findMany(),
      prisma.reservation.findMany({
        where: {
          status: "CONFIRMED"
        },
        orderBy: {
          reservedAt: "desc"
        }
      }),
      prisma.customerMember.findMany({
        orderBy: {
          createdAt: "desc"
        }
      }),
      prisma.inventoryItem.findMany({
        orderBy: {
          updatedAt: "desc"
        }
      }),
      prisma.inventoryMovement.findMany({
        orderBy: {
          createdAt: "desc"
        },
        take: 50
      }),
      prisma.shiftPlan.findMany({
        orderBy: {
          shiftDate: "asc"
        }
      }),
      prisma.leaveRequest.findMany({
        orderBy: {
          requestedAt: "desc"
        }
      }),
      prisma.swapShiftRequest.findMany({
        orderBy: {
          requestedAt: "desc"
        }
      }),
      prisma.shiftSession.findMany({
        orderBy: {
          startedAt: "desc"
        }
      }),
      operationalPrisma.staffNotificationRecord.findMany({
        orderBy: {
          createdAt: "desc"
        },
        take: 100
      }),
      operationalPrisma.kitchenChatRecord.findMany({
        orderBy: {
          createdAt: "desc"
        },
        take: 100
      }),
      prisma.menuItem.findMany({
        include: {
          category: true,
          modifierGroups: {
            include: {
              options: true
            }
          }
        }
      }),
      prisma.order.findMany({
        include: {
          table: true,
          items: {
            include: {
              menuItem: true
            }
          },
          kitchenTickets: true,
          payments: true,
          receipts: true
        },
        orderBy: {
          createdAt: "desc"
        }
      }),
      prisma.auditLog.findMany({
        orderBy: {
          createdAt: "desc"
        },
        take: 50
      }),
      operationalPrisma.receiptDispatchAttempt.findMany({
        orderBy: {
          createdAt: "desc"
        },
        take: 50
      }),
      operationalPrisma.paymentGatewaySession.findMany({
        include: {
          order: {
            select: {
              orderNo: true
            }
          }
        },
        orderBy: {
          createdAt: "desc"
        },
        take: 50
      })
    ]);

    const deliveryPlatformConfigs = await operationalPrisma.deliveryPlatformConnection.findMany({
      orderBy: {
        displayName: "asc"
      }
    });
    const deliveryOrders = (await (
      prisma as PrismaClient & {
        deliveryOrder: {
          findMany(args: object): Promise<DeliveryOrderWithRelations[]>;
        };
      }
    ).deliveryOrder.findMany({
      include: {
        order: {
          include: {
            items: {
              include: {
                menuItem: true
              }
            }
          }
        }
      },
      orderBy: {
        placedAt: "desc"
      }
    })) as DeliveryOrderWithRelations[];
    const exceptionRecords = await operationalPrisma.exceptionRecord.findMany({
      orderBy: {
        createdAt: "desc"
      },
      take: 100
    });

    const floorplanLayouts =
      branch?.floorplanJson &&
      typeof branch.floorplanJson === "object" &&
      !Array.isArray(branch.floorplanJson) &&
      "layouts" in branch.floorplanJson &&
      branch.floorplanJson.layouts &&
      typeof branch.floorplanJson.layouts === "object" &&
      !Array.isArray(branch.floorplanJson.layouts)
        ? (branch.floorplanJson.layouts as Record<
            string,
            { x?: number; y?: number; width?: number; height?: number }
          >)
        : {};
    const reservationMap = new Map(
      reservations.map((reservation) => [reservation.tableId ?? "", reservation])
    );
    const userMap = new Map(users.map((user) => [user.id, user.displayName]));
    const activeTableOrders = orders.filter(
      (order) => order.tableId && order.status !== "PAID" && order.status !== "VOIDED"
    );
    const tableAmountMap = new Map<string, number>();
    const tableStartedAtMap = new Map<string, number>();

    for (const order of activeTableOrders) {
      if (!order.tableId) {
        continue;
      }

      tableAmountMap.set(
        order.tableId,
        (tableAmountMap.get(order.tableId) ?? 0) + toDecimalNumber(order.totalAmount)
      );

      const existingStartedAt = tableStartedAtMap.get(order.tableId);
      const orderStartedAt = order.createdAt.getTime();
      tableStartedAtMap.set(
        order.tableId,
        typeof existingStartedAt === "number"
          ? Math.min(existingStartedAt, orderStartedAt)
          : orderStartedAt
      );
    }
    const elapsedMinutesFromDate = (date: Date | null | undefined) =>
      Math.max(Math.floor((now - new Date(date ?? now).getTime()) / 60000), 0);
    const toItemStatus = (status: KitchenLineStatus) => {
      switch (status) {
        case "READY":
          return "READY";
        case "IN_PROGRESS":
        case "ACKNOWLEDGED":
          return "IN_PROGRESS";
        default:
          return "SENT_TO_KITCHEN";
      }
    };
    const toColorState = (status: KitchenLineStatus, priority: string, elapsedMinutes: number) => {
      if (status === "READY") {
        return "GREEN";
      }

      if (priority === "VIP") {
        return "PURPLE";
      }

      if (status === "OUT_OF_STOCK" || elapsedMinutes >= 15) {
        return "BLUE";
      }

      if (elapsedMinutes >= 5) {
        return "YELLOW";
      }

      return "RED";
    };

    return {
      users: users.map((user) => ({
        id: user.id,
        username: user.username,
        displayName: user.displayName,
        role: user.role,
        branchId: user.branchId,
        pin: user.pinHash,
        accountStatus: user.isActive ? "ACTIVE" : "BLOCKED",
        expiresAt: user.accountExpires?.toISOString(),
        blockedAt: user.blockedAt?.toISOString(),
        forceLogoutAfter: user.forceLogoutAfter?.toISOString(),
        lastLoginAt: user.lastLoginAt?.toISOString()
      })),
      securityPolicy: securityConfig
        ? {
            adminIpWhitelist: securityConfig.adminIpWhitelist,
            twoFactorRoles: securityConfig.twoFactorRoles as Array<"OWNER" | "MANAGER" | "CASHIER" | "STAFF" | "KITCHEN">,
            receiptTemplate:
              (securityConfig.receiptTemplateJson as MutableAppState["securityPolicy"]["receiptTemplate"] | null) ?? {
                businessName: "MyPOS Night Kitchen",
                branchLabel: "Bangkok Riverside Branch",
                footerMessage: "Thank you and see you again.",
                contactLine: "LINE OA: @myposnight · 02-123-4567",
                showQrLookupOnPrint: true,
                showTipLine: true
              }
          }
        : undefined,
      tables: tables.map((table, index) => ({
        ...(reservationMap.has(table.id)
          ? {
              reservation: {
                id: reservationMap.get(table.id)!.id,
                guestName: reservationMap.get(table.id)!.customerName,
                reservedAt: reservationMap.get(table.id)!.reservedAt.toISOString(),
                partySize: reservationMap.get(table.id)!.partySize,
                contactPhone: reservationMap.get(table.id)!.customerPhone
              }
            }
          : {}),
        id: table.id,
        label: table.label,
        seats: table.seats,
        zone: table.zone,
        status: table.status,
        occupiedMinutes: tableStartedAtMap.has(table.id)
          ? elapsedMinutesFromDate(new Date(tableStartedAtMap.get(table.id)!))
          : 0,
        currentAmount: tableAmountMap.get(table.id) ?? 0,
        qrLocked: Boolean(table.qrLockedAt),
        layout: {
          x: floorplanLayouts[table.id]?.x ?? 8 + (index % 4) * 22,
          y: floorplanLayouts[table.id]?.y ?? 10 + Math.floor(index / 4) * 24,
          width: floorplanLayouts[table.id]?.width ?? (table.seats >= 6 ? 34 : table.seats >= 4 ? 28 : 22),
          height: floorplanLayouts[table.id]?.height ?? (table.seats >= 6 ? 24 : 20)
        }
      })),
      menu: menuItems.map((item) => ({
        id: item.id,
        category: item.category.name,
        name: item.name,
        price: toDecimalNumber(item.basePrice),
        imageUrl: item.imageUrl ?? "",
        tags: item.allergenInfo,
        description: item.description ?? undefined,
        allergenInfo: item.allergenInfo,
        inStock: item.isActive,
        happyHourPrice: item.happyHourPrice ? toDecimalNumber(item.happyHourPrice) : undefined,
        translations: toMenuTranslations(item.translationsJson),
        modifierGroups: item.modifierGroups.map((group) => ({
          id: group.id,
          name: group.name,
          required: group.minSelect > 0,
          multiSelect: group.maxSelect !== 1,
          options: group.options.map((option) => ({
            id: option.id,
            label: option.name,
            extraPrice: toDecimalNumber(option.extraPrice)
          }))
        }))
      })),
      members: customers.map((member) => ({
        id: member.id,
        fullName: member.fullName,
        phone: member.phone,
        tier: member.tier as "BRONZE" | "SILVER" | "GOLD",
        pointsBalance: member.pointsBalance,
        totalSpend: toDecimalNumber(member.totalSpend),
        lastVisitAt: member.lastVisitAt?.toISOString(),
        favoriteItems: member.favoriteItems,
        preferredLanguage: member.preferredLanguage as "th" | "en" | "zh" | "ja" | undefined,
        birthDate: member.birthDate?.toISOString().slice(0, 10),
        lineUserId: member.lineUserId ?? undefined
      })),
      inventoryItems: inventoryItems.map((item) => ({
        id: item.id,
        name: item.name,
        category: item.category,
        unit: item.unit as MutableAppState["inventoryItems"][number]["unit"],
        onHand: toDecimalNumber(item.onHand),
        minLevel: toDecimalNumber(item.minLevel),
        reorderQty: toDecimalNumber(item.reorderQty),
        avgUnitCost: toDecimalNumber(item.avgUnitCost),
        supplierName: item.supplierName ?? undefined,
        linkedMenuItems: item.linkedMenuItemIds,
        recipeUsage:
          item.recipeUsageJson && Array.isArray(item.recipeUsageJson)
            ? (item.recipeUsageJson as unknown as MutableAppState["inventoryItems"][number]["recipeUsage"])
            : undefined,
        status:
          toDecimalNumber(item.onHand) <= 0
            ? "OUT_OF_STOCK"
            : toDecimalNumber(item.onHand) <= toDecimalNumber(item.minLevel)
              ? "LOW_STOCK"
              : "IN_STOCK",
        lastUpdatedAt: item.updatedAt.toISOString()
      })),
      stockMovements: inventoryMovements.map((movement) => ({
        id: movement.id,
        itemId: movement.itemId,
        itemName: movement.itemName,
        type: movement.type as MutableAppState["stockMovements"][number]["type"],
        quantity: toDecimalNumber(movement.quantity),
        unit: movement.unit as MutableAppState["stockMovements"][number]["unit"],
        note: movement.note ?? undefined,
        createdAt: movement.createdAt.toISOString(),
        actorName: movement.actorName
      })),
      scheduledShifts: shiftPlans.map((shift) => ({
        id: shift.id,
        userId: shift.userId,
        staffName: shift.staffName,
        role: shift.role as MutableAppState["scheduledShifts"][number]["role"],
        shiftDate: shift.shiftDate.toISOString().slice(0, 10),
        startTime: shift.startTime,
        endTime: shift.endTime,
        zone: shift.zone,
        status: shift.status as MutableAppState["scheduledShifts"][number]["status"],
        assignedByName: shift.assignedByName ?? undefined,
        note: shift.note ?? undefined
      })),
      leaveRequests: leaveRequests.map((request) => ({
        id: request.id,
        userId: request.userId,
        staffName: request.staffName,
        leaveDate: request.leaveDate.toISOString().slice(0, 10),
        leaveType: request.leaveType as MutableAppState["leaveRequests"][number]["leaveType"],
        reason: request.reason,
        status: request.status as MutableAppState["leaveRequests"][number]["status"],
        requestedAt: request.requestedAt.toISOString(),
        reviewerName: request.reviewerName ?? undefined,
        reviewedAt: request.reviewedAt?.toISOString(),
        coverStaffUserId: request.coverStaffUserId ?? undefined,
        coverStaffName: request.coverStaffName ?? undefined
      })),
      swapRequests: swapShiftRequests.map((request) => ({
        id: request.id,
        shiftId: request.shiftPlanId,
        requesterUserId: request.requesterUserId,
        requesterName: request.requesterName,
        targetUserId: request.targetUserId ?? undefined,
        targetStaffName: request.targetStaffName ?? undefined,
        shiftDate: request.shiftDate.toISOString().slice(0, 10),
        reason: request.reason,
        status: request.status as MutableAppState["swapRequests"][number]["status"],
        requestedAt: request.requestedAt.toISOString(),
        reviewerName: request.reviewerName ?? undefined,
        reviewedAt: request.reviewedAt?.toISOString()
      })),
      shifts: shiftSessions.map((shift) => ({
        id: shift.id,
        userId: shift.userId,
        staffName: userMap.get(shift.userId) ?? "Staff",
        role: (shift.roleLabel as MutableAppState["shifts"][number]["role"] | null) ?? "Server",
        geofenceStatus: shift.geofenceStatus,
        checkInAt: shift.startedAt.toISOString(),
        checkOutAt: shift.endedAt?.toISOString(),
        sessionActive: !shift.endedAt,
        distanceMeters: shift.distanceMeters,
        tipAmount: toDecimalNumber(shift.tipAmount),
        ordersHandled: shift.ordersHandled,
        deviceId: shift.deviceId,
        ipAddress: shift.ipAddress
      })),
      notifications: staffNotifications.map((notification) => ({
        id: notification.id,
        type: notification.type as MutableAppState["notifications"][number]["type"],
        title: notification.title,
        message: notification.message,
        createdAt: notification.createdAt.toISOString(),
        read: notification.isRead,
        audienceRole: notification.audienceRole as MutableAppState["notifications"][number]["audienceRole"],
        audienceUserId: notification.audienceUserId ?? undefined,
        tableLabel: notification.tableLabel ?? undefined
      })),
      chatMessages: kitchenChats.map((message) => ({
        id: message.id,
        fromName: message.fromName,
        fromRole: message.fromRole as MutableAppState["chatMessages"][number]["fromRole"],
        target: message.target as MutableAppState["chatMessages"][number]["target"],
        tableLabel: message.tableLabel ?? undefined,
        message: message.message,
        createdAt: message.createdAt.toISOString()
      })),
      ...(deliveryPlatformConfigs.length > 0
        ? {
            deliveryPlatforms: deliveryPlatformConfigs.map((platform) => ({
              platform: toDomainDeliveryPlatform(platform.platform),
              displayName: platform.displayName,
              enabled: platform.enabled,
              acceptsOrders: platform.acceptsOrders,
              menuSyncState: platform.menuSyncState as MutableAppState["deliveryPlatforms"][number]["menuSyncState"],
              lastSyncAt: platform.lastSyncAt?.toISOString(),
              commissionRate: toDecimalNumber(platform.commissionRate)
            }))
          }
        : {}),
      ...(deliveryOrders.length > 0
        ? {
            deliveryOrders: deliveryOrders.map((deliveryOrder) => ({
              id: deliveryOrder.id,
              platform: toDomainDeliveryPlatform(deliveryOrder.platform),
              externalOrderNo: deliveryOrder.externalOrderId,
              customerName: deliveryOrder.customerName,
              status: toDomainDeliveryStatus(deliveryOrder.deliveryStatus),
              placedAt: deliveryOrder.placedAt.toISOString(),
              etaMinutes: deliveryOrder.riderEtaMinutes ?? 0,
              totalAmount: toDecimalNumber(deliveryOrder.totalAmount),
              commissionAmount: toDecimalNumber(deliveryOrder.commission),
              branchStatus: deliveryOrder.branchStatus as MutableAppState["deliveryOrders"][number]["branchStatus"],
              items: deliveryOrder.order.items.map((item) => ({
                name: item.menuItem.name,
                quantity: item.quantity
              }))
            }))
          }
        : {}),
      ...(exceptionRecords.length > 0
        ? {
            exceptions: exceptionRecords.map((record: PrismaExceptionRecord) => ({
              id: record.id,
              kind: record.kind as MutableAppState["exceptions"][number]["kind"],
              orderId: record.orderId,
              receiptId: record.receiptId ?? undefined,
              reason: record.reason,
              amount: record.amount ? toDecimalNumber(record.amount) : undefined,
              actorName: record.actorName,
              actorRole: record.actorRole as MutableAppState["exceptions"][number]["actorRole"],
              createdAt: record.createdAt.toISOString()
            }))
          }
        : {}),
      ...(receiptDispatchAttempts.length > 0
        ? {
            receiptDispatchAttempts: receiptDispatchAttempts.map((attempt) => ({
              id: attempt.id,
              receiptId: attempt.receiptId,
              receiptNo: attempt.receiptNo,
              channel: attempt.channel as MutableAppState["receiptDispatchAttempts"][number]["channel"],
              target: attempt.target,
              status: attempt.status as MutableAppState["receiptDispatchAttempts"][number]["status"],
              provider: attempt.provider,
              message: attempt.message ?? undefined,
              createdAt: attempt.createdAt.toISOString()
            }))
          }
        : {}),
      ...(paymentGatewaySessions.length > 0
        ? {
            paymentSessions: paymentGatewaySessions.map((session) => ({
              id: session.id,
              orderId: session.order.orderNo,
              tableLabel: session.tableLabel,
              method: session.method as MutableAppState["paymentSessions"][number]["method"],
              provider: session.provider as MutableAppState["paymentSessions"][number]["provider"],
              amount: toDecimalNumber(session.amount),
              tipAmount: toDecimalNumber(session.tipAmount),
              status: session.status as MutableAppState["paymentSessions"][number]["status"],
              reference: session.reference,
              qrPayload: session.qrPayload ?? undefined,
              checkoutUrl: session.checkoutUrl ?? undefined,
              createdAt: session.createdAt.toISOString(),
              expiresAt: session.expiresAt.toISOString(),
              capturedAt: session.capturedAt?.toISOString(),
              failureReason: session.failureReason ?? undefined
            }))
          }
        : {}),
      orders: orders.map((order) => ({
        id: order.orderNo,
        tableLabel: order.table?.label ?? "DELIVERY",
        waiterName: userMap.get(order.openedByUserId ?? "") ?? "System",
        memberId: order.memberId ?? undefined,
        memberName: customers.find((member) => member.id === order.memberId)?.fullName,
        status: order.status,
        priority: order.priority,
        guests: order.guestCount,
        createdAt: order.createdAt.toISOString(),
        updatedAt: order.updatedAt.toISOString(),
        totalAmount: toDecimalNumber(order.totalAmount),
        items: order.items.map((item) => ({
          id: item.id,
          menuItemId: item.menuItemId,
          name: item.menuItem.name,
          quantity: item.quantity,
          price: toDecimalNumber(item.unitPrice),
          station: item.station,
          note: item.note ?? undefined,
          allergenFlags: item.allergens,
          modifiers: toModifierSelections(item.modifiersJson),
          status: toItemStatus(item.lineStatus)
        }))
      })),
      kitchen: orders.filter((order) => order.status !== "PAID" && order.status !== "VOIDED").flatMap((order) =>
        order.kitchenTickets.filter((ticket) => ticket.status !== "READY").map((ticket, index) => {
          const elapsedMinutes = elapsedMinutesFromDate(ticket.startedAt ?? order.createdAt);

          return {
            id: ticket.id,
            tableLabel: order.table?.label ?? "DELIVERY",
            ticketNo: `${ticket.station}-${order.orderNo.replace(/\D+/g, "") || index + 1}`,
            station: ticket.station,
            priority: order.priority,
            elapsedMinutes,
            items: order.items
              .filter((item) => item.station === ticket.station)
              .map((item) => `${item.menuItem.name} x${item.quantity}`),
            note: order.specialNote ?? undefined,
            colorState: toColorState(ticket.status, order.priority, elapsedMinutes)
          };
        })
      ),
      receipts: orders.flatMap((order) =>
        order.receipts.map((receipt, index) => {
          const matchedPayment =
            order.payments[index] ??
            order.payments.find(
              (payment) =>
                receipt.guestLabel &&
                payment.referenceNo &&
                payment.referenceNo.toLowerCase() === receipt.guestLabel.toLowerCase()
            ) ??
            order.payments[0];
            const receiptRecord = receipt as typeof receipt & {
              splitGroupId?: string | null;
              splitIndex?: number | null;
              splitCount?: number | null;
              guestLabel?: string | null;
            email?: string | null;
            lineUserId?: string | null;
            emailSharedAt?: Date | null;
            lineSharedAt?: Date | null;
              printedAt?: Date | null;
              printerName?: string | null;
              refundedAt?: Date | null;
              refundedAmount?: { toNumber: () => number } | number | null;
              refundReason?: string | null;
              taxPayerName?: string | null;
              taxId?: string | null;
              taxBranchAddress?: string | null;
              taxEmail?: string | null;
              taxIssuedAt?: Date | null;
              eTaxStatus?: string | null;
              eTaxSubmissionReference?: string | null;
              eTaxSubmittedAt?: Date | null;
              eTaxError?: string | null;
            };

          return {
            id: receipt.id,
            orderId: order.orderNo,
            receiptNo: receipt.receiptNo,
            receiptType: receipt.receiptType,
            totalAmount: toDecimalNumber(matchedPayment?.amount ?? order.totalAmount),
            tipAmount: toDecimalNumber(matchedPayment?.tipAmount),
            paidAt: (matchedPayment?.paidAt ?? order.updatedAt).toISOString(),
            paymentMethod: matchedPayment?.method ?? "CASH",
            qrLookupToken: receipt.qrLookupToken,
            splitGroupId: receiptRecord.splitGroupId ?? undefined,
            splitIndex: receiptRecord.splitIndex ?? undefined,
            splitCount: receiptRecord.splitCount ?? undefined,
            guestLabel: receiptRecord.guestLabel ?? matchedPayment?.referenceNo ?? undefined,
            status: receiptRecord.refundedAt ? "REFUNDED" : "ISSUED",
            email: receiptRecord.email ?? undefined,
            lineUserId: receiptRecord.lineUserId ?? undefined,
            emailSharedAt: receiptRecord.emailSharedAt?.toISOString(),
              lineSharedAt: receiptRecord.lineSharedAt?.toISOString(),
              printedAt: receiptRecord.printedAt?.toISOString(),
              printerName: receiptRecord.printerName ?? undefined,
              taxPayerName: receiptRecord.taxPayerName ?? undefined,
              taxId: receiptRecord.taxId ?? undefined,
              taxBranchAddress: receiptRecord.taxBranchAddress ?? undefined,
              taxEmail: receiptRecord.taxEmail ?? undefined,
              taxIssuedAt: receiptRecord.taxIssuedAt?.toISOString(),
              eTaxStatus:
                (receiptRecord.eTaxStatus as "PENDING_SUBMISSION" | "SUBMITTED" | "FAILED" | undefined) ??
                undefined,
              eTaxSubmissionReference: receiptRecord.eTaxSubmissionReference ?? undefined,
              eTaxSubmittedAt: receiptRecord.eTaxSubmittedAt?.toISOString(),
              eTaxError: receiptRecord.eTaxError ?? undefined,
              refundedAmount: receiptRecord.refundedAmount
                ? toDecimalNumber(receiptRecord.refundedAmount)
                : undefined,
            refundedAt: receiptRecord.refundedAt?.toISOString(),
            refundReason: receiptRecord.refundReason ?? undefined
          };
        })
      ),
      auditEntries: auditLogs.map((entry) => ({
        id: entry.id,
        actorName: userMap.get(entry.actorId ?? "") ?? entry.actorRole,
        actorRole: entry.actorRole as MutableAppState["users"][number]["role"],
        action: entry.action,
        entityType: entry.entityType as
          | "AUTH"
          | "ORDER"
          | "TABLE"
          | "KITCHEN"
          | "PAYMENT"
          | "RECEIPT"
          | "MEMBER",
        entityId: entry.entityId,
        createdAt: entry.createdAt.toISOString(),
        metadata:
          entry.metadata && typeof entry.metadata === "object" && !Array.isArray(entry.metadata)
            ? (entry.metadata as Record<string, string | number | boolean>)
            : undefined
      }))
    };
  } catch {
    return null;
  }
};
