import Link from "next/link";

const demoTables = ["T1", "T2", "T3", "T4"];

export default function HomePage() {
  return (
    <main className="qr-page">
      <section className="hero-card">
        <p className="eyebrow">MyPOS QR Ordering</p>
        <h1>Scan and order from your table</h1>
        <p className="subtitle">เปิดเมนูจาก QR, ส่งออเดอร์เข้าร้านทันที, และขอเช็คบิลได้จากมือถือ</p>
        <p className="status-line">Production demo path: /table/[tableId]</p>
      </section>

      <section className="panel">
        <div className="panel-head">
          <div>
            <p className="eyebrow">Demo Tables</p>
            <h2>Open a QR session</h2>
          </div>
        </div>
        <div className="menu-grid">
          {demoTables.map((tableId) => (
            <Link className="menu-card" key={tableId} href={`/table/${tableId}`}>
              <strong>Table {tableId}</strong>
              <span>Open guest menu</span>
              <small>Tap to order</small>
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}
