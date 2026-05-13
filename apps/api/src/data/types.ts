import type {
  AppPermission,
  AuditEntry,
  AuthUser,
  BackofficeReport,
  ClockInRequest,
  ClockOutRequest,
  CreateMemberRequest,
  CreateLeaveRequestRequest,
  CreateScheduledShiftRequest,
  CreateSwapShiftRequest,
  CreateUserAccountRequest,
  CreatePaymentSessionRequest,
  CrmOverview,
  CreateMenuItemRequest,
  CustomerMember,
  CreateReservationRequest,
  CreateOrderRequest,
  DeliveryCenterSnapshot,
  DeliveryPlatformConnection,
  DeliveryPlatform,
  DiningTable,
  ExceptionRecord,
  HrOverview,
  InventoryOverview,
  LeaveRequest,
  ManagedUserAccount,
  PaymentGatewayProvider,
  PaymentSessionStatus,
  PrintReceiptRequest,
  RecordStockMovementRequest,
  ReceiptDispatchAttempt,
  ShareReceiptRequest,
  SubmitEtaxRequest,
  ReviewHrRequestRequest,
  ScheduledShift,
  SecurityPolicy,
  StockItem,
  StockMovement,
  KitchenChatMessage,
  KitchenQueueCard,
  OrderTicket,
  PublicCheckBillRequest,
  PublicOrderRequest,
  ReceiptSummary,
  PlatformOverview,
  PaymentSessionSummary,
  IssueTaxInvoiceRequest,
  RefundReceiptRequest,
  TableLayoutPosition,
  SettlePaymentRequest,
  SplitPaymentRequest,
  UpdateMenuItemRequest,
  UpdateSecurityPolicyRequest,
  UpdateUserAccountRequest,
  StaffNotification,
  StaffHrWorkspace,
  TwoFactorChallenge,
  ShiftSession,
  SwapShiftRequest,
  UserAccount,
  VoidOrderRequest,
  UserRole
} from "@mypos/domain";

export interface AppSnapshot extends PlatformOverview {}

export interface ActionActor {
  id: string;
  displayName: string;
  role: UserRole;
}

export interface MutableAppState extends AppSnapshot {
  users: UserAccount[];
  members: CustomerMember[];
  receipts: ReceiptSummary[];
  paymentSessions: PaymentSessionSummary[];
  auditEntries: AuditEntry[];
  exceptions: ExceptionRecord[];
  receiptDispatchAttempts: ReceiptDispatchAttempt[];
  notifications: StaffNotification[];
  chatMessages: KitchenChatMessage[];
  inventoryItems: StockItem[];
  stockMovements: StockMovement[];
  scheduledShifts: ScheduledShift[];
  leaveRequests: LeaveRequest[];
  swapRequests: SwapShiftRequest[];
  securityPolicy: SecurityPolicy;
  deliveryOrders: import("@mypos/domain").DeliveryOrder[];
  deliveryPlatforms: import("@mypos/domain").DeliveryPlatformConnection[];
}

export interface AppRepository {
  getSnapshot(): AppSnapshot;
  hydrate(partial: Partial<MutableAppState>): void;
  resetDemoState(): boolean;
  getPermissions(role: UserRole): AppPermission[];
  findUserByCredentials(username: string, pin: string): UserAccount | null;
  getUserById(userId: string): UserAccount | null;
  getAuthUser(user: UserAccount): AuthUser;
  getAuditEntries(): AuditEntry[];
  getManagedUsers(): ManagedUserAccount[];
  getSecurityPolicy(): SecurityPolicy;
  getMembers(): CustomerMember[];
  getReceipts(): ReceiptSummary[];
  getPaymentSessions(): PaymentSessionSummary[];
  getReceiptById(receiptId: string): ReceiptSummary | null;
  getReceiptDispatchAttempts(): ReceiptDispatchAttempt[];
  getExceptions(): ExceptionRecord[];
  getStaffNotifications(userId: string, role: UserRole): StaffNotification[];
  getAllStaffNotifications(): StaffNotification[];
  getChatMessages(role: UserRole): KitchenChatMessage[];
  getAllChatMessages(): KitchenChatMessage[];
  getInventoryOverview(): InventoryOverview;
  getHrOverview(): HrOverview;
  getStaffHrWorkspace(userId: string): StaffHrWorkspace;
  getBackofficeReport(options?: { includeHr?: boolean }): BackofficeReport;
  getCrmOverview(): CrmOverview;
  getDeliveryCenterSnapshot(): DeliveryCenterSnapshot;
  getShiftSessions(): ShiftSession[];
  getActiveShiftForUser(userId: string): ShiftSession | null;
  getPublicTableSession(tableId: string): { table: DiningTable; orders: OrderTicket[] } | null;
  isAdminIpAllowed(ipAddress: string): boolean;
  requiresTwoFactor(role: UserRole): boolean;
  recordAuthEvent(actor: ActionActor, action: string, entityId: string): void;
  createTwoFactorChallenge(user: AuthUser): TwoFactorChallenge;
  verifyTwoFactorChallenge(challengeId: string, code: string): AuthUser | null;
  clockInStaff(user: AuthUser, payload: ClockInRequest): ShiftSession | null;
  clockOutStaff(user: AuthUser, payload: ClockOutRequest): ShiftSession | null;
  lockTableForQr(tableId: string): DiningTable | null;
  createPublicOrder(tableId: string, payload: PublicOrderRequest): OrderTicket | null;
  requestCheckBill(tableId: string, payload?: PublicCheckBillRequest): DiningTable | null;
  toggleDeliveryPlatform(
    platform: DeliveryPlatform,
    enabled: boolean,
    actor: ActionActor
  ): DeliveryCenterSnapshot["platforms"][number] | null;
  syncDeliveryPlatformMenu(
    platform: DeliveryPlatform,
    actor: ActionActor
  ): DeliveryCenterSnapshot["platforms"][number] | null;
  markKitchenReady(ticketId: string, actor: ActionActor): KitchenQueueCard | null;
  acknowledgeKitchenTicket(ticketId: string, actor: ActionActor): KitchenQueueCard | null;
  markKitchenOutOfStock(ticketId: string, actor: ActionActor): KitchenQueueCard | null;
  updateTableStatus(tableId: string, status: DiningTable["status"], actor: ActionActor): DiningTable | null;
  updateTableLayout(
    tableId: string,
    payload: { x: number; y: number; width?: number; height?: number },
    actor: ActionActor
  ): DiningTable | null;
  reserveTable(
    tableId: string,
    payload: CreateReservationRequest,
    actor: ActionActor
  ): DiningTable | null;
  clearTableReservation(tableId: string, actor: ActionActor): DiningTable | null;
  createMember(
    payload: CreateMemberRequest,
    actor: ActionActor
  ): CustomerMember;
  assignMemberToOrder(
    orderId: string,
    memberId: string,
    actor: ActionActor
  ): { order: OrderTicket; member: CustomerMember } | null;
  sendKitchenChatMessage(
    payload: { message: string; tableLabel?: string; target: "KITCHEN" | "FLOOR" },
    actor: ActionActor
  ): KitchenChatMessage;
  requestManagerHelp(
    payload: { message: string; tableLabel?: string },
    actor: ActionActor
  ): StaffNotification;
  createScheduledShift(
    payload: CreateScheduledShiftRequest,
    actor: ActionActor
  ): ScheduledShift | null;
  createLeaveRequest(
    user: AuthUser,
    payload: CreateLeaveRequestRequest
  ): LeaveRequest | null;
  reviewLeaveRequest(
    requestId: string,
    payload: ReviewHrRequestRequest,
    actor: ActionActor
  ): LeaveRequest | null;
  createSwapRequest(
    user: AuthUser,
    payload: CreateSwapShiftRequest
  ): SwapShiftRequest | null;
  reviewSwapRequest(
    requestId: string,
    payload: ReviewHrRequestRequest,
    actor: ActionActor
  ): SwapShiftRequest | null;
  createUserAccount(payload: CreateUserAccountRequest, actor: ActionActor): ManagedUserAccount | null;
  updateUserAccount(
    userId: string,
    payload: UpdateUserAccountRequest,
    actor: ActionActor
  ): ManagedUserAccount | null;
  forceLogoutUser(userId: string, actor: ActionActor): ManagedUserAccount | null;
  updateSecurityPolicy(
    payload: UpdateSecurityPolicyRequest,
    actor: ActionActor
  ): SecurityPolicy;
  createMenuItem(
    payload: CreateMenuItemRequest,
    actor: ActionActor
  ): import("@mypos/domain").MenuItemSummary;
  updateMenuItem(
    menuItemId: string,
    payload: UpdateMenuItemRequest,
    actor: ActionActor
  ): import("@mypos/domain").MenuItemSummary | null;
  recordStockMovement(
    payload: RecordStockMovementRequest,
    actor: ActionActor
  ): { item: StockItem; movement: StockMovement } | null;
  createOrder(payload: CreateOrderRequest, actor: ActionActor): OrderTicket | null;
  voidOrder(
    orderId: string,
    payload: VoidOrderRequest,
    actor: ActionActor
  ): { order: OrderTicket } | null;
  settlePayment(
    orderId: string,
    payload: SettlePaymentRequest,
    actor: ActionActor
  ): { order: OrderTicket; receipt: ReceiptSummary } | null;
  createPaymentSession(
    orderId: string,
    payload: CreatePaymentSessionRequest,
    actor: ActionActor
  ): PaymentSessionSummary | null;
  capturePaymentSession(
    sessionId: string,
    actor: ActionActor
  ): { session: PaymentSessionSummary; order: OrderTicket; receipt: ReceiptSummary } | null;
  retryPaymentSession(
    sessionId: string,
    actor: ActionActor
  ): { priorSession: PaymentSessionSummary; session: PaymentSessionSummary } | null;
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
  ): { session: PaymentSessionSummary; order?: OrderTicket; receipt?: ReceiptSummary } | null;
  splitSettlePayment(
    orderId: string,
    payload: SplitPaymentRequest,
    actor: ActionActor
  ): { order: OrderTicket; receipts: ReceiptSummary[] } | null;
  refundReceipt(
    receiptId: string,
    payload: RefundReceiptRequest,
    actor: ActionActor
  ): { order: OrderTicket; receipt: ReceiptSummary } | null;
  shareReceipt(
    receiptId: string,
    payload: ShareReceiptRequest,
    actor: ActionActor,
    dispatchMeta?: { provider?: string; message?: string }
  ): { receipt: ReceiptSummary } | null;
  printReceipt(
    receiptId: string,
    payload: PrintReceiptRequest,
    actor: ActionActor,
    dispatchMeta?: { provider?: string; message?: string }
  ): { receipt: ReceiptSummary } | null;
  issueTaxInvoice(
    receiptId: string,
    payload: IssueTaxInvoiceRequest,
    actor: ActionActor
  ): { receipt: ReceiptSummary } | null;
  submitEtax(
    receiptId: string,
    payload: SubmitEtaxRequest,
    actor: ActionActor,
    submissionMeta?: { provider?: string; reference?: string; message?: string; failed?: boolean }
  ): { receipt: ReceiptSummary } | null;
  recordReceiptDispatchAttempt(
    attempt: ReceiptDispatchAttempt,
    actor: ActionActor
  ): ReceiptDispatchAttempt;
}

export interface AppPersistenceAdapter {
  persistAuthEvent(actor: ActionActor, action: string, entityId: string): Promise<void>;
  persistTableStatus(tableId: string, status: DiningTable["status"], actor: ActionActor): Promise<void>;
  persistQrTableLock(
    tableId: string,
    actor: ActionActor
  ): Promise<void>;
  persistTableCheckBillRequested(
    tableId: string,
    requestedBy: string,
    actor: ActionActor
  ): Promise<void>;
  persistTableLayout(
    tableId: string,
    layout: TableLayoutPosition,
    actor: ActionActor
  ): Promise<void>;
  persistTableReservation(
    table: DiningTable,
    actor: ActionActor
  ): Promise<void>;
  clearTableReservation(
    tableId: string,
    actor: ActionActor
  ): Promise<void>;
  persistOrderCreated(
    order: OrderTicket,
    payload: CreateOrderRequest,
    actor: ActionActor
  ): Promise<void>;
  persistKitchenTicketUpdate(
    ticket: KitchenQueueCard,
    action: string,
    actor: ActionActor
  ): Promise<void>;
  persistPaymentSettled(
    order: OrderTicket,
    receipt: ReceiptSummary,
    payload: SettlePaymentRequest,
    actor: ActionActor
  ): Promise<void>;
  persistPaymentSession(
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
  ): Promise<void>;
  persistOrderVoided(
    order: OrderTicket,
    payload: VoidOrderRequest,
    actor: ActionActor
  ): Promise<void>;
  persistReceiptRefunded(
    order: OrderTicket,
    receipt: ReceiptSummary,
    payload: RefundReceiptRequest,
    actor: ActionActor
  ): Promise<void>;
  persistReceiptShared(
    receipt: ReceiptSummary,
    payload: ShareReceiptRequest,
    actor: ActionActor
  ): Promise<void>;
  persistReceiptPrinted(
    receipt: ReceiptSummary,
    payload: PrintReceiptRequest,
    actor: ActionActor
  ): Promise<void>;
  persistReceiptTaxInvoiceIssued(
    receipt: ReceiptSummary,
    payload: IssueTaxInvoiceRequest,
    actor: ActionActor
  ): Promise<void>;
  persistReceiptEtaxSubmitted(
    receipt: ReceiptSummary,
    payload: SubmitEtaxRequest,
    actor: ActionActor
  ): Promise<void>;
  persistReceiptDispatchAttempt(
    attempt: ReceiptDispatchAttempt,
    actor: ActionActor
  ): Promise<void>;
  persistMemberCreated(
    member: CustomerMember,
    actor: ActionActor
  ): Promise<void>;
  persistOrderMemberAssigned(
    orderId: string,
    memberId: string,
    actor: ActionActor
  ): Promise<void>;
  persistInventoryMovement(
    item: StockItem,
    movement: StockMovement,
    actor: ActionActor
  ): Promise<void>;
  persistScheduledShift(
    shift: ScheduledShift,
    actor: ActionActor
  ): Promise<void>;
  persistLeaveRequest(
    request: LeaveRequest,
    actor: ActionActor
  ): Promise<void>;
  persistLeaveReview(
    request: LeaveRequest,
    actor: ActionActor
  ): Promise<void>;
  persistSwapRequest(
    request: SwapShiftRequest,
    actor: ActionActor
  ): Promise<void>;
  persistSwapReview(
    request: SwapShiftRequest,
    actor: ActionActor
  ): Promise<void>;
  persistSecurityPolicy(
    policy: SecurityPolicy,
    actor: ActionActor
  ): Promise<void>;
  persistShiftSession(
    shift: ShiftSession,
    actor: ActionActor
  ): Promise<void>;
  persistStaffNotification(
    notification: StaffNotification,
    actor?: ActionActor | null
  ): Promise<void>;
  persistChatMessage(
    message: KitchenChatMessage,
    actor: ActionActor
  ): Promise<void>;
  persistExceptionRecord(
    record: ExceptionRecord,
    actor: ActionActor
  ): Promise<void>;
  persistDeliveryPlatformConnection(
    platform: DeliveryPlatformConnection,
    actor: ActionActor,
    audit?: {
      action: "delivery.platform_toggle" | "delivery.menu_sync";
      metadata: Record<string, string | number | boolean>;
    }
  ): Promise<void>;
  persistUserAccountCreated(
    user: UserAccount,
    actor: ActionActor
  ): Promise<void>;
  persistUserAccountUpdated(
    user: UserAccount,
    actor: ActionActor
  ): Promise<void>;
  persistUserAccountForcedLogout(
    user: UserAccount,
    actor: ActionActor
  ): Promise<void>;
  persistMenuItemCreated(
    menuItem: import("@mypos/domain").MenuItemSummary,
    actor: ActionActor
  ): Promise<void>;
  persistMenuItemUpdated(
    menuItem: import("@mypos/domain").MenuItemSummary,
    actor: ActionActor
  ): Promise<void>;
}
