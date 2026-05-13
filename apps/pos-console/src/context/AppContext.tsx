import { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import {
  type AppPermission,
  type AssignMemberRequest,
  type AuditEntry,
  type AuthSession,
  type BackofficeReport,
  type BackofficeReportResponse,
  type CreateMenuItemRequest,
  type CreateMemberRequest,
  type CreatePaymentSessionRequest,
  type CreateReservationRequest,
  type CreateScheduledShiftRequest,
  type CreateUserAccountRequest,
  type CrmOverview,
  type CrmOverviewResponse,
  type CustomerMember,
  dashboardMetrics,
  type DeliveryCenterResponse,
  type DeliveryCenterSnapshot,
  type DiningTable,
  diningTables,
  type ExceptionFeedResponse,
  type ExceptionRecord,
  type HrOverview,
  type HrOverviewResponse,
  type InventoryOverview,
  type InventoryOverviewResponse,
  type IssueTaxInvoiceRequest,
  type LoginResponse,
  type ManagedUserAccount,
  type ManagedUserFeedResponse,
  type MemberFeedResponse,
  menuItems,
  type MenuItemSummary,
  type OrderTicket,
  orderTickets,
  type PaymentMethod,
  type PaymentSessionFeedResponse,
  type PaymentSessionSummary,
  type PlatformOverview,
  type PrintReceiptRequest,
  type ReceiptDispatchAttempt,
  type ReceiptFeedResponse,
  type ReceiptSummary,
  type ReceiptTemplateSettings,
  type RecordStockMovementRequest,
  type RefundReceiptRequest,
  type SecurityPolicy,
  type SecurityPolicyResponse,
  type SettlePaymentRequest,
  shiftSessions,
  type ShareReceiptRequest,
  type SplitPaymentRequest,
  type SubmitEtaxRequest,
  type TwoFactorChallenge,
  type UpdateMenuItemRequest,
  type UpdateSecurityPolicyRequest,
  type UpdateUserAccountRequest,
  type VerifyTwoFactorRequest,
  type VoidOrderRequest,
  type LiveEvent
} from "@mypos/domain";
import { apiBaseUrl, toWsUrl } from "../api";

// ── Shared constants ─────────────────────────────────────────────────────────

export const modules = [
  "Service Floor",
  "Payments",
  "Menu Hub",
  "Delivery Center",
  "Backoffice",
  "HR",
  "Security"
];

export const statusTone: Record<string, string> = {
  AVAILABLE: "green",
  SEATED: "amber",
  PENDING_PAYMENT: "red",
  LOCKED_BY_QR: "blue",
  RESERVED: "violet",
  CLEANING: "slate"
};

export const formatCurrency = (amount: number) => `THB ${amount.toLocaleString("en-US")}`;

export const paymentMethodOptions: Array<{ value: PaymentMethod; label: string }> = [
  { value: "CASH", label: "Cash" },
  { value: "PROMPTPAY", label: "PromptPay" },
  { value: "CARD", label: "Card" },
  { value: "RABBIT_LINE_PAY", label: "Rabbit LINE Pay" },
  { value: "TRUE_MONEY", label: "TrueMoney" }
];

// ── Local form types ──────────────────────────────────────────────────────────

export type ReservationFormState = {
  guestName: string;
  reservedAt: string;
  partySize: number;
  contactPhone: string;
  note: string;
};

export type MemberFormState = {
  fullName: string;
  phone: string;
  preferredLanguage: string;
  birthDate: string;
  lineUserId: string;
};

export type MenuFormState = {
  category: string;
  name: string;
  price: string;
  happyHourPrice: string;
  description: string;
  imageUrl: string;
};

export type SecurityFormState = {
  username: string;
  displayName: string;
  role: string;
  pin: string;
  expiresAt: string;
};

export type ScheduleFormState = {
  userId: string;
  role: CreateScheduledShiftRequest["role"];
  shiftDate: string;
  startTime: string;
  endTime: string;
  zone: string;
  note: string;
};

export type SplitPaymentPreview = {
  guestLabel: string;
  method: PaymentMethod;
  amount: number;
  tipAmount: number;
};

// ── Context type ──────────────────────────────────────────────────────────────

export type AppContextValue = {
  connectionState: string;
  lastHeartbeat: string | null;
  session: AuthSession | null;
  permissions: AppPermission[];
  mfaChallenge: TwoFactorChallenge | null;
  mfaCode: string;
  setMfaCode: React.Dispatch<React.SetStateAction<string>>;
  operationState: string;
  busyAction: string | null;
  authHeaders: { Authorization: string; "Content-Type": string } | null;
  overview: PlatformOverview;
  receipts: ReceiptSummary[];
  paymentSessions: PaymentSessionSummary[];
  auditEntries: AuditEntry[];
  exceptions: ExceptionRecord[];
  report: BackofficeReport | null;
  crmOverview: CrmOverview | null;
  members: CustomerMember[];
  managedUsers: ManagedUserAccount[];
  securityPolicy: SecurityPolicy | null;
  deliveryCenter: DeliveryCenterSnapshot | null;
  inventoryOverview: InventoryOverview | null;
  hrOverview: HrOverview | null;
  selectedTableId: string;
  setSelectedTableId: React.Dispatch<React.SetStateAction<string>>;
  selectedOrderId: string;
  setSelectedOrderId: React.Dispatch<React.SetStateAction<string>>;
  selectedMenuId: string;
  setSelectedMenuId: React.Dispatch<React.SetStateAction<string>>;
  splitCount: string;
  setSplitCount: React.Dispatch<React.SetStateAction<string>>;
  paymentTip: string;
  setPaymentTip: React.Dispatch<React.SetStateAction<string>>;
  paymentMethod: PaymentMethod;
  setPaymentMethod: React.Dispatch<React.SetStateAction<PaymentMethod>>;
  splitGuestMethods: PaymentMethod[];
  setSplitGuestMethods: React.Dispatch<React.SetStateAction<PaymentMethod[]>>;
  splitGuestCount: number;
  splitPaymentsPreview: SplitPaymentPreview[];
  selectedTable: DiningTable | null;
  selectedOrder: OrderTicket | null;
  selectedMenuItem: MenuItemSummary | null;
  reservationForm: ReservationFormState;
  setReservationForm: React.Dispatch<React.SetStateAction<ReservationFormState>>;
  voidReason: string;
  setVoidReason: React.Dispatch<React.SetStateAction<string>>;
  refundReason: string;
  setRefundReason: React.Dispatch<React.SetStateAction<string>>;
  receiptEmail: string;
  setReceiptEmail: React.Dispatch<React.SetStateAction<string>>;
  receiptLineUserId: string;
  setReceiptLineUserId: React.Dispatch<React.SetStateAction<string>>;
  receiptPrinterName: string;
  setReceiptPrinterName: React.Dispatch<React.SetStateAction<string>>;
  taxInvoiceForm: IssueTaxInvoiceRequest;
  setTaxInvoiceForm: React.Dispatch<React.SetStateAction<IssueTaxInvoiceRequest>>;
  etaxSubmitChannel: SubmitEtaxRequest["channel"];
  setEtaxSubmitChannel: React.Dispatch<React.SetStateAction<SubmitEtaxRequest["channel"]>>;
  memberForm: MemberFormState;
  setMemberForm: React.Dispatch<React.SetStateAction<MemberFormState>>;
  inventoryNote: string;
  setInventoryNote: React.Dispatch<React.SetStateAction<string>>;
  menuForm: MenuFormState;
  setMenuForm: React.Dispatch<React.SetStateAction<MenuFormState>>;
  securityForm: SecurityFormState;
  setSecurityForm: React.Dispatch<React.SetStateAction<SecurityFormState>>;
  adminIpInput: string;
  setAdminIpInput: React.Dispatch<React.SetStateAction<string>>;
  receiptTemplateForm: ReceiptTemplateSettings;
  setReceiptTemplateForm: React.Dispatch<React.SetStateAction<ReceiptTemplateSettings>>;
  scheduleForm: ScheduleFormState;
  setScheduleForm: React.Dispatch<React.SetStateAction<ScheduleFormState>>;
  receiptFeedVersion: number;
  setReceiptFeedVersion: React.Dispatch<React.SetStateAction<number>>;
  loginAs: (username: string, pin: string) => Promise<void>;
  verifyTwoFactor: () => Promise<void>;
  logout: () => Promise<void>;
  resetDemo: () => Promise<void>;
  createSampleOrder: () => Promise<void>;
  settleOrder: (orderId: string, amount: number) => Promise<void>;
  createPaymentSession: (orderId: string, amount: number) => Promise<void>;
  capturePaymentSession: (paymentSessionId: string) => Promise<void>;
  retryPaymentSession: (paymentSessionId: string) => Promise<void>;
  splitSettleOrder: (orderId: string, amount: number, splitPeople: number) => Promise<void>;
  voidOrder: (orderId: string) => Promise<void>;
  refundReceipt: (receipt: ReceiptSummary) => Promise<void>;
  shareReceipt: (receipt: ReceiptSummary, channel: ShareReceiptRequest["channel"]) => Promise<void>;
  printReceipt: (receipt: ReceiptSummary) => Promise<void>;
  issueTaxInvoice: (receipt: ReceiptSummary) => Promise<void>;
  submitEtax: (receipt: ReceiptSummary) => Promise<void>;
  retryDispatchAttempt: (attempt: ReceiptDispatchAttempt) => Promise<void>;
  createMember: () => Promise<void>;
  createMenuItem: () => Promise<void>;
  updateMenuItem: (menuItemId: string, payload: UpdateMenuItemRequest) => Promise<void>;
  createSecurityUser: () => Promise<void>;
  updateSecurityUser: (userId: string, payload: UpdateUserAccountRequest) => Promise<void>;
  forceLogoutUser: (userId: string) => Promise<void>;
  saveSecurityPolicy: (payload: UpdateSecurityPolicyRequest) => Promise<void>;
  createScheduledShift: () => Promise<void>;
  reviewLeaveRequest: (requestId: string, status: "APPROVED" | "REJECTED") => Promise<void>;
  reviewSwapRequest: (requestId: string, status: "APPROVED" | "REJECTED") => Promise<void>;
  updateTableLayout: (table: DiningTable, x: number, y: number) => Promise<void>;
  reserveSelectedTable: () => Promise<void>;
  clearSelectedReservation: () => Promise<void>;
  assignMemberToOrder: (memberId: string) => Promise<void>;
  toggleDeliveryPlatform: (platform: string, enabled: boolean) => Promise<void>;
  syncDeliveryMenu: (platform: string) => Promise<void>;
  recordInventoryMovement: (
    itemId: string,
    type: RecordStockMovementRequest["type"],
    quantity: number
  ) => Promise<void>;
  downloadCsv: (path: string, filename: string, actionLabel: string) => Promise<void>;
};

const AppContext = createContext<AppContextValue | null>(null);

export function useApp(): AppContextValue {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used inside AppProvider");
  return ctx;
}

// ── Provider ──────────────────────────────────────────────────────────────────

export function AppProvider({ children }: { children: ReactNode }) {
  const fallbackOverview = useMemo<PlatformOverview>(
    () => ({
      metrics: dashboardMetrics,
      tables: diningTables,
      orders: orderTickets,
      menu: menuItems,
      shifts: shiftSessions,
      kitchen: []
    }),
    []
  );

  const [overview, setOverview] = useState<PlatformOverview>(fallbackOverview);
  const [connectionState, setConnectionState] = useState("Fallback demo data");
  const [lastHeartbeat, setLastHeartbeat] = useState<string | null>(null);
  const [session, setSession] = useState<AuthSession | null>(null);
  const [permissions, setPermissions] = useState<AppPermission[]>([]);
  const [mfaChallenge, setMfaChallenge] = useState<TwoFactorChallenge | null>(null);
  const [mfaCode, setMfaCode] = useState("");
  const [operationState, setOperationState] = useState("Login required for write actions");
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [receipts, setReceipts] = useState<ReceiptSummary[]>([]);
  const [paymentSessions, setPaymentSessions] = useState<PaymentSessionSummary[]>([]);
  const [auditEntries, setAuditEntries] = useState<AuditEntry[]>([]);
  const [exceptions, setExceptions] = useState<ExceptionRecord[]>([]);
  const [report, setReport] = useState<BackofficeReport | null>(null);
  const [crmOverview, setCrmOverview] = useState<CrmOverview | null>(null);
  const [members, setMembers] = useState<CustomerMember[]>([]);
  const [managedUsers, setManagedUsers] = useState<ManagedUserAccount[]>([]);
  const [securityPolicy, setSecurityPolicy] = useState<SecurityPolicy | null>(null);
  const [deliveryCenter, setDeliveryCenter] = useState<DeliveryCenterSnapshot | null>(null);
  const [inventoryOverview, setInventoryOverview] = useState<InventoryOverview | null>(null);
  const [hrOverview, setHrOverview] = useState<HrOverview | null>(null);
  const [selectedTableId, setSelectedTableId] = useState<string>("T1");
  const [selectedOrderId, setSelectedOrderId] = useState<string>("");
  const [selectedMenuId, setSelectedMenuId] = useState<string>("M1");
  const [splitCount, setSplitCount] = useState("2");
  const [paymentTip, setPaymentTip] = useState("0");
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>("CASH");
  const [splitGuestMethods, setSplitGuestMethods] = useState<PaymentMethod[]>(["CASH", "CASH"]);
  const [reservationForm, setReservationForm] = useState<ReservationFormState>({
    guestName: "",
    reservedAt: "2026-03-25T19:30",
    partySize: 2,
    contactPhone: "",
    note: ""
  });
  const [voidReason, setVoidReason] = useState("Customer changed mind");
  const [refundReason, setRefundReason] = useState("Payment issue");
  const [receiptEmail, setReceiptEmail] = useState("guest@example.com");
  const [receiptLineUserId, setReceiptLineUserId] = useState("line-demo-user");
  const [receiptPrinterName, setReceiptPrinterName] = useState("Epson TM-T82X");
  const [taxInvoiceForm, setTaxInvoiceForm] = useState<IssueTaxInvoiceRequest>({
    receiptType: "TAX_INVOICE",
    taxPayerName: "MyPOS Demo Co., Ltd.",
    taxId: "0105559999999",
    taxBranchAddress: "99 Silom Road, Bangkok",
    taxEmail: "tax@example.com"
  });
  const [etaxSubmitChannel, setEtaxSubmitChannel] = useState<SubmitEtaxRequest["channel"]>("EMAIL");
  const [memberForm, setMemberForm] = useState<MemberFormState>({
    fullName: "",
    phone: "",
    preferredLanguage: "th",
    birthDate: "",
    lineUserId: ""
  });
  const [inventoryNote, setInventoryNote] = useState("Late-night replenishment");
  const [menuForm, setMenuForm] = useState<MenuFormState>({
    category: "Seasonal",
    name: "",
    price: "0",
    happyHourPrice: "",
    description: "",
    imageUrl: ""
  });
  const [securityForm, setSecurityForm] = useState<SecurityFormState>({
    username: "",
    displayName: "",
    role: "STAFF",
    pin: "2468",
    expiresAt: ""
  });
  const [adminIpInput, setAdminIpInput] = useState("127.0.0.1");
  const [receiptTemplateForm, setReceiptTemplateForm] = useState<ReceiptTemplateSettings>({
    businessName: "MyPOS Night Kitchen",
    branchLabel: "Bangkok Riverside Branch",
    footerMessage: "Thank you and see you again.",
    contactLine: "LINE OA: @myposnight · 02-123-4567",
    showQrLookupOnPrint: true,
    showTipLine: true
  });
  const [receiptFeedVersion, setReceiptFeedVersion] = useState(0);
  const [scheduleForm, setScheduleForm] = useState<ScheduleFormState>({
    userId: "USR-STAFF-01",
    role: "Server",
    shiftDate: "2026-03-29",
    startTime: "17:00",
    endTime: "01:00",
    zone: "Main Hall",
    note: ""
  });

  const authHeaders = useMemo(
    () =>
      session
        ? {
            Authorization: `Bearer ${session.accessToken}`,
            "Content-Type": "application/json"
          }
        : null,
    [session]
  );

  const selectedTable = useMemo(
    () => overview.tables.find((t) => t.id === selectedTableId) ?? overview.tables[0] ?? null,
    [overview.tables, selectedTableId]
  );
  const selectedOrder = useMemo(
    () =>
      overview.orders.find((o) => o.id === selectedOrderId) ??
      overview.orders.find((o) => o.status !== "PAID" && o.status !== "VOIDED") ??
      null,
    [overview.orders, selectedOrderId]
  );
  const selectedMenuItem = useMemo(
    () => overview.menu.find((item) => item.id === selectedMenuId) ?? overview.menu[0] ?? null,
    [overview.menu, selectedMenuId]
  );
  const splitGuestCount = Math.min(Math.max(Number(splitCount) || 2, 2), 8);
  const splitPaymentsPreview = useMemo<SplitPaymentPreview[]>(() => {
    if (!selectedOrder) return [];
    const totalTip = Number(paymentTip || "0");
    const baseShare = Math.floor((selectedOrder.totalAmount / splitGuestCount) * 100) / 100;
    const baseTipShare = Math.floor((totalTip / splitGuestCount) * 100) / 100;
    return Array.from({ length: splitGuestCount }, (_, i) => {
      const amount =
        i === splitGuestCount - 1
          ? Number((selectedOrder.totalAmount - baseShare * (splitGuestCount - 1)).toFixed(2))
          : Number(baseShare.toFixed(2));
      const tipAmount =
        i === splitGuestCount - 1
          ? Number((totalTip - baseTipShare * (splitGuestCount - 1)).toFixed(2))
          : Number(baseTipShare.toFixed(2));
      return { guestLabel: `Guest ${i + 1}`, method: splitGuestMethods[i] ?? paymentMethod, amount, tipAmount };
    });
  }, [paymentMethod, paymentTip, selectedOrder, splitGuestCount, splitGuestMethods]);

  useEffect(() => {
    setSplitGuestMethods((current) =>
      Array.from({ length: splitGuestCount }, (_, i) => current[i] ?? paymentMethod)
    );
  }, [paymentMethod, splitGuestCount]);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const res = await fetch(`${apiBaseUrl}/api/overview`);
        const data = (await res.json()) as PlatformOverview;
        if (mounted) {
          setOverview(data);
          setConnectionState("Connected to API");
        }
      } catch {
        if (mounted) setConnectionState("API offline, using fallback data");
      }
    };
    load().catch(() => undefined);
    return () => { mounted = false; };
  }, [fallbackOverview]);

  useEffect(() => {
    const socket = new WebSocket(toWsUrl(apiBaseUrl));
    socket.onopen = () => setConnectionState("Live websocket connected");
    socket.onmessage = (msg) => {
      const event = JSON.parse(msg.data) as LiveEvent;
      if (event.type === "snapshot") setOverview(event.payload);
      if (event.type === "heartbeat") setLastHeartbeat(event.payload.now);
    };
    socket.onclose = () => setConnectionState("Websocket disconnected");
    socket.onerror = () => setConnectionState("Websocket unavailable");
    return () => { socket.close(); };
  }, []);

  useEffect(() => {
    if (!authHeaders) return;
    const load = async () => {
      try {
        const [
          receiptsRes, sessionsRes, auditRes, exceptionsRes,
          membersRes, usersRes, policyRes, crmRes,
          reportRes, deliveryRes, inventoryRes, hrRes
        ] = await Promise.all([
          fetch(`${apiBaseUrl}/api/receipts`, { headers: authHeaders }),
          fetch(`${apiBaseUrl}/api/payment-sessions`, { headers: authHeaders }),
          fetch(`${apiBaseUrl}/api/audit`, { headers: authHeaders }),
          fetch(`${apiBaseUrl}/api/exceptions`, { headers: authHeaders }),
          fetch(`${apiBaseUrl}/api/members`, { headers: authHeaders }),
          fetch(`${apiBaseUrl}/api/security/users`, { headers: authHeaders }),
          fetch(`${apiBaseUrl}/api/security/policy`, { headers: authHeaders }),
          fetch(`${apiBaseUrl}/api/crm/overview`, { headers: authHeaders }),
          fetch(`${apiBaseUrl}/api/reports/backoffice`, { headers: authHeaders }),
          fetch(`${apiBaseUrl}/api/delivery/overview`, { headers: authHeaders }),
          fetch(`${apiBaseUrl}/api/inventory/overview`, { headers: authHeaders }),
          fetch(`${apiBaseUrl}/api/hr/overview`, { headers: authHeaders })
        ]);
        setReceipts(receiptsRes.ok ? ((await receiptsRes.json()) as ReceiptFeedResponse).receipts : []);
        setPaymentSessions(sessionsRes.ok ? ((await sessionsRes.json()) as PaymentSessionFeedResponse).sessions : []);
        setAuditEntries(auditRes.ok ? ((await auditRes.json()) as { entries: AuditEntry[] }).entries : []);
        setExceptions(exceptionsRes.ok ? ((await exceptionsRes.json()) as ExceptionFeedResponse).exceptions : []);
        setMembers(membersRes.ok ? ((await membersRes.json()) as MemberFeedResponse).members : []);
        setManagedUsers(usersRes.ok ? ((await usersRes.json()) as ManagedUserFeedResponse).users : []);
        setSecurityPolicy(policyRes.ok ? ((await policyRes.json()) as SecurityPolicyResponse).policy : null);
        setCrmOverview(crmRes.ok ? ((await crmRes.json()) as CrmOverviewResponse).overview : null);
        setReport(reportRes.ok ? ((await reportRes.json()) as BackofficeReportResponse).report : null);
        setDeliveryCenter(deliveryRes.ok ? ((await deliveryRes.json()) as DeliveryCenterResponse).center : null);
        setInventoryOverview(inventoryRes.ok ? ((await inventoryRes.json()) as InventoryOverviewResponse).overview : null);
        setHrOverview(hrRes.ok ? ((await hrRes.json()) as HrOverviewResponse).overview : null);
      } catch {
        setOperationState("Protected feeds unavailable");
      }
    };
    load().catch(() => undefined);
  }, [authHeaders, operationState, receiptFeedVersion]);

  useEffect(() => {
    if (!selectedTable) return;
    if (selectedTable.reservation) {
      setReservationForm({
        guestName: selectedTable.reservation.guestName,
        reservedAt: selectedTable.reservation.reservedAt.slice(0, 16),
        partySize: selectedTable.reservation.partySize,
        contactPhone: selectedTable.reservation.contactPhone ?? "",
        note: selectedTable.reservation.note ?? ""
      });
      return;
    }
    setReservationForm((cur) => ({ ...cur, guestName: "", partySize: selectedTable.seats, contactPhone: "", note: "" }));
  }, [selectedTable]);

  useEffect(() => {
    if (securityPolicy) {
      setAdminIpInput(securityPolicy.adminIpWhitelist.join(", "));
      setReceiptTemplateForm({
        ...securityPolicy.receiptTemplate,
        contactLine: securityPolicy.receiptTemplate.contactLine ?? ""
      });
    }
  }, [securityPolicy]);

  // ── Handlers ────────────────────────────────────────────────────────────────

  const downloadCsv = async (path: string, filename: string, actionLabel: string) => {
    if (!session) { setOperationState("Login required for export actions"); return; }
    setBusyAction(actionLabel);
    try {
      const res = await fetch(`${apiBaseUrl}${path}`, { headers: { Authorization: `Bearer ${session.accessToken}` } });
      if (!res.ok) throw new Error(`Export failed (${res.status})`);
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = filename;
      document.body.appendChild(a); a.click(); a.remove();
      window.URL.revokeObjectURL(url);
      setOperationState(`Downloaded ${filename}`);
    } catch (err) {
      setOperationState(err instanceof Error ? err.message : "Export failed");
    } finally { setBusyAction(null); }
  };

  const loginAs = async (username: string, pin: string) => {
    try {
      setBusyAction(`login:${username}`);
      const res = await fetch(`${apiBaseUrl}/api/auth/login`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, pin, deviceId: "POS-CONSOLE-DEMO" })
      });
      if (!res.ok) throw new Error("Login failed");
      const data = (await res.json()) as LoginResponse;
      if (data.challenge) {
        setMfaChallenge(data.challenge);
        setMfaCode(data.challenge.demoCode);
        setOperationState(`2FA required for ${username}. Use demo code ${data.challenge.demoCode}`);
        return;
      }
      if (!data.session || !data.permissions) throw new Error("Login failed");
      setMfaChallenge(null);
      setSession(data.session);
      setPermissions(data.permissions);
      setOperationState(`Signed in as ${data.session.user.displayName}`);
    } catch { setOperationState("Login failed"); }
    finally { setBusyAction(null); }
  };

  const verifyTwoFactor = async () => {
    if (!mfaChallenge) { setOperationState("No 2FA challenge pending"); return; }
    try {
      setBusyAction("verify-2fa");
      const payload: VerifyTwoFactorRequest = { challengeId: mfaChallenge.challengeId, code: mfaCode };
      const res = await fetch(`${apiBaseUrl}/api/auth/verify-2fa`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error("2FA verification failed");
      const data = (await res.json()) as LoginResponse;
      if (!data.session || !data.permissions) throw new Error("2FA verification failed");
      setSession(data.session); setPermissions(data.permissions); setMfaChallenge(null);
      setOperationState(`Signed in as ${data.session.user.displayName} with 2FA`);
    } catch { setOperationState("2FA verification failed"); }
    finally { setBusyAction(null); }
  };

  const logout = async () => {
    if (!session) return;
    try {
      setBusyAction("logout");
      await fetch(`${apiBaseUrl}/api/auth/logout`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refreshToken: session.refreshToken })
      });
    } finally {
      setSession(null); setPermissions([]); setMfaChallenge(null); setMfaCode("");
      setManagedUsers([]); setSecurityPolicy(null); setReceipts([]); setPaymentSessions([]);
      setAuditEntries([]); setExceptions([]); setMembers([]); setCrmOverview(null);
      setHrOverview(null); setReport(null); setDeliveryCenter(null); setInventoryOverview(null);
      setBusyAction(null); setOperationState("Logged out");
    }
  };

  const resetDemo = async () => {
    if (!authHeaders) { setOperationState("Please login first"); return; }
    try {
      setBusyAction("reset-demo");
      const res = await fetch(`${apiBaseUrl}/api/system/reset-demo`, { method: "POST", headers: authHeaders });
      if (!res.ok) throw new Error("Demo reset failed");
      setReceiptFeedVersion((v) => v + 1);
      setOperationState("Demo state reset");
    } catch { setOperationState("Demo reset failed"); }
    finally { setBusyAction(null); }
  };

  const createSampleOrder = async () => {
    if (!authHeaders) { setOperationState("Please login first"); return; }
    const targetTable = overview.tables.find((t) => t.status === "AVAILABLE") ?? overview.tables[0];
    const primaryFood = overview.menu.find((item) => item.inStock);
    const drink = overview.menu.find((item) => item.tags.includes("bar")) ?? overview.menu[1];
    if (!targetTable || !primaryFood || !drink) { setOperationState("Not enough data to create order"); return; }
    try {
      setBusyAction("create-order");
      const res = await fetch(`${apiBaseUrl}/api/orders`, {
        method: "POST", headers: authHeaders,
        body: JSON.stringify({
          tableId: targetTable.id, guestCount: Math.max(targetTable.seats - 1, 2),
          waiterName: session?.user.displayName ?? "Cashier", priority: "NORMAL", source: "POS",
          specialNote: "Demo order from POS console",
          items: [
            { menuItemId: primaryFood.id, quantity: 1, note: "Less spicy" },
            { menuItemId: drink.id, quantity: 2, note: "No garnish" }
          ]
        })
      });
      if (!res.ok) throw new Error("Create order failed");
      setOperationState(`Created new order for table ${targetTable.label}`);
    } catch { setOperationState("Create order failed"); }
    finally { setBusyAction(null); }
  };

  const settleOrder = async (orderId: string, amount: number) => {
    if (!authHeaders) { setOperationState("Please login first"); return; }
    try {
      setBusyAction(`pay:${orderId}`);
      const payload: SettlePaymentRequest = { method: paymentMethod, amount, tipAmount: Number(paymentTip || "0") };
      const res = await fetch(`${apiBaseUrl}/api/orders/${orderId}/pay`, { method: "POST", headers: authHeaders, body: JSON.stringify(payload) });
      if (!res.ok) throw new Error("Payment failed");
      setOperationState(`Settled ${paymentMethod} payment for ${orderId}${Number(paymentTip || "0") > 0 ? ` with tip ${formatCurrency(Number(paymentTip || "0"))}` : ""}`);
    } catch { setOperationState("Payment failed"); }
    finally { setBusyAction(null); }
  };

  const createPaymentSession = async (orderId: string, amount: number) => {
    if (!authHeaders) { setOperationState("Please login first"); return; }
    if (paymentMethod === "CASH") { setOperationState("Gateway session is for non-cash methods only"); return; }
    try {
      setBusyAction(`payment-session:${orderId}`);
      const payload: CreatePaymentSessionRequest = { method: paymentMethod, amount, tipAmount: Number(paymentTip || "0") };
      const res = await fetch(`${apiBaseUrl}/api/orders/${orderId}/payment-session`, { method: "POST", headers: authHeaders, body: JSON.stringify(payload) });
      if (!res.ok) throw new Error("Create payment session failed");
      setReceiptFeedVersion((v) => v + 1);
      setOperationState(`Created ${paymentMethod} session for ${orderId}`);
    } catch { setOperationState("Create payment session failed"); }
    finally { setBusyAction(null); }
  };

  const capturePaymentSession = async (paymentSessionId: string) => {
    if (!authHeaders) { setOperationState("Please login first"); return; }
    try {
      setBusyAction(`capture-session:${paymentSessionId}`);
      const res = await fetch(`${apiBaseUrl}/api/payment-sessions/${paymentSessionId}/capture`, { method: "POST", headers: authHeaders });
      if (!res.ok) throw new Error("Capture payment session failed");
      setReceiptFeedVersion((v) => v + 1);
      setOperationState(`Captured payment session ${paymentSessionId}`);
    } catch {
      setReceiptFeedVersion((v) => v + 1);
      setOperationState("Capture payment session failed");
    } finally { setBusyAction(null); }
  };

  const retryPaymentSession = async (paymentSessionId: string) => {
    if (!authHeaders) { setOperationState("Please login first"); return; }
    try {
      setBusyAction(`retry-session:${paymentSessionId}`);
      const res = await fetch(`${apiBaseUrl}/api/payment-sessions/${paymentSessionId}/retry`, { method: "POST", headers: authHeaders });
      if (!res.ok) throw new Error("Retry payment session failed");
      setReceiptFeedVersion((v) => v + 1);
      setOperationState(`Retried payment session ${paymentSessionId}`);
    } catch {
      setReceiptFeedVersion((v) => v + 1);
      setOperationState("Retry payment session failed");
    } finally { setBusyAction(null); }
  };

  const splitSettleOrder = async (orderId: string, amount: number, splitPeople: number) => {
    if (!authHeaders) { setOperationState("Please login first"); return; }
    if (splitPeople < 2) { setOperationState("Split bill requires at least 2 guests"); return; }
    const payments = splitPaymentsPreview.map((p) => ({ method: p.method, amount: p.amount, tipAmount: p.tipAmount, guestLabel: p.guestLabel }));
    const splitBaseTotal = Number(payments.reduce((s, p) => s + p.amount, 0).toFixed(2));
    if (splitBaseTotal !== Number(amount.toFixed(2))) { setOperationState("Split bill preview is out of sync with the order total"); return; }
    try {
      setBusyAction(`split-pay:${orderId}`);
      const payload: SplitPaymentRequest = { payments };
      const res = await fetch(`${apiBaseUrl}/api/orders/${orderId}/split-pay`, { method: "POST", headers: authHeaders, body: JSON.stringify(payload) });
      if (!res.ok) throw new Error("Split payment failed");
      setOperationState(`Split payment settled for ${orderId} across ${splitPeople} guests${Number(paymentTip || "0") > 0 ? ` with total tip ${formatCurrency(Number(paymentTip || "0"))}` : ""}`);
    } catch { setOperationState("Split payment failed"); }
    finally { setBusyAction(null); }
  };

  const voidOrder = async (orderId: string) => {
    if (!authHeaders) { setOperationState("Please login first"); return; }
    try {
      setBusyAction(`void:${orderId}`);
      const payload: VoidOrderRequest = { reason: voidReason };
      const res = await fetch(`${apiBaseUrl}/api/orders/${orderId}/void`, { method: "POST", headers: authHeaders, body: JSON.stringify(payload) });
      if (!res.ok) throw new Error("Void failed");
      setOperationState(`Voided ${orderId}`);
    } catch { setOperationState("Void order failed"); }
    finally { setBusyAction(null); }
  };

  const refundReceipt = async (receipt: ReceiptSummary) => {
    if (!authHeaders) { setOperationState("Please login first"); return; }
    try {
      setBusyAction(`refund:${receipt.id}`);
      const payload: RefundReceiptRequest = { reason: refundReason, amount: receipt.totalAmount };
      const res = await fetch(`${apiBaseUrl}/api/receipts/${receipt.id}/refund`, { method: "POST", headers: authHeaders, body: JSON.stringify(payload) });
      if (!res.ok) throw new Error("Refund failed");
      setOperationState(`Refunded ${receipt.receiptNo}`);
    } catch { setOperationState("Refund failed"); }
    finally { setBusyAction(null); }
  };

  const shareReceipt = async (receipt: ReceiptSummary, channel: ShareReceiptRequest["channel"]) => {
    if (!authHeaders) { setOperationState("Please login first"); return; }
    const recipient = channel === "EMAIL" ? receiptEmail.trim() : receiptLineUserId.trim();
    if (!recipient) { setOperationState(`Enter a ${channel === "EMAIL" ? "recipient email" : "LINE user id"} first`); return; }
    try {
      setBusyAction(`share:${receipt.id}:${channel}`);
      const payload: ShareReceiptRequest = { channel, recipient };
      const res = await fetch(`${apiBaseUrl}/api/receipts/${receipt.id}/share`, { method: "POST", headers: authHeaders, body: JSON.stringify(payload) });
      if (!res.ok) throw new Error("Share receipt failed");
      setReceiptFeedVersion((v) => v + 1);
      setOperationState(`Shared ${receipt.receiptNo} via ${channel === "EMAIL" ? "Email" : "LINE"} to ${recipient}`);
    } catch {
      setReceiptFeedVersion((v) => v + 1);
      setOperationState("Share receipt failed");
    } finally { setBusyAction(null); }
  };

  const printReceipt = async (receipt: ReceiptSummary) => {
    if (!authHeaders) { setOperationState("Please login first"); return; }
    const printerName = receiptPrinterName.trim();
    if (!printerName) { setOperationState("Enter a printer name first"); return; }
    try {
      setBusyAction(`print:${receipt.id}`);
      const payload: PrintReceiptRequest = { printerName, copies: 1 };
      const res = await fetch(`${apiBaseUrl}/api/receipts/${receipt.id}/print`, { method: "POST", headers: authHeaders, body: JSON.stringify(payload) });
      if (!res.ok) throw new Error("Print receipt failed");
      setReceiptFeedVersion((v) => v + 1);
      setOperationState(`Printed ${receipt.receiptNo} to ${printerName}`);
    } catch {
      setReceiptFeedVersion((v) => v + 1);
      setOperationState("Print receipt failed");
    } finally { setBusyAction(null); }
  };

  const issueTaxInvoice = async (receipt: ReceiptSummary) => {
    if (!authHeaders) { setOperationState("Please login first"); return; }
    if (!taxInvoiceForm.taxPayerName.trim() || !taxInvoiceForm.taxId.trim()) { setOperationState("Enter tax payer name and tax id first"); return; }
    try {
      setBusyAction(`tax-invoice:${receipt.id}`);
      const res = await fetch(`${apiBaseUrl}/api/receipts/${receipt.id}/tax-invoice`, {
        method: "POST", headers: authHeaders,
        body: JSON.stringify({
          ...taxInvoiceForm,
          taxPayerName: taxInvoiceForm.taxPayerName.trim(),
          taxId: taxInvoiceForm.taxId.trim(),
          taxBranchAddress: taxInvoiceForm.taxBranchAddress?.trim() || undefined,
          taxEmail: taxInvoiceForm.taxEmail?.trim() || undefined
        })
      });
      if (!res.ok) throw new Error("Tax invoice failed");
      setReceiptFeedVersion((v) => v + 1);
      setOperationState(`Issued ${taxInvoiceForm.receiptType} for ${receipt.receiptNo}`);
    } catch {
      setReceiptFeedVersion((v) => v + 1);
      setOperationState("Tax invoice failed");
    } finally { setBusyAction(null); }
  };

  const submitEtax = async (receipt: ReceiptSummary) => {
    if (!authHeaders) { setOperationState("Please login first"); return; }
    if (receipt.receiptType !== "E_TAX") { setOperationState("Receipt must be marked as E-TAX first"); return; }
    const recipient = (taxInvoiceForm.taxEmail ?? "").trim();
    if (etaxSubmitChannel === "EMAIL" && !recipient) { setOperationState("Enter e-tax email first"); return; }
    try {
      setBusyAction(`etax-submit:${receipt.id}`);
      const res = await fetch(`${apiBaseUrl}/api/receipts/${receipt.id}/e-tax-submit`, {
        method: "POST", headers: authHeaders,
        body: JSON.stringify({ channel: etaxSubmitChannel, recipient: etaxSubmitChannel === "EMAIL" ? recipient : undefined } satisfies SubmitEtaxRequest)
      });
      setReceiptFeedVersion((v) => v + 1);
      if (!res.ok) throw new Error("E-Tax submission failed");
      setOperationState(`Submitted E-Tax for ${receipt.receiptNo}`);
    } catch { setOperationState("E-Tax submission failed"); }
    finally { setBusyAction(null); }
  };

  const retryDispatchAttempt = async (attempt: ReceiptDispatchAttempt) => {
    if (!authHeaders) { setOperationState("Please login first"); return; }
    try {
      setBusyAction(`retry-dispatch:${attempt.id}`);
      const res = await fetch(`${apiBaseUrl}/api/receipts/dispatch-attempts/${attempt.id}/retry`, { method: "POST", headers: authHeaders });
      if (!res.ok) throw new Error("Retry dispatch failed");
      setReceiptFeedVersion((v) => v + 1);
      setOperationState(`Retried ${attempt.channel} for ${attempt.receiptNo}`);
    } catch {
      setReceiptFeedVersion((v) => v + 1);
      setOperationState(`Retry failed for ${attempt.receiptNo}`);
    } finally { setBusyAction(null); }
  };

  const createMember = async () => {
    if (!authHeaders) { setOperationState("Please login first"); return; }
    try {
      setBusyAction("create-member");
      const payload: CreateMemberRequest = {
        fullName: memberForm.fullName, phone: memberForm.phone,
        preferredLanguage: memberForm.preferredLanguage as CreateMemberRequest["preferredLanguage"],
        birthDate: memberForm.birthDate || undefined, lineUserId: memberForm.lineUserId || undefined
      };
      const res = await fetch(`${apiBaseUrl}/api/members`, { method: "POST", headers: authHeaders, body: JSON.stringify(payload) });
      if (!res.ok) throw new Error("Create member failed");
      setMemberForm({ fullName: "", phone: "", preferredLanguage: "th", birthDate: "", lineUserId: "" });
      setOperationState(`Created member ${payload.fullName}`);
    } catch { setOperationState("Create member failed"); }
    finally { setBusyAction(null); }
  };

  const createMenuItem = async () => {
    if (!authHeaders) { setOperationState("Please login first"); return; }
    try {
      setBusyAction("create-menu");
      const payload: CreateMenuItemRequest = {
        category: menuForm.category, name: menuForm.name, price: Number(menuForm.price),
        description: menuForm.description || undefined, imageUrl: menuForm.imageUrl || undefined,
        happyHourPrice: menuForm.happyHourPrice ? Number(menuForm.happyHourPrice) : undefined
      };
      const res = await fetch(`${apiBaseUrl}/api/menu`, { method: "POST", headers: authHeaders, body: JSON.stringify(payload) });
      if (!res.ok) throw new Error("Create menu item failed");
      setMenuForm({ category: "Seasonal", name: "", price: "0", happyHourPrice: "", description: "", imageUrl: "" });
      setOperationState(`Created menu item ${payload.name}`);
    } catch { setOperationState("Create menu item failed"); }
    finally { setBusyAction(null); }
  };

  const updateMenuItem = async (menuItemId: string, payload: UpdateMenuItemRequest) => {
    if (!authHeaders) { setOperationState("Please login first"); return; }
    try {
      setBusyAction(`menu-update:${menuItemId}`);
      const res = await fetch(`${apiBaseUrl}/api/menu/${menuItemId}`, { method: "POST", headers: authHeaders, body: JSON.stringify(payload) });
      if (!res.ok) throw new Error("Update menu item failed");
      setOperationState(`Updated menu item ${menuItemId}`);
    } catch { setOperationState("Update menu item failed"); }
    finally { setBusyAction(null); }
  };

  const createSecurityUser = async () => {
    if (!authHeaders) { setOperationState("Please login first"); return; }
    try {
      setBusyAction("create-security-user");
      const payload: CreateUserAccountRequest = {
        username: securityForm.username, displayName: securityForm.displayName,
        role: securityForm.role as CreateUserAccountRequest["role"], pin: securityForm.pin,
        expiresAt: securityForm.expiresAt ? new Date(securityForm.expiresAt).toISOString() : undefined
      };
      const res = await fetch(`${apiBaseUrl}/api/security/users`, { method: "POST", headers: authHeaders, body: JSON.stringify(payload) });
      if (!res.ok) throw new Error("Create security user failed");
      setSecurityForm({ username: "", displayName: "", role: "STAFF", pin: "2468", expiresAt: "" });
      setOperationState(`Created account ${payload.username}`);
    } catch { setOperationState("Create security user failed"); }
    finally { setBusyAction(null); }
  };

  const updateSecurityUser = async (userId: string, payload: UpdateUserAccountRequest) => {
    if (!authHeaders) { setOperationState("Please login first"); return; }
    try {
      setBusyAction(`security-user:${userId}`);
      const res = await fetch(`${apiBaseUrl}/api/security/users/${userId}`, { method: "POST", headers: authHeaders, body: JSON.stringify(payload) });
      if (!res.ok) throw new Error("Update security user failed");
      setOperationState(`Updated account ${userId}`);
    } catch { setOperationState("Update security user failed"); }
    finally { setBusyAction(null); }
  };

  const forceLogoutUser = async (userId: string) => {
    if (!authHeaders) { setOperationState("Please login first"); return; }
    try {
      setBusyAction(`force-logout:${userId}`);
      const res = await fetch(`${apiBaseUrl}/api/security/users/${userId}/force-logout`, { method: "POST", headers: authHeaders, body: JSON.stringify({}) });
      if (!res.ok) throw new Error("Force logout failed");
      setOperationState(`Forced logout for ${userId}`);
    } catch { setOperationState("Force logout failed"); }
    finally { setBusyAction(null); }
  };

  const saveSecurityPolicy = async (payload: UpdateSecurityPolicyRequest) => {
    if (!authHeaders) { setOperationState("Please login first"); return; }
    try {
      setBusyAction("security-policy");
      const res = await fetch(`${apiBaseUrl}/api/security/policy`, { method: "POST", headers: authHeaders, body: JSON.stringify(payload) });
      if (!res.ok) throw new Error("Security policy update failed");
      setOperationState("Security policy updated");
    } catch { setOperationState("Security policy update failed"); }
    finally { setBusyAction(null); }
  };

  const createScheduledShift = async () => {
    if (!authHeaders) { setOperationState("Please login first"); return; }
    try {
      setBusyAction("create-schedule");
      const payload: CreateScheduledShiftRequest = {
        userId: scheduleForm.userId, role: scheduleForm.role, shiftDate: scheduleForm.shiftDate,
        startTime: scheduleForm.startTime, endTime: scheduleForm.endTime, zone: scheduleForm.zone,
        note: scheduleForm.note || undefined
      };
      const res = await fetch(`${apiBaseUrl}/api/hr/schedules`, { method: "POST", headers: authHeaders, body: JSON.stringify(payload) });
      if (!res.ok) throw new Error("Create shift failed");
      setOperationState(`Created shift for ${scheduleForm.shiftDate} ${scheduleForm.startTime}`);
    } catch { setOperationState("Create shift failed"); }
    finally { setBusyAction(null); }
  };

  const reviewLeaveRequest = async (requestId: string, status: "APPROVED" | "REJECTED") => {
    if (!authHeaders) { setOperationState("Please login first"); return; }
    try {
      setBusyAction(`leave-review:${requestId}`);
      const res = await fetch(`${apiBaseUrl}/api/hr/leave-requests/${requestId}`, { method: "POST", headers: authHeaders, body: JSON.stringify({ status }) });
      if (!res.ok) throw new Error("Review leave request failed");
      setOperationState(`${status === "APPROVED" ? "Approved" : "Rejected"} leave request ${requestId}`);
    } catch { setOperationState("Review leave request failed"); }
    finally { setBusyAction(null); }
  };

  const reviewSwapRequest = async (requestId: string, status: "APPROVED" | "REJECTED") => {
    if (!authHeaders) { setOperationState("Please login first"); return; }
    try {
      setBusyAction(`swap-review:${requestId}`);
      const res = await fetch(`${apiBaseUrl}/api/hr/swap-requests/${requestId}`, { method: "POST", headers: authHeaders, body: JSON.stringify({ status }) });
      if (!res.ok) throw new Error("Review swap request failed");
      setOperationState(`${status === "APPROVED" ? "Approved" : "Rejected"} swap request ${requestId}`);
    } catch { setOperationState("Review swap request failed"); }
    finally { setBusyAction(null); }
  };

  const updateTableLayout = async (table: DiningTable, x: number, y: number) => {
    if (!authHeaders) { setOperationState("Please login first"); return; }
    try {
      setBusyAction(`layout:${table.id}`);
      const res = await fetch(`${apiBaseUrl}/api/tables/${table.id}/layout`, { method: "POST", headers: authHeaders, body: JSON.stringify({ x, y }) });
      if (!res.ok) throw new Error("Layout update failed");
      setOperationState(`Moved table ${table.label}`);
    } catch { setOperationState("Table layout update failed"); }
    finally { setBusyAction(null); }
  };

  const reserveSelectedTable = async () => {
    if (!authHeaders || !selectedTable) { setOperationState("Please login first"); return; }
    try {
      setBusyAction(`reserve:${selectedTable.id}`);
      const payload: CreateReservationRequest = {
        guestName: reservationForm.guestName, reservedAt: new Date(reservationForm.reservedAt).toISOString(),
        partySize: reservationForm.partySize, contactPhone: reservationForm.contactPhone || undefined,
        note: reservationForm.note || undefined
      };
      const res = await fetch(`${apiBaseUrl}/api/tables/${selectedTable.id}/reserve`, { method: "POST", headers: authHeaders, body: JSON.stringify(payload) });
      if (!res.ok) throw new Error("Reservation failed");
      setOperationState(`Reserved ${selectedTable.label} for ${payload.guestName}`);
    } catch { setOperationState("Reservation failed"); }
    finally { setBusyAction(null); }
  };

  const clearSelectedReservation = async () => {
    if (!authHeaders || !selectedTable) { setOperationState("Please login first"); return; }
    try {
      setBusyAction(`clear-reservation:${selectedTable.id}`);
      const res = await fetch(`${apiBaseUrl}/api/tables/${selectedTable.id}/clear-reservation`, { method: "POST", headers: authHeaders, body: JSON.stringify({}) });
      if (!res.ok) throw new Error("Clear reservation failed");
      setOperationState(`Cleared reservation for ${selectedTable.label}`);
    } catch { setOperationState("Clear reservation failed"); }
    finally { setBusyAction(null); }
  };

  const assignMemberToOrder = async (memberId: string) => {
    if (!authHeaders || !selectedOrder) { setOperationState("Select an open order first"); return; }
    try {
      setBusyAction(`assign-member:${selectedOrder.id}`);
      const payload: AssignMemberRequest = { memberId };
      const res = await fetch(`${apiBaseUrl}/api/orders/${selectedOrder.id}/assign-member`, { method: "POST", headers: authHeaders, body: JSON.stringify(payload) });
      if (!res.ok) throw new Error("Assign member failed");
      const member = members.find((m) => m.id === memberId);
      setOperationState(`Assigned ${member?.fullName ?? memberId} to ${selectedOrder.id}`);
    } catch { setOperationState("Assign member failed"); }
    finally { setBusyAction(null); }
  };

  const toggleDeliveryPlatform = async (platform: string, enabled: boolean) => {
    if (!authHeaders) { setOperationState("Please login first"); return; }
    try {
      setBusyAction(`delivery-toggle:${platform}`);
      const res = await fetch(`${apiBaseUrl}/api/delivery/platforms/${platform}/toggle`, { method: "POST", headers: authHeaders, body: JSON.stringify({ enabled }) });
      if (!res.ok) throw new Error("Toggle failed");
      setOperationState(`${enabled ? "Enabled" : "Disabled"} ${platform}`);
    } catch { setOperationState("Delivery platform toggle failed"); }
    finally { setBusyAction(null); }
  };

  const syncDeliveryMenu = async (platform: string) => {
    if (!authHeaders) { setOperationState("Please login first"); return; }
    try {
      setBusyAction(`delivery-sync:${platform}`);
      const res = await fetch(`${apiBaseUrl}/api/delivery/platforms/${platform}/sync-menu`, { method: "POST", headers: authHeaders, body: JSON.stringify({ propagateOutOfStock: true }) });
      if (!res.ok) throw new Error("Sync failed");
      setOperationState(`Synced menu to ${platform}`);
    } catch { setOperationState("Delivery menu sync failed"); }
    finally { setBusyAction(null); }
  };

  const recordInventoryMovement = async (itemId: string, type: RecordStockMovementRequest["type"], quantity: number) => {
    if (!authHeaders) { setOperationState("Please login first"); return; }
    try {
      setBusyAction(`inventory:${itemId}:${type}`);
      const payload: RecordStockMovementRequest = { itemId, type, quantity, note: inventoryNote || undefined };
      const res = await fetch(`${apiBaseUrl}/api/inventory/movements`, { method: "POST", headers: authHeaders, body: JSON.stringify(payload) });
      if (!res.ok) throw new Error("Inventory movement failed");
      setOperationState(`${type} recorded for ${itemId}`);
    } catch { setOperationState("Inventory movement failed"); }
    finally { setBusyAction(null); }
  };

  const value: AppContextValue = {
    connectionState, lastHeartbeat,
    session, permissions, mfaChallenge, mfaCode, setMfaCode, operationState, busyAction, authHeaders,
    overview, receipts, paymentSessions, auditEntries, exceptions, report, crmOverview, members,
    managedUsers, securityPolicy, deliveryCenter, inventoryOverview, hrOverview,
    selectedTableId, setSelectedTableId, selectedOrderId, setSelectedOrderId,
    selectedMenuId, setSelectedMenuId,
    splitCount, setSplitCount, paymentTip, setPaymentTip, paymentMethod, setPaymentMethod,
    splitGuestMethods, setSplitGuestMethods, splitGuestCount, splitPaymentsPreview,
    selectedTable, selectedOrder, selectedMenuItem,
    reservationForm, setReservationForm, voidReason, setVoidReason, refundReason, setRefundReason,
    receiptEmail, setReceiptEmail, receiptLineUserId, setReceiptLineUserId,
    receiptPrinterName, setReceiptPrinterName, taxInvoiceForm, setTaxInvoiceForm,
    etaxSubmitChannel, setEtaxSubmitChannel, memberForm, setMemberForm,
    inventoryNote, setInventoryNote, menuForm, setMenuForm, securityForm, setSecurityForm,
    adminIpInput, setAdminIpInput, receiptTemplateForm, setReceiptTemplateForm,
    scheduleForm, setScheduleForm, receiptFeedVersion, setReceiptFeedVersion,
    loginAs, verifyTwoFactor, logout, resetDemo, createSampleOrder, settleOrder,
    createPaymentSession, capturePaymentSession, retryPaymentSession, splitSettleOrder,
    voidOrder, refundReceipt, shareReceipt, printReceipt, issueTaxInvoice, submitEtax,
    retryDispatchAttempt, createMember, createMenuItem, updateMenuItem,
    createSecurityUser, updateSecurityUser, forceLogoutUser, saveSecurityPolicy,
    createScheduledShift, reviewLeaveRequest, reviewSwapRequest,
    updateTableLayout, reserveSelectedTable, clearSelectedReservation, assignMemberToOrder,
    toggleDeliveryPlatform, syncDeliveryMenu, recordInventoryMovement, downloadCsv
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}
