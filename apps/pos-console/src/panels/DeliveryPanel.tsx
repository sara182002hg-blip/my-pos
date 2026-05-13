import { useApp, formatCurrency } from "../context/AppContext";

export function DeliveryPanel() {
  const {
    session, busyAction, deliveryCenter,
    downloadCsv, toggleDeliveryPlatform, syncDeliveryMenu
  } = useApp();

  return (
    <article className="panel">
      <header className="panel-header">
        <div>
          <p className="panel-kicker">Delivery Center</p>
          <h2>รวมออเดอร์ delivery และ sync เมนูกลาง</h2>
        </div>
        <div className="panel-actions">
          <button
            type="button"
            disabled={!session || busyAction === "export-delivery"}
            onClick={() => downloadCsv("/api/delivery/export.csv", "delivery-center.csv", "export-delivery")}
          >
            Export Delivery CSV
          </button>
        </div>
      </header>
      <div className="report-grid">
        <div className="report-chip">
          <span>Delivery Sales</span>
          <strong>
            {deliveryCenter ? formatCurrency(deliveryCenter.summary.grossSales) : "Login required"}
          </strong>
        </div>
        <div className="report-chip">
          <span>Commission</span>
          <strong>{deliveryCenter ? formatCurrency(deliveryCenter.summary.commissionTotal) : "-"}</strong>
        </div>
        <div className="report-chip">
          <span>Active Orders</span>
          <strong>{deliveryCenter ? deliveryCenter.summary.activeOrders : "-"}</strong>
        </div>
        <div className="report-chip">
          <span>Avg ETA</span>
          <strong>{deliveryCenter ? `${deliveryCenter.summary.avgEtaMinutes} min` : "-"}</strong>
        </div>
      </div>
      <div className="security-list">
        {deliveryCenter?.platforms.length ? null : <p>Login to load delivery center</p>}
        {deliveryCenter?.platforms.map((platform) => (
          <div className="platform-card" key={platform.platform}>
            <div className="report-row">
              <div>
                <strong>{platform.displayName}</strong>
                <p>
                  {platform.menuSyncState} · {Math.round(platform.commissionRate * 100)}% commission
                </p>
              </div>
              <strong>{platform.enabled ? "Enabled" : "Disabled"}</strong>
            </div>
            <div className="platform-actions">
              <button
                type="button"
                disabled={busyAction === `delivery-toggle:${platform.platform}`}
                onClick={() => toggleDeliveryPlatform(platform.platform, !platform.enabled)}
              >
                {platform.enabled ? "Pause Platform" : "Enable Platform"}
              </button>
              <button
                type="button"
                disabled={busyAction === `delivery-sync:${platform.platform}`}
                onClick={() => syncDeliveryMenu(platform.platform)}
              >
                Sync Menu
              </button>
            </div>
          </div>
        ))}
      </div>
      <div className="security-list">
        {deliveryCenter?.orders.map((order) => (
          <div className="report-row" key={order.id}>
            <div>
              <strong>{order.externalOrderNo}</strong>
              <p>
                {order.platform} · {order.branchStatus} · {order.items.length} items
              </p>
            </div>
            <strong>{formatCurrency(order.totalAmount)}</strong>
          </div>
        ))}
      </div>
    </article>
  );
}
