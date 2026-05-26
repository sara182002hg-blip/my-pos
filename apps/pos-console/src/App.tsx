import { useState } from "react";
import { AppProvider, useApp, modules } from "./context/AppContext";
import { FloorPanel } from "./panels/FloorPanel";
import { PaymentsPanel } from "./panels/PaymentsPanel";
import { MenuPanel } from "./panels/MenuPanel";
import { DeliveryPanel } from "./panels/DeliveryPanel";
import { BackofficePanel } from "./panels/BackofficePanel";
import { HRPanel } from "./panels/HRPanel";
import { SecurityPanel } from "./panels/SecurityPanel";
import { SettingsPanel } from "./panels/SettingsPanel";

export default function App() {
  return (
    <AppProvider>
      <AppShell />
    </AppProvider>
  );
}

function AppShell() {
  const [activeTab, setActiveTab] = useState(modules[0]);
  const {
    overview, connectionState, lastHeartbeat, operationState,
    session, permissions, mfaChallenge, mfaCode, setMfaCode, busyAction,
    loginAs, verifyTwoFactor, logout, resetDemo, createSampleOrder
  } = useApp();

  return (
    <main className="console-page">
      <section className="hero">
        <div>
          <p className="eyebrow">MyPOS Console</p>
          <h1>ร้านเดียววันนี้ หลายสาขาพรุ่งนี้ ใช้โครงสร้างเดียวกันได้เลย</h1>
          <p className="hero-copy">
            คอนโซลหลักรวม POS, QR ordering, delivery aggregation, reporting และ security
            โดยออกแบบให้ต่อ kiosk, staff mobile, kitchen display และระบบหลังบ้านได้บน domain เดียวกัน
          </p>
        </div>
        <div className="hero-panel">
          <span className="live-dot" />
          <strong>Live Operations Snapshot</strong>
          <p>
            {connectionState}
            {lastHeartbeat ? ` · heartbeat ${new Date(lastHeartbeat).toLocaleTimeString("th-TH")}` : ""}
          </p>
          <p className="status-copy">{operationState}</p>
        </div>
      </section>

      <section className="auth-strip">
        <article className="auth-card">
          <div>
            <p className="panel-kicker">Session</p>
            <h2>{session ? session.user.displayName : "No active operator session"}</h2>
            <p>
              {session
                ? `${session.user.role} · ${permissions.length} permissions · expires ${new Date(session.expiresAt).toLocaleTimeString("th-TH")}`
                : "Use a demo role to unlock order creation and payment actions"}
            </p>
          </div>
          <div className="auth-actions">
            <button type="button" disabled={busyAction === "login:owner01"} onClick={() => loginAs("owner01", "9999")}>
              Login Owner
            </button>
            <button type="button" disabled={busyAction === "login:cashier01"} onClick={() => loginAs("cashier01", "1234")}>
              Login Cashier
            </button>
            <button type="button" disabled={busyAction === "login:manager01"} onClick={() => loginAs("manager01", "5678")}>
              Login Manager
            </button>
            <button type="button" disabled={busyAction === "create-order"} onClick={createSampleOrder}>
              Create Sample Order
            </button>
            {permissions.includes("system.manage") ? (
              <button type="button" disabled={busyAction === "reset-demo"} onClick={resetDemo}>
                Reset Demo
              </button>
            ) : null}
            <button type="button" disabled={busyAction === "logout" || !session} onClick={logout}>
              Logout
            </button>
          </div>
        </article>
        {mfaChallenge ? (
          <article className="auth-card">
            <div>
              <p className="panel-kicker">Two-Factor Login</p>
              <h2>{mfaChallenge.role} challenge pending</h2>
              <p>
                Demo code {mfaChallenge.demoCode} · expires{" "}
                {new Date(mfaChallenge.expiresAt).toLocaleTimeString("th-TH")}
              </p>
            </div>
            <div className="auth-actions auth-actions-mfa">
              <input
                value={mfaCode}
                onChange={(e) => setMfaCode(e.target.value)}
                placeholder="Enter 6-digit code"
              />
              <button type="button" disabled={busyAction === "verify-2fa"} onClick={verifyTwoFactor}>
                Verify 2FA
              </button>
            </div>
          </article>
        ) : null}
      </section>

      <section className="metrics-grid">
        {overview.metrics.map((metric) => (
          <article className="metric-card" key={metric.label}>
            <p>{metric.label}</p>
            <strong>{metric.value}</strong>
            <span>{metric.delta}</span>
          </article>
        ))}
      </section>

      <section className="module-strip">
        {modules.map((module) => (
          <button
            key={module}
            type="button"
            className={`module-pill ${activeTab === module ? "is-active" : ""}`}
            onClick={() => setActiveTab(module)}
          >
            {module}
          </button>
        ))}
      </section>

      <section className="content-grid">
        {activeTab === "Service Floor" && <FloorPanel />}
        {activeTab === "Payments" && <PaymentsPanel />}
        {activeTab === "Menu Hub" && <MenuPanel />}
        {activeTab === "Delivery Center" && <DeliveryPanel />}
        {activeTab === "Backoffice" && <BackofficePanel />}
        {activeTab === "HR" && <HRPanel />}
        {activeTab === "Security" && <SecurityPanel />}
        {activeTab === "Settings" && <SettingsPanel />}
      </section>
    </main>
  );
}
