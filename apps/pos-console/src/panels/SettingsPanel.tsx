import { useState, useEffect } from "react";
import type { StoreSettings } from "@mypos/domain";
import { useApp } from "../context/AppContext";
import { apiBaseUrl } from "../api";

type Tab = "store" | "payment" | "notification" | "printer";

const TABS: { id: Tab; label: string }[] = [
  { id: "store",        label: "ข้อมูลร้าน" },
  { id: "payment",      label: "การชำระเงิน" },
  { id: "notification", label: "การแจ้งเตือน" },
  { id: "printer",      label: "เครื่องพิมพ์" },
];

const MASKED = "***SET***";

export function SettingsPanel() {
  const { session, permissions } = useApp();
  const canEdit = permissions.includes("system.manage");

  const [tab, setTab] = useState<Tab>("store");
  const [form, setForm] = useState<Partial<StoreSettings>>({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);

  const token = session?.accessToken;

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    fetch(`${apiBaseUrl}/api/settings`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then((r) => r.json())
      .then((data) => setForm(data.settings ?? {}))
      .catch(() => setMessage({ ok: false, text: "โหลดการตั้งค่าไม่สำเร็จ" }))
      .finally(() => setLoading(false));
  }, [token]);

  const set = (key: keyof StoreSettings, value: string) =>
    setForm((cur) => ({ ...cur, [key]: value }));

  const save = async () => {
    if (!token) return;
    setSaving(true);
    setMessage(null);
    try {
      const res = await fetch(`${apiBaseUrl}/api/settings`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify(form)
      });
      const data = await res.json();
      if (res.ok) {
        setForm(data.settings ?? form);
        setMessage({ ok: true, text: "บันทึกการตั้งค่าเรียบร้อยแล้ว" });
      } else {
        setMessage({ ok: false, text: data.message ?? "บันทึกไม่สำเร็จ" });
      }
    } catch {
      setMessage({ ok: false, text: "เกิดข้อผิดพลาด กรุณาลองใหม่" });
    } finally {
      setSaving(false);
    }
  };

  const field = (
    key: keyof StoreSettings,
    label: string,
    opts?: { placeholder?: string; type?: string; hint?: string; rows?: number }
  ) => {
    const isMasked = form[key] === MASKED;
    return (
      <label key={key}>
        <span>{label}{opts?.hint && <small> — {opts.hint}</small>}</span>
        {opts?.rows ? (
          <textarea
            rows={opts.rows}
            disabled={!canEdit}
            placeholder={isMasked ? "●●●●●●●● (ตั้งค่าแล้ว — พิมพ์ทับเพื่อเปลี่ยน)" : opts.placeholder}
            value={isMasked ? "" : (form[key] as string) ?? ""}
            onChange={(e) => set(key, e.target.value)}
          />
        ) : (
          <input
            type={opts?.type ?? "text"}
            disabled={!canEdit}
            placeholder={isMasked ? "●●●●●●●● (ตั้งค่าแล้ว — พิมพ์ทับเพื่อเปลี่ยน)" : opts?.placeholder}
            value={isMasked ? "" : (form[key] as string) ?? ""}
            onChange={(e) => set(key, e.target.value)}
          />
        )}
      </label>
    );
  };

  const select = (
    key: keyof StoreSettings,
    label: string,
    options: { value: string; label: string }[]
  ) => (
    <label key={key}>
      <span>{label}</span>
      <select
        disabled={!canEdit}
        value={(form[key] as string) ?? ""}
        onChange={(e) => set(key, e.target.value)}
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </label>
  );

  if (!session) {
    return (
      <article className="panel">
        <header className="panel-header">
          <div>
            <p className="panel-kicker">Settings</p>
            <h2>ตั้งค่าร้านค้า</h2>
          </div>
        </header>
        <p>กรุณาเข้าสู่ระบบก่อน</p>
      </article>
    );
  }

  if (!canEdit) {
    return (
      <article className="panel">
        <header className="panel-header">
          <div>
            <p className="panel-kicker">Settings</p>
            <h2>ตั้งค่าร้านค้า</h2>
          </div>
        </header>
        <p>เฉพาะ Manager และ Owner เท่านั้นที่สามารถแก้ไขการตั้งค่าได้</p>
      </article>
    );
  }

  return (
    <article className="panel">
      <header className="panel-header">
        <div>
          <p className="panel-kicker">Settings</p>
          <h2>ตั้งค่าร้านค้า</h2>
          <p>แก้ไขข้อมูลร้าน, การชำระเงิน, การแจ้งเตือน และเครื่องพิมพ์</p>
        </div>
        <div className="panel-actions">
          <button type="button" disabled={saving || loading} onClick={save}>
            {saving ? "กำลังบันทึก…" : "บันทึก"}
          </button>
        </div>
      </header>

      {message && (
        <p style={{ color: message.ok ? "green" : "red", marginBottom: "1rem" }}>
          {message.text}
        </p>
      )}

      {loading ? (
        <p>กำลังโหลด…</p>
      ) : (
        <>
          {/* Tab bar */}
          <div className="tab-bar" style={{ display: "flex", gap: "0.5rem", marginBottom: "1.5rem" }}>
            {TABS.map((t) => (
              <button
                key={t.id}
                type="button"
                style={{
                  padding: "0.4rem 1rem",
                  borderRadius: "6px",
                  border: "none",
                  cursor: "pointer",
                  background: tab === t.id ? "#1a1a2e" : "#e5e7eb",
                  color: tab === t.id ? "#fff" : "#374151",
                  fontWeight: tab === t.id ? 600 : 400
                }}
                onClick={() => setTab(t.id)}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* ── ข้อมูลร้าน ── */}
          {tab === "store" && (
            <div className="form-grid">
              {field("storeName",    "ชื่อร้าน",         { placeholder: "เช่น ร้านอาหารไทยรัตนา" })}
              {field("storeAddress", "ที่อยู่",           { placeholder: "เลขที่ ถนน แขวง เขต กรุงเทพฯ", rows: 3 })}
              {field("storeTaxId",   "เลขประจำตัวผู้เสียภาษี", { placeholder: "13 หลัก" })}
              {field("storePhone",   "เบอร์โทรร้าน",     { placeholder: "02-xxx-xxxx" })}
              <hr style={{ gridColumn: "1/-1" }} />
              <p style={{ gridColumn: "1/-1", fontWeight: 600 }}>ข้อความบนใบเสร็จ</p>
              {field("receiptBusinessName",  "ชื่อร้านบนใบเสร็จ",  { placeholder: "MyPOS Night Kitchen" })}
              {field("receiptBranchLabel",   "ชื่อสาขาบนใบเสร็จ",  { placeholder: "Bangkok Riverside Branch" })}
              {field("receiptFooterMessage", "ข้อความท้ายใบเสร็จ", { placeholder: "Thank you and see you again." })}
              {field("receiptContactLine",   "ข้อมูลติดต่อ",        { placeholder: "LINE OA: @mypos · 02-123-4567" })}
            </div>
          )}

          {/* ── การชำระเงิน ── */}
          {tab === "payment" && (
            <div className="form-grid">
              <p style={{ gridColumn: "1/-1", fontWeight: 600 }}>PromptPay</p>
              {field("promptpayMerchantId", "Merchant ID",  { placeholder: "เลขนิติบุคคล / เบอร์โทร" })}
              {field("promptpayPhone",      "เบอร์โทรที่ลงทะเบียน", { placeholder: "0812345678" })}
              <hr style={{ gridColumn: "1/-1" }} />
              <p style={{ gridColumn: "1/-1", fontWeight: 600 }}>Card Gateway</p>
              {select("cardProvider", "ผู้ให้บริการ", [
                { value: "",           label: "— เลือก —" },
                { value: "OMISE_STUB", label: "Omise (ทดสอบ)" },
                { value: "OMISE_REAL", label: "Omise (จริง)" },
                { value: "TWOC2P_STUB", label: "2C2P (ทดสอบ)" },
                { value: "2C2P_REAL",  label: "2C2P (จริง)" },
              ])}
              {field("omisePublicKey",  "Omise Public Key",  { placeholder: "pkey_…" })}
              {field("omiseSecretKey",  "Omise Secret Key",  { placeholder: "skey_…", type: "password" })}
              {field("twoc2pMerchantId", "2C2P Merchant ID", { placeholder: "merchant ID" })}
              {field("twoc2pSecretKey",  "2C2P Secret Key",  { placeholder: "secret key", type: "password" })}
              <hr style={{ gridColumn: "1/-1" }} />
              {field("paymentWebhookSecret", "Payment Webhook Secret", {
                type: "password",
                hint: "รับจาก dashboard ของ payment provider"
              })}
            </div>
          )}

          {/* ── การแจ้งเตือน ── */}
          {tab === "notification" && (
            <div className="form-grid">
              <p style={{ gridColumn: "1/-1", fontWeight: 600 }}>LINE OA (ส่งใบเสร็จ)</p>
              {field("lineChannelAccessToken", "Channel Access Token", {
                type: "password",
                hint: "LINE Developers Console → Messaging API → Channel access token → Issue"
              })}
              <hr style={{ gridColumn: "1/-1" }} />
              <p style={{ gridColumn: "1/-1", fontWeight: 600 }}>Email (SMTP)</p>
              {field("smtpHost", "SMTP Host",     { placeholder: "smtp.gmail.com" })}
              {field("smtpPort", "SMTP Port",     { placeholder: "587" })}
              {field("smtpUser", "SMTP Username", { placeholder: "receipts@yourstore.com" })}
              {field("smtpPass", "SMTP Password", { placeholder: "App Password", type: "password" })}
              {field("smtpFrom", "From Address",  { placeholder: "receipts@yourstore.com" })}
            </div>
          )}

          {/* ── เครื่องพิมพ์ ── */}
          {tab === "printer" && (
            <div className="form-grid">
              {field("printerTcpMap", "Printer Map", {
                placeholder: "main=192.168.1.50:9100,kitchen=192.168.1.51:9100",
                hint: "ชื่อ=IP:port คั่นด้วย comma"
              })}
              {select("printerMode", "Printer Mode", [
                { value: "TEXT",   label: "TEXT (ทั่วไป)" },
                { value: "ESCPOS", label: "ESCPOS (thermal printer)" },
              ])}
            </div>
          )}
        </>
      )}
    </article>
  );
}
