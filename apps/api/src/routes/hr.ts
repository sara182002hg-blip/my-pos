import type {
  CreateScheduledShiftRequest,
  HrOverviewResponse,
  ReviewHrRequestRequest,
  ScheduledShiftResponse,
  LeaveRequestResponse,
  SwapShiftRequestResponse
} from "@mypos/domain";
import type { FastifyInstance } from "fastify";
import { appRepository } from "../data/app-state";
import { asDownloadFilename, toCsv } from "../lib/csv";
import { requirePermission } from "../lib/guards";

export const registerHrRoutes = async (app: FastifyInstance) => {
  app.get("/api/hr/overview", async (request, reply) => {
    const session = requirePermission(request, reply, "hr.view");

    if (!session) {
      return { message: "Forbidden" };
    }

    const response: HrOverviewResponse = {
      overview: appRepository.getHrOverview()
    };

    return response;
  });

  app.get("/api/hr/export.csv", async (request, reply) => {
    const session = requirePermission(request, reply, "hr.view");

    if (!session) {
      return { message: "Forbidden" };
    }

    const overview = appRepository.getHrOverview();
    const rows = [
      {
        section: "hr_summary",
        generatedAt: overview.generatedAt,
        scheduledStaffToday: overview.summary.scheduledStaffToday,
        pendingLeaveRequests: overview.summary.pendingLeaveRequests,
        pendingSwapRequests: overview.summary.pendingSwapRequests,
        approvedLeavesThisWeek: overview.summary.approvedLeavesThisWeek
      },
      ...overview.schedules.map((shift) => ({
        section: "scheduled_shift",
        id: shift.id,
        userId: shift.userId,
        staffName: shift.staffName,
        role: shift.role,
        shiftDate: shift.shiftDate,
        startTime: shift.startTime,
        endTime: shift.endTime,
        zone: shift.zone,
        status: shift.status,
        assignedByName: shift.assignedByName ?? "",
        note: shift.note ?? ""
      })),
      ...overview.leaveRequests.map((request) => ({
        section: "leave_request",
        id: request.id,
        userId: request.userId,
        staffName: request.staffName,
        leaveDate: request.leaveDate,
        leaveType: request.leaveType,
        reason: request.reason,
        status: request.status,
        requestedAt: request.requestedAt,
        reviewerName: request.reviewerName ?? "",
        reviewedAt: request.reviewedAt ?? "",
        coverStaffUserId: request.coverStaffUserId ?? "",
        coverStaffName: request.coverStaffName ?? ""
      })),
      ...overview.swapRequests.map((request) => ({
        section: "swap_request",
        id: request.id,
        shiftId: request.shiftId,
        requesterUserId: request.requesterUserId,
        requesterName: request.requesterName,
        targetUserId: request.targetUserId ?? "",
        targetStaffName: request.targetStaffName ?? "",
        shiftDate: request.shiftDate,
        reason: request.reason,
        status: request.status,
        requestedAt: request.requestedAt,
        reviewerName: request.reviewerName ?? "",
        reviewedAt: request.reviewedAt ?? ""
      }))
    ];

    reply.header("content-type", "text/csv; charset=utf-8");
    reply.header("content-disposition", `attachment; filename="${asDownloadFilename("hr-desk")}"`);
    return toCsv(rows);
  });

  app.get("/api/hr/payroll/export.csv", async (request, reply) => {
    const session = requirePermission(request, reply, "hr.view");

    if (!session) {
      return { message: "Forbidden" };
    }

    const rows = appRepository.getShiftSessions().map((shift) => {
      const checkIn = new Date(shift.checkInAt).getTime();
      const checkOut = shift.checkOutAt
        ? new Date(shift.checkOutAt).getTime()
        : shift.sessionActive
          ? Date.now()
          : checkIn;
      const hoursWorked = Math.max((checkOut - checkIn) / (1000 * 60 * 60), 0);
      const regularHours = Math.min(hoursWorked, 8);
      const otHours = Math.max(hoursWorked - 8, 0);

      return {
        shiftId: shift.id,
        staffName: shift.staffName,
        role: shift.role,
        geofenceStatus: shift.geofenceStatus,
        sessionActive: shift.sessionActive ? "YES" : "NO",
        checkInAt: shift.checkInAt,
        checkOutAt: shift.checkOutAt ?? "",
        regularHours: regularHours.toFixed(2),
        otHours: otHours.toFixed(2),
        totalHours: hoursWorked.toFixed(2),
        ordersHandled: shift.ordersHandled,
        tipAmount: shift.tipAmount.toFixed(2),
        distanceMeters: shift.distanceMeters ?? "",
        deviceId: shift.deviceId,
        ipAddress: shift.ipAddress ?? ""
      };
    });

    reply.header("content-type", "text/csv; charset=utf-8");
    reply.header("content-disposition", `attachment; filename="${asDownloadFilename("payroll")}"`);
    return toCsv(rows);
  });

  app.post<{ Body: CreateScheduledShiftRequest }>("/api/hr/schedules", async (request, reply) => {
    const session = requirePermission(request, reply, "hr.view");

    if (!session) {
      return { message: "Forbidden" };
    }

    const shift = appRepository.createScheduledShift(request.body, {
      id: session.user.id,
      displayName: session.user.displayName,
      role: session.user.role
    });

    if (!shift) {
      reply.status(400);
      return { message: "Could not create shift" };
    }

    const response: ScheduledShiftResponse = {
      shift
    };

    return response;
  });

  app.post<{ Params: { requestId: string }; Body: ReviewHrRequestRequest }>(
    "/api/hr/leave-requests/:requestId",
    async (request, reply) => {
      const session = requirePermission(request, reply, "hr.view");

      if (!session) {
        return { message: "Forbidden" };
      }

      const hrRequest = appRepository.reviewLeaveRequest(request.params.requestId, request.body, {
        id: session.user.id,
        displayName: session.user.displayName,
        role: session.user.role
      });

      if (!hrRequest) {
        reply.status(404);
        return { message: "Leave request not found" };
      }

      const response: LeaveRequestResponse = {
        request: hrRequest
      };

      return response;
    }
  );

  app.post<{ Params: { requestId: string }; Body: ReviewHrRequestRequest }>(
    "/api/hr/swap-requests/:requestId",
    async (request, reply) => {
      const session = requirePermission(request, reply, "hr.view");

      if (!session) {
        return { message: "Forbidden" };
      }

      const hrRequest = appRepository.reviewSwapRequest(request.params.requestId, request.body, {
        id: session.user.id,
        displayName: session.user.displayName,
        role: session.user.role
      });

      if (!hrRequest) {
        reply.status(404);
        return { message: "Swap request not found" };
      }

      const response: SwapShiftRequestResponse = {
        request: hrRequest
      };

      return response;
    }
  );
};
