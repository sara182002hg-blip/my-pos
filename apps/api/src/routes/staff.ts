import type {
  ClockInRequest,
  ClockOutRequest,
  CreateLeaveRequestRequest,
  CreateSwapShiftRequest,
  KitchenChatFeedResponse,
  RequestManagerHelpRequest,
  SendKitchenChatRequest,
  StaffNotificationFeedResponse,
  StaffHrWorkspaceResponse,
  StaffOrdersResponse,
  LeaveRequestResponse,
  ShiftSessionResponse,
  SwapShiftRequestResponse
} from "@mypos/domain";
import type { FastifyInstance } from "fastify";
import { appRepository } from "../data/app-state";
import { asDownloadFilename, toCsv } from "../lib/csv";
import { requirePermission } from "../lib/guards";

export const registerStaffRoutes = async (app: FastifyInstance) => {
  app.get("/api/staff/current-shift", async (request, reply) => {
    const session = requirePermission(request, reply, "orders.manage");

    if (!session) {
      return { message: "Forbidden" };
    }

    const shift = appRepository.getActiveShiftForUser(session.user.id);

    if (!shift) {
      reply.status(404);
      return { message: "No active shift" };
    }

    const response: ShiftSessionResponse = {
      shift
    };

    return response;
  });

  app.post<{ Body: ClockInRequest }>("/api/staff/clock-in", async (request, reply) => {
    const session = requirePermission(request, reply, "orders.manage");

    if (!session) {
      return { message: "Forbidden" };
    }

    const shift = appRepository.clockInStaff(session.user, request.body);

    if (!shift) {
      reply.status(403);
      return { message: "คุณอยู่นอกร้าน" };
    }

    const response: ShiftSessionResponse = {
      shift
    };

    return response;
  });

  app.post<{ Body: ClockOutRequest }>("/api/staff/clock-out", async (request, reply) => {
    const session = requirePermission(request, reply, "orders.manage");

    if (!session) {
      return { message: "Forbidden" };
    }

    const shift = appRepository.clockOutStaff(session.user, request.body);

    if (!shift) {
      reply.status(404);
      return { message: "No active shift" };
    }

    const response: ShiftSessionResponse = {
      shift
    };

    return response;
  });

  app.get("/api/staff/my-orders", async (request, reply) => {
    const session = requirePermission(request, reply, "orders.manage");

    if (!session) {
      return { message: "Forbidden" };
    }

    const orders = appRepository
      .getSnapshot()
      .orders.filter((order) => order.waiterName === session.user.displayName);

    const response: StaffOrdersResponse = {
      orders
    };

    return response;
  });

  app.get("/api/staff/hr", async (request, reply) => {
    const session = requirePermission(request, reply, "orders.manage");

    if (!session) {
      return { message: "Forbidden" };
    }

    const response: StaffHrWorkspaceResponse = {
      workspace: appRepository.getStaffHrWorkspace(session.user.id)
    };

    return response;
  });

  app.get("/api/staff/notifications", async (request, reply) => {
    const session = requirePermission(request, reply, "orders.manage");

    if (!session) {
      return { message: "Forbidden" };
    }

    const response: StaffNotificationFeedResponse = {
      notifications: appRepository.getStaffNotifications(session.user.id, session.user.role)
    };

    return response;
  });

  app.get("/api/staff/notifications/export.csv", async (request, reply) => {
    const session = requirePermission(request, reply, "audit.view");

    if (!session) {
      return { message: "Forbidden" };
    }

    const rows = appRepository.getAllStaffNotifications().map((notification) => ({
      id: notification.id,
      type: notification.type,
      title: notification.title,
      message: notification.message,
      createdAt: notification.createdAt,
      read: notification.read,
      audienceRole: notification.audienceRole,
      audienceUserId: notification.audienceUserId ?? "",
      tableLabel: notification.tableLabel ?? ""
    }));

    reply.header("content-type", "text/csv; charset=utf-8");
    reply.header("content-disposition", `attachment; filename="${asDownloadFilename("staff-notifications")}"`);
    return rows.length
      ? toCsv(rows)
      : "id,type,title,message,createdAt,read,audienceRole,audienceUserId,tableLabel\n";
  });

  app.get("/api/staff/chat", async (request, reply) => {
    const session = requirePermission(request, reply, "orders.manage");

    if (!session) {
      return { message: "Forbidden" };
    }

    const response: KitchenChatFeedResponse = {
      messages: appRepository.getChatMessages(session.user.role)
    };

    return response;
  });

  app.get("/api/staff/chat/export.csv", async (request, reply) => {
    const session = requirePermission(request, reply, "audit.view");

    if (!session) {
      return { message: "Forbidden" };
    }

    const rows = appRepository.getAllChatMessages().map((message) => ({
      id: message.id,
      fromName: message.fromName,
      fromRole: message.fromRole,
      target: message.target,
      tableLabel: message.tableLabel ?? "",
      message: message.message,
      createdAt: message.createdAt
    }));

    reply.header("content-type", "text/csv; charset=utf-8");
    reply.header("content-disposition", `attachment; filename="${asDownloadFilename("kitchen-chat")}"`);
    return rows.length
      ? toCsv(rows)
      : "id,fromName,fromRole,target,tableLabel,message,createdAt\n";
  });

  app.post<{ Body: SendKitchenChatRequest }>("/api/staff/chat", async (request, reply) => {
    const session = requirePermission(request, reply, "orders.manage");

    if (!session) {
      return { message: "Forbidden" };
    }

    return {
      message: appRepository.sendKitchenChatMessage(request.body, {
        id: session.user.id,
        displayName: session.user.displayName,
        role: session.user.role
      })
    };
  });

  app.post<{ Body: RequestManagerHelpRequest }>("/api/staff/request-help", async (request, reply) => {
    const session = requirePermission(request, reply, "orders.manage");

    if (!session) {
      return { message: "Forbidden" };
    }

    return {
      notification: appRepository.requestManagerHelp(request.body, {
        id: session.user.id,
        displayName: session.user.displayName,
        role: session.user.role
      })
    };
  });

  app.post<{ Body: CreateLeaveRequestRequest }>("/api/staff/leave-requests", async (request, reply) => {
    const session = requirePermission(request, reply, "orders.manage");

    if (!session) {
      return { message: "Forbidden" };
    }

    const hrRequest = appRepository.createLeaveRequest(session.user, request.body);

    if (!hrRequest) {
      reply.status(400);
      return { message: "Could not create leave request" };
    }

    const response: LeaveRequestResponse = {
      request: hrRequest
    };

    return response;
  });

  app.post<{ Body: CreateSwapShiftRequest }>("/api/staff/swap-requests", async (request, reply) => {
    const session = requirePermission(request, reply, "orders.manage");

    if (!session) {
      return { message: "Forbidden" };
    }

    const hrRequest = appRepository.createSwapRequest(session.user, request.body);

    if (!hrRequest) {
      reply.status(400);
      return { message: "Could not create swap request" };
    }

    const response: SwapShiftRequestResponse = {
      request: hrRequest
    };

    return response;
  });
};
