import { useApp, formatCurrency } from "../context/AppContext";

export function PaymentsPanel() {
  const {
    session, busyAction, report, receipts, permissions,
    receiptEmail, setReceiptEmail, receiptLineUserId, setReceiptLineUserId,
    receiptPrinterName, setReceiptPrinterName, taxInvoiceForm, setTaxInvoiceForm,
    etaxSubmitChannel, setEtaxSubmitChannel,
    downloadCsv, capturePaymentSession, retryPaymentSession,
    refundReceipt, shareReceipt, printReceipt, issueTaxInvoice, submitEtax, retryDispatchAttempt
  } = useApp();

  return (
    <>
      <article className="panel">
        <header className="panel-header">
          <div>
            <p className="panel-kicker">Gateway Ops</p>
            <h2>สถานะ payment session และความเสี่ยงค้างจ่าย</h2>
          </div>
          <div className="panel-actions">
            <button
              type="button"
              disabled={!session || busyAction === "export-gateway"}
              onClick={() => downloadCsv("/api/payment-sessions/export.csv", "payment-sessions.csv", "export-gateway")}
            >
              Export CSV
            </button>
          </div>
        </header>
        <div className="report-grid">
          <div className="report-chip">
            <span>Total Sessions</span>
            <strong>{report ? report.gatewayOps.totalSessions : "Login required"}</strong>
          </div>
          <div className="report-chip">
            <span>Pending</span>
            <strong>{report ? report.gatewayOps.pendingCount : "-"}</strong>
          </div>
          <div className="report-chip">
            <span>Captured</span>
            <strong>{report ? report.gatewayOps.capturedCount : "-"}</strong>
          </div>
          <div className="report-chip">
            <span>Failed + Expired</span>
            <strong>{report ? report.gatewayOps.failedCount + report.gatewayOps.expiredCount : "-"}</strong>
          </div>
        </div>
        <div className="security-list">
          <p>Total gateway amount: {report ? formatCurrency(report.gatewayOps.totalAmount) : "-"}</p>
          <p>Pending gateway amount: {report ? formatCurrency(report.gatewayOps.pendingAmount) : "-"}</p>
          <p>Failed sessions: {report ? report.gatewayOps.failedCount : "-"}</p>
          <p>Expired sessions: {report ? report.gatewayOps.expiredCount : "-"}</p>
        </div>
        <div className="security-list">
          {report?.recentGatewaySessions.length ? null : <p>No recent gateway sessions</p>}
          {report?.recentGatewaySessions.map((gs) => (
            <div className="report-row" key={gs.id}>
              <div>
                <strong>{gs.method} · {gs.status}</strong>
                <p>
                  {gs.orderId} · {gs.provider} · {formatCurrency(gs.amount)}
                  {gs.tipAmount ? ` + tip ${formatCurrency(gs.tipAmount)}` : ""}
                  {gs.failureReason ? ` · ${gs.failureReason}` : ""}
                </p>
              </div>
              <span>{new Date(gs.createdAt).toLocaleTimeString("th-TH")}</span>
            </div>
          ))}
        </div>
      </article>

      <article className="panel">
        <header className="panel-header">
          <div>
            <p className="panel-kicker">Receipt Ops</p>
            <h2>สถานะการพิมพ์และการส่งใบเสร็จ</h2>
          </div>
          <div className="panel-actions">
            <button
              type="button"
              disabled={!session || busyAction === "export-receipts"}
              onClick={() => downloadCsv("/api/receipts/export.csv", "receipts.csv", "export-receipts")}
            >
              Export Receipts CSV
            </button>
            <button
              type="button"
              disabled={!session || busyAction === "export-dispatches"}
              onClick={() =>
                downloadCsv("/api/receipts/dispatch-attempts/export.csv", "receipt-dispatches.csv", "export-dispatches")
              }
            >
              Export Dispatch CSV
            </button>
          </div>
        </header>
        <div className="report-grid">
          <div className="report-chip">
            <span>Issued</span>
            <strong>{report ? report.receiptOps.totalIssued : "Login required"}</strong>
          </div>
          <div className="report-chip">
            <span>Printed</span>
            <strong>{report ? report.receiptOps.printedCount : "-"}</strong>
          </div>
          <div className="report-chip">
            <span>Emailed</span>
            <strong>{report ? report.receiptOps.emailedCount : "-"}</strong>
          </div>
          <div className="report-chip">
            <span>LINE Shared</span>
            <strong>{report ? report.receiptOps.lineSharedCount : "-"}</strong>
          </div>
          <div className="report-chip">
            <span>Tax Invoice</span>
            <strong>{report ? report.receiptOps.taxInvoiceCount : "-"}</strong>
          </div>
          <div className="report-chip">
            <span>E-Tax</span>
            <strong>{report ? report.receiptOps.eTaxCount : "-"}</strong>
          </div>
          <div className="report-chip">
            <span>E-Tax Pending</span>
            <strong>{report ? report.receiptOps.pendingETaxSubmissionCount : "-"}</strong>
          </div>
          <div className="report-chip">
            <span>E-Tax Submitted</span>
            <strong>{report ? report.receiptOps.submittedETaxCount : "-"}</strong>
          </div>
        </div>
        <div className="security-list">
          <p>Pending share: {report ? report.receiptOps.pendingShareCount : "-"}</p>
          <p>Pending print: {report ? report.receiptOps.pendingPrintCount : "-"}</p>
        </div>
        <div className="security-list">
          {report?.recentReceiptDispatches.length ? null : <p>No recent dispatch attempts</p>}
          {report?.recentReceiptDispatches.map((attempt) => (
            <div className="report-row" key={attempt.id}>
              <div>
                <strong>{attempt.channel}</strong>
                <p>
                  {attempt.receiptNo} · {attempt.provider} · {attempt.target}
                  {attempt.message ? ` · ${attempt.message}` : ""}
                </p>
              </div>
              <div className="platform-actions">
                <strong>{attempt.status}</strong>
                {attempt.status === "FAILED" ? (
                  <button
                    type="button"
                    disabled={busyAction === `retry-dispatch:${attempt.id}`}
                    onClick={() => retryDispatchAttempt(attempt)}
                  >
                    Retry
                  </button>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      </article>

      <article className="panel">
        <header className="panel-header">
          <div>
            <p className="panel-kicker">Payment Mix</p>
            <h2>การชำระเงินและ traffic รายชั่วโมง</h2>
          </div>
        </header>
        <div className="security-list">
          {report?.paymentMethods.length ? null : <p>Login to load payment mix</p>}
          {report?.paymentMethods.map((method) => (
            <div className="report-row" key={method.method}>
              <div>
                <strong>{method.method}</strong>
                <p>
                  {method.count} receipts · sales {formatCurrency(method.salesAmount)} · tip{" "}
                  {formatCurrency(method.tipAmount)}
                </p>
              </div>
              <strong>{formatCurrency(method.amount)}</strong>
            </div>
          ))}
        </div>
        <div className="chart-stack">
          {report?.hourlySales.length ? null : <p>No hourly sales data yet</p>}
          {report?.hourlySales.map((bucket) => {
            const maxSales = Math.max(...(report.hourlySales.map((item) => item.sales)), 1);
            const width = `${Math.max((bucket.sales / maxSales) * 100, 8)}%`;
            return (
              <div className="bar-row" key={bucket.hour}>
                <span>{bucket.hour}:00</span>
                <div className="bar-track">
                  <div className="bar-fill" style={{ width }} />
                </div>
                <strong>{formatCurrency(bucket.sales)}</strong>
              </div>
            );
          })}
        </div>
      </article>

      <article className="panel">
        <header className="panel-header">
          <div>
            <p className="panel-kicker">Receipts</p>
            <h2>ใบเสร็จล่าสุด</h2>
          </div>
        </header>
        <div className="form-grid">
          <label>
            <span>Receipt email</span>
            <input value={receiptEmail} onChange={(e) => setReceiptEmail(e.target.value)} />
          </label>
          <label>
            <span>LINE user id</span>
            <input value={receiptLineUserId} onChange={(e) => setReceiptLineUserId(e.target.value)} />
          </label>
          <label>
            <span>Printer name</span>
            <input value={receiptPrinterName} onChange={(e) => setReceiptPrinterName(e.target.value)} />
          </label>
          <label>
            <span>Tax document type</span>
            <select
              value={taxInvoiceForm.receiptType}
              onChange={(e) =>
                setTaxInvoiceForm((cur) => ({
                  ...cur,
                  receiptType: e.target.value as typeof taxInvoiceForm.receiptType
                }))
              }
            >
              <option value="TAX_INVOICE">Tax Invoice</option>
              <option value="E_TAX">E-Tax</option>
            </select>
          </label>
          <label>
            <span>Tax payer name</span>
            <input
              value={taxInvoiceForm.taxPayerName}
              onChange={(e) => setTaxInvoiceForm((cur) => ({ ...cur, taxPayerName: e.target.value }))}
            />
          </label>
          <label>
            <span>Tax ID</span>
            <input
              value={taxInvoiceForm.taxId}
              onChange={(e) => setTaxInvoiceForm((cur) => ({ ...cur, taxId: e.target.value }))}
            />
          </label>
          <label className="full-width">
            <span>Branch / address</span>
            <input
              value={taxInvoiceForm.taxBranchAddress ?? ""}
              onChange={(e) => setTaxInvoiceForm((cur) => ({ ...cur, taxBranchAddress: e.target.value }))}
            />
          </label>
          <label>
            <span>E-Tax email</span>
            <input
              value={taxInvoiceForm.taxEmail ?? ""}
              onChange={(e) => setTaxInvoiceForm((cur) => ({ ...cur, taxEmail: e.target.value }))}
            />
          </label>
          <label>
            <span>E-Tax submit channel</span>
            <select
              value={etaxSubmitChannel}
              onChange={(e) => setEtaxSubmitChannel(e.target.value as typeof etaxSubmitChannel)}
            >
              <option value="EMAIL">Email</option>
              <option value="RD_PORTAL">RD Portal</option>
            </select>
          </label>
        </div>
        <div className="security-list">
          {receipts.length === 0 ? <p>No receipts loaded</p> : null}
          {receipts.slice(0, 4).map((receipt) => (
            <div className="report-row" key={receipt.id}>
              <div>
                <strong>{receipt.receiptNo}</strong>
                <p>
                  {receipt.paymentMethod} · {receipt.status ?? "ISSUED"} · {formatCurrency(receipt.totalAmount)}
                  {receipt.tipAmount ? ` · tip ${formatCurrency(receipt.tipAmount)}` : ""}
                  {receipt.splitCount ? ` · split ${receipt.splitIndex}/${receipt.splitCount}` : ""}
                  {receipt.guestLabel ? ` · ${receipt.guestLabel}` : ""}
                  {receipt.email ? ` · email ${receipt.email}` : ""}
                  {receipt.lineUserId ? ` · LINE ${receipt.lineUserId}` : ""}
                  {receipt.emailSharedAt ? ` · emailed ${new Date(receipt.emailSharedAt).toLocaleString("th-TH")}` : ""}
                  {receipt.lineSharedAt ? ` · line sent ${new Date(receipt.lineSharedAt).toLocaleString("th-TH")}` : ""}
                  {receipt.printerName ? ` · printed ${receipt.printerName}` : ""}
                  {receipt.printedAt ? ` · ${new Date(receipt.printedAt).toLocaleString("th-TH")}` : ""}
                  {receipt.taxId ? ` · tax ${receipt.taxId}` : ""}
                  {receipt.taxIssuedAt ? ` · tax issued ${new Date(receipt.taxIssuedAt).toLocaleString("th-TH")}` : ""}
                  {receipt.eTaxStatus ? ` · e-tax ${receipt.eTaxStatus}` : ""}
                  {receipt.eTaxSubmissionReference ? ` · ref ${receipt.eTaxSubmissionReference}` : ""}
                </p>
              </div>
              <div className="platform-actions">
                <button
                  type="button"
                  disabled={busyAction === `print:${receipt.id}`}
                  onClick={() => printReceipt(receipt)}
                >
                  Print
                </button>
                <button
                  type="button"
                  disabled={busyAction === `share:${receipt.id}:EMAIL`}
                  onClick={() => shareReceipt(receipt, "EMAIL")}
                >
                  Send Email
                </button>
                <button
                  type="button"
                  disabled={busyAction === `share:${receipt.id}:LINE`}
                  onClick={() => shareReceipt(receipt, "LINE")}
                >
                  Send LINE
                </button>
                <button
                  type="button"
                  disabled={busyAction === `tax-invoice:${receipt.id}`}
                  onClick={() => issueTaxInvoice(receipt)}
                >
                  {taxInvoiceForm.receiptType === "E_TAX" ? "Issue E-Tax" : "Issue Tax Invoice"}
                </button>
                {receipt.receiptType === "E_TAX" ? (
                  <button
                    type="button"
                    disabled={busyAction === `etax-submit:${receipt.id}`}
                    onClick={() => submitEtax(receipt)}
                  >
                    Submit E-Tax
                  </button>
                ) : null}
                {permissions.includes("receipts.void") && receipt.status !== "REFUNDED" ? (
                  <button
                    type="button"
                    disabled={busyAction === `refund:${receipt.id}`}
                    onClick={() => refundReceipt(receipt)}
                  >
                    Refund
                  </button>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      </article>
    </>
  );
}
