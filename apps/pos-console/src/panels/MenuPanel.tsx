import { useApp, formatCurrency } from "../context/AppContext";

export function MenuPanel() {
  const {
    session, busyAction, overview, inventoryOverview,
    selectedMenuItem, selectedMenuId, setSelectedMenuId,
    menuForm, setMenuForm, inventoryNote, setInventoryNote,
    downloadCsv, createMenuItem, updateMenuItem, recordInventoryMovement
  } = useApp();

  return (
    <>
      <article className="panel">
        <header className="panel-header">
          <div>
            <p className="panel-kicker">Menu Hub</p>
            <h2>เมนูกลางและราคาแบบหลายช่องทาง</h2>
          </div>
          <div className="panel-actions">
            <button
              type="button"
              disabled={!session || busyAction === "export-menu"}
              onClick={() => downloadCsv("/api/menu/export.csv", "menu.csv", "export-menu")}
            >
              Export Menu CSV
            </button>
          </div>
        </header>
        <div className="form-grid">
          <label>
            <span>Name</span>
            <input
              value={menuForm.name}
              onChange={(e) => setMenuForm((cur) => ({ ...cur, name: e.target.value }))}
            />
          </label>
          <label>
            <span>Category</span>
            <input
              value={menuForm.category}
              onChange={(e) => setMenuForm((cur) => ({ ...cur, category: e.target.value }))}
            />
          </label>
          <label>
            <span>Price</span>
            <input
              type="number"
              value={menuForm.price}
              onChange={(e) => setMenuForm((cur) => ({ ...cur, price: e.target.value }))}
            />
          </label>
          <label>
            <span>Happy hour</span>
            <input
              type="number"
              value={menuForm.happyHourPrice}
              onChange={(e) => setMenuForm((cur) => ({ ...cur, happyHourPrice: e.target.value }))}
            />
          </label>
          <label className="full-width">
            <span>Description</span>
            <input
              value={menuForm.description}
              onChange={(e) => setMenuForm((cur) => ({ ...cur, description: e.target.value }))}
            />
          </label>
        </div>
        <div className="platform-actions">
          <button type="button" disabled={busyAction === "create-menu"} onClick={createMenuItem}>
            Create Menu Item
          </button>
          {selectedMenuItem ? (
            <>
              <button
                type="button"
                disabled={busyAction === `menu-update:${selectedMenuItem.id}`}
                onClick={() => updateMenuItem(selectedMenuItem.id, { inStock: !selectedMenuItem.inStock })}
              >
                {selectedMenuItem.inStock ? "Pause Sale" : "Resume Sale"}
              </button>
              <button
                type="button"
                disabled={busyAction === `menu-update:${selectedMenuItem.id}`}
                onClick={() => updateMenuItem(selectedMenuItem.id, { price: selectedMenuItem.price + 10 })}
              >
                Raise Price +10
              </button>
              <button
                type="button"
                disabled={busyAction === `menu-update:${selectedMenuItem.id}`}
                onClick={() => updateMenuItem(selectedMenuItem.id, { happyHourPrice: Math.max(selectedMenuItem.price - 40, 0) })}
              >
                Set Happy Hour
              </button>
            </>
          ) : null}
        </div>
        <div className="menu-stack">
          {overview.menu.map((item) => (
            <div
              className="menu-row"
              key={item.id}
              onClick={() => setSelectedMenuId(item.id)}
              style={{
                cursor: "pointer",
                outline: selectedMenuId === item.id ? "1px solid rgba(255,255,255,0.24)" : "none"
              }}
            >
              <div>
                <strong>{item.name}</strong>
                <p>
                  {item.category}
                  {item.happyHourPrice ? ` · Happy hour ${formatCurrency(item.happyHourPrice)}` : ""}
                </p>
              </div>
              <div className="price-block">
                <strong>THB {item.price}</strong>
                <span>{item.inStock ? "พร้อมขาย" : "หมดชั่วคราว"}</span>
              </div>
            </div>
          ))}
        </div>
      </article>

      <article className="panel">
        <header className="panel-header">
          <div>
            <p className="panel-kicker">Inventory Control</p>
            <h2>สต็อกวัตถุดิบ, low stock และ reorder queue</h2>
          </div>
          <div className="panel-actions">
            <button
              type="button"
              disabled={!session || busyAction === "export-inventory"}
              onClick={() => downloadCsv("/api/inventory/export.csv", "inventory.csv", "export-inventory")}
            >
              Export CSV
            </button>
          </div>
        </header>
        <div className="report-grid">
          <div className="report-chip">
            <span>Stock Value</span>
            <strong>{inventoryOverview ? formatCurrency(inventoryOverview.stockValue) : "Login required"}</strong>
          </div>
          <div className="report-chip">
            <span>Low Stock</span>
            <strong>{inventoryOverview ? inventoryOverview.lowStockCount : "-"}</strong>
          </div>
          <div className="report-chip">
            <span>Out Of Stock</span>
            <strong>{inventoryOverview ? inventoryOverview.outOfStockCount : "-"}</strong>
          </div>
          <div className="report-chip">
            <span>Waste Value</span>
            <strong>{inventoryOverview ? formatCurrency(inventoryOverview.wasteValue) : "-"}</strong>
          </div>
        </div>
        <div className="form-grid">
          <label className="full-width">
            <span>Inventory note</span>
            <input value={inventoryNote} onChange={(e) => setInventoryNote(e.target.value)} />
          </label>
        </div>
        <div className="security-list">
          {inventoryOverview?.items.length ? null : <p>Login to load inventory overview</p>}
          {inventoryOverview?.items.map((item) => (
            <div className="platform-card" key={item.id}>
              <div className="report-row">
                <div>
                  <strong>{item.name}</strong>
                  <p>
                    {item.category} · {item.onHand} {item.unit} on hand · min {item.minLevel}
                  </p>
                </div>
                <strong>{item.status}</strong>
              </div>
              <p>
                Supplier: {item.supplierName ?? "N/A"} · Reorder {item.reorderQty} {item.unit}
              </p>
              {item.linkedMenuItems.length ? <p>Linked menu: {item.linkedMenuItems.join(", ")}</p> : null}
              <div className="platform-actions">
                <button
                  type="button"
                  disabled={busyAction === `inventory:${item.id}:PURCHASE`}
                  onClick={() => recordInventoryMovement(item.id, "PURCHASE", item.reorderQty)}
                >
                  Receive Reorder
                </button>
                <button
                  type="button"
                  disabled={busyAction === `inventory:${item.id}:WASTE`}
                  onClick={() =>
                    recordInventoryMovement(
                      item.id,
                      "WASTE",
                      item.unit === "kg" ? 0.5 : item.unit === "bottle" ? 1 : 2
                    )
                  }
                >
                  Log Waste
                </button>
              </div>
            </div>
          ))}
        </div>
        <div className="security-list">
          <p>Purchase suggestions</p>
          {inventoryOverview?.purchaseSuggestions.length ? null : <p>No reorder suggestions</p>}
          {inventoryOverview?.purchaseSuggestions.map((item) => (
            <div className="report-row" key={`purchase-${item.itemId}`}>
              <div>
                <strong>{item.itemName}</strong>
                <p>{item.supplierName ?? "Preferred supplier not set"}</p>
              </div>
              <strong>{item.reorderQty} {item.unit}</strong>
            </div>
          ))}
        </div>
        <div className="security-list">
          <p>Recent stock movements</p>
          {inventoryOverview?.recentMovements.length ? null : <p>No stock movement recorded yet</p>}
          {inventoryOverview?.recentMovements.map((movement) => (
            <div className="report-row" key={movement.id}>
              <div>
                <strong>{movement.itemName}</strong>
                <p>
                  {movement.type} · {movement.actorName}
                  {movement.note ? ` · ${movement.note}` : ""}
                </p>
              </div>
              <strong>{movement.quantity} {movement.unit}</strong>
            </div>
          ))}
        </div>
      </article>
    </>
  );
}
