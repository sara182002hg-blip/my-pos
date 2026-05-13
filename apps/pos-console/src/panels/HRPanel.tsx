import { useApp, formatCurrency } from "../context/AppContext";

export function HRPanel() {
  const {
    session, busyAction, report, hrOverview, managedUsers, overview,
    scheduleForm, setScheduleForm,
    downloadCsv, createScheduledShift, reviewLeaveRequest, reviewSwapRequest
  } = useApp();

  return (
    <>
      <article className="panel">
        <header className="panel-header">
          <div>
            <p className="panel-kicker">Attendance &amp; Performance</p>
            <h2>กะงาน, ทิป และ geofence</h2>
          </div>
        </header>
        <div className="shift-stack">
          {report?.staffPerformance.length ? (
            report.staffPerformance.map((staff) => (
              <div className="shift-card" key={`${staff.staffName}-${staff.role}`}>
                <div>
                  <strong>{staff.staffName}</strong>
                  <p>{staff.role} · {staff.geofenceStatus}</p>
                </div>
                <div>
                  <strong>{staff.ordersHandled} orders</strong>
                  <p>{formatCurrency(staff.tipAmount)} · {staff.hoursWorked}h</p>
                </div>
              </div>
            ))
          ) : (
            overview.shifts.map((shift) => (
              <div className="shift-card" key={shift.id}>
                <div>
                  <strong>{shift.staffName}</strong>
                  <p>{shift.role}</p>
                </div>
                <div>
                  <strong>{shift.ordersHandled} orders</strong>
                  <p>Tips THB {shift.tipAmount}</p>
                </div>
              </div>
            ))
          )}
        </div>
        {report?.hrRestricted ? (
          <p className="hint-copy">HR metrics are hidden for non-manager roles</p>
        ) : null}
      </article>

      <article className="panel">
        <header className="panel-header">
          <div>
            <p className="panel-kicker">HR Schedule Desk</p>
            <h2>ตารางกะ, คำขอลา และคำขอสลับกะ</h2>
          </div>
          <div className="panel-actions">
            <button
              type="button"
              disabled={!session || busyAction === "export-hr"}
              onClick={() => downloadCsv("/api/hr/export.csv", "hr-desk.csv", "export-hr")}
            >
              Export HR CSV
            </button>
            <button
              type="button"
              disabled={!session || busyAction === "export-payroll"}
              onClick={() => downloadCsv("/api/hr/payroll/export.csv", "payroll.csv", "export-payroll")}
            >
              Export Payroll CSV
            </button>
          </div>
        </header>
        <div className="report-grid">
          <div className="report-chip">
            <span>Scheduled Today</span>
            <strong>{hrOverview ? hrOverview.summary.scheduledStaffToday : "Login required"}</strong>
          </div>
          <div className="report-chip">
            <span>Pending Leave</span>
            <strong>{hrOverview ? hrOverview.summary.pendingLeaveRequests : "-"}</strong>
          </div>
          <div className="report-chip">
            <span>Pending Swap</span>
            <strong>{hrOverview ? hrOverview.summary.pendingSwapRequests : "-"}</strong>
          </div>
          <div className="report-chip">
            <span>Approved Leave 7d</span>
            <strong>{hrOverview ? hrOverview.summary.approvedLeavesThisWeek : "-"}</strong>
          </div>
        </div>
        <div className="form-grid">
          <label>
            <span>Assign to user</span>
            <input
              value={scheduleForm.userId}
              onChange={(e) => setScheduleForm((cur) => ({ ...cur, userId: e.target.value }))}
              list="managed-user-options"
            />
          </label>
          <label>
            <span>Shift role</span>
            <input
              value={scheduleForm.role}
              onChange={(e) =>
                setScheduleForm((cur) => ({
                  ...cur,
                  role: e.target.value as typeof scheduleForm.role
                }))
              }
            />
          </label>
          <label>
            <span>Shift date</span>
            <input
              type="date"
              value={scheduleForm.shiftDate}
              onChange={(e) => setScheduleForm((cur) => ({ ...cur, shiftDate: e.target.value }))}
            />
          </label>
          <label>
            <span>Zone</span>
            <input
              value={scheduleForm.zone}
              onChange={(e) => setScheduleForm((cur) => ({ ...cur, zone: e.target.value }))}
            />
          </label>
          <label>
            <span>Start</span>
            <input
              type="time"
              value={scheduleForm.startTime}
              onChange={(e) => setScheduleForm((cur) => ({ ...cur, startTime: e.target.value }))}
            />
          </label>
          <label>
            <span>End</span>
            <input
              type="time"
              value={scheduleForm.endTime}
              onChange={(e) => setScheduleForm((cur) => ({ ...cur, endTime: e.target.value }))}
            />
          </label>
          <label className="full-width">
            <span>Note</span>
            <input
              value={scheduleForm.note}
              onChange={(e) => setScheduleForm((cur) => ({ ...cur, note: e.target.value }))}
            />
          </label>
        </div>
        <datalist id="managed-user-options">
          {managedUsers.map((user) => (
            <option key={`managed-user-${user.id}`} value={user.id}>
              {user.displayName}
            </option>
          ))}
        </datalist>
        <div className="platform-actions">
          <button type="button" disabled={busyAction === "create-schedule"} onClick={createScheduledShift}>
            Create Shift
          </button>
        </div>
        <div className="security-list">
          <p>Upcoming schedules</p>
          {hrOverview?.schedules.length ? null : <p>No schedules loaded</p>}
          {hrOverview?.schedules.slice(0, 5).map((shift) => (
            <div className="platform-card" key={shift.id}>
              <div className="report-row">
                <div>
                  <strong>{shift.staffName}</strong>
                  <p>
                    {shift.shiftDate} · {shift.startTime}-{shift.endTime} · {shift.zone}
                  </p>
                </div>
                <strong>{shift.status}</strong>
              </div>
              <p>{shift.role}{shift.note ? ` · ${shift.note}` : ""}</p>
            </div>
          ))}
        </div>
        <div className="security-list">
          <p>Leave requests</p>
          {hrOverview?.leaveRequests.length ? null : <p>No leave requests</p>}
          {hrOverview?.leaveRequests.slice(0, 4).map((request) => (
            <div className="platform-card" key={request.id}>
              <div className="report-row">
                <div>
                  <strong>{request.staffName}</strong>
                  <p>
                    {request.leaveDate} · {request.leaveType} · {request.status}
                  </p>
                </div>
                <strong>{new Date(request.requestedAt).toLocaleDateString("th-TH")}</strong>
              </div>
              <p>{request.reason}</p>
              {request.status === "PENDING" ? (
                <div className="platform-actions">
                  <button
                    type="button"
                    disabled={busyAction === `leave-review:${request.id}`}
                    onClick={() => reviewLeaveRequest(request.id, "APPROVED")}
                  >
                    Approve
                  </button>
                  <button
                    type="button"
                    disabled={busyAction === `leave-review:${request.id}`}
                    onClick={() => reviewLeaveRequest(request.id, "REJECTED")}
                  >
                    Reject
                  </button>
                </div>
              ) : null}
            </div>
          ))}
        </div>
        <div className="security-list">
          <p>Swap requests</p>
          {hrOverview?.swapRequests.length ? null : <p>No swap requests</p>}
          {hrOverview?.swapRequests.slice(0, 4).map((request) => (
            <div className="platform-card" key={request.id}>
              <div className="report-row">
                <div>
                  <strong>{request.requesterName}</strong>
                  <p>
                    {request.shiftDate} · target {request.targetStaffName ?? "Open"} · {request.status}
                  </p>
                </div>
                <strong>{new Date(request.requestedAt).toLocaleDateString("th-TH")}</strong>
              </div>
              <p>{request.reason}</p>
              {request.status === "PENDING" ? (
                <div className="platform-actions">
                  <button
                    type="button"
                    disabled={busyAction === `swap-review:${request.id}`}
                    onClick={() => reviewSwapRequest(request.id, "APPROVED")}
                  >
                    Approve
                  </button>
                  <button
                    type="button"
                    disabled={busyAction === `swap-review:${request.id}`}
                    onClick={() => reviewSwapRequest(request.id, "REJECTED")}
                  >
                    Reject
                  </button>
                </div>
              ) : null}
            </div>
          ))}
        </div>
      </article>
    </>
  );
}
