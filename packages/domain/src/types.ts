export type TableStatus =
  | "AVAILABLE"
  | "SEATED"
  | "PENDING_PAYMENT"
  | "CLEANING"
  | "RESERVED"
  | "LOCKED_BY_QR";

export type OrderStatus =
  | "DRAFT"
  | "SENT_TO_KITCHEN"
  | "IN_PROGRESS"
  | "READY"
  | "SERVED"
  | "PAID"
  | "VOIDED";

export type KitchenStation = "HOT" | "COLD" | "BAR" | "DESSERT";

export type PaymentMethod =
  | "CASH"
  | "PROMPTPAY"
  | "CARD"
  | "RABBIT_LINE_PAY"
  | "TRUE_MONEY";

export type PaymentGatewayProvider =
  | "PROMPTPAY_STUB"
  | "PROMPTPAY_REAL"
  | "OMISE_STUB"
  | "OMISE_REAL"
  | "TWOC2P_STUB"
  | "2C2P_REAL"
  | "RABBIT_LINE_PAY_STUB"
  | "TRUE_MONEY_STUB";

export type PaymentSessionStatus = "PENDING" | "CAPTURED" | "FAILED" | "EXPIRED";

export type SupportedLanguage = "th" | "en" | "zh" | "ja";
export type DeliveryPlatform = "GRAB_FOOD" | "LINE_MAN" | "FOODPANDA" | "ROBINHOOD" | "SHOPEE_FOOD" | "LALAMOVE";
export type DeliveryOrderStatus = "NEW" | "ACCEPTED" | "PREPARING" | "READY_FOR_PICKUP" | "OUT_FOR_DELIVERY" | "COMPLETED" | "CANCELLED";

export type UserRole = "OWNER" | "MANAGER" | "CASHIER" | "STAFF" | "KITCHEN";
export type AccountStatus = "ACTIVE" | "BLOCKED" | "EXPIRED";

export type AppPermission =
  | "orders.manage"
  | "payments.capture"
  | "menu.manage"
  | "sales.view_today"
  | "sales.view_all"
  | "hr.view"
  | "system.manage"
  | "audit.view"
  | "receipts.void";

export interface ModifierSelection {
  group: string;
  option: string;
  extraPrice: number;
}

export interface MenuModifierOption {
  id: string;
  label: string;
  extraPrice: number;
}

export interface MenuModifierGroup {
  id: string;
  name: string;
  required?: boolean;
  multiSelect?: boolean;
  options: MenuModifierOption[];
}

export interface MenuTranslation {
  name: string;
  category: string;
  description?: string;
}

export interface OrderItem {
  id: string;
  menuItemId: string;
  name: string;
  quantity: number;
  price: number;
  station: KitchenStation;
  note?: string;
  allergenFlags: string[];
  modifiers: ModifierSelection[];
  status: Exclude<OrderStatus, "PAID" | "VOIDED">;
}

export interface OrderTicket {
  id: string;
  tableLabel: string;
  waiterName: string;
  memberId?: string;
  memberName?: string;
  status: OrderStatus;
  priority: "NORMAL" | "VIP" | "URGENT";
  guests: number;
  createdAt: string;
  updatedAt: string;
  totalAmount: number;
  items: OrderItem[];
}

export interface TableReservation {
  id: string;
  guestName: string;
  reservedAt: string;
  partySize: number;
  contactPhone?: string;
  note?: string;
}

export interface TableLayoutPosition {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface DiningTable {
  id: string;
  label: string;
  seats: number;
  zone: string;
  status: TableStatus;
  occupiedMinutes: number;
  currentAmount: number;
  qrLocked: boolean;
  layout: TableLayoutPosition;
  reservation?: TableReservation;
}

export interface MenuItemSummary {
  id: string;
  category: string;
  name: string;
  price: number;
  description?: string;
  imageUrl: string;
  tags: string[];
  allergenInfo?: string[];
  inStock: boolean;
  happyHourPrice?: number;
  translations?: Partial<Record<SupportedLanguage, MenuTranslation>>;
  modifierGroups?: MenuModifierGroup[];
}

export interface ShiftSession {
  id: string;
  userId?: string;
  staffName: string;
  role: "Server" | "Bartender" | "Cashier";
  geofenceStatus: "IN_RANGE" | "OUT_OF_RANGE";
  checkInAt: string;
  checkOutAt?: string;
  sessionActive?: boolean;
  distanceMeters?: number;
  tipAmount: number;
  ordersHandled: number;
  deviceId: string;
  ipAddress?: string;
}

export type ShiftPlanStatus =
  | "SCHEDULED"
  | "CONFIRMED"
  | "LEAVE_PENDING"
  | "LEAVE_APPROVED"
  | "SWAP_PENDING"
  | "SWAPPED";

export type LeaveRequestType = "SICK" | "VACATION" | "PERSONAL";
export type HrRequestStatus = "PENDING" | "APPROVED" | "REJECTED";

export interface ScheduledShift {
  id: string;
  userId: string;
  staffName: string;
  role: ShiftSession["role"];
  shiftDate: string;
  startTime: string;
  endTime: string;
  zone: string;
  status: ShiftPlanStatus;
  assignedByName?: string;
  note?: string;
}

export interface LeaveRequest {
  id: string;
  userId: string;
  staffName: string;
  leaveDate: string;
  leaveType: LeaveRequestType;
  reason: string;
  status: HrRequestStatus;
  requestedAt: string;
  reviewerName?: string;
  reviewedAt?: string;
  coverStaffUserId?: string;
  coverStaffName?: string;
}

export interface SwapShiftRequest {
  id: string;
  shiftId: string;
  requesterUserId: string;
  requesterName: string;
  targetUserId?: string;
  targetStaffName?: string;
  shiftDate: string;
  reason: string;
  status: HrRequestStatus;
  requestedAt: string;
  reviewerName?: string;
  reviewedAt?: string;
}

export interface HrOverview {
  generatedAt: string;
  summary: {
    scheduledStaffToday: number;
    pendingLeaveRequests: number;
    pendingSwapRequests: number;
    approvedLeavesThisWeek: number;
  };
  schedules: ScheduledShift[];
  leaveRequests: LeaveRequest[];
  swapRequests: SwapShiftRequest[];
}

export interface StaffHrWorkspace {
  generatedAt: string;
  schedules: ScheduledShift[];
  leaveRequests: LeaveRequest[];
  swapRequests: SwapShiftRequest[];
}

export interface DashboardMetric {
  label: string;
  value: string;
  delta: string;
}

export interface SalesSummaryReport {
  grossSales: number;
  refundsTotal: number;
  tipsTotal: number;
  collectedTotal: number;
  paidOrders: number;
  voidedOrders: number;
  openOrders: number;
  averageTicket: number;
  openTables: number;
  pendingPaymentTables: number;
}

export interface HourlySalesBucket {
  hour: string;
  sales: number;
  orders: number;
}

export interface TopMenuItemReport {
  menuItemId: string;
  name: string;
  quantity: number;
  sales: number;
}

export interface PaymentMethodReport {
  method: PaymentMethod;
  amount: number;
  salesAmount: number;
  tipAmount: number;
  count: number;
}

export interface StaffPerformanceReport {
  staffName: string;
  role: ShiftSession["role"];
  ordersHandled: number;
  tipAmount: number;
  hoursWorked: number;
  active: boolean;
  geofenceStatus: ShiftSession["geofenceStatus"];
}

export interface AuditSummaryReport {
  totalEntries: number;
  voidRefundAlerts: number;
  refundEvents: number;
  voidEvents: number;
  authEvents: number;
  kitchenEvents: number;
}

export interface ReceiptOpsSummaryReport {
  totalIssued: number;
  printedCount: number;
  emailedCount: number;
  lineSharedCount: number;
  pendingShareCount: number;
  pendingPrintCount: number;
  taxInvoiceCount: number;
  eTaxCount: number;
  pendingETaxSubmissionCount: number;
  submittedETaxCount: number;
}

export interface PaymentGatewayOpsSummaryReport {
  totalSessions: number;
  pendingCount: number;
  capturedCount: number;
  failedCount: number;
  expiredCount: number;
  totalAmount: number;
  pendingAmount: number;
}

export interface ReceiptTemplateSettings {
  businessName: string;
  branchLabel: string;
  footerMessage: string;
  contactLine?: string;
  showQrLookupOnPrint: boolean;
  showTipLine: boolean;
}

export interface ReceiptDispatchAttempt {
  id: string;
  receiptId: string;
  receiptNo: string;
  channel: "EMAIL" | "LINE" | "PRINT";
  target: string;
  status: "SUCCESS" | "FAILED";
  provider: string;
  message?: string;
  createdAt: string;
}

export interface PaymentSessionSummary {
  id: string;
  orderId: string;
  tableLabel: string;
  method: Exclude<PaymentMethod, "CASH">;
  provider: PaymentGatewayProvider;
  amount: number;
  tipAmount?: number;
  status: PaymentSessionStatus;
  reference: string;
  qrPayload?: string;
  checkoutUrl?: string;
  createdAt: string;
  expiresAt: string;
  capturedAt?: string;
  failureReason?: string;
}

export interface BackofficeReport {
  generatedAt: string;
  sales: SalesSummaryReport;
  hourlySales: HourlySalesBucket[];
  topItems: TopMenuItemReport[];
  paymentMethods: PaymentMethodReport[];
  receiptOps: ReceiptOpsSummaryReport;
  gatewayOps: PaymentGatewayOpsSummaryReport;
  recentGatewaySessions: PaymentSessionSummary[];
  recentReceiptDispatches: ReceiptDispatchAttempt[];
  staffPerformance: StaffPerformanceReport[];
  auditSummary: AuditSummaryReport;
  hrRestricted: boolean;
}

export interface CustomerMember {
  id: string;
  fullName: string;
  phone: string;
  tier: "BRONZE" | "SILVER" | "GOLD";
  pointsBalance: number;
  totalSpend: number;
  lastVisitAt?: string;
  favoriteItems: string[];
  preferredLanguage?: SupportedLanguage;
  birthDate?: string;
  lineUserId?: string;
}

export interface CrmOverview {
  generatedAt: string;
  totalMembers: number;
  loyaltyOutstandingPoints: number;
  activeMembersThisMonth: number;
  topMembers: CustomerMember[];
  birthdayMembers: CustomerMember[];
}

export interface DeliveryPlatformConnection {
  platform: DeliveryPlatform;
  displayName: string;
  enabled: boolean;
  acceptsOrders: boolean;
  menuSyncState: "SYNCED" | "PENDING" | "FAILED";
  lastSyncAt?: string;
  commissionRate: number;
}

export interface DeliveryOrderLine {
  name: string;
  quantity: number;
}

export interface DeliveryOrder {
  id: string;
  platform: DeliveryPlatform;
  externalOrderNo: string;
  customerName: string;
  status: DeliveryOrderStatus;
  placedAt: string;
  etaMinutes: number;
  totalAmount: number;
  commissionAmount: number;
  branchStatus: "QUEUED" | "IN_KITCHEN" | "READY" | "DISPATCHED";
  items: DeliveryOrderLine[];
}

export interface DeliveryCenterSnapshot {
  generatedAt: string;
  platforms: DeliveryPlatformConnection[];
  orders: DeliveryOrder[];
  summary: {
    grossSales: number;
    commissionTotal: number;
    activeOrders: number;
    avgEtaMinutes: number;
  };
}

export type InventoryUnit = "kg" | "g" | "L" | "ml" | "pcs" | "bottle";
export type InventoryStockStatus = "IN_STOCK" | "LOW_STOCK" | "OUT_OF_STOCK";
export type StockMovementType = "PURCHASE" | "USAGE" | "WASTE" | "ADJUSTMENT";

export interface RecipeUsageRule {
  menuItemId: string;
  quantityPerOrder: number;
}

export interface StockItem {
  id: string;
  name: string;
  category: string;
  unit: InventoryUnit;
  onHand: number;
  minLevel: number;
  reorderQty: number;
  avgUnitCost: number;
  supplierName?: string;
  linkedMenuItems: string[];
  recipeUsage?: RecipeUsageRule[];
  status: InventoryStockStatus;
  lastUpdatedAt: string;
}

export interface StockMovement {
  id: string;
  itemId: string;
  itemName: string;
  type: StockMovementType;
  quantity: number;
  unit: InventoryUnit;
  note?: string;
  createdAt: string;
  actorName: string;
}

export interface PurchaseSuggestion {
  itemId: string;
  itemName: string;
  reorderQty: number;
  unit: InventoryUnit;
  supplierName?: string;
}

export interface InventoryOverview {
  generatedAt: string;
  totalItems: number;
  lowStockCount: number;
  outOfStockCount: number;
  stockValue: number;
  wasteValue: number;
  items: StockItem[];
  recentMovements: StockMovement[];
  purchaseSuggestions: PurchaseSuggestion[];
}

export interface KitchenQueueCard {
  id: string;
  tableLabel: string;
  ticketNo: string;
  station: KitchenStation;
  priority: "NORMAL" | "VIP" | "URGENT";
  elapsedMinutes: number;
  items: string[];
  note?: string;
  colorState: "RED" | "YELLOW" | "BLUE" | "PURPLE" | "GREEN";
}

export interface StaffNotification {
  id: string;
  type: "CHECK_BILL" | "KITCHEN_READY" | "HELP_REQUEST" | "GENERAL";
  title: string;
  message: string;
  createdAt: string;
  read: boolean;
  audienceRole: "STAFF" | "MANAGER" | "KITCHEN";
  audienceUserId?: string;
  tableLabel?: string;
}

export interface KitchenChatMessage {
  id: string;
  fromName: string;
  fromRole: UserRole;
  target: "KITCHEN" | "FLOOR";
  tableLabel?: string;
  message: string;
  createdAt: string;
}

export interface UserAccount {
  id: string;
  username: string;
  displayName: string;
  role: UserRole;
  branchId: string;
  pin: string;
  accountStatus?: AccountStatus;
  expiresAt?: string;
  blockedAt?: string;
  forceLogoutAfter?: string;
  lastLoginAt?: string;
}

export interface ManagedUserAccount {
  id: string;
  username: string;
  displayName: string;
  role: UserRole;
  branchId: string;
  accountStatus: AccountStatus;
  expiresAt?: string;
  blockedAt?: string;
  forceLogoutAfter?: string;
  lastLoginAt?: string;
}

export interface TwoFactorChallenge {
  challengeId: string;
  userId: string;
  role: UserRole;
  expiresAt: string;
  delivery: "DEMO_APP";
  demoCode: string;
}

export interface SecurityPolicy {
  adminIpWhitelist: string[];
  twoFactorRoles: UserRole[];
  receiptTemplate: ReceiptTemplateSettings;
}

export interface AuthUser {
  id: string;
  username: string;
  displayName: string;
  role: UserRole;
  branchId: string;
}

export interface AuthSession {
  accessToken: string;
  refreshToken: string;
  expiresAt: string;
  user: AuthUser;
}

export interface ReceiptSummary {
  id: string;
  orderId: string;
  receiptNo: string;
  receiptType: "STANDARD" | "TAX_INVOICE" | "E_TAX";
  totalAmount: number;
  tipAmount?: number;
  paidAt: string;
  paymentMethod: PaymentMethod;
  qrLookupToken: string;
  splitGroupId?: string;
  splitIndex?: number;
  splitCount?: number;
  guestLabel?: string;
  status?: "ISSUED" | "REFUNDED";
  refundedAmount?: number;
  refundedAt?: string;
  refundReason?: string;
  email?: string;
  lineUserId?: string;
  emailSharedAt?: string;
  lineSharedAt?: string;
  printedAt?: string;
  printerName?: string;
  taxPayerName?: string;
  taxId?: string;
  taxBranchAddress?: string;
  taxEmail?: string;
  taxIssuedAt?: string;
  eTaxStatus?: "PENDING_SUBMISSION" | "SUBMITTED" | "FAILED";
  eTaxSubmissionReference?: string;
  eTaxSubmittedAt?: string;
  eTaxError?: string;
}

export interface ExceptionRecord {
  id: string;
  kind: "VOID" | "REFUND";
  orderId: string;
  receiptId?: string;
  reason: string;
  amount?: number;
  actorName: string;
  actorRole: UserRole;
  createdAt: string;
}

export interface AuditEntry {
  id: string;
  actorName: string;
  actorRole: UserRole;
  action: string;
  entityType: "AUTH" | "ORDER" | "TABLE" | "KITCHEN" | "PAYMENT" | "RECEIPT" | "MEMBER";
  entityId: string;
  createdAt: string;
  metadata?: Record<string, string | number | boolean>;
}
