import { useApp } from "../context/AppContext";

export function SecurityPanel() {
  const {
    session, busyAction, managedUsers, securityPolicy,
    securityForm, setSecurityForm,
    adminIpInput, setAdminIpInput,
    receiptTemplateForm, setReceiptTemplateForm,
    downloadCsv, createSecurityUser, updateSecurityUser, forceLogoutUser, saveSecurityPolicy
  } = useApp();

  return (
    <article className="panel">
      <header className="panel-header">
        <div>
          <p className="panel-kicker">Security Admin</p>
          <h2>จัดการบัญชี, block, expiry และ force logout</h2>
        </div>
        <div className="panel-actions">
          <button
            type="button"
            disabled={!session || busyAction === "export-security"}
            onClick={() => downloadCsv("/api/security/export.csv", "security.csv", "export-security")}
          >
            Export Security CSV
          </button>
        </div>
      </header>
      <div className="form-grid">
        <label>
          <span>Username</span>
          <input
            value={securityForm.username}
            onChange={(e) => setSecurityForm((cur) => ({ ...cur, username: e.target.value }))}
          />
        </label>
        <label>
          <span>Display name</span>
          <input
            value={securityForm.displayName}
            onChange={(e) => setSecurityForm((cur) => ({ ...cur, displayName: e.target.value }))}
          />
        </label>
        <label>
          <span>Role</span>
          <input
            value={securityForm.role}
            onChange={(e) => setSecurityForm((cur) => ({ ...cur, role: e.target.value }))}
          />
        </label>
        <label>
          <span>PIN</span>
          <input
            value={securityForm.pin}
            onChange={(e) => setSecurityForm((cur) => ({ ...cur, pin: e.target.value }))}
          />
        </label>
        <label className="full-width">
          <span>Expires at</span>
          <input
            type="datetime-local"
            value={securityForm.expiresAt}
            onChange={(e) => setSecurityForm((cur) => ({ ...cur, expiresAt: e.target.value }))}
          />
        </label>
      </div>
      <div className="platform-actions">
        <button
          type="button"
          disabled={busyAction === "create-security-user"}
          onClick={createSecurityUser}
        >
          Create Account
        </button>
      </div>
      <div className="security-list">
        <p>Security policy</p>
        <div className="report-row">
          <div>
            <strong>Admin IP whitelist</strong>
            <p>
              {securityPolicy
                ? securityPolicy.adminIpWhitelist.join(", ")
                : "Login manager from an allowed IP"}
            </p>
          </div>
        </div>
        <div className="report-row">
          <div>
            <strong>Receipt template</strong>
            <p>
              {securityPolicy
                ? `${securityPolicy.receiptTemplate.businessName} · ${securityPolicy.receiptTemplate.branchLabel}`
                : "Login manager to load receipt branding"}
            </p>
          </div>
        </div>
        <div className="form-grid">
          <label className="full-width">
            <span>Add or replace IP list</span>
            <input value={adminIpInput} onChange={(e) => setAdminIpInput(e.target.value)} />
          </label>
          <label>
            <span>Business name</span>
            <input
              value={receiptTemplateForm.businessName}
              onChange={(e) =>
                setReceiptTemplateForm((cur) => ({ ...cur, businessName: e.target.value }))
              }
            />
          </label>
          <label>
            <span>Branch label</span>
            <input
              value={receiptTemplateForm.branchLabel}
              onChange={(e) =>
                setReceiptTemplateForm((cur) => ({ ...cur, branchLabel: e.target.value }))
              }
            />
          </label>
          <label className="full-width">
            <span>Footer message</span>
            <input
              value={receiptTemplateForm.footerMessage}
              onChange={(e) =>
                setReceiptTemplateForm((cur) => ({ ...cur, footerMessage: e.target.value }))
              }
            />
          </label>
          <label className="full-width">
            <span>Contact line</span>
            <input
              value={receiptTemplateForm.contactLine}
              onChange={(e) =>
                setReceiptTemplateForm((cur) => ({ ...cur, contactLine: e.target.value }))
              }
            />
          </label>
          <label>
            <span>Show QR lookup on print</span>
            <input
              type="checkbox"
              checked={receiptTemplateForm.showQrLookupOnPrint}
              onChange={(e) =>
                setReceiptTemplateForm((cur) => ({ ...cur, showQrLookupOnPrint: e.target.checked }))
              }
            />
          </label>
          <label>
            <span>Show tip line</span>
            <input
              type="checkbox"
              checked={receiptTemplateForm.showTipLine}
              onChange={(e) =>
                setReceiptTemplateForm((cur) => ({ ...cur, showTipLine: e.target.checked }))
              }
            />
          </label>
        </div>
        <div className="platform-actions">
          <button
            type="button"
            disabled={busyAction === "security-policy"}
            onClick={() =>
              saveSecurityPolicy({
                adminIpWhitelist: Array.from(
                  new Set(
                    adminIpInput
                      .split(",")
                      .map((ip) => ip.trim())
                      .filter(Boolean)
                  )
                )
              })
            }
          >
            Save IP Whitelist
          </button>
          <button
            type="button"
            disabled={busyAction === "security-policy"}
            onClick={() => saveSecurityPolicy({ receiptTemplate: receiptTemplateForm })}
          >
            Save Receipt Template
          </button>
          <button
            type="button"
            disabled={busyAction === "security-policy"}
            onClick={() =>
              saveSecurityPolicy({
                twoFactorRoles: securityPolicy?.twoFactorRoles.includes("MANAGER")
                  ? ["OWNER"]
                  : ["OWNER", "MANAGER"]
              })
            }
          >
            {securityPolicy?.twoFactorRoles.includes("MANAGER") ? "2FA Owner Only" : "2FA Owner + Manager"}
          </button>
        </div>
      </div>
      <div className="security-list">
        {managedUsers.length === 0 ? <p>Login manager to manage accounts</p> : null}
        {managedUsers.map((user) => (
          <div className="platform-card" key={user.id}>
            <div className="report-row">
              <div>
                <strong>{user.displayName}</strong>
                <p>
                  {user.username} · {user.role} · {user.accountStatus}
                </p>
              </div>
              <strong>
                {user.expiresAt ? new Date(user.expiresAt).toLocaleDateString("th-TH") : "No expiry"}
              </strong>
            </div>
            <p>
              Last login:{" "}
              {user.lastLoginAt ? new Date(user.lastLoginAt).toLocaleString("th-TH") : "Never"} ·
              Force logout after:{" "}
              {user.forceLogoutAfter
                ? ` ${new Date(user.forceLogoutAfter).toLocaleString("th-TH")}`
                : " not set"}
            </p>
            <div className="platform-actions">
              <button
                type="button"
                disabled={busyAction === `security-user:${user.id}`}
                onClick={() =>
                  updateSecurityUser(user.id, {
                    accountStatus: user.accountStatus === "BLOCKED" ? "ACTIVE" : "BLOCKED"
                  })
                }
              >
                {user.accountStatus === "BLOCKED" ? "Unblock" : "Block"}
              </button>
              <button
                type="button"
                disabled={busyAction === `security-user:${user.id}`}
                onClick={() => updateSecurityUser(user.id, { pin: "0000" })}
              >
                Reset PIN
              </button>
              <button
                type="button"
                disabled={busyAction === `force-logout:${user.id}`}
                onClick={() => forceLogoutUser(user.id)}
              >
                Force Logout
              </button>
            </div>
          </div>
        ))}
      </div>
    </article>
  );
}
