import AsyncStorage from "@react-native-async-storage/async-storage";
import * as Location from "expo-location";
import * as Notifications from "expo-notifications";
import { StatusBar } from "expo-status-bar";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View
} from "react-native";
import {
  diningTables as fallbackTables,
  menuItems as fallbackMenu,
  type CreateLeaveRequestRequest,
  type KitchenChatFeedResponse,
  type KitchenChatMessage,
  type CreateOrderRequest,
  type DiningTable,
  type LeaveRequest,
  type LoginResponse,
  type MenuItemSummary,
  type OrderTicket,
  type RequestManagerHelpRequest,
  type ScheduledShift,
  type SendKitchenChatRequest,
  type ShiftSession,
  type ShiftSessionResponse,
  type StaffHrWorkspaceResponse,
  type StaffNotification,
  type StaffNotificationFeedResponse,
  type StaffOrdersResponse,
  type SwapShiftRequest
} from "@mypos/domain";

// ─── Config ────────────────────────────────────────────────────────────────────

const API = (process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://192.168.100.9:4000").replace(/\/$/, "");
const STORE_KEYS = {
  menu: "cache:menu",
  tables: "cache:tables",
  offlineQueue: "offline:order_queue"
};

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldShowBanner: true,
    shouldShowList: true,
    shouldPlaySound: true,
    shouldSetBadge: true
  })
});

// ─── Types ─────────────────────────────────────────────────────────────────────

type Tab = "home" | "order" | "hr" | "notifications" | "chat";

interface CartLine {
  item: MenuItemSummary;
  quantity: number;
}

interface OfflineOrder {
  id: string;
  payload: CreateOrderRequest;
  tableLabel: string;
  queuedAt: string;
}

// ─── App ───────────────────────────────────────────────────────────────────────

export default function App() {
  // Navigation
  const [activeTab, setActiveTab] = useState<Tab>("home");

  // Auth
  const [session, setSession] = useState<LoginResponse["session"] | null>(null);

  // Data
  const [shift, setShift] = useState<ShiftSession | null>(null);
  const [orders, setOrders] = useState<OrderTicket[]>([]);
  const [tables, setTables] = useState<DiningTable[]>(fallbackTables);
  const [menu, setMenu] = useState<MenuItemSummary[]>(fallbackMenu);
  const [notifications, setNotifications] = useState<StaffNotification[]>([]);
  const [chatMessages, setChatMessages] = useState<KitchenChatMessage[]>([]);
  const [scheduledShifts, setScheduledShifts] = useState<ScheduledShift[]>([]);
  const [leaveRequests, setLeaveRequests] = useState<LeaveRequest[]>([]);
  const [swapRequests, setSwapRequests] = useState<SwapShiftRequest[]>([]);

  // Order / cart
  const [selectedTableId, setSelectedTableId] = useState<string | null>(null);
  const [cart, setCart] = useState<CartLine[]>([]);
  const [chatInput, setChatInput] = useState("");

  // Offline queue
  const [offlineQueue, setOfflineQueue] = useState<OfflineOrder[]>([]);
  const [isOnline, setIsOnline] = useState(true);

  // Loading & status
  const [isLoadingData, setIsLoadingData] = useState(false);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [message, setMessage] = useState("Login as staff to begin shift");

  const chatScrollRef = useRef<ScrollView>(null);

  // ─── Derived ─────────────────────────────────────────────────────────────────

  const authHeaders = useMemo(
    () =>
      session
        ? { Authorization: `Bearer ${session.accessToken}`, "Content-Type": "application/json" }
        : null,
    [session]
  );

  const selectedTable = tables.find((t) => t.id === selectedTableId) ?? null;
  const cartTotal = cart.reduce((sum, l) => sum + l.item.price * l.quantity, 0);
  const unreadCount = notifications.filter((n) => !n.read).length;
  const otShifts = scheduledShifts.filter(
    (s) => (s.zone?.toUpperCase().includes("OT") ?? false) || (s.note?.toUpperCase().includes("OT") ?? false)
  );
  const totalOtHours = otShifts.reduce((acc, s) => {
    const [sh, sm] = s.startTime.split(":").map(Number);
    const [eh, em] = s.endTime.split(":").map(Number);
    return acc + (eh * 60 + em - (sh * 60 + sm)) / 60;
  }, 0);

  // ─── Cache helpers ────────────────────────────────────────────────────────────

  const saveCache = async (key: string, data: unknown) => {
    try {
      await AsyncStorage.setItem(key, JSON.stringify(data));
    } catch {
      // ignore cache errors
    }
  };

  const loadCache = async <T,>(key: string): Promise<T | null> => {
    try {
      const raw = await AsyncStorage.getItem(key);
      return raw ? (JSON.parse(raw) as T) : null;
    } catch {
      return null;
    }
  };

  const loadCachedData = useCallback(async () => {
    const cachedMenu = await loadCache<MenuItemSummary[]>(STORE_KEYS.menu);
    if (cachedMenu) setMenu(cachedMenu);
    const cachedTables = await loadCache<DiningTable[]>(STORE_KEYS.tables);
    if (cachedTables) setTables(cachedTables);
    const cachedQueue = await loadCache<OfflineOrder[]>(STORE_KEYS.offlineQueue);
    if (cachedQueue) setOfflineQueue(cachedQueue);
  }, []);

  // ─── Notifications setup ──────────────────────────────────────────────────────

  useEffect(() => {
    let sub: Notifications.Subscription;
    (async () => {
      const { status } = await Notifications.requestPermissionsAsync();
      if (status !== "granted") return;
      sub = Notifications.addNotificationReceivedListener((notif) => {
        const title = notif.request.content.title ?? "แจ้งเตือนใหม่";
        const body = notif.request.content.body ?? "";
        setNotifications((prev) => [
          {
            id: notif.request.identifier,
            title,
            message: body,
            type: "GENERAL" as const,
            audienceRole: "STAFF" as const,
            createdAt: new Date().toISOString(),
            read: false
          },
          ...prev
        ]);
        setMessage(`🔔 ${title}`);
      });
    })();
    return () => sub?.remove();
  }, []);

  // ─── Load cached data on mount ────────────────────────────────────────────────

  useEffect(() => {
    void loadCachedData();
  }, [loadCachedData]);

  // ─── Auth ─────────────────────────────────────────────────────────────────────

  const loginAsStaff = async () => {
    try {
      setBusyAction("login");
      const res = await fetch(`${API}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: "staff01", pin: "2468", deviceId: "STAFF-MOBILE-DEMO" })
      });
      if (!res.ok) throw new Error("Login failed");
      const data = (await res.json()) as LoginResponse;
      if (!data.session) throw new Error("2FA roles cannot login via mobile");
      setSession(data.session);
      setMessage(`เข้าสู่ระบบในชื่อ ${data.session.user.displayName}`);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Login failed");
    } finally {
      setBusyAction(null);
    }
  };

  const logout = () => {
    setSession(null);
    setShift(null);
    setMessage("ออกจากระบบแล้ว");
  };

  // ─── Data loading ──────────────────────────────────────────────────────────────

  const loadStaffData = useCallback(async () => {
    if (!authHeaders) return;
    setIsLoadingData(true);
    try {
      const [shiftRes, ordersRes, tablesRes, menuRes, notifRes, chatRes, hrRes] = await Promise.all([
        fetch(`${API}/api/staff/current-shift`, { headers: authHeaders }),
        fetch(`${API}/api/staff/my-orders`, { headers: authHeaders }),
        fetch(`${API}/api/tables`, { headers: authHeaders }),
        fetch(`${API}/api/menu`, { headers: authHeaders }),
        fetch(`${API}/api/staff/notifications`, { headers: authHeaders }),
        fetch(`${API}/api/staff/chat`, { headers: authHeaders }),
        fetch(`${API}/api/staff/hr`, { headers: authHeaders })
      ]);

      setIsOnline(true);

      if (shiftRes.ok) setShift(((await shiftRes.json()) as ShiftSessionResponse).shift);
      else setShift(null);

      if (ordersRes.ok) setOrders(((await ordersRes.json()) as StaffOrdersResponse).orders);

      if (tablesRes.ok) {
        const t = (await tablesRes.json()) as DiningTable[];
        setTables(t);
        void saveCache(STORE_KEYS.tables, t);
      }

      if (menuRes.ok) {
        const m = (await menuRes.json()) as MenuItemSummary[];
        setMenu(m);
        void saveCache(STORE_KEYS.menu, m);
      }

      if (notifRes.ok)
        setNotifications(((await notifRes.json()) as StaffNotificationFeedResponse).notifications);

      if (chatRes.ok)
        setChatMessages(((await chatRes.json()) as KitchenChatFeedResponse).messages);

      if (hrRes.ok) {
        const hr = (await hrRes.json()) as StaffHrWorkspaceResponse;
        setScheduledShifts(hr.workspace.schedules);
        setLeaveRequests(hr.workspace.leaveRequests);
        setSwapRequests(hr.workspace.swapRequests);
      } else {
        setScheduledShifts([]);
        setLeaveRequests([]);
        setSwapRequests([]);
      }

      // Flush offline queue when back online
      await flushOfflineQueue();
    } catch {
      setIsOnline(false);
      setMessage("ออฟไลน์ — ใช้ข้อมูลแคชอยู่");
    } finally {
      setIsLoadingData(false);
    }
  }, [authHeaders]);

  useEffect(() => {
    void loadStaffData();
  }, [loadStaffData]);

  // ─── GPS ──────────────────────────────────────────────────────────────────────

  const getGPSLocation = async (): Promise<{ latitude: number; longitude: number }> => {
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== "granted") throw new Error("ไม่ได้รับสิทธิ์ GPS — กรุณาเปิดใน Settings");
    const loc = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.High });
    return { latitude: loc.coords.latitude, longitude: loc.coords.longitude };
  };

  // ─── Shift ────────────────────────────────────────────────────────────────────

  const clockIn = async () => {
    if (!authHeaders) { setMessage("กรุณา login ก่อน"); return; }
    try {
      setBusyAction("clock-in");
      setMessage("กำลังอ่าน GPS…");
      const loc = await getGPSLocation();
      const res = await fetch(`${API}/api/staff/clock-in`, {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify({ ...loc, deviceId: "STAFF-MOBILE-DEMO", ipAddress: "10.0.0.5" })
      });
      if (!res.ok) {
        const err = (await res.json()) as { message?: string };
        throw new Error(err.message ?? "Clock in failed");
      }
      const d = (await res.json()) as ShiftSessionResponse;
      setShift(d.shift);
      setMessage(`เริ่มกะ ${new Date(d.shift.checkInAt).toLocaleTimeString("th-TH")} · ${d.shift.geofenceStatus}`);
      await loadStaffData();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Clock in failed");
    } finally {
      setBusyAction(null);
    }
  };

  const clockOut = async () => {
    if (!authHeaders) { setMessage("กรุณา login ก่อน"); return; }
    try {
      setBusyAction("clock-out");
      setMessage("กำลังอ่าน GPS…");
      const loc = await getGPSLocation();
      const res = await fetch(`${API}/api/staff/clock-out`, {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify(loc)
      });
      if (!res.ok) throw new Error("Clock out failed");
      const d = (await res.json()) as ShiftSessionResponse;
      setShift(d.shift);
      setMessage(`สิ้นสุดกะ ${new Date(d.shift.checkOutAt ?? d.shift.checkInAt).toLocaleTimeString("th-TH")}`);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Clock out failed");
    } finally {
      setBusyAction(null);
    }
  };

  // ─── Offline queue ────────────────────────────────────────────────────────────

  const enqueueOfflineOrder = async (payload: CreateOrderRequest, tableLabel: string) => {
    const entry: OfflineOrder = {
      id: `offline-${Date.now()}`,
      payload,
      tableLabel,
      queuedAt: new Date().toISOString()
    };
    const updated = [...offlineQueue, entry];
    setOfflineQueue(updated);
    await saveCache(STORE_KEYS.offlineQueue, updated);
    setMessage(`บันทึกออเดอร์ออฟไลน์ (${updated.length} รายการรอส่ง)`);
  };

  const flushOfflineQueue = async () => {
    if (!authHeaders) return;
    const queue = await loadCache<OfflineOrder[]>(STORE_KEYS.offlineQueue);
    if (!queue || queue.length === 0) return;

    const remaining: OfflineOrder[] = [];
    for (const entry of queue) {
      try {
        const res = await fetch(`${API}/api/orders`, {
          method: "POST",
          headers: authHeaders,
          body: JSON.stringify(entry.payload)
        });
        if (!res.ok) remaining.push(entry);
      } catch {
        remaining.push(entry);
      }
    }

    setOfflineQueue(remaining);
    await saveCache(STORE_KEYS.offlineQueue, remaining);
    if (remaining.length < queue.length)
      setMessage(`ส่งออเดอร์ออฟไลน์ ${queue.length - remaining.length} รายการสำเร็จ`);
  };

  // ─── Order ────────────────────────────────────────────────────────────────────

  const addToCart = (item: MenuItemSummary) =>
    setCart((cur) => {
      const ex = cur.find((l) => l.item.id === item.id);
      if (!ex) return [...cur, { item, quantity: 1 }];
      return cur.map((l) => (l.item.id === item.id ? { ...l, quantity: l.quantity + 1 } : l));
    });

  const removeFromCart = (itemId: string) =>
    setCart((cur) =>
      cur.map((l) => (l.item.id === itemId ? { ...l, quantity: l.quantity - 1 } : l)).filter((l) => l.quantity > 0)
    );

  const submitOrder = async () => {
    if (!selectedTable || cart.length === 0) { setMessage("เลือกโต๊ะและเพิ่มเมนูก่อน"); return; }
    const payload: CreateOrderRequest = {
      tableId: selectedTable.id,
      guestCount: Math.max(selectedTable.seats - 1, 1),
      waiterName: session?.user.displayName ?? "Floor Staff",
      priority: "NORMAL",
      source: "STAFF_APP",
      specialNote: "สั่งจาก Staff Mobile",
      items: cart.map((l) => ({ menuItemId: l.item.id, quantity: l.quantity }))
    };

    if (!authHeaders || !isOnline) {
      await enqueueOfflineOrder(payload, selectedTable.label);
      setCart([]);
      return;
    }

    try {
      setBusyAction("submit-order");
      const res = await fetch(`${API}/api/orders`, {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error();
      setCart([]);
      setMessage(`ส่งออเดอร์โต๊ะ ${selectedTable.label} สำเร็จ`);
      await loadStaffData();
    } catch {
      await enqueueOfflineOrder(payload, selectedTable.label);
      setCart([]);
    } finally {
      setBusyAction(null);
    }
  };

  // ─── Manager help ──────────────────────────────────────────────────────────────

  const requestManagerHelp = async () => {
    if (!authHeaders) { setMessage("กรุณา login ก่อน"); return; }
    try {
      setBusyAction("request-help");
      const payload: RequestManagerHelpRequest = {
        message: selectedTable ? `ต้องการความช่วยเหลือที่ ${selectedTable.label}` : "ต้องการความช่วยเหลือ",
        tableLabel: selectedTable?.label
      };
      const res = await fetch(`${API}/api/staff/request-help`, {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error();
      setMessage("แจ้งผู้จัดการแล้ว");
      await loadStaffData();
    } catch {
      setMessage("ไม่สามารถแจ้งผู้จัดการได้");
    } finally {
      setBusyAction(null);
    }
  };

  // ─── Chat ─────────────────────────────────────────────────────────────────────

  const sendChat = async () => {
    const text = chatInput.trim();
    if (!authHeaders || !text) { setMessage("กรอกข้อความก่อน"); return; }
    try {
      setBusyAction("send-chat");
      const payload: SendKitchenChatRequest = { message: text, tableLabel: selectedTable?.label, target: "KITCHEN" };
      const res = await fetch(`${API}/api/staff/chat`, {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error();
      setChatInput("");
      setMessage("ส่งข้อความถึงครัวแล้ว");
      await loadStaffData();
      setTimeout(() => chatScrollRef.current?.scrollToEnd({ animated: true }), 300);
    } catch {
      setMessage("ไม่สามารถส่งข้อความได้");
    } finally {
      setBusyAction(null);
    }
  };

  // ─── HR ───────────────────────────────────────────────────────────────────────

  const requestLeave = async (shiftDate: string) => {
    if (!authHeaders) { setMessage("กรุณา login ก่อน"); return; }
    try {
      setBusyAction(`leave:${shiftDate}`);
      const payload: CreateLeaveRequestRequest = { leaveDate: shiftDate, leaveType: "PERSONAL", reason: "ขอลาจาก Staff Mobile" };
      const res = await fetch(`${API}/api/staff/leave-requests`, { method: "POST", headers: authHeaders, body: JSON.stringify(payload) });
      if (!res.ok) throw new Error();
      setMessage(`ส่งคำขอลาวันที่ ${shiftDate} แล้ว`);
      await loadStaffData();
    } catch {
      setMessage("ไม่สามารถส่งคำขอลาได้");
    } finally {
      setBusyAction(null);
    }
  };

  const requestSwap = async (shiftId: string) => {
    if (!authHeaders) { setMessage("กรุณา login ก่อน"); return; }
    try {
      setBusyAction(`swap:${shiftId}`);
      const res = await fetch(`${API}/api/staff/swap-requests`, {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify({ shiftId, targetUserId: "USR-CASH-01", reason: "ขอสลับกะจาก Mobile" })
      });
      if (!res.ok) throw new Error();
      setMessage("ส่งคำขอสลับกะแล้ว");
      await loadStaffData();
    } catch {
      setMessage("ไม่สามารถส่งคำขอสลับกะได้");
    } finally {
      setBusyAction(null);
    }
  };

  // ─── Render helpers ───────────────────────────────────────────────────────────

  const LoadingOverlay = () => (
    <View style={styles.loadingOverlay}>
      <ActivityIndicator size="large" color={C.accent} />
      <Text style={styles.loadingText}>กำลังโหลด…</Text>
    </View>
  );

  const SkeletonCard = () => (
    <View style={[styles.listItem, styles.skeleton]}>
      <View style={styles.skeletonLine} />
      <View style={[styles.skeletonLine, { width: "60%" }]} />
    </View>
  );

  // ─── Tab: Home ────────────────────────────────────────────────────────────────

  const renderHome = () => (
    <ScrollView contentContainerStyle={styles.tabContent}>
      {/* Offline banner */}
      {!isOnline && (
        <View style={styles.offlineBanner}>
          <Text style={styles.offlineBannerText}>
            📡 ออฟไลน์ — เมนูและโต๊ะจากแคช{offlineQueue.length > 0 ? ` · ${offlineQueue.length} ออเดอร์รอส่ง` : ""}
          </Text>
        </View>
      )}

      {/* Status banner */}
      <View style={styles.statusBanner}>
        <Text style={styles.statusBannerText}>{message}</Text>
      </View>

      {/* Session */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Session</Text>
        <View style={styles.row}>
          <View style={{ flex: 1 }}>
            <Text style={styles.primaryText}>{session ? session.user.displayName : "ยังไม่ได้ล็อกอิน"}</Text>
            <Text style={styles.mutedText}>
              {session ? `${session.user.role} · หมดอายุ ${new Date(session.expiresAt).toLocaleTimeString("th-TH")}` : "staff01 / 2468"}
            </Text>
          </View>
          {session ? (
            <Pressable style={styles.dangerButton} onPress={logout}>
              <Text style={styles.dangerButtonText}>ออก</Text>
            </Pressable>
          ) : (
            <Pressable style={styles.primaryButton} onPress={() => void loginAsStaff()} disabled={busyAction === "login"}>
              {busyAction === "login"
                ? <ActivityIndicator color={C.accentDark} />
                : <Text style={styles.primaryButtonText}>เข้าสู่ระบบ</Text>}
            </Pressable>
          )}
        </View>
      </View>

      {/* Shift guard */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>กะงาน</Text>
        {shift ? (
          <>
            <View style={styles.row}>
              <View style={{ flex: 1 }}>
                <Text style={styles.primaryText}>{shift.staffName}</Text>
                <Text style={styles.mutedText}>{shift.geofenceStatus} · {shift.distanceMeters ?? 0}m</Text>
              </View>
              <View style={[styles.badge, shift.sessionActive ? styles.badgeGreen : styles.badgeGray]}>
                <Text style={styles.badgeText}>{shift.sessionActive ? "ON SHIFT" : "OFF"}</Text>
              </View>
            </View>
            <Text style={styles.mutedText}>
              เริ่ม {new Date(shift.checkInAt).toLocaleTimeString("th-TH")}
              {shift.checkOutAt ? ` · สิ้นสุด ${new Date(shift.checkOutAt).toLocaleTimeString("th-TH")}` : ""}
            </Text>
          </>
        ) : (
          <Text style={styles.mutedText}>ยังไม่ได้เริ่มกะ</Text>
        )}
        <View style={styles.grid2}>
          <Pressable style={styles.actionCard} onPress={() => void clockIn()} disabled={!!busyAction}>
            {busyAction === "clock-in"
              ? <ActivityIndicator color={C.text} />
              : <>
                  <Text style={styles.actionText}>Clock In</Text>
                  <Text style={styles.actionSubtext}>📍 GPS จริง</Text>
                </>}
          </Pressable>
          <Pressable
            style={[styles.actionCard, shift?.sessionActive ? styles.actionCardDanger : styles.actionCardDisabled]}
            onPress={() => void clockOut()}
            disabled={!shift?.sessionActive || !!busyAction}
          >
            {busyAction === "clock-out"
              ? <ActivityIndicator color={C.text} />
              : <>
                  <Text style={styles.actionText}>Clock Out</Text>
                  <Text style={styles.actionSubtext}>📍 GPS จริง</Text>
                </>}
          </Pressable>
        </View>
      </View>

      {/* Quick actions */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Quick Actions</Text>
        <View style={styles.grid2}>
          <Pressable style={styles.quickCard} onPress={() => setActiveTab("order")}>
            <Text style={styles.quickIcon}>🛎</Text>
            <Text style={styles.actionText}>รับออเดอร์</Text>
            {cart.length > 0 && <Text style={styles.actionSubtext}>{cart.length} รายการในตะกร้า</Text>}
          </Pressable>
          <Pressable style={styles.quickCard} onPress={() => void requestManagerHelp()} disabled={busyAction === "request-help"}>
            {busyAction === "request-help"
              ? <ActivityIndicator color={C.accent} />
              : <>
                  <Text style={styles.quickIcon}>🆘</Text>
                  <Text style={styles.actionText}>เรียกผู้จัดการ</Text>
                </>}
          </Pressable>
          <Pressable style={styles.quickCard} onPress={() => setActiveTab("hr")}>
            <Text style={styles.quickIcon}>⏱</Text>
            <Text style={styles.actionText}>ดู OT</Text>
            <Text style={styles.actionSubtext}>{otShifts.length > 0 ? `${totalOtHours.toFixed(1)} ชม.` : "ไม่มี OT"}</Text>
          </Pressable>
          <Pressable style={styles.quickCard} onPress={() => setActiveTab("chat")}>
            <Text style={styles.quickIcon}>💬</Text>
            <Text style={styles.actionText}>แจ้งครัว</Text>
          </Pressable>
        </View>
      </View>

      {/* Offline queue indicator */}
      {offlineQueue.length > 0 && (
        <View style={[styles.card, styles.offlineCard]}>
          <Text style={styles.cardTitle}>⏳ ออเดอร์รอส่ง ({offlineQueue.length})</Text>
          {offlineQueue.map((entry) => (
            <View key={entry.id} style={styles.listItem}>
              <Text style={styles.primaryText}>โต๊ะ {entry.tableLabel}</Text>
              <Text style={styles.mutedText}>รอส่งตั้งแต่ {new Date(entry.queuedAt).toLocaleTimeString("th-TH")}</Text>
            </View>
          ))}
          <Pressable style={styles.primaryButton} onPress={() => void flushOfflineQueue()} disabled={!isOnline}>
            <Text style={styles.primaryButtonText}>{isOnline ? "ส่งเดี๋ยวนี้" : "รอสัญญาณอินเทอร์เน็ต"}</Text>
          </Pressable>
        </View>
      )}

      {/* My orders */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>ออเดอร์ของฉัน</Text>
        {isLoadingData
          ? [1, 2].map((i) => <SkeletonCard key={i} />)
          : orders.length === 0
          ? <Text style={styles.mutedText}>ยังไม่มีออเดอร์</Text>
          : orders.slice(0, 3).map((order) => (
              <View key={order.id} style={styles.listItem}>
                <View style={styles.row}>
                  <Text style={styles.primaryText}>{order.tableLabel}</Text>
                  <View style={[styles.statusPill, orderStatusColor(order.status)]}>
                    <Text style={styles.statusPillText}>{order.status}</Text>
                  </View>
                </View>
                <Text style={styles.mutedText}>{order.items.length} รายการ · ฿{order.totalAmount}</Text>
              </View>
            ))}
        <Pressable style={styles.refreshButton} onPress={() => void loadStaffData()} disabled={!session || isLoadingData}>
          {isLoadingData
            ? <ActivityIndicator size="small" color={C.accent} />
            : <Text style={styles.refreshButtonText}>รีเฟรชข้อมูล</Text>}
        </Pressable>
      </View>
    </ScrollView>
  );

  // ─── Tab: Order ───────────────────────────────────────────────────────────────

  const renderOrder = () => (
    <ScrollView contentContainerStyle={styles.tabContent}>
      {!isOnline && (
        <View style={styles.offlineBanner}>
          <Text style={styles.offlineBannerText}>📡 ออฟไลน์ — ออเดอร์จะถูกบันทึกและส่งเมื่อกลับมาออนไลน์</Text>
        </View>
      )}

      {/* Table picker */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>เลือกโต๊ะ</Text>
        {isLoadingData
          ? <ActivityIndicator color={C.accent} />
          : (
            <View style={styles.tableGrid}>
              {tables.map((table) => (
                <Pressable
                  key={table.id}
                  style={[styles.tableCard, selectedTableId === table.id && styles.tableCardActive]}
                  onPress={() => setSelectedTableId(table.id)}
                >
                  <Text style={styles.tableLabel}>{table.label}</Text>
                  <Text style={styles.tableStatus}>{table.status}</Text>
                </Pressable>
              ))}
            </View>
          )}
      </View>

      {/* Menu */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>เมนู</Text>
        {isLoadingData
          ? [1, 2, 3, 4].map((i) => <SkeletonCard key={i} />)
          : (
            <View style={styles.menuGrid}>
              {menu.filter((item) => item.inStock).map((item) => (
                <Pressable key={item.id} style={styles.menuCard} onPress={() => addToCart(item)}>
                  <Text style={styles.menuName}>{item.name}</Text>
                  <Text style={styles.menuPrice}>฿{item.price}</Text>
                  <Text style={styles.menuCategory}>{item.category}</Text>
                </Pressable>
              ))}
            </View>
          )}
      </View>

      {/* Cart */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>ตะกร้า{selectedTable ? ` — โต๊ะ ${selectedTable.label}` : ""}</Text>
        {!selectedTable && <Text style={styles.warningText}>⚠ เลือกโต๊ะก่อนส่งออเดอร์</Text>}
        {cart.length === 0
          ? <Text style={styles.mutedText}>ยังไม่มีรายการ</Text>
          : cart.map((line) => (
              <View key={line.item.id} style={styles.cartLine}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.primaryText}>{line.item.name}</Text>
                  <Text style={styles.mutedText}>฿{line.item.price} × {line.quantity} = ฿{line.item.price * line.quantity}</Text>
                </View>
                <View style={styles.qtyRow}>
                  <Pressable style={styles.qtyButton} onPress={() => removeFromCart(line.item.id)}>
                    <Text style={styles.qtyButtonText}>−</Text>
                  </Pressable>
                  <Text style={styles.qtyValue}>{line.quantity}</Text>
                  <Pressable style={styles.qtyButton} onPress={() => addToCart(line.item)}>
                    <Text style={styles.qtyButtonText}>+</Text>
                  </Pressable>
                </View>
              </View>
            ))}
        {cart.length > 0 && (
          <View style={styles.cartTotal}>
            <Text style={styles.cardTitle}>รวม</Text>
            <Text style={styles.totalAmount}>฿{cartTotal}</Text>
          </View>
        )}
        <Pressable
          style={[styles.submitButton, (cart.length === 0 || !selectedTable) && styles.submitButtonDisabled]}
          onPress={() => void submitOrder()}
          disabled={cart.length === 0 || !selectedTable || busyAction === "submit-order"}
        >
          {busyAction === "submit-order"
            ? <ActivityIndicator color={C.accentDark} />
            : <Text style={styles.submitButtonText}>{isOnline ? "ส่งออเดอร์ไปครัว" : "บันทึกออฟไลน์"}</Text>}
        </Pressable>
        {cart.length > 0 && (
          <Pressable style={styles.clearButton} onPress={() => setCart([])}>
            <Text style={styles.clearButtonText}>ล้างตะกร้า</Text>
          </Pressable>
        )}
      </View>
    </ScrollView>
  );

  // ─── Tab: HR ──────────────────────────────────────────────────────────────────

  const renderHR = () => (
    <ScrollView contentContainerStyle={styles.tabContent}>
      {otShifts.length > 0 && (
        <View style={[styles.card, styles.otCard]}>
          <Text style={styles.cardTitle}>OT ของฉัน</Text>
          <Text style={styles.otHours}>{totalOtHours.toFixed(1)} ชั่วโมง</Text>
          <Text style={styles.mutedText}>{otShifts.length} กะ OT</Text>
        </View>
      )}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>ตารางกะ</Text>
        {isLoadingData
          ? [1, 2].map((i) => <SkeletonCard key={i} />)
          : scheduledShifts.length === 0
          ? <Text style={styles.mutedText}>ยังไม่มีตารางกะ</Text>
          : scheduledShifts.map((s) => (
              <View key={s.id} style={styles.listItem}>
                <View style={styles.row}>
                  <Text style={styles.primaryText}>{s.shiftDate}</Text>
                  <View style={[styles.statusPill, (s.zone?.toUpperCase().includes("OT") ?? false) ? styles.pillOrange : styles.pillBlue]}>
                    <Text style={styles.statusPillText}>{s.status}</Text>
                  </View>
                </View>
                <Text style={styles.mutedText}>{s.startTime}–{s.endTime} · {s.zone}</Text>
                <View style={styles.hrActions}>
                  <Pressable style={styles.hrChip} onPress={() => void requestLeave(s.shiftDate)} disabled={busyAction === `leave:${s.shiftDate}`}>
                    <Text style={styles.hrChipText}>ขอลา</Text>
                  </Pressable>
                  <Pressable style={styles.hrChip} onPress={() => void requestSwap(s.id)} disabled={busyAction === `swap:${s.id}`}>
                    <Text style={styles.hrChipText}>สลับกะ</Text>
                  </Pressable>
                </View>
              </View>
            ))}
      </View>
      <View style={styles.card}>
        <Text style={styles.cardTitle}>คำขอที่รอดำเนินการ</Text>
        {leaveRequests.length === 0 && swapRequests.length === 0
          ? <Text style={styles.mutedText}>ไม่มีคำขอ HR</Text>
          : null}
        {leaveRequests.map((r) => (
          <View key={r.id} style={styles.listItem}>
            <View style={styles.row}>
              <Text style={styles.primaryText}>ลา {r.leaveDate}</Text>
              <View style={[styles.statusPill, requestStatusColor(r.status)]}>
                <Text style={styles.statusPillText}>{r.status}</Text>
              </View>
            </View>
            <Text style={styles.mutedText}>{r.leaveType} · {r.reason}</Text>
          </View>
        ))}
        {swapRequests.map((r) => (
          <View key={r.id} style={styles.listItem}>
            <View style={styles.row}>
              <Text style={styles.primaryText}>สลับกะ {r.shiftDate}</Text>
              <View style={[styles.statusPill, requestStatusColor(r.status)]}>
                <Text style={styles.statusPillText}>{r.status}</Text>
              </View>
            </View>
            <Text style={styles.mutedText}>เป้าหมาย {r.targetStaffName ?? "เปิด"} · {r.reason}</Text>
          </View>
        ))}
      </View>
    </ScrollView>
  );

  // ─── Tab: Notifications ───────────────────────────────────────────────────────

  const renderNotifications = () => (
    <ScrollView contentContainerStyle={styles.tabContent}>
      <View style={styles.card}>
        <View style={styles.row}>
          <Text style={styles.cardTitle}>การแจ้งเตือน</Text>
          {unreadCount > 0 && (
            <View style={styles.badge}>
              <Text style={styles.badgeText}>{unreadCount} ใหม่</Text>
            </View>
          )}
        </View>
        {isLoadingData
          ? [1, 2, 3].map((i) => <SkeletonCard key={i} />)
          : notifications.length === 0
          ? <Text style={styles.mutedText}>ไม่มีการแจ้งเตือน</Text>
          : notifications.map((n) => (
              <View key={n.id} style={[styles.listItem, !n.read && styles.listItemUnread]}>
                <View style={styles.row}>
                  <Text style={styles.primaryText}>{n.title}</Text>
                  <Text style={styles.notifType}>{n.type}</Text>
                </View>
                <Text style={styles.mutedText}>{n.message}</Text>
                <Text style={styles.timeText}>{new Date(n.createdAt).toLocaleString("th-TH")}</Text>
              </View>
            ))}
      </View>
    </ScrollView>
  );

  // ─── Tab: Chat ────────────────────────────────────────────────────────────────

  const renderChat = () => (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : "height"} keyboardVerticalOffset={90}>
      <ScrollView ref={chatScrollRef} contentContainerStyle={styles.tabContent} onContentSizeChange={() => chatScrollRef.current?.scrollToEnd({ animated: false })}>
        <View style={styles.card}>
          <Text style={styles.cardTitle}>แชทกับครัว</Text>
          {selectedTable && (
            <View style={styles.selectedTableBadge}>
              <Text style={styles.selectedTableText}>โต๊ะ {selectedTable.label}</Text>
            </View>
          )}
          {isLoadingData
            ? [1, 2].map((i) => <SkeletonCard key={i} />)
            : chatMessages.length === 0
            ? <Text style={styles.mutedText}>ยังไม่มีข้อความ</Text>
            : chatMessages.map((msg) => {
                const isMe = msg.fromName === session?.user.displayName;
                return (
                  <View key={msg.id} style={[styles.bubble, isMe ? styles.bubbleMe : styles.bubbleThem]}>
                    {!isMe && <Text style={styles.bubbleSender}>{msg.fromName}</Text>}
                    <Text style={styles.bubbleText}>{msg.message}</Text>
                    {msg.tableLabel && <Text style={styles.bubbleMeta}>โต๊ะ {msg.tableLabel}</Text>}
                  </View>
                );
              })}
        </View>
      </ScrollView>
      <View style={styles.composer}>
        <TextInput
          style={styles.chatInput}
          value={chatInput}
          onChangeText={setChatInput}
          placeholder="พิมพ์ข้อความถึงครัว…"
          placeholderTextColor="#4a6a82"
          multiline
          returnKeyType="send"
          onSubmitEditing={() => void sendChat()}
        />
        <Pressable
          style={[styles.sendButton, (!chatInput.trim() || !session) && styles.sendButtonDisabled]}
          onPress={() => void sendChat()}
          disabled={!chatInput.trim() || !session || busyAction === "send-chat"}
        >
          {busyAction === "send-chat"
            ? <ActivityIndicator color={C.accentDark} />
            : <Text style={styles.sendButtonText}>ส่ง</Text>}
        </Pressable>
      </View>
    </KeyboardAvoidingView>
  );

  // ─── Tab bar ──────────────────────────────────────────────────────────────────

  const tabs: { key: Tab; label: string; icon: string; badge?: number }[] = [
    { key: "home", label: "หน้าหลัก", icon: "🏠" },
    { key: "order", label: "ออเดอร์", icon: "🛎", badge: cart.length + offlineQueue.length || undefined },
    { key: "hr", label: "กะงาน", icon: "📅" },
    { key: "notifications", label: "แจ้งเตือน", icon: "🔔", badge: unreadCount || undefined },
    { key: "chat", label: "แชทครัว", icon: "💬" }
  ];

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar style="light" />

      {/* Header */}
      <View style={styles.header}>
        <View style={styles.row}>
          <Text style={styles.headerTitle}>MyPOS Staff</Text>
          {!isOnline && <View style={styles.offlineDot} />}
        </View>
        {session && (
          <View style={styles.headerSession}>
            <Text style={styles.headerSessionText}>{session.user.displayName}</Text>
            {shift?.sessionActive && <View style={styles.onlineDot} />}
          </View>
        )}
      </View>

      {/* Global loading overlay */}
      {isLoadingData && activeTab === "home" && !session && <LoadingOverlay />}

      {/* Content */}
      <View style={{ flex: 1 }}>
        {activeTab === "home" && renderHome()}
        {activeTab === "order" && renderOrder()}
        {activeTab === "hr" && renderHR()}
        {activeTab === "notifications" && renderNotifications()}
        {activeTab === "chat" && renderChat()}
      </View>

      {/* Bottom tab bar */}
      <View style={styles.tabBar}>
        {tabs.map((tab) => (
          <Pressable key={tab.key} style={styles.tabItem} onPress={() => setActiveTab(tab.key)}>
            <View style={styles.tabIconWrap}>
              <Text style={styles.tabIcon}>{tab.icon}</Text>
              {tab.badge != null && tab.badge > 0 && (
                <View style={styles.tabBadge}>
                  <Text style={styles.tabBadgeText}>{tab.badge}</Text>
                </View>
              )}
            </View>
            <Text style={[styles.tabLabel, activeTab === tab.key && styles.tabLabelActive]}>{tab.label}</Text>
            {activeTab === tab.key && <View style={styles.tabActiveBar} />}
          </Pressable>
        ))}
      </View>
    </SafeAreaView>
  );
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function orderStatusColor(status: string) {
  if (status === "PAID") return styles.pillGreen;
  if (status === "CANCELLED" || status === "VOID") return styles.pillRed;
  if (status === "READY") return styles.pillOrange;
  return styles.pillBlue;
}

function requestStatusColor(status: string) {
  if (status === "APPROVED") return styles.pillGreen;
  if (status === "REJECTED") return styles.pillRed;
  return styles.pillGray;
}

// ─── Theme ────────────────────────────────────────────────────────────────────

const C = {
  bg: "#06111c",
  surface: "#0d1a29",
  card: "#122438",
  cardAlt: "#0f1e30",
  border: "#1a3048",
  accent: "#7ad2ff",
  accentDark: "#04131d",
  text: "#f4f7fb",
  muted: "#7a9db8",
  warn: "#ffd58e",
  danger: "#ff6b6b",
  green: "#4ade80",
  orange: "#fb923c"
};

// ─── Styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: C.bg },
  header: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", paddingHorizontal: 20, paddingVertical: 14, backgroundColor: C.surface, borderBottomWidth: 1, borderBottomColor: C.border },
  headerTitle: { color: C.accent, fontSize: 18, fontWeight: "800", letterSpacing: 0.5 },
  headerSession: { flexDirection: "row", alignItems: "center", gap: 8 },
  headerSessionText: { color: C.muted, fontSize: 13 },
  onlineDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: C.green },
  offlineDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: C.danger, marginLeft: 8 },

  tabContent: { padding: 16, gap: 16, paddingBottom: 32 },

  card: { backgroundColor: C.card, borderRadius: 20, padding: 18, gap: 12 },
  cardTitle: { color: C.text, fontSize: 17, fontWeight: "700" },

  row: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: 12 },

  offlineBanner: { backgroundColor: "#1a1200", borderRadius: 14, padding: 12, borderLeftWidth: 3, borderLeftColor: C.warn },
  offlineBannerText: { color: C.warn, fontSize: 13 },
  statusBanner: { backgroundColor: "#0e2236", borderRadius: 14, padding: 14, borderLeftWidth: 3, borderLeftColor: C.accent },
  statusBannerText: { color: C.warn, fontSize: 14 },

  loadingOverlay: { ...StyleSheet.absoluteFillObject, backgroundColor: "rgba(6,17,28,0.85)", alignItems: "center", justifyContent: "center", gap: 12, zIndex: 99 },
  loadingText: { color: C.muted, fontSize: 14 },

  skeleton: { opacity: 0.4 },
  skeletonLine: { height: 14, borderRadius: 7, backgroundColor: C.border, width: "100%", marginBottom: 6 },

  primaryText: { color: C.text, fontSize: 15, fontWeight: "600" },
  mutedText: { color: C.muted, fontSize: 13, lineHeight: 18 },
  warningText: { color: C.warn, fontSize: 13 },
  timeText: { color: C.muted, fontSize: 11, marginTop: 2 },

  primaryButton: { backgroundColor: C.accent, borderRadius: 14, paddingHorizontal: 18, paddingVertical: 10, minWidth: 80, alignItems: "center" },
  primaryButtonText: { color: C.accentDark, fontWeight: "800", fontSize: 14 },
  dangerButton: { backgroundColor: "#2d1a1a", borderRadius: 14, paddingHorizontal: 14, paddingVertical: 10, borderWidth: 1, borderColor: "#5a2020" },
  dangerButtonText: { color: C.danger, fontWeight: "700", fontSize: 13 },
  refreshButton: { alignSelf: "flex-start", borderRadius: 12, paddingHorizontal: 14, paddingVertical: 8, backgroundColor: C.cardAlt, borderWidth: 1, borderColor: C.border, minWidth: 100, alignItems: "center" },
  refreshButtonText: { color: C.accent, fontSize: 13, fontWeight: "600" },

  badge: { borderRadius: 999, paddingHorizontal: 12, paddingVertical: 6, backgroundColor: "#163b2b" },
  badgeGreen: { backgroundColor: "#163b2b" },
  badgeGray: { backgroundColor: "#1a2e3d" },
  badgeText: { color: C.green, fontWeight: "700", fontSize: 12 },

  grid2: { flexDirection: "row", flexWrap: "wrap", gap: 12 },

  actionCard: { flex: 1, minHeight: 80, borderRadius: 16, backgroundColor: "#1d3954", padding: 14, justifyContent: "center", alignItems: "center" },
  actionCardDanger: { backgroundColor: "#2d1010" },
  actionCardDisabled: { backgroundColor: "#111e2b", opacity: 0.5 },
  actionText: { color: C.text, fontSize: 14, fontWeight: "700", textAlign: "center" },
  actionSubtext: { color: C.muted, fontSize: 11, marginTop: 4, textAlign: "center" },

  quickCard: { width: "47%", minHeight: 90, borderRadius: 18, backgroundColor: "#0f1e30", padding: 16, justifyContent: "center", alignItems: "center", borderWidth: 1, borderColor: C.border },
  quickIcon: { fontSize: 24, marginBottom: 6 },

  offlineCard: { borderWidth: 1, borderColor: C.warn },
  otCard: { borderWidth: 1, borderColor: C.orange },
  otHours: { color: C.orange, fontSize: 36, fontWeight: "800" },

  listItem: { backgroundColor: C.cardAlt, borderRadius: 14, padding: 14, gap: 4, borderWidth: 1, borderColor: C.border },
  listItemUnread: { borderColor: C.accent },

  statusPill: { borderRadius: 999, paddingHorizontal: 10, paddingVertical: 4 },
  statusPillText: { fontSize: 11, fontWeight: "700", color: C.text },
  pillGreen: { backgroundColor: "#14532d" },
  pillRed: { backgroundColor: "#450a0a" },
  pillOrange: { backgroundColor: "#431407" },
  pillBlue: { backgroundColor: "#0c2d48" },
  pillGray: { backgroundColor: "#1a2a36" },

  notifType: { color: C.muted, fontSize: 11 },

  tableGrid: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
  tableCard: { width: "30%", minHeight: 72, borderRadius: 14, backgroundColor: "#0f1e30", padding: 12, justifyContent: "center", alignItems: "center", borderWidth: 1, borderColor: C.border },
  tableCardActive: { borderColor: C.accent, backgroundColor: "#0f2a40" },
  tableLabel: { color: C.text, fontSize: 16, fontWeight: "700" },
  tableStatus: { color: C.muted, fontSize: 11, marginTop: 4 },

  menuGrid: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
  menuCard: { width: "47%", borderRadius: 14, backgroundColor: "#0f1e30", padding: 14, borderWidth: 1, borderColor: C.border, gap: 4 },
  menuName: { color: C.text, fontSize: 14, fontWeight: "700" },
  menuPrice: { color: C.accent, fontSize: 16, fontWeight: "800" },
  menuCategory: { color: C.muted, fontSize: 11 },

  cartLine: { flexDirection: "row", alignItems: "center", gap: 12, paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: C.border },
  qtyRow: { flexDirection: "row", alignItems: "center", gap: 10 },
  qtyButton: { width: 32, height: 32, borderRadius: 8, backgroundColor: "#1d3954", alignItems: "center", justifyContent: "center" },
  qtyButtonText: { color: C.text, fontSize: 18, fontWeight: "700" },
  qtyValue: { color: C.text, fontSize: 16, fontWeight: "700", minWidth: 24, textAlign: "center" },
  cartTotal: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", paddingTop: 8 },
  totalAmount: { color: C.accent, fontSize: 24, fontWeight: "800" },
  submitButton: { backgroundColor: C.accent, borderRadius: 16, paddingVertical: 14, alignItems: "center" },
  submitButtonDisabled: { opacity: 0.4 },
  submitButtonText: { color: C.accentDark, fontWeight: "800", fontSize: 16 },
  clearButton: { alignItems: "center", paddingVertical: 8 },
  clearButtonText: { color: C.danger, fontSize: 13 },

  hrActions: { flexDirection: "row", gap: 10, marginTop: 6 },
  hrChip: { borderRadius: 999, paddingHorizontal: 14, paddingVertical: 8, backgroundColor: "#0f2030", borderWidth: 1, borderColor: C.border },
  hrChipText: { color: C.accent, fontSize: 12, fontWeight: "700" },

  bubble: { maxWidth: "80%", borderRadius: 16, padding: 12, marginBottom: 8, gap: 2 },
  bubbleMe: { alignSelf: "flex-end", backgroundColor: "#0f3450" },
  bubbleThem: { alignSelf: "flex-start", backgroundColor: C.cardAlt },
  bubbleSender: { color: C.accent, fontSize: 11, fontWeight: "700" },
  bubbleText: { color: C.text, fontSize: 14 },
  bubbleMeta: { color: C.muted, fontSize: 11 },
  selectedTableBadge: { alignSelf: "flex-start", borderRadius: 999, paddingHorizontal: 12, paddingVertical: 6, backgroundColor: "#0f2030", borderWidth: 1, borderColor: C.accent },
  selectedTableText: { color: C.accent, fontSize: 12, fontWeight: "700" },

  composer: { flexDirection: "row", padding: 12, gap: 10, backgroundColor: C.surface, borderTopWidth: 1, borderTopColor: C.border, alignItems: "flex-end" },
  chatInput: { flex: 1, backgroundColor: C.card, borderRadius: 16, paddingHorizontal: 16, paddingVertical: 12, color: C.text, fontSize: 15, maxHeight: 100, borderWidth: 1, borderColor: C.border },
  sendButton: { backgroundColor: C.accent, borderRadius: 14, paddingHorizontal: 18, paddingVertical: 12, minWidth: 60, alignItems: "center" },
  sendButtonDisabled: { opacity: 0.4 },
  sendButtonText: { color: C.accentDark, fontWeight: "800", fontSize: 14 },

  tabBar: { flexDirection: "row", backgroundColor: C.surface, borderTopWidth: 1, borderTopColor: C.border, paddingBottom: 4 },
  tabItem: { flex: 1, alignItems: "center", paddingTop: 10, paddingBottom: 6, position: "relative" },
  tabIconWrap: { position: "relative" },
  tabIcon: { fontSize: 22 },
  tabLabel: { color: C.muted, fontSize: 10, marginTop: 3 },
  tabLabelActive: { color: C.accent, fontWeight: "700" },
  tabActiveBar: { position: "absolute", top: 0, left: "25%", right: "25%", height: 2, backgroundColor: C.accent, borderRadius: 999 },
  tabBadge: { position: "absolute", top: -4, right: -8, backgroundColor: C.danger, borderRadius: 999, minWidth: 16, height: 16, alignItems: "center", justifyContent: "center", paddingHorizontal: 3 },
  tabBadgeText: { color: "#fff", fontSize: 9, fontWeight: "800" }
});
