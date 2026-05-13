import { useRef } from "react";
import type { DiningTable } from "@mypos/domain";
import { useApp, formatCurrency, paymentMethodOptions, statusTone } from "../context/AppContext";

export function FloorPanel() {
  const {
    overview, session, busyAction, permissions,
    selectedTable, selectedOrder, selectedTableId, setSelectedTableId,
    selectedOrderId, setSelectedOrderId,
    splitCount, setSplitCount, paymentTip, setPaymentTip,
    paymentMethod, setPaymentMethod, splitGuestMethods, setSplitGuestMethods,
    splitGuestCount, splitPaymentsPreview,
    reservationForm, setReservationForm,
    paymentSessions,
    downloadCsv, settleOrder, createPaymentSession, splitSettleOrder, voidOrder,
    capturePaymentSession, retryPaymentSession,
    reserveSelectedTable, clearSelectedReservation,
    updateTableLayout
  } = useApp();

  const floorplanRef = useRef<HTMLDivElement | null>(null);

  const handleTableDragEnd = async (table: DiningTable, clientX: number, clientY: number) => {
    const board = floorplanRef.current;
    if (!board || clientX === 0 || clientY === 0) return;
    const rect = board.getBoundingClientRect();
    const nextX = ((clientX - rect.left) / rect.width) * 100 - table.layout.width / 2;
    const nextY = ((clientY - rect.top) / rect.height) * 100 - table.layout.height / 2;
    await updateTableLayout(table, nextX, nextY);
  };

  return (
    <>
      <article className="panel wide">
        <header className="panel-header">
          <div>
            <p className="panel-kicker">Floorplan &amp; Orders</p>
            <h2>โต๊ะและออเดอร์แบบเรียลไทม์</h2>
          </div>
          <div className="panel-actions">
            <button
              type="button"
              disabled={!session || busyAction === "export-tables"}
              onClick={() => downloadCsv("/api/tables/export.csv", "tables.csv", "export-tables")}
            >
              Export Tables CSV
            </button>
            <button
              type="button"
              disabled={!session || busyAction === "export-orders"}
              onClick={() => downloadCsv("/api/orders/export.csv", "orders.csv", "export-orders")}
            >
              Export Orders CSV
            </button>
            <button
              type="button"
              disabled={!session || busyAction === "export-kitchen"}
              onClick={() => downloadCsv("/api/kitchen/export.csv", "kitchen.csv", "export-kitchen")}
            >
              Export Kitchen CSV
            </button>
            <button type="button" onClick={() => setSelectedTableId(overview.tables[0]?.id ?? "T1")}>
              Reset Focus
            </button>
          </div>
        </header>

        <div className="floorplan-board" ref={floorplanRef}>
          {overview.tables.map((table) => (
            <button
              className={`floorplan-table tone-${statusTone[table.status]} ${
                selectedTable?.id === table.id ? "is-selected" : ""
              }`}
              draggable={Boolean(session)}
              key={table.id}
              type="button"
              style={{
                left: `${table.layout.x}%`,
                top: `${table.layout.y}%`,
                width: `${table.layout.width}%`,
                height: `${table.layout.height}%`
              }}
              onClick={() => setSelectedTableId(table.id)}
              onDragEnd={(event) => { void handleTableDragEnd(table, event.clientX, event.clientY); }}
            >
              <div className="table-top">
                <strong>{table.label}</strong>
                <span>{table.zone}</span>
              </div>
              <p>{table.seats} seats</p>
              <p>{table.occupiedMinutes} min occupied</p>
              <p>THB {table.currentAmount.toLocaleString()}</p>
              <small>
                {table.reservation
                  ? `${table.reservation.guestName} reserved`
                  : table.qrLocked
                  ? "QR locked"
                  : table.status}
              </small>
            </button>
          ))}
        </div>

        <div className="reservation-grid">
          <div className="reservation-card">
            <p className="panel-kicker">Selected Table</p>
            <h3>{selectedTable ? `${selectedTable.label} · ${selectedTable.zone}` : "No table selected"}</h3>
            {selectedTable ? (
              <>
                <p>{selectedTable.seats} seats · {selectedTable.status}</p>
                <p>Layout {Math.round(selectedTable.layout.x)}, {Math.round(selectedTable.layout.y)}</p>
              </>
            ) : null}
          </div>
          <div className="reservation-card">
            <p className="panel-kicker">Reservation</p>
            <div className="form-grid">
              <label>
                <span>Guest name</span>
                <input
                  value={reservationForm.guestName}
                  onChange={(e) => setReservationForm((cur) => ({ ...cur, guestName: e.target.value }))}
                />
              </label>
              <label>
                <span>Reserved at</span>
                <input
                  type="datetime-local"
                  value={reservationForm.reservedAt}
                  onChange={(e) => setReservationForm((cur) => ({ ...cur, reservedAt: e.target.value }))}
                />
              </label>
              <label>
                <span>Party size</span>
                <input
                  type="number"
                  min={1}
                  value={reservationForm.partySize}
                  onChange={(e) =>
                    setReservationForm((cur) => ({ ...cur, partySize: Number(e.target.value || cur.partySize) }))
                  }
                />
              </label>
              <label>
                <span>Phone</span>
                <input
                  value={reservationForm.contactPhone}
                  onChange={(e) => setReservationForm((cur) => ({ ...cur, contactPhone: e.target.value }))}
                />
              </label>
              <label className="full-width">
                <span>Note</span>
                <textarea
                  value={reservationForm.note}
                  onChange={(e) => setReservationForm((cur) => ({ ...cur, note: e.target.value }))}
                />
              </label>
            </div>
            <div className="platform-actions">
              <button
                type="button"
                disabled={!selectedTable || busyAction === `reserve:${selectedTable?.id}`}
                onClick={reserveSelectedTable}
              >
                Save Reservation
              </button>
              <button
                type="button"
                disabled={!selectedTable || busyAction === `clear-reservation:${selectedTable?.id}`}
                onClick={clearSelectedReservation}
              >
                Clear Reservation
              </button>
            </div>
          </div>
        </div>

        <div className="platform-actions">
          <label>
            <span>Split guests</span>
            <input type="number" min={2} max={8} value={splitCount} onChange={(e) => setSplitCount(e.target.value)} />
          </label>
          <label>
            <span>Tip</span>
            <input type="number" min={0} step="0.01" value={paymentTip} onChange={(e) => setPaymentTip(e.target.value)} />
          </label>
          <label>
            <span>Default Method</span>
            <select value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value as typeof paymentMethod)}>
              {paymentMethodOptions.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </label>
          <p className="hint-copy">
            Selected order: {selectedOrder ? selectedOrder.id : "None"} · split preview for {splitGuestCount} guests
            {Number(paymentTip || "0") > 0 ? ` · tip ${formatCurrency(Number(paymentTip || "0"))}` : ""}
          </p>
        </div>

        {selectedOrder ? (
          <div className="security-list">
            {splitPaymentsPreview.map((payment, index) => (
              <div className="report-row" key={`${selectedOrder.id}-split-${index}`}>
                <div>
                  <strong>{payment.guestLabel}</strong>
                  <p>
                    Base {formatCurrency(payment.amount)}
                    {payment.tipAmount > 0 ? ` · tip ${formatCurrency(payment.tipAmount)}` : ""}
                  </p>
                </div>
                <select
                  value={payment.method}
                  onChange={(e) =>
                    setSplitGuestMethods((cur) =>
                      cur.map((m, mi) => (mi === index ? (e.target.value as typeof paymentMethod) : m))
                    )
                  }
                >
                  {paymentMethodOptions.map((o) => (
                    <option key={`${payment.guestLabel}-${o.value}`} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
            ))}
          </div>
        ) : null}

        <div className="tickets">
          {overview.orders.map((order) => (
            <div
              className={`ticket-card ${selectedOrder?.id === order.id ? "is-selected" : ""}`}
              key={order.id}
              onClick={() => setSelectedOrderId(order.id)}
            >
              <div className="ticket-head">
                <strong>{order.tableLabel}</strong>
                <span>{order.priority}</span>
              </div>
              <p>{order.waiterName} · {order.guests} guests</p>
              {order.memberName ? <p>Member · {order.memberName}</p> : null}
              <ul>
                {order.items.map((item) => (
                  <li key={item.id}>{item.name} x{item.quantity}</li>
                ))}
              </ul>
              <footer>
                <span>{order.status}</span>
                <div className="ticket-actions">
                  <strong>
                    {formatCurrency(order.totalAmount)}
                    {order.id === selectedOrder?.id ? ` · split ${splitCount}` : ""}
                    {order.id === selectedOrder?.id && Number(paymentTip || "0") > 0
                      ? ` · tip ${formatCurrency(Number(paymentTip || "0"))}`
                      : ""}
                  </strong>
                  {order.status !== "PAID" ? (
                    <>
                      <button
                        type="button"
                        disabled={busyAction === `pay:${order.id}`}
                        onClick={() => settleOrder(order.id, order.totalAmount)}
                      >
                        Pay {paymentMethodOptions.find((o) => o.value === paymentMethod)?.label ?? paymentMethod}
                      </button>
                      <button
                        type="button"
                        disabled={paymentMethod === "CASH" || busyAction === `payment-session:${order.id}`}
                        onClick={() => createPaymentSession(order.id, order.totalAmount)}
                      >
                        Create Gateway Session
                      </button>
                      <button
                        type="button"
                        disabled={busyAction === `split-pay:${order.id}`}
                        onClick={() => splitSettleOrder(order.id, order.totalAmount, Number(splitCount))}
                      >
                        Split Bill
                      </button>
                      {permissions.includes("receipts.void") ? (
                        <button
                          type="button"
                          disabled={busyAction === `void:${order.id}`}
                          onClick={() => voidOrder(order.id)}
                        >
                          Void
                        </button>
                      ) : null}
                    </>
                  ) : null}
                </div>
              </footer>
            </div>
          ))}
        </div>
      </article>

      <article className="panel">
        <header className="panel-header">
          <div>
            <p className="panel-kicker">Gateway Sessions</p>
            <h2>PromptPay และ checkout sessions</h2>
          </div>
        </header>
        <div className="panel-chips">
          <div className="report-chip">
            <span>Pending</span>
            <strong>{paymentSessions.filter((s) => s.status === "PENDING").length}</strong>
          </div>
          <div className="report-chip">
            <span>Captured</span>
            <strong>{paymentSessions.filter((s) => s.status === "CAPTURED").length}</strong>
          </div>
          <div className="report-chip">
            <span>Failed</span>
            <strong>{paymentSessions.filter((s) => s.status === "FAILED").length}</strong>
          </div>
          <div className="report-chip">
            <span>Expired</span>
            <strong>{paymentSessions.filter((s) => s.status === "EXPIRED").length}</strong>
          </div>
        </div>
        <div className="security-list">
          {paymentSessions.length ? (
            paymentSessions.slice(0, 8).map((gs) => (
              <div className="security-item" key={gs.id}>
                <div>
                  <strong>{gs.method} · {gs.status}</strong>
                  <p>
                    {gs.orderId} · {gs.tableLabel} · {formatCurrency(gs.amount)}
                    {gs.tipAmount ? ` + tip ${formatCurrency(gs.tipAmount)}` : ""}
                  </p>
                  <p>{gs.provider} · ref {gs.reference}</p>
                  {gs.qrPayload ? <p>QR {gs.qrPayload}</p> : null}
                  {gs.checkoutUrl ? <p>{gs.checkoutUrl}</p> : null}
                  <p>
                    Expires {new Date(gs.expiresAt).toLocaleTimeString("th-TH")}
                    {gs.capturedAt ? ` · captured ${new Date(gs.capturedAt).toLocaleTimeString("th-TH")}` : ""}
                  </p>
                  {gs.failureReason ? <p>{gs.failureReason}</p> : null}
                </div>
                {gs.status === "PENDING" ? (
                  <button
                    type="button"
                    disabled={busyAction === `capture-session:${gs.id}`}
                    onClick={() => capturePaymentSession(gs.id)}
                  >
                    Capture
                  </button>
                ) : null}
                {gs.status === "FAILED" || gs.status === "EXPIRED" ? (
                  <button
                    type="button"
                    disabled={busyAction === `retry-session:${gs.id}`}
                    onClick={() => retryPaymentSession(gs.id)}
                  >
                    Retry
                  </button>
                ) : null}
              </div>
            ))
          ) : (
            <p>No gateway sessions yet</p>
          )}
        </div>
      </article>
    </>
  );
}
