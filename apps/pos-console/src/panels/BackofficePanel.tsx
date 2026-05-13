import { useApp, formatCurrency } from "../context/AppContext";

export function BackofficePanel() {
  const {
    session, busyAction, report, crmOverview, members, selectedOrder, auditEntries, exceptions,
    voidReason, setVoidReason, refundReason, setRefundReason,
    memberForm, setMemberForm,
    downloadCsv, createMember, assignMemberToOrder
  } = useApp();

  return (
    <>
      <article className="panel">
        <header className="panel-header">
          <div>
            <p className="panel-kicker">CRM &amp; Loyalty</p>
            <h2>สมาชิก, แต้มสะสม และลูกค้าประจำ</h2>
          </div>
          <div className="panel-actions">
            <button
              type="button"
              disabled={!session || busyAction === "export-crm"}
              onClick={() => downloadCsv("/api/members/export.csv", "crm-members.csv", "export-crm")}
            >
              Export CRM CSV
            </button>
          </div>
        </header>
        <div className="report-grid">
          <div className="report-chip">
            <span>Total Members</span>
            <strong>{crmOverview ? crmOverview.totalMembers : "-"}</strong>
          </div>
          <div className="report-chip">
            <span>Outstanding Points</span>
            <strong>{crmOverview ? crmOverview.loyaltyOutstandingPoints : "-"}</strong>
          </div>
          <div className="report-chip">
            <span>Active This Month</span>
            <strong>{crmOverview ? crmOverview.activeMembersThisMonth : "-"}</strong>
          </div>
          <div className="report-chip">
            <span>Selected Order</span>
            <strong>{selectedOrder ? selectedOrder.id : "None"}</strong>
          </div>
        </div>
        <div className="form-grid">
          <label>
            <span>Full name</span>
            <input
              value={memberForm.fullName}
              onChange={(e) => setMemberForm((cur) => ({ ...cur, fullName: e.target.value }))}
            />
          </label>
          <label>
            <span>Phone</span>
            <input
              value={memberForm.phone}
              onChange={(e) => setMemberForm((cur) => ({ ...cur, phone: e.target.value }))}
            />
          </label>
          <label>
            <span>Preferred language</span>
            <input
              value={memberForm.preferredLanguage}
              onChange={(e) => setMemberForm((cur) => ({ ...cur, preferredLanguage: e.target.value }))}
            />
          </label>
          <label>
            <span>Birth date</span>
            <input
              type="date"
              value={memberForm.birthDate}
              onChange={(e) => setMemberForm((cur) => ({ ...cur, birthDate: e.target.value }))}
            />
          </label>
          <label className="full-width">
            <span>LINE user ID</span>
            <input
              value={memberForm.lineUserId}
              onChange={(e) => setMemberForm((cur) => ({ ...cur, lineUserId: e.target.value }))}
            />
          </label>
        </div>
        <div className="platform-actions">
          <button type="button" disabled={busyAction === "create-member"} onClick={createMember}>
            Create Member
          </button>
        </div>
        <div className="security-list">
          {members.slice(0, 5).map((member) => (
            <div className="platform-card" key={member.id}>
              <div className="report-row">
                <div>
                  <strong>{member.fullName}</strong>
                  <p>
                    {member.tier} · {member.pointsBalance} pts · {formatCurrency(member.totalSpend)}
                  </p>
                </div>
                <button
                  type="button"
                  disabled={!selectedOrder || busyAction === `assign-member:${selectedOrder?.id}`}
                  onClick={() => assignMemberToOrder(member.id)}
                >
                  Assign To Order
                </button>
              </div>
              {member.favoriteItems.length ? <p>{member.favoriteItems.join(", ")}</p> : null}
            </div>
          ))}
        </div>
        {crmOverview?.birthdayMembers.length ? (
          <div className="security-list">
            <p>Birthday list this month:</p>
            {crmOverview.birthdayMembers.map((member) => (
              <p key={`birthday-${member.id}`}>
                {member.fullName} · {member.birthDate}
              </p>
            ))}
          </div>
        ) : null}
      </article>

      <article className="panel">
        <header className="panel-header">
          <div>
            <p className="panel-kicker">Exception Controls</p>
            <h2>Void และ refund แบบมีเหตุผล</h2>
          </div>
        </header>
        <div className="form-grid">
          <label>
            <span>Void reason</span>
            <input value={voidReason} onChange={(e) => setVoidReason(e.target.value)} />
          </label>
          <label>
            <span>Refund reason</span>
            <input value={refundReason} onChange={(e) => setRefundReason(e.target.value)} />
          </label>
        </div>
        <p className="hint-copy">
          Only manager and owner roles can void open orders or refund closed receipts.
        </p>
      </article>

      <article className="panel">
        <header className="panel-header">
          <div>
            <p className="panel-kicker">Backoffice Summary</p>
            <h2>ยอดขายและสถานะร้านแบบ operational</h2>
          </div>
          <div className="panel-actions">
            <button
              type="button"
              disabled={!session || busyAction === "export-backoffice"}
              onClick={() =>
                downloadCsv("/api/reports/backoffice/export.csv", "backoffice-report.csv", "export-backoffice")
              }
            >
              Export Sales CSV
            </button>
            <button
              type="button"
              disabled={!session || busyAction === "export-audit"}
              onClick={() => downloadCsv("/api/audit/export.csv", "audit-feed.csv", "export-audit")}
            >
              Export Audit CSV
            </button>
          </div>
        </header>
        <div className="report-grid">
          <div className="report-chip">
            <span>Gross Sales</span>
            <strong>{report ? formatCurrency(report.sales.grossSales) : "Login required"}</strong>
          </div>
          <div className="report-chip">
            <span>Paid Orders</span>
            <strong>{report ? report.sales.paidOrders : "-"}</strong>
          </div>
          <div className="report-chip">
            <span>Average Ticket</span>
            <strong>{report ? formatCurrency(report.sales.averageTicket) : "-"}</strong>
          </div>
          <div className="report-chip">
            <span>Pending Tables</span>
            <strong>{report ? report.sales.pendingPaymentTables : "-"}</strong>
          </div>
        </div>
        <div className="security-list">
          <p>Open orders: {report ? report.sales.openOrders : "-"}</p>
          <p>Refunds total: {report ? formatCurrency(report.sales.refundsTotal) : "-"}</p>
          <p>Tips total: {report ? formatCurrency(report.sales.tipsTotal) : "-"}</p>
          <p>Collected total: {report ? formatCurrency(report.sales.collectedTotal) : "-"}</p>
          <p>Voided orders: {report ? report.sales.voidedOrders : "-"}</p>
          <p>Open tables: {report ? report.sales.openTables : "-"}</p>
          <p>Audit events: {report ? report.auditSummary.totalEntries : "-"}</p>
        </div>
      </article>

      <article className="panel">
        <header className="panel-header">
          <div>
            <p className="panel-kicker">Top Items</p>
            <h2>เมนูขายดีที่ควรดันต่อ</h2>
          </div>
        </header>
        <div className="security-list">
          {report?.topItems.length ? null : <p>No item sales yet</p>}
          {report?.topItems.map((item) => (
            <div className="report-row" key={item.menuItemId}>
              <div>
                <strong>{item.name}</strong>
                <p>{item.quantity} qty</p>
              </div>
              <strong>{formatCurrency(item.sales)}</strong>
            </div>
          ))}
        </div>
      </article>

      <article className="panel">
        <header className="panel-header">
          <div>
            <p className="panel-kicker">Audit Trail</p>
            <h2>กิจกรรมล่าสุด</h2>
          </div>
          <div className="panel-actions">
            <button
              type="button"
              disabled={!session || busyAction === "export-staff-notifications"}
              onClick={() =>
                downloadCsv("/api/staff/notifications/export.csv", "staff-notifications.csv", "export-staff-notifications")
              }
            >
              Export Alerts CSV
            </button>
            <button
              type="button"
              disabled={!session || busyAction === "export-kitchen-chat"}
              onClick={() => downloadCsv("/api/staff/chat/export.csv", "kitchen-chat.csv", "export-kitchen-chat")}
            >
              Export Chat CSV
            </button>
          </div>
        </header>
        <div className="security-list">
          {auditEntries.length === 0 ? <p>Login manager to view audit trail</p> : null}
          {auditEntries.slice(0, 5).map((entry) => (
            <p key={entry.id}>
              {entry.actorName} · {entry.action} · {entry.entityType}
            </p>
          ))}
        </div>
      </article>

      <article className="panel">
        <header className="panel-header">
          <div>
            <p className="panel-kicker">Exceptions</p>
            <h2>Void และ refund ล่าสุด</h2>
          </div>
          <div className="panel-actions">
            <button
              type="button"
              disabled={!session || busyAction === "export-exceptions"}
              onClick={() => downloadCsv("/api/exceptions/export.csv", "exceptions.csv", "export-exceptions")}
            >
              Export Exceptions CSV
            </button>
          </div>
        </header>
        <div className="security-list">
          {exceptions.length === 0 ? <p>No exception activity</p> : null}
          {exceptions.slice(0, 5).map((record) => (
            <p key={record.id}>
              {record.kind} · {record.reason} · {record.actorName}
              {record.amount ? ` · ${formatCurrency(record.amount)}` : ""}
            </p>
          ))}
        </div>
      </article>
    </>
  );
}
