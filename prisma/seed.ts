import {
  Prisma,
  PrismaClient,
  KitchenLineStatus,
  KitchenStation,
  OrderStatus,
  TableStatus,
  UserRole
} from "@prisma/client";
import {
  type MenuItemSummary,
  customerMembers,
  deliveryOrders,
  deliveryPlatforms,
  demoUsers,
  diningTables,
  inventoryItems,
  kitchenChatMessages,
  leaveRequests,
  menuItems,
  orderTickets,
  scheduledShifts,
  securityPolicy,
  shiftSessions,
  stockMovements,
  staffNotifications,
  swapShiftRequests
} from "@mypos/domain";

const prisma = new PrismaClient();

const toPrismaDeliveryPlatform = (platform: (typeof deliveryPlatforms)[number]["platform"]) => {
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

const toPrismaDeliveryStatus = (status: (typeof deliveryOrders)[number]["status"]) => {
  switch (status) {
    case "NEW":
      return "RECEIVED";
    case "ACCEPTED":
      return "ACCEPTED";
    case "PREPARING":
      return "PREPARING";
    case "READY_FOR_PICKUP":
      return "READY_FOR_PICKUP";
    case "OUT_FOR_DELIVERY":
      return "PICKED_UP";
    case "COMPLETED":
      return "DELIVERED";
    case "CANCELLED":
      return "CANCELLED";
    default:
      return "RECEIVED";
  }
};

const openOrderStatusFromTicket = (
  status: (typeof orderTickets)[number]["status"]
): OrderStatus => {
  switch (status) {
    case "READY":
      return "READY";
    case "IN_PROGRESS":
      return "IN_PROGRESS";
    case "SENT_TO_KITCHEN":
      return "SENT_TO_KITCHEN";
    default:
      return "DRAFT";
  }
};

const lineStatusFromTicket = (
  status: (typeof orderTickets)[number]["items"][number]["status"]
): KitchenLineStatus => {
  switch (status) {
    case "READY":
      return "READY";
    case "IN_PROGRESS":
      return "IN_PROGRESS";
    case "OUT_OF_STOCK":
      return "OUT_OF_STOCK";
    default:
      return "PENDING";
  }
};

async function main() {
  const branch = await prisma.branch.upsert({
    where: { code: "BR-TH-001" },
    update: {},
    create: {
      code: "BR-TH-001",
      name: "MyPOS Demo Branch",
      timezone: "Asia/Bangkok",
      floorplanJson: {
        zones: ["Main Hall", "VIP", "Bar"],
        layouts: Object.fromEntries(
          diningTables.map((table) => [
            table.id,
            {
              x: table.layout.x,
              y: table.layout.y,
              width: table.layout.width,
              height: table.layout.height
            }
          ])
        )
      } as Prisma.InputJsonValue
    }
  });

  for (const user of demoUsers) {
    await prisma.appUser.upsert({
      where: { username: user.username },
      update: {
        displayName: user.displayName,
        role: user.role as UserRole,
        branchId: branch.id,
        pinHash: user.pin,
        accountExpires: user.expiresAt ? new Date(user.expiresAt) : null,
        isActive: user.accountStatus !== "BLOCKED",
        blockedAt: user.blockedAt ? new Date(user.blockedAt) : null,
        forceLogoutAfter: user.forceLogoutAfter ? new Date(user.forceLogoutAfter) : null,
        lastLoginAt: user.lastLoginAt ? new Date(user.lastLoginAt) : null
      },
      create: {
        id: user.id,
        username: user.username,
        displayName: user.displayName,
        role: user.role as UserRole,
        branchId: branch.id,
        pinHash: user.pin,
        accountExpires: user.expiresAt ? new Date(user.expiresAt) : null,
        isActive: user.accountStatus !== "BLOCKED",
        blockedAt: user.blockedAt ? new Date(user.blockedAt) : null,
        forceLogoutAfter: user.forceLogoutAfter ? new Date(user.forceLogoutAfter) : null,
        lastLoginAt: user.lastLoginAt ? new Date(user.lastLoginAt) : null
      }
    });
  }

  await prisma.securityConfig.upsert({
    where: { branchId: branch.id },
    update: {
      adminIpWhitelist: securityPolicy.adminIpWhitelist,
      twoFactorRoles: securityPolicy.twoFactorRoles,
      receiptTemplateJson: securityPolicy.receiptTemplate as Prisma.InputJsonValue
    },
    create: {
      branchId: branch.id,
      adminIpWhitelist: securityPolicy.adminIpWhitelist,
      twoFactorRoles: securityPolicy.twoFactorRoles,
      receiptTemplateJson: securityPolicy.receiptTemplate as Prisma.InputJsonValue
    }
  });

  for (const platform of deliveryPlatforms) {
    await prisma.deliveryPlatformConnection.upsert({
      where: {
        branchId_platform: {
          branchId: branch.id,
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
        branchId: branch.id,
        platform: toPrismaDeliveryPlatform(platform.platform),
        displayName: platform.displayName,
        enabled: platform.enabled,
        acceptsOrders: platform.acceptsOrders,
        menuSyncState: platform.menuSyncState,
        lastSyncAt: platform.lastSyncAt ? new Date(platform.lastSyncAt) : null,
        commissionRate: platform.commissionRate
      }
    });
  }

  const categoryMap = new Map<string, string>();

  for (const item of menuItems) {
    if (!categoryMap.has(item.category)) {
      const existingCategory = await prisma.menuCategory.findFirst({
        where: {
          branchId: branch.id,
          name: item.category
        }
      });

      const category =
        existingCategory ??
        (await prisma.menuCategory.create({
          data: {
            branchId: branch.id,
            name: item.category
          }
        }));

      categoryMap.set(item.category, category.id);
    }
  }

  for (const table of diningTables) {
    await prisma.diningTable.upsert({
      where: {
        id: table.id
      },
      update: {
        label: table.label,
        zone: table.zone,
        seats: table.seats,
        status: table.status as TableStatus
      },
      create: {
        id: table.id,
        branchId: branch.id,
        label: table.label,
        zone: table.zone,
        seats: table.seats,
        status: table.status as TableStatus
      }
    });
  }

  for (const table of diningTables) {
    if (!table.reservation) {
      continue;
    }

    await prisma.reservation.upsert({
      where: { id: table.reservation.id },
      update: {
        branchId: branch.id,
        tableId: table.id,
        customerName: table.reservation.guestName,
        customerPhone: table.reservation.contactPhone ?? "-",
        partySize: table.reservation.partySize,
        reservedAt: new Date(table.reservation.reservedAt),
        status: "CONFIRMED"
      },
      create: {
        id: table.reservation.id,
        branchId: branch.id,
        tableId: table.id,
        customerName: table.reservation.guestName,
        customerPhone: table.reservation.contactPhone ?? "-",
        partySize: table.reservation.partySize,
        reservedAt: new Date(table.reservation.reservedAt),
        status: "CONFIRMED"
      }
    });
  }

  for (const item of menuItems) {
    await prisma.menuItem.upsert({
      where: {
        id: item.id
      },
      update: {
        name: item.name,
        basePrice: item.price,
        happyHourPrice: item.happyHourPrice ?? null,
        imageUrl: item.imageUrl,
        station: item.tags.includes("bar") ? KitchenStation.BAR : KitchenStation.HOT,
        isActive: item.inStock,
        allergenInfo: item.tags,
        translationsJson: item.translations
          ? (item.translations as Prisma.InputJsonValue)
          : Prisma.JsonNull
      },
      create: {
        id: item.id,
        branchId: branch.id,
        categoryId: categoryMap.get(item.category)!,
        name: item.name,
        basePrice: item.price,
        happyHourPrice: item.happyHourPrice ?? null,
        imageUrl: item.imageUrl,
        station: item.tags.includes("bar") ? KitchenStation.BAR : KitchenStation.HOT,
        isActive: item.inStock,
        allergenInfo: item.tags,
        translationsJson: item.translations
          ? (item.translations as Prisma.InputJsonValue)
          : Prisma.JsonNull
      }
    });

    await prisma.modifierOption.deleteMany({
      where: {
        modifierGroup: {
          menuItemId: item.id
        }
      }
    });

    await prisma.modifierGroup.deleteMany({
      where: {
        menuItemId: item.id
      }
    });

    for (const group of item.modifierGroups ?? []) {
      await prisma.modifierGroup.create({
        data: {
          id: group.id,
          menuItemId: item.id,
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

  for (const member of customerMembers) {
    await prisma.customerMember.upsert({
      where: { id: member.id },
      update: {
        branchId: branch.id,
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
        branchId: branch.id,
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
  }

  for (const item of inventoryItems) {
    await prisma.inventoryItem.upsert({
      where: { id: item.id },
      update: {
        branchId: branch.id,
        name: item.name,
        category: item.category,
        unit: item.unit,
        onHand: item.onHand,
        minLevel: item.minLevel,
        reorderQty: item.reorderQty,
        avgUnitCost: item.avgUnitCost,
        supplierName: item.supplierName ?? null,
        linkedMenuItemIds: item.linkedMenuItems,
        recipeUsageJson: item.recipeUsage ? (item.recipeUsage as Prisma.InputJsonValue) : Prisma.JsonNull
      },
      create: {
        id: item.id,
        branchId: branch.id,
        name: item.name,
        category: item.category,
        unit: item.unit,
        onHand: item.onHand,
        minLevel: item.minLevel,
        reorderQty: item.reorderQty,
        avgUnitCost: item.avgUnitCost,
        supplierName: item.supplierName ?? null,
        linkedMenuItemIds: item.linkedMenuItems,
        recipeUsageJson: item.recipeUsage ? (item.recipeUsage as Prisma.InputJsonValue) : Prisma.JsonNull
      }
    });
  }

  for (const movement of stockMovements) {
    await prisma.inventoryMovement.upsert({
      where: { id: movement.id },
      update: {
        branchId: branch.id,
        itemId: movement.itemId,
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
        branchId: branch.id,
        itemId: movement.itemId,
        itemName: movement.itemName,
        type: movement.type,
        quantity: movement.quantity,
        unit: movement.unit,
        note: movement.note ?? null,
        actorName: movement.actorName,
        createdAt: new Date(movement.createdAt)
      }
    });
  }

  for (const shift of scheduledShifts) {
    await prisma.shiftPlan.upsert({
      where: { id: shift.id },
      update: {
        branchId: branch.id,
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
        branchId: branch.id,
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
  }

  const usersByDisplayName = new Map(demoUsers.map((user) => [user.displayName, user]));
  const tableByLabel = new Map(diningTables.map((table) => [table.label, table]));
  const tableIdByLabel = new Map(diningTables.map((table) => [table.label, table.id]));
  const defaultFloorStaff = demoUsers.find((user) => user.role === "STAFF") ?? null;
  const cashierUser = demoUsers.find((user) => user.role === "CASHIER") ?? null;
  const sampleMember = customerMembers[0] ?? null;

  for (const shift of shiftSessions) {
    const matchedUser =
      usersByDisplayName.get(shift.staffName) ??
      (shift.role === "Cashier"
        ? demoUsers.find((user) => user.role === "CASHIER")
        : shift.role === "Bartender"
          ? demoUsers.find((user) => user.role === "KITCHEN")
          : demoUsers.find((user) => user.role === "STAFF"));

    if (!matchedUser) {
      continue;
    }

    await prisma.shiftSession.upsert({
      where: { id: shift.id },
      update: {
        branchId: branch.id,
        userId: matchedUser.id,
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
        ipAddress: shift.ipAddress ?? "127.0.0.1",
        otMinutes: 0
      },
      create: {
        id: shift.id,
        branchId: branch.id,
        userId: matchedUser.id,
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
        ipAddress: shift.ipAddress ?? "127.0.0.1",
        otMinutes: 0
      }
    });
  }

  for (const request of leaveRequests) {
    await prisma.leaveRequest.upsert({
      where: { id: request.id },
      update: {
        branchId: branch.id,
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
        branchId: branch.id,
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
  }

  for (const request of swapShiftRequests) {
    await prisma.swapShiftRequest.upsert({
      where: { id: request.id },
      update: {
        branchId: branch.id,
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
        branchId: branch.id,
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
  }

  const menuByName = new Map<string, MenuItemSummary>(menuItems.map((item) => [item.name, item]));

  for (const ticket of orderTickets) {
    const tableId = tableIdByLabel.get(ticket.tableLabel) ?? null;
    const tableSnapshot = tableByLabel.get(ticket.tableLabel);
    const originalCreatedAt = new Date(ticket.createdAt);
    const originalUpdatedAt = new Date(ticket.updatedAt);
    const activityWindowMs = Math.max(
      originalUpdatedAt.getTime() - originalCreatedAt.getTime(),
      60_000
    );
    const seededCreatedAt = tableSnapshot?.occupiedMinutes
      ? new Date(Date.now() - tableSnapshot.occupiedMinutes * 60_000)
      : originalCreatedAt;
    const seededUpdatedAt = new Date(
      Math.min(seededCreatedAt.getTime() + activityWindowMs, Date.now() - 60_000)
    );

    const orderRecord = await prisma.order.upsert({
      where: { orderNo: ticket.id },
      update: {
        branchId: branch.id,
        tableId,
        source: "POS",
        status: openOrderStatusFromTicket(ticket.status),
        priority: ticket.priority,
        guestCount: ticket.guests,
        subtotalAmount: ticket.totalAmount,
        discountAmount: 0,
        vatAmount: 0,
        totalAmount: ticket.totalAmount,
        specialNote: `Waiter: ${ticket.waiterName}`,
        openedByUserId: defaultFloorStaff?.id ?? null
      },
      create: {
        id: ticket.id,
        branchId: branch.id,
        tableId,
        orderNo: ticket.id,
        source: "POS",
        status: openOrderStatusFromTicket(ticket.status),
        priority: ticket.priority,
        guestCount: ticket.guests,
        subtotalAmount: ticket.totalAmount,
        discountAmount: 0,
        vatAmount: 0,
        totalAmount: ticket.totalAmount,
        specialNote: `Waiter: ${ticket.waiterName}`,
        openedByUserId: defaultFloorStaff?.id ?? null,
        createdAt: seededCreatedAt
      }
    });

    await prisma.order.update({
      where: { id: orderRecord.id },
      data: {
        createdAt: seededCreatedAt
      }
    });

    await prisma.orderItem.deleteMany({
      where: { orderId: orderRecord.id }
    });
    await prisma.kitchenTicket.deleteMany({
      where: { orderId: orderRecord.id }
    });

    for (const item of ticket.items) {
      await prisma.orderItem.create({
        data: {
          id: item.id,
          orderId: orderRecord.id,
          menuItemId: item.menuItemId,
          quantity: item.quantity,
          unitPrice: item.price,
          note: item.note ?? null,
          station: item.station,
          lineStatus: lineStatusFromTicket(item.status),
          allergens: item.allergenFlags,
          modifiersJson: (item.modifiers ?? []) as Prisma.InputJsonValue
        }
      });
    }

    const stations = new Set(ticket.items.map((item) => item.station));

    for (const [index, station] of Array.from(stations).entries()) {
      const stationItems = ticket.items.filter((item) => item.station === station);
      const allReady = stationItems.every((item) => item.status === "READY");
      const anyInProgress = stationItems.some((item) => item.status === "IN_PROGRESS");

      await prisma.kitchenTicket.create({
        data: {
          id: `${ticket.id}-KT-${index + 1}`,
          orderId: orderRecord.id,
          station,
          status: allReady ? "READY" : anyInProgress ? "IN_PROGRESS" : "PENDING",
          startedAt: allReady || anyInProgress ? seededCreatedAt : null,
          finishedAt: allReady ? seededUpdatedAt : null
        }
      });
    }
  }

  const settledOrderCreatedAt = new Date("2026-03-25T17:36:00.000Z");
  const settledOrderPaidAt = new Date("2026-03-25T17:58:00.000Z");
  const settledOrderRecord = await prisma.order.upsert({
    where: { orderNo: "ORD-240250" },
      update: {
        branchId: branch.id,
        tableId: tableIdByLabel.get("A2") ?? null,
        memberId: sampleMember?.id ?? null,
        source: "POS",
      status: "PAID",
      priority: "NORMAL",
      guestCount: 2,
      subtotalAmount: 510,
      discountAmount: 0,
      vatAmount: 0,
        totalAmount: 510,
        specialNote: "Historical settled split-bill order",
        openedByUserId: cashierUser?.id ?? defaultFloorStaff?.id ?? null,
        closedByUserId: cashierUser?.id ?? null,
        memberSettledAt: settledOrderPaidAt
      },
      create: {
        id: "ORD-240250",
        branchId: branch.id,
      tableId: tableIdByLabel.get("A2") ?? null,
      memberId: sampleMember?.id ?? null,
      orderNo: "ORD-240250",
      source: "POS",
      status: "PAID",
      priority: "NORMAL",
      guestCount: 2,
      subtotalAmount: 510,
      discountAmount: 0,
      vatAmount: 0,
        totalAmount: 510,
        specialNote: "Historical settled split-bill order",
        openedByUserId: cashierUser?.id ?? defaultFloorStaff?.id ?? null,
        closedByUserId: cashierUser?.id ?? null,
        memberSettledAt: settledOrderPaidAt,
        createdAt: settledOrderCreatedAt
      }
    });

  await prisma.order.update({
    where: { id: settledOrderRecord.id },
    data: {
      createdAt: settledOrderCreatedAt
    }
  });

  await prisma.orderItem.deleteMany({
    where: { orderId: settledOrderRecord.id }
  });
  await prisma.payment.deleteMany({
    where: { orderId: settledOrderRecord.id }
  });
  await prisma.receipt.deleteMany({
    where: { orderId: settledOrderRecord.id }
  });
  await prisma.kitchenTicket.deleteMany({
    where: { orderId: settledOrderRecord.id }
  });

  await prisma.orderItem.createMany({
    data: [
      {
        id: "ORD-240250-ITEM-1",
        orderId: settledOrderRecord.id,
        menuItemId: "M1",
        quantity: 1,
        unitPrice: 285,
        station: KitchenStation.HOT,
        lineStatus: "READY",
        allergens: ["Dairy", "Egg"],
        modifiersJson: Prisma.JsonNull
      },
      {
        id: "ORD-240250-ITEM-2",
        orderId: settledOrderRecord.id,
        menuItemId: "M2",
        quantity: 1,
        unitPrice: 225,
        station: KitchenStation.HOT,
        lineStatus: "READY",
        allergens: ["Gluten"],
        modifiersJson: Prisma.JsonNull
      }
    ]
  });

  await prisma.kitchenTicket.create({
    data: {
      id: "ORD-240250-KT-1",
      orderId: settledOrderRecord.id,
      station: KitchenStation.HOT,
      status: "READY",
      startedAt: settledOrderCreatedAt,
      finishedAt: settledOrderPaidAt
    }
  });

  await prisma.payment.createMany({
    data: [
      {
        id: "PAY-240250-1",
        orderId: settledOrderRecord.id,
        method: "CASH",
        amount: 255,
        tipAmount: 0,
        referenceNo: "Guest 1",
        splitGroup: "SPLIT-240250",
        paidAt: settledOrderPaidAt
      },
      {
        id: "PAY-240250-2",
        orderId: settledOrderRecord.id,
        method: "CARD",
        amount: 255,
        tipAmount: 0,
        referenceNo: "Guest 2",
        splitGroup: "SPLIT-240250",
        paidAt: settledOrderPaidAt
      }
    ]
  });

  await prisma.receipt.createMany({
    data: [
      {
        id: "RCT-240250-1",
        orderId: settledOrderRecord.id,
        receiptNo: "R-2026-240250-1",
        receiptType: "STANDARD",
        qrLookupToken: "qr-240250-1",
        splitGroupId: "SPLIT-240250",
        splitIndex: 1,
        splitCount: 2,
        guestLabel: "Guest 1"
      },
      {
        id: "RCT-240250-2",
        orderId: settledOrderRecord.id,
        receiptNo: "R-2026-240250-2",
        receiptType: "STANDARD",
        qrLookupToken: "qr-240250-2",
        splitGroupId: "SPLIT-240250",
        splitIndex: 2,
        splitCount: 2,
        guestLabel: "Guest 2"
      }
    ]
  });

  for (const auditLog of [
    {
      id: "AUD-240250-1",
      action: "payment.capture",
      entityType: "PAYMENT",
      entityId: "ORD-240250",
      metadata: { amount: 255, method: "CASH", orderId: "ORD-240250" }
    },
    {
      id: "AUD-240250-2",
      action: "receipt.issue",
      entityType: "RECEIPT",
      entityId: "RCT-240250-1",
      metadata: { receiptNo: "R-2026-240250-1", orderId: "ORD-240250" }
    },
    {
      id: "AUD-240250-3",
      action: "payment.capture",
      entityType: "PAYMENT",
      entityId: "ORD-240250",
      metadata: { amount: 255, method: "CARD", orderId: "ORD-240250" }
    },
    {
      id: "AUD-240250-4",
      action: "receipt.issue",
      entityType: "RECEIPT",
      entityId: "RCT-240250-2",
      metadata: { receiptNo: "R-2026-240250-2", orderId: "ORD-240250" }
    },
    {
      id: "AUD-240250-5",
      action: "member.points_earned",
      entityType: "MEMBER",
      entityId: sampleMember?.id ?? "MBR-001",
      metadata: { earnedPoints: 25, orderId: "ORD-240250" }
    }
  ] as const) {
    await prisma.auditLog.upsert({
      where: { id: auditLog.id },
      update: {
        branchId: branch.id,
        actorId: cashierUser?.id ?? null,
        actorRole: cashierUser?.role ?? "CASHIER",
        action: auditLog.action,
        entityType: auditLog.entityType,
        entityId: auditLog.entityId,
        ipAddress: "127.0.0.1",
        metadata: auditLog.metadata as Prisma.InputJsonValue,
        createdAt: settledOrderPaidAt
      },
      create: {
        id: auditLog.id,
        branchId: branch.id,
        actorId: cashierUser?.id ?? null,
        actorRole: cashierUser?.role ?? "CASHIER",
        action: auditLog.action,
        entityType: auditLog.entityType,
        entityId: auditLog.entityId,
        ipAddress: "127.0.0.1",
        metadata: auditLog.metadata as Prisma.InputJsonValue,
        createdAt: settledOrderPaidAt
      }
    });
  }

  for (const deliveryOrder of deliveryOrders) {
    const orderNo = `ORD-${deliveryOrder.id}`;
    const orderStatus =
      deliveryOrder.branchStatus === "QUEUED"
        ? "SENT_TO_KITCHEN"
        : deliveryOrder.branchStatus === "IN_KITCHEN"
          ? "IN_PROGRESS"
          : deliveryOrder.branchStatus === "READY"
            ? "READY"
            : deliveryOrder.branchStatus === "DISPATCHED"
              ? "SERVED"
              : "DRAFT";

    const orderRecord = await prisma.order.upsert({
      where: { orderNo },
      update: {
        branchId: branch.id,
        tableId: null,
        source: "DELIVERY",
        status: orderStatus,
        priority: "NORMAL",
        guestCount: 1,
        subtotalAmount: deliveryOrder.totalAmount,
        discountAmount: 0,
        vatAmount: 0,
        totalAmount: deliveryOrder.totalAmount,
        specialNote: `Delivery ${deliveryOrder.platform}`
      },
      create: {
        id: orderNo,
        branchId: branch.id,
        tableId: null,
        orderNo,
        source: "DELIVERY",
        status: orderStatus,
        priority: "NORMAL",
        guestCount: 1,
        subtotalAmount: deliveryOrder.totalAmount,
        discountAmount: 0,
        vatAmount: 0,
        totalAmount: deliveryOrder.totalAmount,
        specialNote: `Delivery ${deliveryOrder.platform}`
      }
    });

    await prisma.orderItem.deleteMany({
      where: { orderId: orderRecord.id }
    });
    await prisma.kitchenTicket.deleteMany({
      where: { orderId: orderRecord.id }
    });

    for (const [index, line] of deliveryOrder.items.entries()) {
      const menuItem = menuByName.get(line.name);

      if (!menuItem) {
        continue;
      }

      await prisma.orderItem.create({
        data: {
          id: `${deliveryOrder.id}-ITEM-${index + 1}`,
          orderId: orderRecord.id,
          menuItemId: menuItem.id,
          quantity: line.quantity,
          unitPrice: menuItem.price,
          station: menuItem.tags.includes("bar") ? KitchenStation.BAR : KitchenStation.HOT,
          lineStatus:
            deliveryOrder.branchStatus === "READY" || deliveryOrder.branchStatus === "DISPATCHED"
              ? "READY"
              : deliveryOrder.branchStatus === "IN_KITCHEN"
                ? "IN_PROGRESS"
                : "PENDING",
          allergens: menuItem.allergenInfo ?? [],
          modifiersJson: Prisma.JsonNull
        }
      });
    }

    const stations = new Set(
      deliveryOrder.items
        .map((line) => menuByName.get(line.name))
        .filter((item): item is NonNullable<typeof item> => Boolean(item))
        .map((item) => (item.tags.includes("bar") ? KitchenStation.BAR : KitchenStation.HOT))
    );

    for (const [index, station] of Array.from(stations).entries()) {
      await prisma.kitchenTicket.create({
        data: {
          id: `${deliveryOrder.id}-KT-${index + 1}`,
          orderId: orderRecord.id,
          station,
          status:
            deliveryOrder.branchStatus === "READY" || deliveryOrder.branchStatus === "DISPATCHED"
              ? "READY"
              : deliveryOrder.branchStatus === "IN_KITCHEN"
                ? "IN_PROGRESS"
                : "PENDING"
        }
      });
    }

    await prisma.deliveryOrder.upsert({
      where: { orderId: orderRecord.id },
      update: {
        branchId: branch.id,
        platform: toPrismaDeliveryPlatform(deliveryOrder.platform),
        externalOrderId: deliveryOrder.externalOrderNo,
        customerName: deliveryOrder.customerName,
        branchStatus: deliveryOrder.branchStatus,
        placedAt: new Date(deliveryOrder.placedAt),
        totalAmount: deliveryOrder.totalAmount,
        deliveryStatus: toPrismaDeliveryStatus(deliveryOrder.status),
        commission: deliveryOrder.commissionAmount,
        riderEtaMinutes: deliveryOrder.etaMinutes
      },
      create: {
        id: deliveryOrder.id,
        branchId: branch.id,
        orderId: orderRecord.id,
        platform: toPrismaDeliveryPlatform(deliveryOrder.platform),
        externalOrderId: deliveryOrder.externalOrderNo,
        customerName: deliveryOrder.customerName,
        branchStatus: deliveryOrder.branchStatus,
        placedAt: new Date(deliveryOrder.placedAt),
        totalAmount: deliveryOrder.totalAmount,
        deliveryStatus: toPrismaDeliveryStatus(deliveryOrder.status),
        commission: deliveryOrder.commissionAmount,
        riderEtaMinutes: deliveryOrder.etaMinutes
      }
    });
  }

  for (const notification of staffNotifications) {
    await prisma.staffNotificationRecord.upsert({
      where: { id: notification.id },
      update: {
        branchId: branch.id,
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
        branchId: branch.id,
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
  }

  for (const message of kitchenChatMessages) {
    await prisma.kitchenChatRecord.upsert({
      where: { id: message.id },
      update: {
        branchId: branch.id,
        fromName: message.fromName,
        fromRole: message.fromRole,
        target: message.target,
        tableLabel: message.tableLabel ?? null,
        message: message.message,
        createdAt: new Date(message.createdAt)
      },
      create: {
        id: message.id,
        branchId: branch.id,
        fromName: message.fromName,
        fromRole: message.fromRole,
        target: message.target,
        tableLabel: message.tableLabel ?? null,
        message: message.message,
        createdAt: new Date(message.createdAt)
      }
    });
  }
}

main()
  .then(async () => {
    await prisma.$disconnect();
  })
  .catch(async (error) => {
    console.error(error);
    await prisma.$disconnect();
    process.exit(1);
  });
