import {
  customerMembers,
  dashboardMetrics,
  deliveryOrders,
  deliveryPlatforms,
  demoUsers,
  diningTables,
  inventoryItems,
  kitchenChatMessages,
  kitchenQueueCards,
  leaveRequests,
  menuItems,
  orderTickets,
  securityPolicy,
  scheduledShifts,
  shiftSessions,
  stockMovements,
  staffNotifications,
  swapShiftRequests,
  type AppPermission,
  type AuditEntry,
  type AuthUser,
  type BackofficeReport,
  type ClockInRequest,
  type ClockOutRequest,
  type CreateMemberRequest,
  type CreateLeaveRequestRequest,
  type CreateScheduledShiftRequest,
  type CreateSwapShiftRequest,
  type CreateUserAccountRequest,
  type CreatePaymentSessionRequest,
  type CrmOverview,
  type CreateMenuItemRequest,
  type CustomerMember,
  type CreateReservationRequest,
  type CreateOrderRequest,
  type DeliveryCenterSnapshot,
  type DeliveryPlatform,
  type DiningTable,
  type ExceptionRecord,
  type HrOverview,
  type InventoryOverview,
  type IssueTaxInvoiceRequest,
  type KitchenChatMessage,
  type KitchenQueueCard,
  type KitchenStation,
  type LeaveRequest,
  type ManagedUserAccount,
  type ModifierSelection,
  type PaymentSessionSummary,
  type PaymentGatewayProvider,
  type PaymentSessionStatus,
  type PublicCheckBillRequest,
  type PublicOrderRequest,
  type PrintReceiptRequest,
  type ReceiptDispatchAttempt,
  type ReceiptSummary,
  type RefundReceiptRequest,
  type ReviewHrRequestRequest,
  type ScheduledShift,
  type SecurityPolicy,
  type ShareReceiptRequest,
  type SettlePaymentRequest,
  type SplitPaymentRequest,
  type StockItem,
  type StockMovement,
  type StaffNotification,
  type StaffHrWorkspace,
  type SubmitEtaxRequest,
  type TwoFactorChallenge,
  type ShiftSession,
  type SwapShiftRequest,
  type UpdateSecurityPolicyRequest,
  type UpdateMenuItemRequest,
  type UpdateUserAccountRequest,
  type UserAccount,
  type UserRole,
  type VoidOrderRequest
} from "@mypos/domain";
import type {
  ActionActor,
  AppPersistenceAdapter,
  AppRepository,
  AppSnapshot,
  MutableAppState
} from "./types";
import { createGatewayPaymentSession } from "../lib/payment-gateway";

const clone = <T>(value: T): T => JSON.parse(JSON.stringify(value)) as T;
const branchGeofence = {
  latitude: 13.7563,
  longitude: 100.5018,
  radiusMeters: 100
};

const toRadians = (value: number) => (value * Math.PI) / 180;
const getDistanceMeters = (fromLat: number, fromLng: number, toLat: number, toLng: number) => {
  const earthRadius = 6371000;
  const dLat = toRadians(toLat - fromLat);
  const dLng = toRadians(toLng - fromLng);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRadians(fromLat)) * Math.cos(toRadians(toLat)) * Math.sin(dLng / 2) ** 2;

  return Math.round(earthRadius * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a)));
};

const gatewaySystemActor: ActionActor = {
  id: "gateway-system",
  displayName: "Gateway Lifecycle",
  role: "OWNER"
};

const createInitialState = (): MutableAppState => ({
  users: clone(demoUsers),
  members: clone(customerMembers),
  metrics: clone(dashboardMetrics),
  tables: clone(diningTables),
  orders: clone(orderTickets),
  menu: clone(menuItems),
  shifts: clone(shiftSessions),
  kitchen: clone(kitchenQueueCards),
  receipts: [],
  paymentSessions: [],
  receiptDispatchAttempts: [],
  auditEntries: [],
  exceptions: [],
  notifications: clone(staffNotifications),
  chatMessages: clone(kitchenChatMessages),
  inventoryItems: clone(inventoryItems),
  stockMovements: clone(stockMovements),
  scheduledShifts: clone(scheduledShifts),
  leaveRequests: clone(leaveRequests),
  swapRequests: clone(swapShiftRequests),
  securityPolicy: clone(securityPolicy),
  deliveryOrders: clone(deliveryOrders),
  deliveryPlatforms: clone(deliveryPlatforms),
  pushTokens: []
});

export class MemoryAppRepository implements AppRepository {
  private persistenceAdapter: AppPersistenceAdapter | null = null;
  private readonly twoFactorChallenges = new Map<string, TwoFactorChallenge>();

  private readonly permissionMatrix: Record<UserRole, AppPermission[]> = {
    OWNER: [
      "orders.manage",
      "payments.capture",
      "menu.manage",
      "sales.view_today",
      "sales.view_all",
      "hr.view",
      "system.manage",
      "audit.view",
      "receipts.void"
    ],
    MANAGER: [
      "orders.manage",
      "payments.capture",
      "menu.manage",
      "sales.view_today",
      "sales.view_all",
      "hr.view",
      "audit.view",
      "receipts.void"
    ],
    CASHIER: [
      "orders.manage",
      "payments.capture",
      "menu.manage",
      "sales.view_today"
    ],
    STAFF: ["orders.manage"],
    KITCHEN: ["orders.manage"]
  };

  private state: MutableAppState = createInitialState();

  constructor() {
    this.computeMetrics();
  }

  setPersistenceAdapter(adapter: AppPersistenceAdapter | null) {
    this.persistenceAdapter = adapter;
  }

  getSnapshot(): AppSnapshot {
    return clone({
      metrics: this.state.metrics,
      tables: this.state.tables,
      orders: this.state.orders,
      menu: this.state.menu,
      shifts: this.state.shifts,
      kitchen: this.state.kitchen
    });
  }

  hydrate(partial: Partial<MutableAppState>) {
    this.state = {
      ...this.state,
      ...clone(partial)
    };
    this.computeMetrics();
  }

  resetDemoState() {
    if (this.persistenceAdapter) {
      return false;
    }

    this.state = createInitialState();
    this.twoFactorChallenges.clear();
    this.computeMetrics();
    return true;
  }

  getPermissions(role: UserRole) {
    return clone(this.permissionMatrix[role]);
  }

  findUserByCredentials(username: string, pin: string) {
    return (
      this.state.users.find(
        (item) =>
          item.username === username &&
          item.pin === pin &&
          this.getManagedUserAccount(item).accountStatus === "ACTIVE"
      ) ?? null
    );
  }

  getUserById(userId: string) {
    return this.state.users.find((item) => item.id === userId) ?? null;
  }

  getAuthUser(user: UserAccount): AuthUser {
    return {
      id: user.id,
      username: user.username,
      displayName: user.displayName,
      role: user.role,
      branchId: user.branchId
    };
  }

  getManagedUsers() {
    return clone(this.state.users.map((user) => this.getManagedUserAccount(user)));
  }

  getSecurityPolicy() {
    return clone(this.state.securityPolicy);
  }

  getAuditEntries() {
    return clone(this.state.auditEntries);
  }

  getMembers() {
    return clone(this.state.members);
  }

  getReceipts() {
    return clone(this.state.receipts);
  }

  getPaymentSessions() {
    this.expirePendingPaymentSessions(gatewaySystemActor);
    return clone(this.state.paymentSessions);
  }

  getReceiptById(receiptId: string) {
    return clone(this.state.receipts.find((receipt) => receipt.id === receiptId) ?? null);
  }

  getReceiptDispatchAttempts() {
    return clone(this.state.receiptDispatchAttempts);
  }

  getExceptions() {
    return clone(this.state.exceptions);
  }

  getStaffNotifications(userId: string, role: UserRole) {
    return clone(
      this.state.notifications.filter(
        (notification) =>
          notification.audienceRole === role &&
          (!notification.audienceUserId || notification.audienceUserId === userId)
      )
    );
  }

  getAllStaffNotifications() {
    return clone(this.state.notifications);
  }

  getChatMessages(role: UserRole) {
    const target = role === "KITCHEN" ? "KITCHEN" : "FLOOR";

    return clone(this.state.chatMessages.filter((message) => message.target === target));
  }

  getAllChatMessages() {
    return clone(this.state.chatMessages);
  }

  getInventoryOverview() {
    const items = this.state.inventoryItems.map((item) => this.withInventoryStatus(item));
    const lowStockItems = items.filter((item) => item.status === "LOW_STOCK");
    const outOfStockItems = items.filter((item) => item.status === "OUT_OF_STOCK");
    const stockValue = items.reduce((sum, item) => sum + item.onHand * item.avgUnitCost, 0);
    const wasteValue = this.state.stockMovements
      .filter((movement) => movement.type === "WASTE")
      .reduce((sum, movement) => {
        const item = items.find((entry) => entry.id === movement.itemId);
        return sum + movement.quantity * (item?.avgUnitCost ?? 0);
      }, 0);

    const overview: InventoryOverview = {
      generatedAt: new Date().toISOString(),
      totalItems: items.length,
      lowStockCount: lowStockItems.length,
      outOfStockCount: outOfStockItems.length,
      stockValue: Number(stockValue.toFixed(2)),
      wasteValue: Number(wasteValue.toFixed(2)),
      items,
      recentMovements: this.state.stockMovements.slice(0, 8),
      purchaseSuggestions: items
        .filter((item) => item.status !== "IN_STOCK")
        .map((item) => ({
          itemId: item.id,
          itemName: item.name,
          reorderQty: item.reorderQty,
          unit: item.unit,
          supplierName: item.supplierName
        }))
    };

    return clone(overview);
  }

  getHrOverview() {
    const today = new Date().toISOString().slice(0, 10);
    const weekStart = new Date();
    weekStart.setUTCDate(weekStart.getUTCDate() - 7);

    const overview: HrOverview = {
      generatedAt: new Date().toISOString(),
      summary: {
        scheduledStaffToday: this.state.scheduledShifts.filter((shift) => shift.shiftDate === today)
          .length,
        pendingLeaveRequests: this.state.leaveRequests.filter((request) => request.status === "PENDING")
          .length,
        pendingSwapRequests: this.state.swapRequests.filter((request) => request.status === "PENDING")
          .length,
        approvedLeavesThisWeek: this.state.leaveRequests.filter(
          (request) =>
            request.status === "APPROVED" &&
            new Date(request.requestedAt).getTime() >= weekStart.getTime()
        ).length
      },
      schedules: this.state.scheduledShifts,
      leaveRequests: this.state.leaveRequests,
      swapRequests: this.state.swapRequests
    };

    return clone(overview);
  }

  getStaffHrWorkspace(userId: string) {
    const workspace: StaffHrWorkspace = {
      generatedAt: new Date().toISOString(),
      schedules: this.state.scheduledShifts.filter((shift) => shift.userId === userId),
      leaveRequests: this.state.leaveRequests.filter((request) => request.userId === userId),
      swapRequests: this.state.swapRequests.filter(
        (request) => request.requesterUserId === userId || request.targetUserId === userId
      )
    };

    return clone(workspace);
  }

  getBackofficeReport(options?: { includeHr?: boolean }) {
    this.expirePendingPaymentSessions(gatewaySystemActor);
    const includeHr = options?.includeHr ?? false;
    const paidOrders = this.state.orders.filter((order) => order.status === "PAID");
    const openOrders = this.state.orders.filter((order) => order.status !== "PAID");
    const openTables = this.state.tables.filter((table) => table.status !== "AVAILABLE").length;
    const pendingPaymentTables = this.state.tables.filter(
      (table) => table.status === "PENDING_PAYMENT"
    ).length;

    const hourlyMap = new Map<string, { sales: number; orders: number }>();
    paidOrders.forEach((order) => {
      const hour = new Date(order.updatedAt).toLocaleTimeString("en-US", {
        hour: "2-digit",
        hour12: false,
        timeZone: "UTC"
      });
      const bucket = hourlyMap.get(hour) ?? { sales: 0, orders: 0 };
      bucket.sales += order.totalAmount;
      bucket.orders += 1;
      hourlyMap.set(hour, bucket);
    });

    const itemMap = new Map<string, { menuItemId: string; name: string; quantity: number; sales: number }>();
    this.state.orders.forEach((order) => {
      order.items.forEach((item) => {
        const current = itemMap.get(item.menuItemId) ?? {
          menuItemId: item.menuItemId,
          name: item.name,
          quantity: 0,
          sales: 0
        };
        current.quantity += item.quantity;
        current.sales += item.quantity * item.price;
        itemMap.set(item.menuItemId, current);
      });
    });

    const paymentMap = new Map<
      ReceiptSummary["paymentMethod"],
      {
        method: ReceiptSummary["paymentMethod"];
        amount: number;
        salesAmount: number;
        tipAmount: number;
        count: number;
      }
    >();
    this.state.receipts.forEach((receipt) => {
      const refundedAmount = receipt.refundedAmount ?? 0;
      const netCollected = Math.max(receipt.totalAmount - refundedAmount, 0);
      const refundRatio = receipt.totalAmount > 0 ? Math.min(refundedAmount / receipt.totalAmount, 1) : 0;
      const netTipAmount = Number(((receipt.tipAmount ?? 0) * (1 - refundRatio)).toFixed(2));
      const netSalesAmount = Number((netCollected - netTipAmount).toFixed(2));
      const current = paymentMap.get(receipt.paymentMethod) ?? {
        method: receipt.paymentMethod,
        amount: 0,
        salesAmount: 0,
        tipAmount: 0,
        count: 0
      };
      current.amount += netCollected;
      current.salesAmount += netSalesAmount;
      current.tipAmount += netTipAmount;
      current.count += 1;
      paymentMap.set(receipt.paymentMethod, current);
    });

    const staffPerformance = includeHr
      ? this.state.shifts.map((shift) => {
          const checkIn = new Date(shift.checkInAt).getTime();
          const checkOut = shift.checkOutAt
            ? new Date(shift.checkOutAt).getTime()
            : Date.now();
          const hoursWorked = Math.max((checkOut - checkIn) / (1000 * 60 * 60), 0);

          return {
            staffName: shift.staffName,
            role: shift.role,
            ordersHandled: shift.ordersHandled,
            tipAmount: shift.tipAmount,
            hoursWorked: Number(hoursWorked.toFixed(1)),
            active: Boolean(shift.sessionActive),
            geofenceStatus: shift.geofenceStatus
          };
        })
      : [];

    const auditSummary = {
      totalEntries: this.state.auditEntries.length,
      voidRefundAlerts: this.state.auditEntries.filter((entry) =>
        /(void|refund)/i.test(entry.action)
      ).length,
      refundEvents: this.state.auditEntries.filter((entry) => /refund/i.test(entry.action)).length,
      voidEvents: this.state.auditEntries.filter((entry) => /void/i.test(entry.action)).length,
      authEvents: this.state.auditEntries.filter((entry) => entry.entityType === "AUTH").length,
      kitchenEvents: this.state.auditEntries.filter((entry) => entry.entityType === "KITCHEN").length
    };

    const refundBreakdown = this.state.receipts.reduce(
      (sum, receipt) => {
        const refundedAmount = receipt.refundedAmount ?? 0;
        const refundRatio = receipt.totalAmount > 0 ? Math.min(refundedAmount / receipt.totalAmount, 1) : 0;
        const tipRefund = Number(((receipt.tipAmount ?? 0) * refundRatio).toFixed(2));
        const salesRefund = Number((refundedAmount - tipRefund).toFixed(2));

        sum.refundsTotal += refundedAmount;
        sum.tipRefundsTotal += tipRefund;
        sum.salesRefundsTotal += salesRefund;
        return sum;
      },
      { refundsTotal: 0, salesRefundsTotal: 0, tipRefundsTotal: 0 }
    );
    const grossSalesBeforeRefunds = paidOrders.reduce((sum, order) => sum + order.totalAmount, 0);
    const grossTipsBeforeRefunds = this.state.receipts.reduce((sum, receipt) => sum + (receipt.tipAmount ?? 0), 0);
    const netSales = grossSalesBeforeRefunds - refundBreakdown.salesRefundsTotal;
    const netTips = grossTipsBeforeRefunds - refundBreakdown.tipRefundsTotal;
    const collectedTotal = netSales + netTips;
    const averageTicket = paidOrders.length > 0 ? netSales / paidOrders.length : 0;
      const receiptOps = {
        totalIssued: this.state.receipts.length,
        printedCount: this.state.receipts.filter((receipt) => Boolean(receipt.printedAt)).length,
        emailedCount: this.state.receipts.filter((receipt) => Boolean(receipt.emailSharedAt)).length,
        lineSharedCount: this.state.receipts.filter((receipt) => Boolean(receipt.lineSharedAt)).length,
        pendingShareCount: this.state.receipts.filter(
          (receipt) => !receipt.emailSharedAt && !receipt.lineSharedAt
        ).length,
        pendingPrintCount: this.state.receipts.filter((receipt) => !receipt.printedAt).length,
        taxInvoiceCount: this.state.receipts.filter((receipt) => receipt.receiptType === "TAX_INVOICE").length,
        eTaxCount: this.state.receipts.filter((receipt) => receipt.receiptType === "E_TAX").length,
        pendingETaxSubmissionCount: this.state.receipts.filter(
          (receipt) => receipt.receiptType === "E_TAX" && receipt.eTaxStatus !== "SUBMITTED"
        ).length,
        submittedETaxCount: this.state.receipts.filter((receipt) => receipt.eTaxStatus === "SUBMITTED").length
      };

    const gatewayOps = {
      totalSessions: this.state.paymentSessions.length,
      pendingCount: this.state.paymentSessions.filter((session) => session.status === "PENDING").length,
      capturedCount: this.state.paymentSessions.filter((session) => session.status === "CAPTURED").length,
      failedCount: this.state.paymentSessions.filter((session) => session.status === "FAILED").length,
      expiredCount: this.state.paymentSessions.filter((session) => session.status === "EXPIRED").length,
      totalAmount: Number(
        this.state.paymentSessions.reduce((sum, session) => sum + session.amount + (session.tipAmount ?? 0), 0).toFixed(2)
      ),
      pendingAmount: Number(
        this.state.paymentSessions
          .filter((session) => session.status === "PENDING")
          .reduce((sum, session) => sum + session.amount + (session.tipAmount ?? 0), 0)
          .toFixed(2)
      )
    };

    const report: BackofficeReport = {
      generatedAt: new Date().toISOString(),
      sales: {
        grossSales: netSales,
        refundsTotal: Number(refundBreakdown.refundsTotal.toFixed(2)),
        tipsTotal: Number(netTips.toFixed(2)),
        collectedTotal: Number(collectedTotal.toFixed(2)),
        paidOrders: paidOrders.length,
        voidedOrders: this.state.orders.filter((order) => order.status === "VOIDED").length,
        openOrders: openOrders.length,
        averageTicket: Number(averageTicket.toFixed(2)),
        openTables,
        pendingPaymentTables
      },
      hourlySales: Array.from(hourlyMap.entries())
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([hour, bucket]) => ({
          hour,
          sales: bucket.sales,
          orders: bucket.orders
        })),
      topItems: Array.from(itemMap.values())
        .sort((left, right) => right.quantity - left.quantity || right.sales - left.sales)
        .slice(0, 5),
      paymentMethods: Array.from(paymentMap.values()).sort((left, right) => right.amount - left.amount),
      receiptOps,
      gatewayOps,
      recentGatewaySessions: this.state.paymentSessions.slice(0, 8),
      recentReceiptDispatches: this.state.receiptDispatchAttempts.slice(0, 8),
      staffPerformance,
      auditSummary,
      hrRestricted: !includeHr
    };

    return clone(report);
  }

  getCrmOverview() {
    const activeThreshold = new Date();
    activeThreshold.setDate(activeThreshold.getDate() - 30);
    const monthToken = new Date().toISOString().slice(5, 7);

    return clone({
      generatedAt: new Date().toISOString(),
      totalMembers: this.state.members.length,
      loyaltyOutstandingPoints: this.state.members.reduce((sum, member) => sum + member.pointsBalance, 0),
      activeMembersThisMonth: this.state.members.filter(
        (member) => member.lastVisitAt && new Date(member.lastVisitAt) >= activeThreshold
      ).length,
      topMembers: [...this.state.members]
        .sort((left, right) => right.totalSpend - left.totalSpend)
        .slice(0, 5),
      birthdayMembers: this.state.members.filter(
        (member) => member.birthDate?.slice(5, 7) === monthToken
      )
    } satisfies CrmOverview);
  }

  getDeliveryCenterSnapshot() {
    const grossSales = this.state.deliveryOrders.reduce((sum, order) => sum + order.totalAmount, 0);
    const commissionTotal = this.state.deliveryOrders.reduce(
      (sum, order) => sum + order.commissionAmount,
      0
    );
    const activeOrders = this.state.deliveryOrders.filter(
      (order) => !["COMPLETED", "CANCELLED"].includes(order.status)
    );
    const avgEtaMinutes =
      activeOrders.length > 0
        ? activeOrders.reduce((sum, order) => sum + order.etaMinutes, 0) / activeOrders.length
        : 0;

    const center: DeliveryCenterSnapshot = {
      generatedAt: new Date().toISOString(),
      platforms: this.state.deliveryPlatforms,
      orders: this.state.deliveryOrders,
      summary: {
        grossSales,
        commissionTotal,
        activeOrders: activeOrders.length,
        avgEtaMinutes: Number(avgEtaMinutes.toFixed(1))
      }
    };

    return clone(center);
  }

  getShiftSessions() {
    return clone(this.state.shifts);
  }

  getActiveShiftForUser(userId: string) {
    return clone(
      this.state.shifts.find((shift) => shift.userId === userId && shift.sessionActive) ?? null
    );
  }

  getPublicTableSession(tableId: string) {
    const table = this.state.tables.find((item) => item.id === tableId);

    if (!table) {
      return null;
    }

    return clone({
      table,
      orders: this.state.orders.filter((order) => order.tableLabel === table.label && order.status !== "PAID")
    });
  }

  isAdminIpAllowed(ipAddress: string) {
    const normalizedIp = this.normalizeIp(ipAddress);
    return this.state.securityPolicy.adminIpWhitelist
      .map((item) => this.normalizeIp(item))
      .includes(normalizedIp);
  }

  requiresTwoFactor(role: UserRole) {
    return this.state.securityPolicy.twoFactorRoles.includes(role);
  }

  createTwoFactorChallenge(user: AuthUser) {
    const challengeId = crypto.randomUUID();
    const challenge: TwoFactorChallenge = {
      challengeId,
      userId: user.id,
      role: user.role,
      expiresAt: new Date(Date.now() + 5 * 60 * 1000).toISOString(),
      delivery: "DEMO_APP",
      demoCode: this.buildTwoFactorCode(user)
    };

    this.twoFactorChallenges.set(challengeId, challenge);
    return clone(challenge);
  }

  verifyTwoFactorChallenge(challengeId: string, code: string) {
    const challenge = this.twoFactorChallenges.get(challengeId);

    if (!challenge || new Date(challenge.expiresAt).getTime() < Date.now() || challenge.demoCode !== code) {
      return null;
    }

    this.twoFactorChallenges.delete(challengeId);
    const user = this.getUserById(challenge.userId);

    if (!user || this.getManagedUserAccount(user).accountStatus !== "ACTIVE") {
      return null;
    }

    return this.getAuthUser(user);
  }

  recordAuthEvent(actor: ActionActor, action: string, entityId: string) {
    this.appendAudit(actor, action, "AUTH", entityId);
    this.persist(() => this.persistenceAdapter?.persistAuthEvent(actor, action, entityId));
  }

  clockInStaff(user: AuthUser, payload: ClockInRequest) {
    const existing = this.state.shifts.find((shift) => shift.userId === user.id && shift.sessionActive);

    if (existing) {
      return clone(existing);
    }

    const distanceMeters = getDistanceMeters(
      payload.latitude,
      payload.longitude,
      branchGeofence.latitude,
      branchGeofence.longitude
    );
    const geofenceStatus = distanceMeters <= branchGeofence.radiusMeters ? "IN_RANGE" : "OUT_OF_RANGE";

    if (geofenceStatus === "OUT_OF_RANGE") {
      return null;
    }

    const shift: ShiftSession = {
      id: `SHIFT-${this.state.shifts.length + 1}`,
      userId: user.id,
      staffName: user.displayName,
      role: user.role === "CASHIER" ? "Cashier" : user.role === "STAFF" ? "Server" : "Bartender",
      geofenceStatus,
      checkInAt: new Date().toISOString(),
      sessionActive: true,
      distanceMeters,
      tipAmount: 0,
      ordersHandled: 0,
      deviceId: payload.deviceId,
      ipAddress: payload.ipAddress
    };

    this.state.shifts.unshift(shift);
    this.appendAudit(
      { id: user.id, displayName: user.displayName, role: user.role },
      "shift.clock_in",
      "AUTH",
      shift.id,
      { distanceMeters }
    );
    this.persist(() =>
      this.persistenceAdapter?.persistShiftSession(shift, {
        id: user.id,
        displayName: user.displayName,
        role: user.role
      })
    );
    return clone(shift);
  }

  clockOutStaff(user: AuthUser, payload: ClockOutRequest) {
    const shift = this.state.shifts.find((item) => item.userId === user.id && item.sessionActive);

    if (!shift) {
      return null;
    }

    const distanceMeters = getDistanceMeters(
      payload.latitude,
      payload.longitude,
      branchGeofence.latitude,
      branchGeofence.longitude
    );

    shift.checkOutAt = new Date().toISOString();
    shift.sessionActive = false;
    shift.distanceMeters = distanceMeters;
    shift.geofenceStatus = distanceMeters <= branchGeofence.radiusMeters ? "IN_RANGE" : "OUT_OF_RANGE";
    this.appendAudit(
      { id: user.id, displayName: user.displayName, role: user.role },
      "shift.clock_out",
      "AUTH",
      shift.id,
      { distanceMeters }
    );
    this.persist(() =>
      this.persistenceAdapter?.persistShiftSession(shift, {
        id: user.id,
        displayName: user.displayName,
        role: user.role
      })
    );
    return clone(shift);
  }

  lockTableForQr(tableId: string) {
    const table = this.state.tables.find((item) => item.id === tableId);

    if (!table) {
      return null;
    }

    const actor = {
      id: `QR-${tableId}`,
      displayName: "QR Guest",
      role: "STAFF" as const
    };

    table.status = "LOCKED_BY_QR";
    table.qrLocked = true;
    this.computeMetrics();
    this.appendAudit(actor, "table.qr_lock", "TABLE", table.id, {
      status: table.status
    });
    this.persist(() => this.persistenceAdapter?.persistQrTableLock(table.id, actor));
    return clone(table);
  }

  createPublicOrder(tableId: string, payload: PublicOrderRequest) {
    const table = this.state.tables.find((item) => item.id === tableId);

    if (!table) {
      return null;
    }

    if (!table.qrLocked) {
      this.lockTableForQr(tableId);
    }

    return this.createOrder(
      {
        tableId,
        guestCount: payload.guestCount,
        waiterName: payload.customerName?.trim() || "QR Guest",
        priority: "NORMAL",
        source: "QR",
        specialNote: payload.specialNote,
        items: payload.items
      },
      {
        id: `QR-${tableId}`,
        displayName: payload.customerName?.trim() || "QR Guest",
        role: "STAFF"
      }
    );
  }

  requestCheckBill(tableId: string, payload?: PublicCheckBillRequest) {
    const table = this.state.tables.find((item) => item.id === tableId);

    if (!table) {
      return null;
    }

    const actor = {
      id: `QR-${tableId}`,
      displayName: payload?.requestedBy?.trim() || "QR Guest",
      role: "STAFF" as const
    };

    table.status = "PENDING_PAYMENT";
    this.computeMetrics();
    this.appendAudit(actor, "table.check_bill_requested", "TABLE", table.id, {
      requestedBy: payload?.requestedBy?.trim() || "QR Guest"
    });
    this.persist(() =>
      this.persistenceAdapter?.persistTableCheckBillRequested(
        table.id,
        payload?.requestedBy?.trim() || "QR Guest",
        actor
      )
    );
    this.pushNotification({
      type: "CHECK_BILL",
      title: "Check bill requested",
      message: `Table ${table.label} requested check bill`,
      audienceRole: "STAFF",
      tableLabel: table.label
    });
    return clone(table);
  }

  toggleDeliveryPlatform(platform: DeliveryPlatform, enabled: boolean, actor: ActionActor) {
    const target = this.state.deliveryPlatforms.find((item) => item.platform === platform);

    if (!target) {
      return null;
    }

    target.enabled = enabled;
    target.acceptsOrders = enabled;
    target.menuSyncState = enabled ? "PENDING" : target.menuSyncState;
    this.appendAudit(actor, "delivery.platform_toggle", "ORDER", platform, {
      platform,
      enabled
    });
    this.persist(() =>
      this.persistenceAdapter?.persistDeliveryPlatformConnection(target, actor, {
        action: "delivery.platform_toggle",
        metadata: {
          platform,
          enabled
        }
      })
    );
    this.computeMetrics();
    return clone(target);
  }

  syncDeliveryPlatformMenu(platform: DeliveryPlatform, actor: ActionActor) {
    const target = this.state.deliveryPlatforms.find((item) => item.platform === platform);

    if (!target) {
      return null;
    }

    target.menuSyncState = "SYNCED";
    target.lastSyncAt = new Date().toISOString();
    this.appendAudit(actor, "delivery.menu_sync", "ORDER", platform, {
      platform,
      inStockMenuItems: this.state.menu.filter((item) => item.inStock).length
    });
    this.persist(() =>
      this.persistenceAdapter?.persistDeliveryPlatformConnection(target, actor, {
        action: "delivery.menu_sync",
        metadata: {
          platform,
          inStockMenuItems: this.state.menu.filter((item) => item.inStock).length
        }
      })
    );
    this.computeMetrics();
    return clone(target);
  }

  markKitchenReady(ticketId: string, actor: ActionActor) {
    return this.updateKitchenTicket(
      ticketId,
      actor,
      (ticket) => {
        ticket.colorState = "GREEN";
        ticket.elapsedMinutes = Math.max(ticket.elapsedMinutes, 6);
        this.notifyKitchenReady(ticket.tableLabel);
      },
      "kitchen.ready"
    );
  }

  acknowledgeKitchenTicket(ticketId: string, actor: ActionActor) {
    return this.updateKitchenTicket(
      ticketId,
      actor,
      (ticket) => {
        if (ticket.colorState === "RED") {
          ticket.colorState = "YELLOW";
        }

        ticket.elapsedMinutes = Math.max(ticket.elapsedMinutes, 5);
      },
      "kitchen.acknowledge"
    );
  }

  markKitchenOutOfStock(ticketId: string, actor: ActionActor) {
    return this.updateKitchenTicket(
      ticketId,
      actor,
      (ticket) => {
        ticket.note = [ticket.note, "Marked out of stock"].filter(Boolean).join(" · ");
        ticket.colorState = "BLUE";
      },
      "kitchen.out_of_stock"
    );
  }

  updateTableStatus(tableId: string, status: DiningTable["status"], actor: ActionActor) {
    const table = this.state.tables.find((item) => item.id === tableId);

    if (!table) {
      return null;
    }

    table.status = status;
    this.computeMetrics();
    this.appendAudit(actor, "table.status_change", "TABLE", table.id, { status });
    this.persist(() => this.persistenceAdapter?.persistTableStatus(table.id, status, actor));
    return clone(table);
  }

  updateTableLayout(
    tableId: string,
    payload: { x: number; y: number; width?: number; height?: number },
    actor: ActionActor
  ) {
    const table = this.state.tables.find((item) => item.id === tableId);

    if (!table) {
      return null;
    }

    table.layout = {
      x: Math.max(0, Math.min(payload.x, 90)),
      y: Math.max(0, Math.min(payload.y, 90)),
      width: payload.width ?? table.layout.width,
      height: payload.height ?? table.layout.height
    };
    this.appendAudit(actor, "table.layout_update", "TABLE", table.id, {
      x: table.layout.x,
      y: table.layout.y,
      width: table.layout.width,
      height: table.layout.height
    });
    this.persist(() => this.persistenceAdapter?.persistTableLayout(table.id, table.layout, actor));
    return clone(table);
  }

  reserveTable(tableId: string, payload: CreateReservationRequest, actor: ActionActor) {
    const table = this.state.tables.find((item) => item.id === tableId);

    if (!table) {
      return null;
    }

    table.status = "RESERVED";
    table.reservation = {
      id: table.reservation?.id ?? `RSV-${Date.now()}`,
      guestName: payload.guestName,
      reservedAt: payload.reservedAt,
      partySize: payload.partySize,
      contactPhone: payload.contactPhone,
      note: payload.note
    };
    this.computeMetrics();
    this.appendAudit(actor, "table.reserve", "TABLE", table.id, {
      guestName: payload.guestName,
      partySize: payload.partySize
    });
    this.persist(() => this.persistenceAdapter?.persistTableReservation(table, actor));
    return clone(table);
  }

  clearTableReservation(tableId: string, actor: ActionActor) {
    const table = this.state.tables.find((item) => item.id === tableId);

    if (!table) {
      return null;
    }

    table.reservation = undefined;
    if (table.status === "RESERVED") {
      table.status = "AVAILABLE";
    }
    this.computeMetrics();
    this.appendAudit(actor, "table.reservation_clear", "TABLE", table.id);
    this.persist(() => this.persistenceAdapter?.clearTableReservation(table.id, actor));
    return clone(table);
  }

  createMember(
    payload: CreateMemberRequest,
    actor: ActionActor
  ) {
    const member: CustomerMember = {
      id: `MBR-${String(this.state.members.length + 1).padStart(3, "0")}`,
      fullName: payload.fullName,
      phone: payload.phone,
      tier: "BRONZE",
      pointsBalance: 0,
      totalSpend: 0,
      favoriteItems: [],
      preferredLanguage: payload.preferredLanguage,
      birthDate: payload.birthDate,
      lineUserId: payload.lineUserId
    };

    this.state.members.unshift(member);
    this.appendAudit(actor, "member.create", "MEMBER", member.id, {
      fullName: member.fullName
    });
    this.persist(() => this.persistenceAdapter?.persistMemberCreated(member, actor));
    return clone(member);
  }

  assignMemberToOrder(orderId: string, memberId: string, actor: ActionActor) {
    const order = this.state.orders.find((item) => item.id === orderId);
    const member = this.state.members.find((item) => item.id === memberId);

    if (!order || !member || order.status === "PAID" || order.status === "VOIDED") {
      return null;
    }

    order.memberId = member.id;
    order.memberName = member.fullName;
    this.appendAudit(actor, "order.assign_member", "MEMBER", member.id, {
      memberId: member.id
    });
    this.persist(() =>
      this.persistenceAdapter?.persistOrderMemberAssigned(order.id, member.id, actor)
    );

    return clone({ order, member });
  }

  sendKitchenChatMessage(
    payload: { message: string; tableLabel?: string; target: "KITCHEN" | "FLOOR" },
    actor: ActionActor
  ) {
    const message: KitchenChatMessage = {
      id: `CHAT-${Date.now()}-${this.state.chatMessages.length + 1}`,
      fromName: actor.displayName,
      fromRole: actor.role,
      target: payload.target,
      tableLabel: payload.tableLabel,
      message: payload.message,
      createdAt: new Date().toISOString()
    };

    this.state.chatMessages.unshift(message);
    this.appendAudit(actor, "staff.chat_message", "KITCHEN", message.id, {
      target: payload.target,
      tableLabel: payload.tableLabel ?? ""
    });
    this.persist(() => this.persistenceAdapter?.persistChatMessage(message, actor));

    return clone(message);
  }

  requestManagerHelp(payload: { message: string; tableLabel?: string }, actor: ActionActor) {
    const notification: StaffNotification = {
      id: `NTF-${Date.now()}-${this.state.notifications.length + 1}`,
      type: "HELP_REQUEST",
      title: "Manager assistance requested",
      message: payload.message,
      createdAt: new Date().toISOString(),
      read: false,
      audienceRole: "MANAGER",
      tableLabel: payload.tableLabel
    };

    this.state.notifications.unshift(notification);
    this.appendAudit(actor, "staff.request_help", "AUTH", notification.id, {
      tableLabel: payload.tableLabel ?? ""
    });
    this.persist(() => this.persistenceAdapter?.persistStaffNotification(notification, actor));

    return clone(notification);
  }

  createScheduledShift(payload: CreateScheduledShiftRequest, actor: ActionActor) {
    const user = this.state.users.find((item) => item.id === payload.userId);

    if (!user) {
      return null;
    }

    const shift: ScheduledShift = {
      id: `SCH-${String(this.state.scheduledShifts.length + 1).padStart(3, "0")}`,
      userId: user.id,
      staffName: user.displayName,
      role: payload.role,
      shiftDate: payload.shiftDate,
      startTime: payload.startTime,
      endTime: payload.endTime,
      zone: payload.zone,
      status: "SCHEDULED",
      assignedByName: actor.displayName,
      note: payload.note
    };

    this.state.scheduledShifts.unshift(shift);
    this.appendAudit(actor, "hr.schedule_create", "AUTH", shift.id, {
      userId: user.id,
      shiftDate: shift.shiftDate,
      zone: shift.zone
    });
    this.pushNotification({
      type: "GENERAL",
      title: "New shift assigned",
      message: `${shift.shiftDate} ${shift.startTime}-${shift.endTime} at ${shift.zone}`,
      audienceRole: "STAFF",
      audienceUserId: user.id
    });
    this.persist(() => this.persistenceAdapter?.persistScheduledShift(shift, actor));
    return clone(shift);
  }

  createLeaveRequest(user: AuthUser, payload: CreateLeaveRequestRequest) {
    const coverStaff = payload.coverStaffUserId
      ? this.state.users.find((item) => item.id === payload.coverStaffUserId)
      : undefined;

    const request: LeaveRequest = {
      id: `LV-${String(this.state.leaveRequests.length + 1).padStart(3, "0")}`,
      userId: user.id,
      staffName: user.displayName,
      leaveDate: payload.leaveDate,
      leaveType: payload.leaveType,
      reason: payload.reason,
      status: "PENDING",
      requestedAt: new Date().toISOString(),
      coverStaffUserId: coverStaff?.id,
      coverStaffName: coverStaff?.displayName
    };

    this.state.leaveRequests.unshift(request);
    this.state.scheduledShifts.forEach((shift) => {
      if (shift.userId === user.id && shift.shiftDate === payload.leaveDate) {
        shift.status = "LEAVE_PENDING";
      }
    });

    this.appendAudit(
      { id: user.id, displayName: user.displayName, role: user.role },
      "hr.leave_request",
      "AUTH",
      request.id,
      {
        leaveDate: request.leaveDate,
        leaveType: request.leaveType
      }
    );
    this.pushNotification({
      type: "GENERAL",
      title: "Leave request pending",
      message: `${user.displayName} requested ${payload.leaveType.toLowerCase()} leave for ${payload.leaveDate}`,
      audienceRole: "MANAGER"
    });
    this.persist(() =>
      this.persistenceAdapter?.persistLeaveRequest(request, {
        id: user.id,
        displayName: user.displayName,
        role: user.role
      })
    );
    return clone(request);
  }

  reviewLeaveRequest(requestId: string, payload: ReviewHrRequestRequest, actor: ActionActor) {
    const request = this.state.leaveRequests.find((item) => item.id === requestId);

    if (!request) {
      return null;
    }

    request.status = payload.status;
    request.reviewerName = actor.displayName;
    request.reviewedAt = new Date().toISOString();

    this.state.scheduledShifts.forEach((shift) => {
      if (shift.userId === request.userId && shift.shiftDate === request.leaveDate) {
        shift.status = payload.status === "APPROVED" ? "LEAVE_APPROVED" : "CONFIRMED";
      }
    });

    this.appendAudit(actor, "hr.leave_review", "AUTH", request.id, {
      status: request.status,
      leaveDate: request.leaveDate
    });
    this.pushNotification({
      type: "GENERAL",
      title: `Leave request ${payload.status.toLowerCase()}`,
      message: `${request.leaveDate} · ${request.leaveType}`,
      audienceRole: "STAFF",
      audienceUserId: request.userId
    });
    this.persist(() => this.persistenceAdapter?.persistLeaveReview(request, actor));
    return clone(request);
  }

  createSwapRequest(user: AuthUser, payload: CreateSwapShiftRequest) {
    const shift = this.state.scheduledShifts.find((item) => item.id === payload.shiftId && item.userId === user.id);

    if (!shift) {
      return null;
    }

    const targetUser = payload.targetUserId
      ? this.state.users.find((item) => item.id === payload.targetUserId)
      : undefined;
    const request: SwapShiftRequest = {
      id: `SWAP-${String(this.state.swapRequests.length + 1).padStart(3, "0")}`,
      shiftId: shift.id,
      requesterUserId: user.id,
      requesterName: user.displayName,
      targetUserId: targetUser?.id,
      targetStaffName: targetUser?.displayName,
      shiftDate: shift.shiftDate,
      reason: payload.reason,
      status: "PENDING",
      requestedAt: new Date().toISOString()
    };

    this.state.swapRequests.unshift(request);
    shift.status = "SWAP_PENDING";

    this.appendAudit(
      { id: user.id, displayName: user.displayName, role: user.role },
      "hr.swap_request",
      "AUTH",
      request.id,
      {
        shiftId: shift.id,
        targetUserId: targetUser?.id ?? ""
      }
    );
    this.pushNotification({
      type: "GENERAL",
      title: "Swap shift pending",
      message: `${user.displayName} asked to swap ${shift.shiftDate} ${shift.startTime}-${shift.endTime}`,
      audienceRole: "MANAGER"
    });
    this.persist(() =>
      this.persistenceAdapter?.persistSwapRequest(request, {
        id: user.id,
        displayName: user.displayName,
        role: user.role
      })
    );
    return clone(request);
  }

  reviewSwapRequest(requestId: string, payload: ReviewHrRequestRequest, actor: ActionActor) {
    const request = this.state.swapRequests.find((item) => item.id === requestId);

    if (!request) {
      return null;
    }

    const shift = this.state.scheduledShifts.find((item) => item.id === request.shiftId);

    if (!shift) {
      return null;
    }

    request.status = payload.status;
    request.reviewerName = actor.displayName;
    request.reviewedAt = new Date().toISOString();

    if (payload.status === "APPROVED" && request.targetUserId) {
      const targetUser = this.state.users.find((item) => item.id === request.targetUserId);

      if (targetUser) {
        shift.userId = targetUser.id;
        shift.staffName = targetUser.displayName;
        shift.status = "SWAPPED";
      }
    } else {
      shift.status = "CONFIRMED";
    }

    this.appendAudit(actor, "hr.swap_review", "AUTH", request.id, {
      status: request.status,
      shiftId: shift.id
    });
    this.pushNotification({
      type: "GENERAL",
      title: `Swap request ${payload.status.toLowerCase()}`,
      message: `${shift.shiftDate} ${shift.startTime}-${shift.endTime} at ${shift.zone}`,
      audienceRole: "STAFF",
      audienceUserId: request.requesterUserId
    });
    if (payload.status === "APPROVED" && request.targetUserId) {
      this.pushNotification({
        type: "GENERAL",
        title: "Shift reassigned to you",
        message: `${shift.shiftDate} ${shift.startTime}-${shift.endTime} at ${shift.zone}`,
        audienceRole: "STAFF",
        audienceUserId: request.targetUserId
      });
    }

    this.persist(() => this.persistenceAdapter?.persistSwapReview(request, actor));

    return clone(request);
  }

  createUserAccount(payload: CreateUserAccountRequest, actor: ActionActor) {
    if (this.state.users.some((user) => user.username === payload.username)) {
      return null;
    }

    const user: UserAccount = {
      id: `USR-${payload.role}-${String(this.state.users.length + 1).padStart(2, "0")}`,
      username: payload.username,
      displayName: payload.displayName,
      role: payload.role,
      branchId: actor.role === "OWNER" ? "BR-TH-001" : "BR-TH-001",
      pin: payload.pin,
      accountStatus: "ACTIVE",
      expiresAt: payload.expiresAt
    };

    this.state.users.unshift(user);
    this.appendAudit(actor, "user.create", "AUTH", user.id, {
      username: user.username,
      role: user.role
    });
    const managedUser = this.getManagedUserAccount(user);
    this.persist(() => this.persistenceAdapter?.persistUserAccountCreated(user, actor));
    return clone(managedUser);
  }

  updateUserAccount(userId: string, payload: UpdateUserAccountRequest, actor: ActionActor) {
    const user = this.state.users.find((item) => item.id === userId);

    if (!user) {
      return null;
    }

    if (payload.displayName !== undefined) {
      user.displayName = payload.displayName;
    }

    if (payload.role !== undefined) {
      user.role = payload.role;
    }

    if (payload.pin !== undefined) {
      user.pin = payload.pin;
    }

    if (payload.expiresAt !== undefined) {
      user.expiresAt = payload.expiresAt ?? undefined;
    }

    if (payload.accountStatus !== undefined) {
      user.accountStatus = payload.accountStatus;
      user.blockedAt =
        payload.accountStatus === "BLOCKED" ? new Date().toISOString() : undefined;
    }

    this.appendAudit(actor, "user.update", "AUTH", user.id, {
      username: user.username,
      role: user.role,
      accountStatus: this.getManagedUserAccount(user).accountStatus
    });
    const managedUser = this.getManagedUserAccount(user);
    this.persist(() => this.persistenceAdapter?.persistUserAccountUpdated(user, actor));
    return clone(managedUser);
  }

  forceLogoutUser(userId: string, actor: ActionActor) {
    const user = this.state.users.find((item) => item.id === userId);

    if (!user) {
      return null;
    }

    user.forceLogoutAfter = new Date().toISOString();
    this.appendAudit(actor, "user.force_logout", "AUTH", user.id, {
      username: user.username
    });
    const managedUser = this.getManagedUserAccount(user);
    this.persist(() => this.persistenceAdapter?.persistUserAccountForcedLogout(user, actor));
    return clone(managedUser);
  }

  updateSecurityPolicy(payload: UpdateSecurityPolicyRequest, actor: ActionActor) {
    if (payload.adminIpWhitelist) {
      this.state.securityPolicy.adminIpWhitelist = Array.from(
        new Set(payload.adminIpWhitelist.map((item) => this.normalizeIp(item)).filter(Boolean))
      );
    }

    if (payload.twoFactorRoles) {
      this.state.securityPolicy.twoFactorRoles = payload.twoFactorRoles;
    }

    if (payload.receiptTemplate) {
      this.state.securityPolicy.receiptTemplate = {
        ...this.state.securityPolicy.receiptTemplate,
        ...payload.receiptTemplate
      };
    }

    this.appendAudit(actor, "security.policy_update", "AUTH", "SECURITY-POLICY", {
      adminIpWhitelist: this.state.securityPolicy.adminIpWhitelist.join(","),
      twoFactorRoles: this.state.securityPolicy.twoFactorRoles.join(","),
      receiptBusinessName: this.state.securityPolicy.receiptTemplate.businessName
    });
    this.persist(() => this.persistenceAdapter?.persistSecurityPolicy(this.state.securityPolicy, actor));
    return clone(this.state.securityPolicy);
  }

  createMenuItem(payload: CreateMenuItemRequest, actor: ActionActor) {
    const menuItem = {
      id: `M${this.state.menu.length + 1}`,
      category: payload.category,
      name: payload.name,
      price: payload.price,
      description: payload.description,
      imageUrl:
        payload.imageUrl ||
        "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80",
      tags: payload.tags?.length ? payload.tags : ["new"],
      allergenInfo: payload.allergenInfo,
      inStock: true,
      happyHourPrice: payload.happyHourPrice
    };

    this.state.menu.unshift(menuItem);
    this.appendAudit(actor, "menu.create", "ORDER", menuItem.id, {
      name: menuItem.name,
      price: menuItem.price
    });
    this.persist(() => this.persistenceAdapter?.persistMenuItemCreated(menuItem, actor));
    return clone(menuItem);
  }

  updateMenuItem(menuItemId: string, payload: UpdateMenuItemRequest, actor: ActionActor) {
    const menuItem = this.state.menu.find((item) => item.id === menuItemId);

    if (!menuItem) {
      return null;
    }

    if (payload.name !== undefined) {
      menuItem.name = payload.name;
    }

    if (payload.category !== undefined) {
      menuItem.category = payload.category;
    }

    if (payload.price !== undefined) {
      menuItem.price = payload.price;
    }

    if (payload.description !== undefined) {
      menuItem.description = payload.description;
    }

    if (payload.imageUrl !== undefined) {
      menuItem.imageUrl = payload.imageUrl;
    }

    if (payload.inStock !== undefined) {
      menuItem.inStock = payload.inStock;
    }

    if (payload.happyHourPrice !== undefined) {
      menuItem.happyHourPrice = payload.happyHourPrice ?? undefined;
    }

    this.appendAudit(actor, "menu.update", "ORDER", menuItem.id, {
      inStock: menuItem.inStock,
      price: menuItem.price
    });
    this.persist(() => this.persistenceAdapter?.persistMenuItemUpdated(menuItem, actor));
    return clone(menuItem);
  }

  recordStockMovement(
    payload: {
      itemId: string;
      type: "PURCHASE" | "USAGE" | "WASTE" | "ADJUSTMENT";
      quantity: number;
      note?: string;
    },
    actor: ActionActor
  ) {
    const item = this.state.inventoryItems.find((entry) => entry.id === payload.itemId);

    if (!item || !Number.isFinite(payload.quantity) || payload.quantity <= 0) {
      return null;
    }

    const movement = this.applyInventoryMovement(item, payload.type, payload.quantity, actor.displayName, payload.note);
    this.appendAudit(actor, "inventory.movement", "ORDER", item.id, {
      type: payload.type,
      quantity: payload.quantity
    });
    this.persist(() => this.persistenceAdapter?.persistInventoryMovement(this.withInventoryStatus(item), movement, actor));

    return clone({
      item: this.withInventoryStatus(item),
      movement
    });
  }

  createOrder(payload: CreateOrderRequest, actor: ActionActor) {
    const table = this.state.tables.find((item) => item.id === payload.tableId);

    if (!table) {
      return null;
    }

    const selectedItems = payload.items
      .map((line) => {
        const menuItem = this.state.menu.find((item) => item.id === line.menuItemId);
        return menuItem && menuItem.inStock ? { line, menuItem } : null;
      })
      .filter(Boolean) as Array<{
      line: CreateOrderRequest["items"][number];
      menuItem: MutableAppState["menu"][number];
    }>;

    if (selectedItems.length === 0) {
      return null;
    }

    const now = new Date().toISOString();
    const nextOrderNumber = this.state.orders.length + 301;
    const items = selectedItems.map(({ line, menuItem }, index) => {
      const station: KitchenStation = menuItem.tags.includes("bar") ? "BAR" : "HOT";
      const modifiers = this.resolveModifiers(menuItem, line.modifiers);
      const modifierTotal = modifiers.reduce((sum, modifier) => sum + modifier.extraPrice, 0);
      const unitPrice = menuItem.price + modifierTotal;

      return {
        id: `ITEM-${nextOrderNumber}-${index + 1}`,
        menuItemId: menuItem.id,
        name: menuItem.name,
        quantity: line.quantity,
        price: unitPrice,
        station,
        note: line.note,
        allergenFlags: menuItem.allergenInfo?.length ? menuItem.allergenInfo : menuItem.tags,
        modifiers,
        status: "SENT_TO_KITCHEN" as const
      };
    });

    const totalAmount = items.reduce((sum, item) => sum + item.price * item.quantity, 0);
    const order = {
      id: `ORD-${nextOrderNumber}`,
      tableLabel: table.label,
      waiterName: payload.waiterName,
      status: "SENT_TO_KITCHEN" as const,
      priority: payload.priority,
      guests: payload.guestCount,
      createdAt: now,
      updatedAt: now,
      totalAmount,
      items
    };

    this.state.orders.unshift(order);
    table.status = "SEATED";
    table.reservation = undefined;
    table.currentAmount += totalAmount;
    table.occupiedMinutes = Math.max(table.occupiedMinutes, 1);

    const stations = Array.from(new Set(items.map((item) => item.station)));
    const newKitchenCards: KitchenQueueCard[] = stations.map((station, index) => ({
      id: `K-${nextOrderNumber}-${index + 1}`,
      tableLabel: table.label,
      ticketNo: `${station}-${nextOrderNumber + index}`,
      station,
      priority: payload.priority,
      elapsedMinutes: 0,
      items: items
        .filter((item) => item.station === station)
        .map((item) =>
          `${item.name} x${item.quantity}${
            item.modifiers.length ? ` (${item.modifiers.map((modifier) => modifier.option).join(", ")})` : ""
          }`
        ),
      note: payload.specialNote,
      colorState: payload.priority === "VIP" ? "PURPLE" : payload.priority === "URGENT" ? "BLUE" : "RED"
    }));

    this.state.kitchen.unshift(...newKitchenCards);
    this.incrementOrdersHandledForActiveShift(actor);
    this.computeMetrics();
    this.consumeInventoryForOrder(order, actor);
    this.appendAudit(actor, "order.create", "ORDER", order.id, {
      tableLabel: table.label,
      totalAmount,
      items: items.length
    });
    this.persist(() => this.persistenceAdapter?.persistOrderCreated(order, payload, actor));
    return clone(order);
  }

  voidOrder(orderId: string, payload: VoidOrderRequest, actor: ActionActor) {
    const order = this.state.orders.find((item) => item.id === orderId);

    if (!order || order.status === "PAID" || order.status === "VOIDED") {
      return null;
    }

    order.status = "VOIDED";
    order.updatedAt = new Date().toISOString();

    const table = this.state.tables.find((item) => item.label === order.tableLabel);

    if (table) {
      table.status = "AVAILABLE";
      table.currentAmount = Math.max(table.currentAmount - order.totalAmount, 0);
      table.qrLocked = false;
      table.occupiedMinutes = 0;
    }

    this.state.kitchen = this.state.kitchen.filter(
      (ticket) => ticket.tableLabel !== order.tableLabel
    );

    this.appendAudit(actor, "order.void", "ORDER", order.id, {
      reason: payload.reason
    });
    this.appendException({
      id: `EXC-${Date.now()}-${this.state.exceptions.length + 1}`,
      kind: "VOID",
      orderId: order.id,
      reason: payload.reason,
      actorName: actor.displayName,
      actorRole: actor.role,
      createdAt: new Date().toISOString()
    }, actor);
    this.computeMetrics();
    this.persist(() => this.persistenceAdapter?.persistOrderVoided(order, payload, actor));

    return clone({ order });
  }

  settlePayment(orderId: string, payload: SettlePaymentRequest, actor: ActionActor) {
    const order = this.state.orders.find((item) => item.id === orderId);

    if (!order || order.status === "PAID" || order.status === "VOIDED") {
      return null;
    }

    this.closeOrderAsPaid(order);
    const receipt = this.issueReceipt(order, {
      amount: payload.amount,
      method: payload.method,
      tipAmount: payload.tipAmount
    });
    const memberSettlement = this.applyMemberSettlement(order);
    this.allocateTipToShift(order, payload.tipAmount ?? 0, actor);
    this.computeMetrics();
    this.auditReceiptIssued(order.id, receipt, payload.method, payload.amount, actor);
    this.auditMemberSettlement(order.id, memberSettlement, actor);
    this.persist(() => this.persistenceAdapter?.persistPaymentSettled(order, receipt, payload, actor));

    return clone({
      order,
      receipt
    });
  }

  createPaymentSession(orderId: string, payload: CreatePaymentSessionRequest, actor: ActionActor) {
    const order = this.state.orders.find((item) => item.id === orderId);

    if (!order || order.status === "PAID" || order.status === "VOIDED") {
      return null;
    }

    const session = createGatewayPaymentSession(order, payload);
    this.state.paymentSessions.unshift(session);
    this.appendAudit(actor, "payment.session_create", "PAYMENT", order.id, {
      sessionId: session.id,
      method: session.method,
      provider: session.provider,
      reference: session.reference,
      amount: session.amount,
      tipAmount: session.tipAmount ?? 0
    });
    this.persist(() =>
      this.persistenceAdapter?.persistPaymentSession(session, actor, {
        action: "payment.session_create",
        metadata: {
          sessionId: session.id,
          method: session.method,
          provider: session.provider,
          reference: session.reference,
          amount: session.amount,
          tipAmount: session.tipAmount ?? 0
        }
      })
    );
    return clone(session);
  }

  capturePaymentSession(sessionId: string, actor: ActionActor) {
    this.expirePendingPaymentSessions(actor);
    const session = this.state.paymentSessions.find((item) => item.id === sessionId);

    if (!session || session.status !== "PENDING") {
      return null;
    }

    const settled = this.settlePayment(
      session.orderId,
      {
        method: session.method,
        amount: session.amount,
        tipAmount: session.tipAmount
      },
      actor
    );

    if (!settled) {
      session.status = "FAILED";
      session.failureReason = "Order is no longer payable";
      this.persist(() =>
        this.persistenceAdapter?.persistPaymentSession(session, actor, {
          action: "payment.session_fail",
          metadata: {
            sessionId: session.id,
            method: session.method,
            provider: session.provider,
            reference: session.reference,
            reason: session.failureReason ?? ""
          }
        })
      );
      return null;
    }

    session.status = "CAPTURED";
    session.capturedAt = new Date().toISOString();
    this.appendAudit(actor, "payment.session_capture", "PAYMENT", session.orderId, {
      sessionId: session.id,
      method: session.method,
      provider: session.provider,
      reference: session.reference,
      receiptNo: settled.receipt.receiptNo
    });
    this.persist(() =>
      this.persistenceAdapter?.persistPaymentSession(session, actor, {
        action: "payment.session_capture",
        metadata: {
          sessionId: session.id,
          method: session.method,
          provider: session.provider,
          reference: session.reference,
          receiptNo: settled.receipt.receiptNo
        }
      })
    );

    return clone({
      session,
      order: settled.order,
      receipt: settled.receipt
    });
  }

  retryPaymentSession(sessionId: string, actor: ActionActor) {
    this.expirePendingPaymentSessions(actor);
    const priorSession = this.state.paymentSessions.find((item) => item.id === sessionId);

    if (!priorSession || !["FAILED", "EXPIRED"].includes(priorSession.status)) {
      return null;
    }

    const order = this.state.orders.find((item) => item.id === priorSession.orderId);

    if (!order || order.status === "PAID" || order.status === "VOIDED") {
      return null;
    }

    const nextSession = createGatewayPaymentSession(order, {
      method: priorSession.method,
      amount: priorSession.amount,
      tipAmount: priorSession.tipAmount
    });
    this.state.paymentSessions.unshift(nextSession);
    this.appendAudit(actor, "payment.session_retry", "PAYMENT", order.id, {
      priorSessionId: priorSession.id,
      sessionId: nextSession.id,
      method: nextSession.method,
      provider: nextSession.provider,
      reference: nextSession.reference
    });
    this.persist(() =>
      this.persistenceAdapter?.persistPaymentSession(nextSession, actor, {
        action: "payment.session_retry",
        metadata: {
          sessionId: nextSession.id,
          priorSessionId: priorSession.id,
          method: nextSession.method,
          provider: nextSession.provider,
          reference: nextSession.reference,
          amount: nextSession.amount,
          tipAmount: nextSession.tipAmount ?? 0
        }
      })
    );

    return clone({
      priorSession,
      session: nextSession
    });
  }

  processPaymentWebhook(
    payload: {
      sessionId?: string;
      reference?: string;
      provider?: PaymentGatewayProvider;
      status: PaymentSessionStatus;
      amount?: number;
      message?: string;
    },
    actor: ActionActor
  ) {
    const session = this.state.paymentSessions.find(
      (item) =>
        (payload.sessionId && item.id === payload.sessionId) ||
        (payload.reference && item.reference === payload.reference)
    );

    if (!session) {
      return null;
    }

    if (session.status === "CAPTURED") {
      return clone({
        session,
        order: this.state.orders.find((item) => item.id === session.orderId),
        receipt: this.getLatestReceiptForOrder(session.orderId)
      });
    }

    if (payload.status === "CAPTURED") {
      const captured = this.capturePaymentSession(session.id, actor);

      if (captured) {
        return captured;
      }

      return clone({
        session,
        order: this.state.orders.find((item) => item.id === session.orderId),
        receipt: this.getLatestReceiptForOrder(session.orderId)
      });
    }

    session.status = payload.status;
    session.failureReason = payload.message ?? (payload.status === "EXPIRED" ? "Gateway session expired" : "Gateway rejected payment");
    session.capturedAt = undefined;
    this.appendAudit(actor, `payment.session_${payload.status.toLowerCase()}`, "PAYMENT", session.orderId, {
      sessionId: session.id,
      method: session.method,
      provider: session.provider,
      reference: session.reference,
      reason: session.failureReason ?? ""
    });
    this.persist(() =>
      this.persistenceAdapter?.persistPaymentSession(session, actor, {
        action: payload.status === "EXPIRED" ? "payment.session_expire" : "payment.session_fail",
        metadata: {
          sessionId: session.id,
          method: session.method,
          provider: session.provider,
          reference: session.reference,
          reason: session.failureReason ?? ""
        }
      })
    );

    return clone({ session });
  }

  splitSettlePayment(orderId: string, payload: SplitPaymentRequest, actor: ActionActor) {
    const order = this.state.orders.find((item) => item.id === orderId);

    if (!order || order.status === "PAID" || order.status === "VOIDED") {
      return null;
    }

    if (!payload.payments.length) {
      return null;
    }

    const splitTotal = Number(
      payload.payments.reduce((sum, payment) => sum + payment.amount, 0).toFixed(2)
    );

    if (splitTotal !== Number(order.totalAmount.toFixed(2))) {
      return null;
    }

    this.closeOrderAsPaid(order);

    const splitGroupId = `SPL-${order.id}-${Date.now()}`;
    const receipts = payload.payments.map((payment, index) =>
      this.issueReceipt(order, payment, {
        splitGroupId,
        splitIndex: index + 1,
        splitCount: payload.payments.length,
        guestLabel: payment.guestLabel
      })
    );

    const memberSettlement = this.applyMemberSettlement(order);
    this.allocateTipToShift(
      order,
      payload.payments.reduce((sum, payment) => sum + (payment.tipAmount ?? 0), 0),
      actor
    );
    this.computeMetrics();
    receipts.forEach((receipt, index) => {
      const payment = payload.payments[index];
      this.auditReceiptIssued(order.id, receipt, payment.method, payment.amount, actor);
      this.persist(() =>
        this.persistenceAdapter?.persistPaymentSettled(
          order,
          receipt,
          {
            method: payment.method,
            amount: payment.amount,
            tipAmount: payment.tipAmount
          },
          actor
        )
      );
    });
    this.auditMemberSettlement(order.id, memberSettlement, actor);

    return clone({
      order,
      receipts
    });
  }

  refundReceipt(receiptId: string, payload: RefundReceiptRequest, actor: ActionActor) {
    const receipt = this.state.receipts.find((item) => item.id === receiptId);

    if (!receipt || receipt.status === "REFUNDED") {
      return null;
    }

    const order = this.state.orders.find((item) => item.id === receipt.orderId);

    if (!order) {
      return null;
    }

    const refundAmount = Math.min(payload.amount ?? receipt.totalAmount, receipt.totalAmount);
    receipt.status = "REFUNDED";
    receipt.refundedAmount = refundAmount;
    receipt.refundedAt = new Date().toISOString();
    receipt.refundReason = payload.reason;

    this.appendAudit(actor, "receipt.refund", "RECEIPT", receipt.id, {
      reason: payload.reason,
      amount: refundAmount
    });
    this.appendException({
      id: `EXC-${Date.now()}-${this.state.exceptions.length + 1}`,
      kind: "REFUND",
      orderId: order.id,
      receiptId: receipt.id,
      reason: payload.reason,
      amount: refundAmount,
      actorName: actor.displayName,
      actorRole: actor.role,
      createdAt: new Date().toISOString()
    }, actor);
    this.computeMetrics();
    this.persist(() => this.persistenceAdapter?.persistReceiptRefunded(order, receipt, payload, actor));

    return clone({
      order,
      receipt
    });
  }

  shareReceipt(
    receiptId: string,
    payload: ShareReceiptRequest,
    actor: ActionActor,
    dispatchMeta?: { provider?: string; message?: string }
  ) {
    const receipt = this.state.receipts.find((item) => item.id === receiptId);

    if (!receipt) {
      return null;
    }

    if (payload.channel === "EMAIL") {
      receipt.email = payload.recipient;
      receipt.emailSharedAt = new Date().toISOString();
    } else {
      receipt.lineUserId = payload.recipient;
      receipt.lineSharedAt = new Date().toISOString();
    }

    this.appendAudit(actor, "receipt.share", "RECEIPT", receipt.id, {
      channel: payload.channel,
      recipient: payload.recipient,
      receiptNo: receipt.receiptNo
    });
    this.appendReceiptDispatchAttempt(
      {
        id: `RDA-${Date.now()}-${this.state.receiptDispatchAttempts.length + 1}`,
        receiptId: receipt.id,
        receiptNo: receipt.receiptNo,
        channel: payload.channel,
        target: payload.recipient,
        status: "SUCCESS",
        provider:
          dispatchMeta?.provider ??
          (payload.channel === "EMAIL" ? "INTERNAL_EMAIL_QUEUE" : "LINE_OA_STUB"),
        message: dispatchMeta?.message ?? "Queued for dispatch",
        createdAt: new Date().toISOString()
      },
      actor
    );
    this.persist(() => this.persistenceAdapter?.persistReceiptShared(receipt, payload, actor));

    return clone({ receipt });
  }

    printReceipt(
      receiptId: string,
      payload: PrintReceiptRequest,
      actor: ActionActor,
      dispatchMeta?: { provider?: string; message?: string }
  ) {
    const receipt = this.state.receipts.find((item) => item.id === receiptId);

    if (!receipt) {
      return null;
    }

    receipt.printerName = payload.printerName;
    receipt.printedAt = new Date().toISOString();

    this.appendAudit(actor, "receipt.print", "RECEIPT", receipt.id, {
      printerName: payload.printerName,
      copies: payload.copies ?? 1,
      receiptNo: receipt.receiptNo
    });
    this.appendReceiptDispatchAttempt(
      {
        id: `RDA-${Date.now()}-${this.state.receiptDispatchAttempts.length + 1}`,
        receiptId: receipt.id,
        receiptNo: receipt.receiptNo,
        channel: "PRINT",
        target: payload.printerName,
        status: "SUCCESS",
        provider: dispatchMeta?.provider ?? "LOCAL_PRINTER_STUB",
        message: dispatchMeta?.message ?? `Printed ${payload.copies ?? 1} copy`,
        createdAt: new Date().toISOString()
      },
      actor
    );
    this.persist(() => this.persistenceAdapter?.persistReceiptPrinted(receipt, payload, actor));

      return clone({ receipt });
    }

    issueTaxInvoice(receiptId: string, payload: IssueTaxInvoiceRequest, actor: ActionActor) {
      const receipt = this.state.receipts.find((item) => item.id === receiptId);

      if (!receipt || receipt.status === "REFUNDED") {
        return null;
      }

      if (payload.receiptType === "E_TAX" && !payload.taxEmail?.trim()) {
        return null;
      }

      receipt.receiptType = payload.receiptType;
      receipt.taxPayerName = payload.taxPayerName.trim();
      receipt.taxId = payload.taxId.trim();
      receipt.taxBranchAddress = payload.taxBranchAddress?.trim() || undefined;
      receipt.taxEmail = payload.taxEmail?.trim() || undefined;
      receipt.taxIssuedAt = new Date().toISOString();
      receipt.eTaxStatus = payload.receiptType === "E_TAX" ? "PENDING_SUBMISSION" : undefined;
      receipt.eTaxSubmissionReference = undefined;
      receipt.eTaxSubmittedAt = undefined;
      receipt.eTaxError = undefined;

      this.appendAudit(actor, "receipt.tax_invoice_issue", "RECEIPT", receipt.id, {
        receiptNo: receipt.receiptNo,
        receiptType: receipt.receiptType,
        taxPayerName: receipt.taxPayerName,
        taxId: receipt.taxId
      });
      this.persist(() =>
        this.persistenceAdapter?.persistReceiptTaxInvoiceIssued(receipt, payload, actor)
      );
      this.computeMetrics();

      return clone({ receipt });
    }

    submitEtax(
      receiptId: string,
      payload: SubmitEtaxRequest,
      actor: ActionActor,
      submissionMeta?: { provider?: string; reference?: string; message?: string; failed?: boolean }
    ) {
      const receipt = this.state.receipts.find((item) => item.id === receiptId);

      if (!receipt || receipt.receiptType !== "E_TAX") {
        return null;
      }

      receipt.taxEmail = payload.channel === "EMAIL" ? payload.recipient?.trim() || receipt.taxEmail : receipt.taxEmail;
      receipt.eTaxStatus = submissionMeta?.failed ? "FAILED" : "SUBMITTED";
      receipt.eTaxSubmissionReference = submissionMeta?.reference ?? undefined;
      receipt.eTaxSubmittedAt = submissionMeta?.failed ? undefined : new Date().toISOString();
      receipt.eTaxError = submissionMeta?.failed ? submissionMeta.message ?? "Submission failed" : undefined;

      this.appendAudit(actor, "receipt.etax_submit", "RECEIPT", receipt.id, {
        receiptNo: receipt.receiptNo,
        channel: payload.channel,
        provider: submissionMeta?.provider ?? "RD_STUB",
        reference: submissionMeta?.reference ?? "",
        status: receipt.eTaxStatus
      });
      this.persist(() =>
        this.persistenceAdapter?.persistReceiptEtaxSubmitted(receipt, payload, actor)
      );
      this.computeMetrics();

      return clone({ receipt });
    }

  recordReceiptDispatchAttempt(attempt: ReceiptDispatchAttempt, actor: ActionActor) {
    this.appendReceiptDispatchAttempt(attempt, actor);
    return clone(attempt);
  }

  registerPushToken(userId: string, token: string, platform: string) {
    // In-memory: tokens not persisted across restarts.
    // Production: persist to DB and use Expo Push API for targeted delivery.
    const existing = this.state.pushTokens.findIndex((t) => t.userId === userId && t.platform === platform);
    const entry = { userId, token, platform, registeredAt: new Date().toISOString() };
    if (existing >= 0) this.state.pushTokens[existing] = entry;
    else this.state.pushTokens.push(entry);
  }

  private closeOrderAsPaid(order: MutableAppState["orders"][number]) {
    order.status = "PAID";
    order.updatedAt = new Date().toISOString();

    const table = this.state.tables.find((item) => item.label === order.tableLabel);

    if (table) {
      table.status = "AVAILABLE";
      table.currentAmount = 0;
      table.qrLocked = false;
      table.occupiedMinutes = 0;
    }

    this.state.kitchen = this.state.kitchen.filter(
      (ticket) => ticket.tableLabel !== order.tableLabel
    );
  }

  private incrementOrdersHandledForActiveShift(actor: ActionActor) {
    const activeShift = this.state.shifts.find(
      (shift) => shift.userId === actor.id && shift.sessionActive
    );

    if (!activeShift) {
      return;
    }

    activeShift.ordersHandled += 1;
    this.persist(() => this.persistenceAdapter?.persistShiftSession(activeShift, actor));
  }

  private issueReceipt(
    order: MutableAppState["orders"][number],
    payment: {
      method: ReceiptSummary["paymentMethod"];
      amount: number;
      tipAmount?: number;
      guestLabel?: string;
    },
    split?: {
      splitGroupId?: string;
      splitIndex?: number;
      splitCount?: number;
      guestLabel?: string;
    }
  ) {
    const tipAmount = payment.tipAmount ?? 0;
    const receipt: ReceiptSummary = {
      id: `RCPT-${this.state.receipts.length + 1}`,
      orderId: order.id,
      receiptNo: `R-${new Date().getFullYear()}-${String(this.state.receipts.length + 1).padStart(5, "0")}`,
      receiptType: "STANDARD",
      totalAmount: Number((payment.amount + tipAmount).toFixed(2)),
      tipAmount,
      paidAt: new Date().toISOString(),
      paymentMethod: payment.method,
      qrLookupToken: crypto.randomUUID(),
      splitGroupId: split?.splitGroupId,
      splitIndex: split?.splitIndex,
      splitCount: split?.splitCount,
      guestLabel: split?.guestLabel ?? payment.guestLabel,
      status: "ISSUED",
      email: undefined,
      lineUserId: undefined,
        emailSharedAt: undefined,
        lineSharedAt: undefined,
        printedAt: undefined,
        printerName: undefined,
        taxPayerName: undefined,
        taxId: undefined,
        taxBranchAddress: undefined,
        taxEmail: undefined,
        taxIssuedAt: undefined,
        eTaxStatus: undefined,
        eTaxSubmissionReference: undefined,
        eTaxSubmittedAt: undefined,
        eTaxError: undefined
      };

    this.state.receipts.unshift(receipt);
    return receipt;
  }

  private getLatestReceiptForOrder(orderId: string) {
    return this.state.receipts.find((receipt) => receipt.orderId === orderId);
  }

  private expirePendingPaymentSessions(actor: ActionActor) {
    const now = Date.now();
    const expiredSessions = this.state.paymentSessions.filter(
      (session) => session.status === "PENDING" && new Date(session.expiresAt).getTime() <= now
    );

    if (!expiredSessions.length) {
      return;
    }

    expiredSessions.forEach((session) => {
      session.status = "EXPIRED";
      session.failureReason = session.failureReason ?? "Gateway session expired";
      this.appendAudit(actor, "payment.session_expire", "PAYMENT", session.orderId, {
        sessionId: session.id,
        method: session.method,
        provider: session.provider,
        reference: session.reference,
        reason: session.failureReason ?? ""
      });
      this.persist(() =>
        this.persistenceAdapter?.persistPaymentSession(session, actor, {
          action: "payment.session_expire",
          metadata: {
            sessionId: session.id,
            method: session.method,
            provider: session.provider,
            reference: session.reference,
            reason: session.failureReason ?? ""
          }
        })
      );
    });
  }

  private auditReceiptIssued(
    orderId: string,
    receipt: ReceiptSummary,
    method: ReceiptSummary["paymentMethod"],
    amount: number,
    actor: ActionActor
  ) {
    const tipAmount = receipt.tipAmount ?? 0;
    this.appendAudit(actor, "payment.capture", "PAYMENT", orderId, {
      amount: Number((amount + tipAmount).toFixed(2)),
      baseAmount: amount,
      tipAmount,
      method
    });
    this.appendAudit(actor, "receipt.issue", "RECEIPT", receipt.id, {
      receiptNo: receipt.receiptNo,
      tipAmount,
      splitIndex: receipt.splitIndex ?? 1,
      splitCount: receipt.splitCount ?? 1
    });
  }

  private allocateTipToShift(
    order: MutableAppState["orders"][number],
    tipAmount: number,
    actor: ActionActor
  ) {
    if (tipAmount <= 0) {
      return;
    }

    const activeShift =
      this.state.shifts.find((shift) => shift.sessionActive && shift.staffName === order.waiterName) ??
      this.state.shifts.find((shift) => shift.sessionActive && shift.userId === actor.id);

    if (!activeShift) {
      return;
    }

    activeShift.tipAmount = Number((activeShift.tipAmount + tipAmount).toFixed(2));
    this.persist(() => this.persistenceAdapter?.persistShiftSession(activeShift, actor));
  }

  private auditMemberSettlement(
    orderId: string,
    memberSettlement: ReturnType<MemoryAppRepository["applyMemberSettlement"]>,
    actor: ActionActor
  ) {
    if (!memberSettlement) {
      return;
    }

    this.appendAudit(actor, "member.points_earned", "MEMBER", memberSettlement.member.id, {
      earnedPoints: memberSettlement.earnedPoints,
      orderId
    });
  }

  private getManagedUserAccount(user: UserAccount): ManagedUserAccount {
    const now = Date.now();
    const expired = user.expiresAt ? new Date(user.expiresAt).getTime() <= now : false;
    const accountStatus =
      user.accountStatus === "BLOCKED"
        ? "BLOCKED"
        : expired
          ? "EXPIRED"
          : user.accountStatus ?? "ACTIVE";

    return {
      id: user.id,
      username: user.username,
      displayName: user.displayName,
      role: user.role,
      branchId: user.branchId,
      accountStatus,
      expiresAt: user.expiresAt,
      blockedAt: user.blockedAt,
      forceLogoutAfter: user.forceLogoutAfter,
      lastLoginAt: user.lastLoginAt
    };
  }

  private consumeInventoryForOrder(order: MutableAppState["orders"][number], actor: ActionActor) {
    order.items.forEach((orderItem) => {
      this.state.inventoryItems.forEach((item) => {
        const usageRule = item.recipeUsage?.find((rule) => rule.menuItemId === orderItem.menuItemId);

        if (!usageRule) {
          return;
        }

        const quantity = Number((usageRule.quantityPerOrder * orderItem.quantity).toFixed(3));
        this.applyInventoryMovement(
          item,
          "USAGE",
          quantity,
          actor.displayName,
          `Auto-consume from ${order.id}`
        );
      });
    });
  }

  private applyInventoryMovement(
    item: StockItem,
    type: StockMovement["type"],
    quantity: number,
    actorName: string,
    note?: string
  ) {
    const previousStatus = this.getInventoryStatus(item);
    const delta = type === "PURCHASE" ? quantity : -quantity;

    item.onHand = Number(Math.max(item.onHand + delta, 0).toFixed(3));
    item.status = this.getInventoryStatus(item);
    item.lastUpdatedAt = new Date().toISOString();

    const movement: StockMovement = {
      id: `STK-${Date.now()}-${this.state.stockMovements.length + 1}`,
      itemId: item.id,
      itemName: item.name,
      type,
      quantity,
      unit: item.unit,
      note,
      createdAt: new Date().toISOString(),
      actorName
    };

    this.state.stockMovements.unshift(movement);
    this.maybeNotifyInventoryStatus(item, previousStatus);

    return movement;
  }

  private maybeNotifyInventoryStatus(item: StockItem, previousStatus: StockItem["status"]) {
    if (item.status === previousStatus || item.status === "IN_STOCK") {
      return;
    }

    const title = item.status === "OUT_OF_STOCK" ? "Out of stock alert" : "Low stock alert";
    const message =
      item.status === "OUT_OF_STOCK"
        ? `${item.name} is out of stock`
        : `${item.name} dropped below minimum level`;

    this.pushNotification({
      type: "GENERAL",
      title,
      message,
      audienceRole: "MANAGER"
    });
  }

  private withInventoryStatus(item: StockItem) {
    return {
      ...item,
      status: this.getInventoryStatus(item)
    };
  }

  private getInventoryStatus(item: Pick<StockItem, "onHand" | "minLevel">): StockItem["status"] {
    if (item.onHand <= 0) {
      return "OUT_OF_STOCK";
    }

    if (item.onHand <= item.minLevel) {
      return "LOW_STOCK";
    }

    return "IN_STOCK";
  }

  private normalizeIp(ipAddress: string) {
    return ipAddress.replace(/^::ffff:/, "").trim();
  }

  private buildTwoFactorCode(user: AuthUser) {
    const numericUserId = user.id.replace(/\D/g, "").slice(-3).padStart(3, "0");
    const numericBranchId = user.branchId.replace(/\D/g, "").slice(-3).padStart(3, "0");
    return `${numericUserId}${numericBranchId}`;
  }

  private appendAudit(
    actor: ActionActor,
    action: AuditEntry["action"],
    entityType: AuditEntry["entityType"],
    entityId: string,
    metadata?: AuditEntry["metadata"]
  ) {
    this.state.auditEntries.unshift({
      id: `AUD-${Date.now()}-${this.state.auditEntries.length + 1}`,
      actorName: actor.displayName,
      actorRole: actor.role,
      action,
      entityType,
      entityId,
      createdAt: new Date().toISOString(),
      metadata
    });
  }

  private appendException(record: ExceptionRecord, actor: ActionActor) {
    this.state.exceptions.unshift(record);
    this.persist(() => this.persistenceAdapter?.persistExceptionRecord(record, actor));
  }

  private appendReceiptDispatchAttempt(attempt: ReceiptDispatchAttempt, actor: ActionActor) {
    this.state.receiptDispatchAttempts.unshift(attempt);
    this.persist(() => this.persistenceAdapter?.persistReceiptDispatchAttempt(attempt, actor));
  }

  private pushNotification(
    input: Omit<StaffNotification, "id" | "createdAt" | "read">,
    actor?: ActionActor | null
  ) {
    const notification = {
      id: `NTF-${Date.now()}-${this.state.notifications.length + 1}`,
      createdAt: new Date().toISOString(),
      read: false,
      ...input
    };

    this.state.notifications.unshift(notification);
    this.persist(() => this.persistenceAdapter?.persistStaffNotification(notification, actor ?? null));
  }

  private notifyKitchenReady(tableLabel: string) {
    const targetOrder = this.state.orders.find(
      (order) => order.tableLabel === tableLabel && order.status !== "PAID" && order.status !== "VOIDED"
    );

    if (!targetOrder) {
      return;
    }

    this.pushNotification({
      type: "KITCHEN_READY",
      title: "Kitchen ready",
      message: `${tableLabel} is ready to serve`,
      audienceRole: "STAFF",
      tableLabel
    });
  }

  private applyMemberSettlement(order: MutableAppState["orders"][number]) {
    if (!order.memberId) {
      return null;
    }

    const member = this.state.members.find(
      (item: MutableAppState["members"][number]) => item.id === order.memberId
    );

    if (!member) {
      return null;
    }

    const earnedPoints = Math.floor(order.totalAmount / 25);
    member.pointsBalance += earnedPoints;
    member.totalSpend += order.totalAmount;
    member.lastVisitAt = new Date().toISOString();

    const itemNames = order.items.map((item) => item.name);
    member.favoriteItems = Array.from(
      new Set([...itemNames, ...member.favoriteItems])
    ).slice(0, 5);

    member.tier =
      member.totalSpend >= 15000 ? "GOLD" : member.totalSpend >= 5000 ? "SILVER" : "BRONZE";

    return {
      member,
      earnedPoints
    };
  }

  private computeMetrics() {
    const activeKitchen = this.state.kitchen.filter((card) => card.colorState !== "GREEN").length;
    const openTables = this.state.tables.filter((table) => table.status !== "AVAILABLE").length;
    const paidSales = this.state.orders
      .filter((order) => order.status === "PAID")
      .reduce((sum, order) => sum + order.totalAmount, 0);
    const deliveryGross = this.state.deliveryOrders.reduce((sum, order) => sum + order.totalAmount, 0);
    const platformMix = this.state.deliveryOrders.reduce<Record<string, number>>((acc, order) => {
      acc[order.platform] = (acc[order.platform] ?? 0) + order.totalAmount;
      return acc;
    }, {});
    const topPlatform = Object.entries(platformMix).sort((left, right) => right[1] - left[1])[0];

    this.state.metrics = [
      {
        label: "Sales Today",
        value: `THB ${(paidSales || 128450).toLocaleString("en-US")}`,
        delta: `${this.state.orders.filter((order) => order.status === "PAID").length} tickets closed`
      },
      {
        label: "Open Tables",
        value: `${openTables} / 26`,
        delta: `${this.state.tables.filter((table) => table.status === "PENDING_PAYMENT").length} waiting payment`
      },
      {
        label: "Delivery Mix",
        value: `THB ${(deliveryGross || 22900).toLocaleString("en-US")}`,
        delta: topPlatform ? `${topPlatform[0]} lead channel` : "No delivery sales yet"
      },
      {
        label: "Kitchen Queue",
        value: `${activeKitchen}`,
        delta: `${this.state.kitchen.filter((card) => card.elapsedMinutes >= 15).length} SLA risk`
      }
    ];
  }

  private resolveModifiers(
    menuItem: MutableAppState["menu"][number],
    requestedModifiers?: ModifierSelection[]
  ) {
    if (!requestedModifiers?.length || !menuItem.modifierGroups?.length) {
      return [];
    }

    return requestedModifiers.flatMap((requestedModifier) => {
      const group = menuItem.modifierGroups?.find(
        (modifierGroup) => modifierGroup.name === requestedModifier.group
      );
      const option = group?.options.find((modifierOption) => modifierOption.label === requestedModifier.option);

      if (!group || !option) {
        return [];
      }

      return [
        {
          group: group.name,
          option: option.label,
          extraPrice: option.extraPrice
        }
      ];
    });
  }

  private updateKitchenTicket(
    ticketId: string,
    actor: ActionActor,
    updater: (ticket: KitchenQueueCard) => void,
    action: string
  ) {
    const ticket = this.state.kitchen.find((item) => item.id === ticketId);

    if (!ticket) {
      return null;
    }

    updater(ticket);
    this.computeMetrics();
    this.appendAudit(actor, action, "KITCHEN", ticket.id, {
      tableLabel: ticket.tableLabel,
      station: ticket.station
    });
    this.persist(() => this.persistenceAdapter?.persistKitchenTicketUpdate(ticket, action, actor));
    return clone(ticket);
  }

  private persist(run: () => Promise<void> | void) {
    try {
      const result = run();

      if (result && typeof (result as Promise<void>).catch === "function") {
        void (result as Promise<void>).catch((error) => {
          console.error("Prisma persistence sync failed", error);
        });
      }
    } catch (error) {
      console.error("Prisma persistence sync failed", error);
    }
  }
}
