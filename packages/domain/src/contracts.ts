import type {
  AppPermission,
  AuditEntry,
  AuthSession,
  BackofficeReport,
  CrmOverview,
  CustomerMember,
  DashboardMetric,
  DeliveryCenterSnapshot,
  DeliveryPlatform,
  DiningTable,
  ExceptionRecord,
  HrOverview,
  InventoryOverview,
  InventoryUnit,
  LeaveRequest,
  LeaveRequestType,
  ManagedUserAccount,
  StockMovement,
  StockMovementType,
  KitchenQueueCard,
  KitchenChatMessage,
  MenuItemSummary,
  ModifierSelection,
  PaymentMethod,
  PaymentGatewayProvider,
  PaymentSessionSummary,
  OrderTicket,
  ReceiptSummary,
  ScheduledShift,
  SecurityPolicy,
  ReceiptTemplateSettings,
  ShiftSession,
  StaffHrWorkspace,
  StaffNotification,
  TwoFactorChallenge,
  SwapShiftRequest
} from "./types";

export interface PlatformOverview {
  metrics: DashboardMetric[];
  tables: DiningTable[];
  orders: OrderTicket[];
  menu: MenuItemSummary[];
  shifts: ShiftSession[];
  kitchen: KitchenQueueCard[];
}

export interface LiveHeartbeatEvent {
  type: "heartbeat";
  payload: {
    now: string;
  };
}

export interface LiveSnapshotEvent {
  type: "snapshot";
  payload: PlatformOverview;
}

export type LiveEvent = LiveHeartbeatEvent | LiveSnapshotEvent;

export interface LoginRequest {
  username: string;
  pin: string;
  deviceId?: string;
  ipAddress?: string;
}

export interface LoginResponse {
  session?: AuthSession;
  permissions?: AppPermission[];
  challenge?: TwoFactorChallenge;
}

export interface RefreshSessionRequest {
  refreshToken: string;
}

export interface RefreshSessionResponse {
  session: AuthSession;
  permissions: AppPermission[];
}

export interface VerifyTwoFactorRequest {
  challengeId: string;
  code: string;
}

export interface CreateOrderLineRequest {
  menuItemId: string;
  quantity: number;
  note?: string;
  modifiers?: ModifierSelection[];
}

export interface CreateOrderRequest {
  tableId: string;
  guestCount: number;
  waiterName: string;
  priority: "NORMAL" | "VIP" | "URGENT";
  source?: "POS" | "QR" | "DELIVERY" | "STAFF_APP";
  specialNote?: string;
  items: CreateOrderLineRequest[];
}

export interface SettlePaymentRequest {
  method: PaymentMethod;
  amount: number;
  tipAmount?: number;
}

export interface SettlePaymentResponse {
  order: OrderTicket;
  receipt: ReceiptSummary;
}

export interface CreatePaymentSessionRequest {
  method: Exclude<PaymentMethod, "CASH">;
  amount: number;
  tipAmount?: number;
}

export interface CreatePaymentSessionResponse {
  session: PaymentSessionSummary;
}

export interface CapturePaymentSessionResponse {
  session: PaymentSessionSummary;
  order: OrderTicket;
  receipt: ReceiptSummary;
}

export interface PaymentWebhookRequest {
  sessionId?: string;
  reference?: string;
  provider?: PaymentGatewayProvider;
  event: string;
  amount?: number;
  message?: string;
}

export interface PaymentWebhookResponse {
  session: PaymentSessionSummary;
  order?: OrderTicket;
  receipt?: ReceiptSummary;
}

export interface RetryPaymentSessionResponse {
  priorSession: PaymentSessionSummary;
  session: PaymentSessionSummary;
}

export interface SplitPaymentPart {
  method: PaymentMethod;
  amount: number;
  tipAmount?: number;
  guestLabel?: string;
}

export interface SplitPaymentRequest {
  payments: SplitPaymentPart[];
}

export interface SplitPaymentResponse {
  order: OrderTicket;
  receipts: ReceiptSummary[];
}

export interface VoidOrderRequest {
  reason: string;
}

export interface RefundReceiptRequest {
  reason: string;
  amount?: number;
}

export interface ShareReceiptRequest {
  channel: "EMAIL" | "LINE";
  recipient: string;
}

export interface PrintReceiptRequest {
  printerName: string;
  copies?: number;
}

export interface IssueTaxInvoiceRequest {
  receiptType: "TAX_INVOICE" | "E_TAX";
  taxPayerName: string;
  taxId: string;
  taxBranchAddress?: string;
  taxEmail?: string;
}

export interface AuditFeedResponse {
  entries: AuditEntry[];
}

export interface ReceiptFeedResponse {
  receipts: ReceiptSummary[];
}

export interface IssueTaxInvoiceResponse {
  receipt: ReceiptSummary;
}

export interface SubmitEtaxRequest {
  channel: "EMAIL" | "RD_PORTAL";
  recipient?: string;
}

export interface SubmitEtaxResponse {
  receipt: ReceiptSummary;
}

export interface PaymentSessionFeedResponse {
  sessions: PaymentSessionSummary[];
}

export interface ExceptionFeedResponse {
  exceptions: ExceptionRecord[];
}

export interface MemberFeedResponse {
  members: CustomerMember[];
}

export interface CreateMemberRequest {
  fullName: string;
  phone: string;
  preferredLanguage?: "th" | "en" | "zh" | "ja";
  birthDate?: string;
  lineUserId?: string;
}

export interface AssignMemberRequest {
  memberId: string;
}

export interface CrmOverviewResponse {
  overview: CrmOverview;
}

export interface BackofficeReportResponse {
  report: BackofficeReport;
}

export interface DeliveryCenterResponse {
  center: DeliveryCenterSnapshot;
}

export interface DeliveryPlatformToggleRequest {
  enabled: boolean;
}

export interface DeliveryMenuSyncRequest {
  propagateOutOfStock?: boolean;
}

export interface DeliveryPlatformResponse {
  platform: DeliveryPlatform;
}

export interface CreateMenuItemRequest {
  category: string;
  name: string;
  price: number;
  description?: string;
  imageUrl?: string;
  tags?: string[];
  allergenInfo?: string[];
  happyHourPrice?: number;
}

export interface UpdateMenuItemRequest {
  name?: string;
  category?: string;
  price?: number;
  description?: string;
  imageUrl?: string;
  inStock?: boolean;
  happyHourPrice?: number | null;
}

export interface InventoryOverviewResponse {
  overview: InventoryOverview;
}

export interface InventoryMovementFeedResponse {
  movements: StockMovement[];
}

export interface RecordStockMovementRequest {
  itemId: string;
  type: StockMovementType;
  quantity: number;
  unit?: InventoryUnit;
  note?: string;
}

export interface UpdateTableLayoutRequest {
  x: number;
  y: number;
  width?: number;
  height?: number;
}

export interface CreateReservationRequest {
  guestName: string;
  reservedAt: string;
  partySize: number;
  contactPhone?: string;
  note?: string;
}

export interface TableResponse {
  table: DiningTable;
}

export interface ClockInRequest {
  latitude: number;
  longitude: number;
  deviceId: string;
  ipAddress?: string;
}

export interface ClockOutRequest {
  latitude: number;
  longitude: number;
}

export interface ShiftSessionResponse {
  shift: ShiftSession;
}

export interface StaffOrdersResponse {
  orders: OrderTicket[];
}

export interface HrOverviewResponse {
  overview: HrOverview;
}

export interface StaffHrWorkspaceResponse {
  workspace: StaffHrWorkspace;
}

export interface CreateScheduledShiftRequest {
  userId: string;
  role: ShiftSession["role"];
  shiftDate: string;
  startTime: string;
  endTime: string;
  zone: string;
  note?: string;
}

export interface CreateLeaveRequestRequest {
  leaveDate: string;
  leaveType: LeaveRequestType;
  reason: string;
  coverStaffUserId?: string;
}

export interface CreateSwapShiftRequest {
  shiftId: string;
  targetUserId?: string;
  reason: string;
}

export interface ReviewHrRequestRequest {
  status: "APPROVED" | "REJECTED";
}

export interface ScheduledShiftResponse {
  shift: ScheduledShift;
}

export interface LeaveRequestResponse {
  request: LeaveRequest;
}

export interface SwapShiftRequestResponse {
  request: SwapShiftRequest;
}

export interface StaffNotificationFeedResponse {
  notifications: StaffNotification[];
}

export interface KitchenChatFeedResponse {
  messages: KitchenChatMessage[];
}

export interface SendKitchenChatRequest {
  message: string;
  tableLabel?: string;
  target: "KITCHEN" | "FLOOR";
}

export interface RequestManagerHelpRequest {
  message: string;
  tableLabel?: string;
}

export interface PublicTableResponse {
  table: DiningTable;
  menu: MenuItemSummary[];
  orders: OrderTicket[];
}

export interface PublicOrderRequest {
  guestCount: number;
  customerName?: string;
  items: CreateOrderLineRequest[];
  specialNote?: string;
}

export interface PublicCheckBillRequest {
  requestedBy?: string;
}

export interface ManagedUserFeedResponse {
  users: ManagedUserAccount[];
}

export interface SecurityPolicyResponse {
  policy: SecurityPolicy;
}

export interface CreateUserAccountRequest {
  username: string;
  displayName: string;
  role: "OWNER" | "MANAGER" | "CASHIER" | "STAFF" | "KITCHEN";
  pin: string;
  expiresAt?: string;
}

export interface UpdateUserAccountRequest {
  displayName?: string;
  role?: "OWNER" | "MANAGER" | "CASHIER" | "STAFF" | "KITCHEN";
  pin?: string;
  expiresAt?: string | null;
  accountStatus?: "ACTIVE" | "BLOCKED" | "EXPIRED";
}

export interface UpdateSecurityPolicyRequest {
  adminIpWhitelist?: string[];
  twoFactorRoles?: ("OWNER" | "MANAGER" | "CASHIER" | "STAFF" | "KITCHEN")[];
  receiptTemplate?: Partial<ReceiptTemplateSettings>;
}
