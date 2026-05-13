-- CreateEnum
CREATE TYPE "public"."TableStatus" AS ENUM ('AVAILABLE', 'SEATED', 'PENDING_PAYMENT', 'CLEANING', 'RESERVED', 'LOCKED_BY_QR');

-- CreateEnum
CREATE TYPE "public"."OrderStatus" AS ENUM ('DRAFT', 'SENT_TO_KITCHEN', 'IN_PROGRESS', 'READY', 'SERVED', 'PAID', 'VOIDED');

-- CreateEnum
CREATE TYPE "public"."OrderSource" AS ENUM ('POS', 'QR', 'DELIVERY', 'STAFF_APP');

-- CreateEnum
CREATE TYPE "public"."OrderPriority" AS ENUM ('NORMAL', 'VIP', 'URGENT');

-- CreateEnum
CREATE TYPE "public"."KitchenStation" AS ENUM ('HOT', 'COLD', 'BAR', 'DESSERT');

-- CreateEnum
CREATE TYPE "public"."KitchenLineStatus" AS ENUM ('PENDING', 'ACKNOWLEDGED', 'IN_PROGRESS', 'READY', 'OUT_OF_STOCK');

-- CreateEnum
CREATE TYPE "public"."PaymentMethod" AS ENUM ('CASH', 'PROMPTPAY', 'CARD', 'RABBIT_LINE_PAY', 'TRUE_MONEY');

-- CreateEnum
CREATE TYPE "public"."ReceiptType" AS ENUM ('STANDARD', 'TAX_INVOICE', 'E_TAX');

-- CreateEnum
CREATE TYPE "public"."ReservationStatus" AS ENUM ('CONFIRMED', 'CHECKED_IN', 'CANCELLED', 'NO_SHOW');

-- CreateEnum
CREATE TYPE "public"."DeliveryPlatform" AS ENUM ('GRAB', 'LINE_MAN', 'FOODPANDA', 'ROBINHOOD', 'SHOPEE_FOOD', 'LALAMOVE');

-- CreateEnum
CREATE TYPE "public"."DeliveryStatus" AS ENUM ('RECEIVED', 'ACCEPTED', 'PREPARING', 'READY_FOR_PICKUP', 'PICKED_UP', 'DELIVERED', 'CANCELLED');

-- CreateEnum
CREATE TYPE "public"."GeofenceStatus" AS ENUM ('IN_RANGE', 'OUT_OF_RANGE');

-- CreateEnum
CREATE TYPE "public"."UserRole" AS ENUM ('OWNER', 'MANAGER', 'CASHIER', 'STAFF', 'KITCHEN');

-- CreateTable
CREATE TABLE "public"."Branch" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "code" TEXT NOT NULL,
    "timezone" TEXT NOT NULL DEFAULT 'Asia/Bangkok',
    "floorplanJson" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Branch_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."AppUser" (
    "id" TEXT NOT NULL,
    "branchId" TEXT NOT NULL,
    "username" TEXT NOT NULL,
    "displayName" TEXT NOT NULL,
    "role" "public"."UserRole" NOT NULL,
    "pinHash" TEXT NOT NULL,
    "accountExpires" TIMESTAMP(3),
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "blockedAt" TIMESTAMP(3),
    "forceLogoutAfter" TIMESTAMP(3),
    "lastLoginAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "AppUser_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."DiningTable" (
    "id" TEXT NOT NULL,
    "branchId" TEXT NOT NULL,
    "label" TEXT NOT NULL,
    "zone" TEXT NOT NULL,
    "seats" INTEGER NOT NULL,
    "status" "public"."TableStatus" NOT NULL DEFAULT 'AVAILABLE',
    "qrToken" TEXT,
    "qrLockedAt" TIMESTAMP(3),

    CONSTRAINT "DiningTable_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."MenuCategory" (
    "id" TEXT NOT NULL,
    "branchId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "sortOrder" INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT "MenuCategory_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."MenuItem" (
    "id" TEXT NOT NULL,
    "branchId" TEXT NOT NULL,
    "categoryId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "sku" TEXT,
    "description" TEXT,
    "basePrice" DECIMAL(10,2) NOT NULL,
    "deliveryPrice" DECIMAL(10,2),
    "happyHourPrice" DECIMAL(10,2),
    "imageUrl" TEXT,
    "station" "public"."KitchenStation" NOT NULL,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "isLowStock" BOOLEAN NOT NULL DEFAULT false,
    "allergenInfo" TEXT[],
    "translationsJson" JSONB,

    CONSTRAINT "MenuItem_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."ModifierGroup" (
    "id" TEXT NOT NULL,
    "menuItemId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "minSelect" INTEGER NOT NULL DEFAULT 0,
    "maxSelect" INTEGER NOT NULL DEFAULT 1,

    CONSTRAINT "ModifierGroup_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."ModifierOption" (
    "id" TEXT NOT NULL,
    "modifierGroupId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "extraPrice" DECIMAL(10,2) NOT NULL,

    CONSTRAINT "ModifierOption_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."Order" (
    "id" TEXT NOT NULL,
    "branchId" TEXT NOT NULL,
    "tableId" TEXT,
    "memberId" TEXT,
    "orderNo" TEXT NOT NULL,
    "source" "public"."OrderSource" NOT NULL,
    "status" "public"."OrderStatus" NOT NULL DEFAULT 'DRAFT',
    "priority" "public"."OrderPriority" NOT NULL DEFAULT 'NORMAL',
    "guestCount" INTEGER NOT NULL,
    "subtotalAmount" DECIMAL(10,2) NOT NULL,
    "discountAmount" DECIMAL(10,2) NOT NULL,
    "vatAmount" DECIMAL(10,2) NOT NULL,
    "totalAmount" DECIMAL(10,2) NOT NULL,
    "specialNote" TEXT,
    "openedByUserId" TEXT,
    "closedByUserId" TEXT,
    "memberSettledAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Order_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."CustomerMember" (
    "id" TEXT NOT NULL,
    "branchId" TEXT NOT NULL,
    "fullName" TEXT NOT NULL,
    "phone" TEXT NOT NULL,
    "tier" TEXT NOT NULL,
    "pointsBalance" INTEGER NOT NULL DEFAULT 0,
    "totalSpend" DECIMAL(10,2) NOT NULL,
    "lastVisitAt" TIMESTAMP(3),
    "favoriteItems" TEXT[],
    "preferredLanguage" TEXT,
    "birthDate" TIMESTAMP(3),
    "lineUserId" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "CustomerMember_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."OrderItem" (
    "id" TEXT NOT NULL,
    "orderId" TEXT NOT NULL,
    "menuItemId" TEXT NOT NULL,
    "quantity" INTEGER NOT NULL,
    "unitPrice" DECIMAL(10,2) NOT NULL,
    "note" TEXT,
    "station" "public"."KitchenStation" NOT NULL,
    "lineStatus" "public"."KitchenLineStatus" NOT NULL DEFAULT 'PENDING',
    "allergens" TEXT[],
    "modifiersJson" JSONB NOT NULL,

    CONSTRAINT "OrderItem_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."KitchenTicket" (
    "id" TEXT NOT NULL,
    "orderId" TEXT NOT NULL,
    "station" "public"."KitchenStation" NOT NULL,
    "status" "public"."KitchenLineStatus" NOT NULL DEFAULT 'PENDING',
    "delayReason" TEXT,
    "startedAt" TIMESTAMP(3),
    "finishedAt" TIMESTAMP(3),

    CONSTRAINT "KitchenTicket_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."Payment" (
    "id" TEXT NOT NULL,
    "orderId" TEXT NOT NULL,
    "method" "public"."PaymentMethod" NOT NULL,
    "amount" DECIMAL(10,2) NOT NULL,
    "tipAmount" DECIMAL(10,2) NOT NULL DEFAULT 0,
    "referenceNo" TEXT,
    "splitGroup" TEXT,
    "paidAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Payment_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."PaymentGatewaySession" (
    "id" TEXT NOT NULL,
    "branchId" TEXT NOT NULL,
    "orderId" TEXT NOT NULL,
    "tableLabel" TEXT NOT NULL,
    "method" "public"."PaymentMethod" NOT NULL,
    "provider" TEXT NOT NULL,
    "amount" DECIMAL(10,2) NOT NULL,
    "tipAmount" DECIMAL(10,2) NOT NULL DEFAULT 0,
    "status" TEXT NOT NULL,
    "reference" TEXT NOT NULL,
    "qrPayload" TEXT,
    "checkoutUrl" TEXT,
    "failureReason" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL,
    "expiresAt" TIMESTAMP(3) NOT NULL,
    "capturedAt" TIMESTAMP(3),

    CONSTRAINT "PaymentGatewaySession_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."Receipt" (
    "id" TEXT NOT NULL,
    "orderId" TEXT NOT NULL,
    "receiptNo" TEXT NOT NULL,
    "receiptType" "public"."ReceiptType" NOT NULL,
    "qrLookupToken" TEXT NOT NULL,
    "splitGroupId" TEXT,
    "splitIndex" INTEGER,
    "splitCount" INTEGER,
    "guestLabel" TEXT,
    "email" TEXT,
    "lineUserId" TEXT,
    "emailSharedAt" TIMESTAMP(3),
    "lineSharedAt" TIMESTAMP(3),
    "printedAt" TIMESTAMP(3),
    "printerName" TEXT,
    "taxPayerName" TEXT,
    "taxId" TEXT,
    "taxBranchAddress" TEXT,
    "taxEmail" TEXT,
    "taxIssuedAt" TIMESTAMP(3),
    "eTaxStatus" TEXT,
    "eTaxSubmissionReference" TEXT,
    "eTaxSubmittedAt" TIMESTAMP(3),
    "eTaxError" TEXT,
    "voidedAt" TIMESTAMP(3),
    "voidReason" TEXT,
    "refundedAt" TIMESTAMP(3),
    "refundedAmount" DECIMAL(10,2),
    "refundReason" TEXT,

    CONSTRAINT "Receipt_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."ReceiptDispatchAttempt" (
    "id" TEXT NOT NULL,
    "branchId" TEXT NOT NULL,
    "receiptId" TEXT NOT NULL,
    "receiptNo" TEXT NOT NULL,
    "channel" TEXT NOT NULL,
    "target" TEXT NOT NULL,
    "status" TEXT NOT NULL,
    "provider" TEXT NOT NULL,
    "message" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ReceiptDispatchAttempt_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."Reservation" (
    "id" TEXT NOT NULL,
    "branchId" TEXT NOT NULL,
    "tableId" TEXT,
    "customerName" TEXT NOT NULL,
    "customerPhone" TEXT NOT NULL,
    "partySize" INTEGER NOT NULL,
    "reservedAt" TIMESTAMP(3) NOT NULL,
    "status" "public"."ReservationStatus" NOT NULL DEFAULT 'CONFIRMED',

    CONSTRAINT "Reservation_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."InventoryItem" (
    "id" TEXT NOT NULL,
    "branchId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "category" TEXT NOT NULL,
    "unit" TEXT NOT NULL,
    "onHand" DECIMAL(12,3) NOT NULL,
    "minLevel" DECIMAL(12,3) NOT NULL,
    "reorderQty" DECIMAL(12,3) NOT NULL,
    "avgUnitCost" DECIMAL(10,2) NOT NULL,
    "supplierName" TEXT,
    "linkedMenuItemIds" TEXT[],
    "recipeUsageJson" JSONB,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "InventoryItem_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."InventoryMovement" (
    "id" TEXT NOT NULL,
    "branchId" TEXT NOT NULL,
    "itemId" TEXT NOT NULL,
    "itemName" TEXT NOT NULL,
    "type" TEXT NOT NULL,
    "quantity" DECIMAL(12,3) NOT NULL,
    "unit" TEXT NOT NULL,
    "note" TEXT,
    "actorName" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "InventoryMovement_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."ShiftSession" (
    "id" TEXT NOT NULL,
    "branchId" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "startedAt" TIMESTAMP(3) NOT NULL,
    "endedAt" TIMESTAMP(3),
    "roleLabel" TEXT,
    "checkInLat" DECIMAL(9,6) NOT NULL,
    "checkInLng" DECIMAL(9,6) NOT NULL,
    "checkOutLat" DECIMAL(9,6),
    "checkOutLng" DECIMAL(9,6),
    "geofenceStatus" "public"."GeofenceStatus" NOT NULL,
    "distanceMeters" INTEGER NOT NULL DEFAULT 0,
    "tipAmount" DECIMAL(10,2) NOT NULL DEFAULT 0,
    "ordersHandled" INTEGER NOT NULL DEFAULT 0,
    "deviceId" TEXT NOT NULL,
    "ipAddress" TEXT NOT NULL,
    "otMinutes" INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT "ShiftSession_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."StaffNotificationRecord" (
    "id" TEXT NOT NULL,
    "branchId" TEXT NOT NULL,
    "type" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "message" TEXT NOT NULL,
    "audienceRole" TEXT NOT NULL,
    "audienceUserId" TEXT,
    "tableLabel" TEXT,
    "isRead" BOOLEAN NOT NULL DEFAULT false,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "StaffNotificationRecord_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."KitchenChatRecord" (
    "id" TEXT NOT NULL,
    "branchId" TEXT NOT NULL,
    "fromName" TEXT NOT NULL,
    "fromRole" TEXT NOT NULL,
    "target" TEXT NOT NULL,
    "tableLabel" TEXT,
    "message" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "KitchenChatRecord_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."ShiftPlan" (
    "id" TEXT NOT NULL,
    "branchId" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "staffName" TEXT NOT NULL,
    "role" TEXT NOT NULL,
    "shiftDate" TIMESTAMP(3) NOT NULL,
    "startTime" TEXT NOT NULL,
    "endTime" TEXT NOT NULL,
    "zone" TEXT NOT NULL,
    "status" TEXT NOT NULL,
    "assignedByName" TEXT,
    "note" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "ShiftPlan_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."LeaveRequest" (
    "id" TEXT NOT NULL,
    "branchId" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "staffName" TEXT NOT NULL,
    "leaveDate" TIMESTAMP(3) NOT NULL,
    "leaveType" TEXT NOT NULL,
    "reason" TEXT NOT NULL,
    "status" TEXT NOT NULL,
    "requestedAt" TIMESTAMP(3) NOT NULL,
    "reviewerName" TEXT,
    "reviewedAt" TIMESTAMP(3),
    "coverStaffUserId" TEXT,
    "coverStaffName" TEXT,

    CONSTRAINT "LeaveRequest_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."SwapShiftRequest" (
    "id" TEXT NOT NULL,
    "branchId" TEXT NOT NULL,
    "shiftPlanId" TEXT NOT NULL,
    "requesterUserId" TEXT NOT NULL,
    "requesterName" TEXT NOT NULL,
    "targetUserId" TEXT,
    "targetStaffName" TEXT,
    "shiftDate" TIMESTAMP(3) NOT NULL,
    "reason" TEXT NOT NULL,
    "status" TEXT NOT NULL,
    "requestedAt" TIMESTAMP(3) NOT NULL,
    "reviewerName" TEXT,
    "reviewedAt" TIMESTAMP(3),

    CONSTRAINT "SwapShiftRequest_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."SecurityConfig" (
    "id" TEXT NOT NULL,
    "branchId" TEXT NOT NULL,
    "adminIpWhitelist" TEXT[],
    "twoFactorRoles" TEXT[],
    "receiptTemplateJson" JSONB,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "SecurityConfig_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."DeliveryPlatformConnection" (
    "id" TEXT NOT NULL,
    "branchId" TEXT NOT NULL,
    "platform" "public"."DeliveryPlatform" NOT NULL,
    "displayName" TEXT NOT NULL,
    "enabled" BOOLEAN NOT NULL DEFAULT true,
    "acceptsOrders" BOOLEAN NOT NULL DEFAULT true,
    "menuSyncState" TEXT NOT NULL,
    "lastSyncAt" TIMESTAMP(3),
    "commissionRate" DECIMAL(6,4) NOT NULL,

    CONSTRAINT "DeliveryPlatformConnection_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."DeliveryOrder" (
    "branchId" TEXT NOT NULL,
    "id" TEXT NOT NULL,
    "orderId" TEXT NOT NULL,
    "platform" "public"."DeliveryPlatform" NOT NULL,
    "externalOrderId" TEXT NOT NULL,
    "customerName" TEXT NOT NULL,
    "branchStatus" TEXT NOT NULL,
    "placedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "totalAmount" DECIMAL(10,2) NOT NULL,
    "deliveryStatus" "public"."DeliveryStatus" NOT NULL,
    "commission" DECIMAL(10,2) NOT NULL,
    "riderEtaMinutes" INTEGER,

    CONSTRAINT "DeliveryOrder_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."ExceptionRecord" (
    "id" TEXT NOT NULL,
    "branchId" TEXT NOT NULL,
    "kind" TEXT NOT NULL,
    "orderId" TEXT NOT NULL,
    "receiptId" TEXT,
    "reason" TEXT NOT NULL,
    "amount" DECIMAL(10,2),
    "actorName" TEXT NOT NULL,
    "actorRole" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ExceptionRecord_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."AuditLog" (
    "id" TEXT NOT NULL,
    "branchId" TEXT NOT NULL,
    "actorId" TEXT,
    "actorRole" TEXT NOT NULL,
    "action" TEXT NOT NULL,
    "entityType" TEXT NOT NULL,
    "entityId" TEXT NOT NULL,
    "ipAddress" TEXT,
    "metadata" JSONB NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "AuditLog_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "Branch_code_key" ON "public"."Branch"("code");

-- CreateIndex
CREATE UNIQUE INDEX "AppUser_username_key" ON "public"."AppUser"("username");

-- CreateIndex
CREATE UNIQUE INDEX "Order_orderNo_key" ON "public"."Order"("orderNo");

-- CreateIndex
CREATE UNIQUE INDEX "PaymentGatewaySession_reference_key" ON "public"."PaymentGatewaySession"("reference");

-- CreateIndex
CREATE UNIQUE INDEX "Receipt_receiptNo_key" ON "public"."Receipt"("receiptNo");

-- CreateIndex
CREATE UNIQUE INDEX "Receipt_qrLookupToken_key" ON "public"."Receipt"("qrLookupToken");

-- CreateIndex
CREATE UNIQUE INDEX "SecurityConfig_branchId_key" ON "public"."SecurityConfig"("branchId");

-- CreateIndex
CREATE UNIQUE INDEX "DeliveryPlatformConnection_branchId_platform_key" ON "public"."DeliveryPlatformConnection"("branchId", "platform");

-- CreateIndex
CREATE UNIQUE INDEX "DeliveryOrder_orderId_key" ON "public"."DeliveryOrder"("orderId");

-- AddForeignKey
ALTER TABLE "public"."AppUser" ADD CONSTRAINT "AppUser_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES "public"."Branch"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."DiningTable" ADD CONSTRAINT "DiningTable_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES "public"."Branch"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."MenuCategory" ADD CONSTRAINT "MenuCategory_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES "public"."Branch"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."MenuItem" ADD CONSTRAINT "MenuItem_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES "public"."Branch"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."MenuItem" ADD CONSTRAINT "MenuItem_categoryId_fkey" FOREIGN KEY ("categoryId") REFERENCES "public"."MenuCategory"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."ModifierGroup" ADD CONSTRAINT "ModifierGroup_menuItemId_fkey" FOREIGN KEY ("menuItemId") REFERENCES "public"."MenuItem"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."ModifierOption" ADD CONSTRAINT "ModifierOption_modifierGroupId_fkey" FOREIGN KEY ("modifierGroupId") REFERENCES "public"."ModifierGroup"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."Order" ADD CONSTRAINT "Order_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES "public"."Branch"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."Order" ADD CONSTRAINT "Order_tableId_fkey" FOREIGN KEY ("tableId") REFERENCES "public"."DiningTable"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."Order" ADD CONSTRAINT "Order_memberId_fkey" FOREIGN KEY ("memberId") REFERENCES "public"."CustomerMember"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."CustomerMember" ADD CONSTRAINT "CustomerMember_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES "public"."Branch"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."OrderItem" ADD CONSTRAINT "OrderItem_orderId_fkey" FOREIGN KEY ("orderId") REFERENCES "public"."Order"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."OrderItem" ADD CONSTRAINT "OrderItem_menuItemId_fkey" FOREIGN KEY ("menuItemId") REFERENCES "public"."MenuItem"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."KitchenTicket" ADD CONSTRAINT "KitchenTicket_orderId_fkey" FOREIGN KEY ("orderId") REFERENCES "public"."Order"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."Payment" ADD CONSTRAINT "Payment_orderId_fkey" FOREIGN KEY ("orderId") REFERENCES "public"."Order"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."PaymentGatewaySession" ADD CONSTRAINT "PaymentGatewaySession_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES "public"."Branch"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."PaymentGatewaySession" ADD CONSTRAINT "PaymentGatewaySession_orderId_fkey" FOREIGN KEY ("orderId") REFERENCES "public"."Order"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."Receipt" ADD CONSTRAINT "Receipt_orderId_fkey" FOREIGN KEY ("orderId") REFERENCES "public"."Order"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."ReceiptDispatchAttempt" ADD CONSTRAINT "ReceiptDispatchAttempt_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES "public"."Branch"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."Reservation" ADD CONSTRAINT "Reservation_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES "public"."Branch"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."Reservation" ADD CONSTRAINT "Reservation_tableId_fkey" FOREIGN KEY ("tableId") REFERENCES "public"."DiningTable"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."InventoryItem" ADD CONSTRAINT "InventoryItem_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES "public"."Branch"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."InventoryMovement" ADD CONSTRAINT "InventoryMovement_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES "public"."Branch"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."InventoryMovement" ADD CONSTRAINT "InventoryMovement_itemId_fkey" FOREIGN KEY ("itemId") REFERENCES "public"."InventoryItem"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."ShiftSession" ADD CONSTRAINT "ShiftSession_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES "public"."Branch"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."StaffNotificationRecord" ADD CONSTRAINT "StaffNotificationRecord_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES "public"."Branch"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."KitchenChatRecord" ADD CONSTRAINT "KitchenChatRecord_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES "public"."Branch"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."ShiftPlan" ADD CONSTRAINT "ShiftPlan_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES "public"."Branch"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."ShiftPlan" ADD CONSTRAINT "ShiftPlan_userId_fkey" FOREIGN KEY ("userId") REFERENCES "public"."AppUser"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."LeaveRequest" ADD CONSTRAINT "LeaveRequest_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES "public"."Branch"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."SwapShiftRequest" ADD CONSTRAINT "SwapShiftRequest_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES "public"."Branch"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."SwapShiftRequest" ADD CONSTRAINT "SwapShiftRequest_shiftPlanId_fkey" FOREIGN KEY ("shiftPlanId") REFERENCES "public"."ShiftPlan"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."SecurityConfig" ADD CONSTRAINT "SecurityConfig_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES "public"."Branch"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."DeliveryPlatformConnection" ADD CONSTRAINT "DeliveryPlatformConnection_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES "public"."Branch"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."DeliveryOrder" ADD CONSTRAINT "DeliveryOrder_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES "public"."Branch"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."DeliveryOrder" ADD CONSTRAINT "DeliveryOrder_orderId_fkey" FOREIGN KEY ("orderId") REFERENCES "public"."Order"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."ExceptionRecord" ADD CONSTRAINT "ExceptionRecord_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES "public"."Branch"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."AuditLog" ADD CONSTRAINT "AuditLog_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES "public"."Branch"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
