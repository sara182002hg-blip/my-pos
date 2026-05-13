import type {
  CustomerMember,
  DeliveryOrder,
  DeliveryPlatformConnection,
  LeaveRequest,
  StockItem,
  StockMovement,
  KitchenChatMessage,
  ScheduledShift,
  SecurityPolicy,
  StaffNotification,
  UserAccount,
  DashboardMetric,
  DiningTable,
  KitchenQueueCard,
  MenuItemSummary,
  OrderTicket,
  ShiftSession,
  SwapShiftRequest
} from "./types";

export const dashboardMetrics: DashboardMetric[] = [
  { label: "Sales Today", value: "THB 128,450", delta: "+18% vs yesterday" },
  { label: "Open Tables", value: "14 / 26", delta: "4 waiting payment" },
  { label: "Delivery Mix", value: "THB 22,900", delta: "Grab 46%, LINE MAN 31%" },
  { label: "Staff On Shift", value: "11", delta: "1 overtime alert" }
];

export const securityPolicy: SecurityPolicy = {
  adminIpWhitelist: ["127.0.0.1", "::1", "10.0.0.5"],
  twoFactorRoles: ["OWNER", "MANAGER"],
  receiptTemplate: {
    businessName: "MyPOS Night Kitchen",
    branchLabel: "Bangkok Riverside Branch",
    footerMessage: "Thank you and see you again.",
    contactLine: "LINE OA: @myposnight · 02-123-4567",
    showQrLookupOnPrint: true,
    showTipLine: true
  }
};

export const demoUsers: UserAccount[] = [
  {
    id: "USR-OWNER-01",
    username: "owner01",
    displayName: "Restaurant Owner",
    role: "OWNER",
    branchId: "BR-TH-001",
    pin: "9999",
    accountStatus: "ACTIVE"
  },
  {
    id: "USR-MGR-01",
    username: "manager01",
    displayName: "Night Shift Manager",
    role: "MANAGER",
    branchId: "BR-TH-001",
    pin: "5678",
    accountStatus: "ACTIVE"
  },
  {
    id: "USR-CASH-01",
    username: "cashier01",
    displayName: "Front Cashier",
    role: "CASHIER",
    branchId: "BR-TH-001",
    pin: "1234",
    accountStatus: "ACTIVE"
  },
  {
    id: "USR-STAFF-01",
    username: "staff01",
    displayName: "Floor Staff",
    role: "STAFF",
    branchId: "BR-TH-001",
    pin: "2468",
    accountStatus: "ACTIVE"
  },
  {
    id: "USR-KDS-01",
    username: "kitchen01",
    displayName: "Kitchen Station",
    role: "KITCHEN",
    branchId: "BR-TH-001",
    pin: "1357",
    accountStatus: "ACTIVE"
  }
];

export const diningTables: DiningTable[] = [
  {
    id: "T1",
    label: "A1",
    seats: 4,
    zone: "Main Hall",
    status: "SEATED",
    occupiedMinutes: 42,
    currentAmount: 1620,
    qrLocked: true,
    layout: { x: 10, y: 12, width: 28, height: 22 }
  },
  {
    id: "T2",
    label: "A2",
    seats: 2,
    zone: "Main Hall",
    status: "AVAILABLE",
    occupiedMinutes: 0,
    currentAmount: 0,
    qrLocked: false,
    layout: { x: 46, y: 15, width: 24, height: 20 }
  },
  {
    id: "T3",
    label: "B1",
    seats: 6,
    zone: "VIP",
    status: "PENDING_PAYMENT",
    occupiedMinutes: 88,
    currentAmount: 3840,
    qrLocked: false,
    layout: { x: 18, y: 48, width: 34, height: 24 }
  },
  {
    id: "T4",
    label: "Bar-3",
    seats: 3,
    zone: "Bar",
    status: "RESERVED",
    occupiedMinutes: 0,
    currentAmount: 0,
    qrLocked: false,
    layout: { x: 64, y: 44, width: 22, height: 18 },
    reservation: {
      id: "RSV-1",
      guestName: "Khun Beam",
      reservedAt: "2026-03-25T19:30:00.000Z",
      partySize: 3,
      contactPhone: "089-888-1234",
      note: "Birthday setup"
    }
  }
];

export const menuItems: MenuItemSummary[] = [
  {
    id: "M1",
    category: "Signature Food",
    name: "Truffle Fried Rice",
    price: 285,
    description: "Wok-fried jasmine rice with truffle aroma and parmesan finish.",
    imageUrl: "https://images.unsplash.com/photo-1512058564366-18510be2db19?auto=format&fit=crop&w=800&q=80",
    tags: ["popular", "contains dairy"],
    allergenInfo: ["Dairy", "Egg"],
    inStock: true,
    happyHourPrice: 245,
    translations: {
      th: {
        name: "ข้าวผัดทรัฟเฟิล",
        category: "อาหารซิกเนเจอร์",
        description: "ข้าวหอมมะลิผัดกลิ่นทรัฟเฟิล โรยพาร์เมซาน"
      },
      en: {
        name: "Truffle Fried Rice",
        category: "Signature Food",
        description: "Wok-fried jasmine rice with truffle aroma and parmesan finish."
      },
      zh: {
        name: "松露炒饭",
        category: "招牌主食",
        description: "茉莉香米加入松露香气翻炒，搭配帕玛森起司"
      },
      ja: {
        name: "トリュフ炒飯",
        category: "シグネチャーフード",
        description: "ジャスミンライスをトリュフの香りで炒め、パルメザンで仕上げ"
      }
    },
    modifierGroups: [
      {
        id: "protein",
        name: "Protein",
        options: [
          { id: "onsen-egg", label: "Add onsen egg", extraPrice: 25 },
          { id: "grilled-prawn", label: "Add grilled prawn", extraPrice: 90 }
        ]
      },
      {
        id: "spice",
        name: "Spice Level",
        required: true,
        options: [
          { id: "mild", label: "Mild", extraPrice: 0 },
          { id: "medium", label: "Medium", extraPrice: 0 },
          { id: "hot", label: "Hot", extraPrice: 0 }
        ]
      }
    ]
  },
  {
    id: "M2",
    category: "Bar Bites",
    name: "Spicy Chicken Karaage",
    price: 225,
    description: "Japanese fried chicken with bold chili seasoning.",
    imageUrl: "https://images.unsplash.com/photo-1604908554027-0d8fe1ca7ec3?auto=format&fit=crop&w=800&q=80",
    tags: ["spicy", "best seller"],
    allergenInfo: ["Gluten"],
    inStock: true,
    translations: {
      th: {
        name: "คาราเกะไก่สไปซี่",
        category: "ของทานเล่นบาร์",
        description: "ไก่ทอดสไตล์ญี่ปุ่น ปรุงรสเผ็ดจัดจ้าน"
      },
      en: {
        name: "Spicy Chicken Karaage",
        category: "Bar Bites",
        description: "Japanese fried chicken with bold chili seasoning."
      },
      zh: {
        name: "香辣唐扬鸡",
        category: "酒吧小食",
        description: "日式炸鸡块，带有香辣调味"
      },
      ja: {
        name: "スパイシー唐揚げ",
        category: "バーフード",
        description: "しっかり辛味を効かせた和風フライドチキン"
      }
    },
    modifierGroups: [
      {
        id: "sauce",
        name: "Sauce",
        multiSelect: true,
        options: [
          { id: "yuzu-mayo", label: "Extra yuzu mayo", extraPrice: 20 },
          { id: "garlic-aioli", label: "Garlic aioli", extraPrice: 20 }
        ]
      },
      {
        id: "topping",
        name: "Topping",
        options: [
          { id: "no-spring-onion", label: "No spring onion", extraPrice: 0 },
          { id: "extra-chili", label: "Extra chili flakes", extraPrice: 10 }
        ]
      }
    ]
  },
  {
    id: "M3",
    category: "Cocktails",
    name: "Lychee Negroni",
    price: 320,
    description: "Lychee-forward twist on a bitter classic.",
    imageUrl: "https://images.unsplash.com/photo-1563225409-127c18758bd5?auto=format&fit=crop&w=800&q=80",
    tags: ["vip", "bar"],
    allergenInfo: [],
    inStock: false,
    translations: {
      th: {
        name: "ลิ้นจี่เนโกรนี",
        category: "ค็อกเทล",
        description: "เนโกรนีตีความใหม่ด้วยกลิ่นลิ้นจี่"
      },
      en: {
        name: "Lychee Negroni",
        category: "Cocktails",
        description: "Lychee-forward twist on a bitter classic."
      },
      zh: {
        name: "荔枝尼格罗尼",
        category: "鸡尾酒",
        description: "以荔枝香气重新诠释经典苦甜调酒"
      },
      ja: {
        name: "ライチネグローニ",
        category: "カクテル",
        description: "クラシックなネグローニにライチの香りを加えた一杯"
      }
    },
    modifierGroups: [
      {
        id: "serve",
        name: "Serve Style",
        options: [
          { id: "classic", label: "Classic garnish", extraPrice: 0 },
          { id: "no-garnish", label: "No garnish", extraPrice: 0 }
        ]
      }
    ]
  }
];

export const orderTickets: OrderTicket[] = [
  {
    id: "ORD-240301",
    tableLabel: "A1",
    waiterName: "Nicha",
    status: "IN_PROGRESS",
    priority: "NORMAL",
    guests: 4,
    createdAt: "2026-03-25T18:15:00.000Z",
    updatedAt: "2026-03-25T18:24:00.000Z",
    totalAmount: 1620,
    items: [
      {
        id: "ITEM-1",
        menuItemId: "M1",
        name: "Truffle Fried Rice",
        quantity: 2,
        price: 285,
        station: "HOT",
        note: "Less spicy",
        allergenFlags: ["Dairy"],
        modifiers: [{ group: "Protein", option: "Add onsen egg", extraPrice: 25 }],
        status: "IN_PROGRESS"
      },
      {
        id: "ITEM-2",
        menuItemId: "M2",
        name: "Spicy Chicken Karaage",
        quantity: 1,
        price: 225,
        station: "HOT",
        allergenFlags: ["Gluten"],
        modifiers: [],
        status: "READY"
      },
      {
        id: "ITEM-3",
        menuItemId: "M3",
        name: "Lychee Negroni",
        quantity: 2,
        price: 320,
        station: "BAR",
        note: "No garnish",
        allergenFlags: [],
        modifiers: [],
        status: "IN_PROGRESS"
      }
    ]
  },
  {
    id: "ORD-240302",
    tableLabel: "B1",
    waiterName: "Ploy",
    status: "SENT_TO_KITCHEN",
    priority: "VIP",
    guests: 6,
    createdAt: "2026-03-25T18:29:00.000Z",
    updatedAt: "2026-03-25T18:30:00.000Z",
    totalAmount: 3840,
    items: [
      {
        id: "ITEM-4",
        menuItemId: "M2",
        name: "Spicy Chicken Karaage",
        quantity: 3,
        price: 225,
        station: "HOT",
        note: "No spring onion",
        allergenFlags: ["Gluten"],
        modifiers: [{ group: "Sauce", option: "Extra yuzu mayo", extraPrice: 20 }],
        status: "SENT_TO_KITCHEN"
      }
    ]
  }
];

export const shiftSessions: ShiftSession[] = [
  {
    id: "SHIFT-1",
    staffName: "Nicha",
    role: "Server",
    geofenceStatus: "IN_RANGE",
    checkInAt: "2026-03-25T10:05:00.000Z",
    tipAmount: 890,
    ordersHandled: 14,
    deviceId: "PIXEL-8-PRO-01"
  },
  {
    id: "SHIFT-2",
    staffName: "Ton",
    role: "Bartender",
    geofenceStatus: "IN_RANGE",
    checkInAt: "2026-03-25T12:00:00.000Z",
    tipAmount: 460,
    ordersHandled: 10,
    deviceId: "IPHONE-13-02"
  }
];

export const scheduledShifts: ScheduledShift[] = [
  {
    id: "SCH-001",
    userId: "USR-STAFF-01",
    staffName: "Floor Staff",
    role: "Server",
    shiftDate: "2026-03-28",
    startTime: "17:00",
    endTime: "01:00",
    zone: "Main Hall",
    status: "CONFIRMED",
    assignedByName: "Night Shift Manager",
    note: "Friday rush coverage"
  },
  {
    id: "SCH-002",
    userId: "USR-CASH-01",
    staffName: "Front Cashier",
    role: "Cashier",
    shiftDate: "2026-03-28",
    startTime: "16:00",
    endTime: "00:00",
    zone: "Cashier",
    status: "SCHEDULED",
    assignedByName: "Night Shift Manager"
  },
  {
    id: "SCH-003",
    userId: "USR-KDS-01",
    staffName: "Kitchen Station",
    role: "Bartender",
    shiftDate: "2026-03-29",
    startTime: "18:00",
    endTime: "02:00",
    zone: "Bar",
    status: "SCHEDULED",
    assignedByName: "Night Shift Manager"
  }
];

export const leaveRequests: LeaveRequest[] = [
  {
    id: "LV-001",
    userId: "USR-STAFF-01",
    staffName: "Floor Staff",
    leaveDate: "2026-03-30",
    leaveType: "VACATION",
    reason: "Family event",
    status: "PENDING",
    requestedAt: "2026-03-27T14:30:00.000Z"
  }
];

export const swapShiftRequests: SwapShiftRequest[] = [
  {
    id: "SWAP-001",
    shiftId: "SCH-002",
    requesterUserId: "USR-CASH-01",
    requesterName: "Front Cashier",
    targetUserId: "USR-STAFF-01",
    targetStaffName: "Floor Staff",
    shiftDate: "2026-03-28",
    reason: "Need to attend training in the evening",
    status: "PENDING",
    requestedAt: "2026-03-27T16:45:00.000Z"
  }
];

export const kitchenQueueCards: KitchenQueueCard[] = [
  {
    id: "K1",
    tableLabel: "A1",
    ticketNo: "HOT-104",
    station: "HOT",
    priority: "NORMAL",
    elapsedMinutes: 4,
    items: ["Truffle Fried Rice x2", "Spicy Chicken Karaage x1"],
    note: "Less spicy, dairy warning",
    colorState: "RED"
  },
  {
    id: "K2",
    tableLabel: "VIP-B1",
    ticketNo: "HOT-105",
    station: "HOT",
    priority: "VIP",
    elapsedMinutes: 16,
    items: ["Spicy Chicken Karaage x3"],
    note: "VIP table, no spring onion",
    colorState: "PURPLE"
  },
  {
    id: "K3",
    tableLabel: "A1",
    ticketNo: "BAR-301",
    station: "BAR",
    priority: "URGENT",
    elapsedMinutes: 17,
    items: ["Lychee Negroni x2"],
    note: "No garnish",
    colorState: "BLUE"
  }
];

export const deliveryPlatforms: DeliveryPlatformConnection[] = [
  {
    platform: "GRAB_FOOD",
    displayName: "GrabFood",
    enabled: true,
    acceptsOrders: true,
    menuSyncState: "SYNCED",
    lastSyncAt: "2026-03-25T18:40:00.000Z",
    commissionRate: 0.3
  },
  {
    platform: "LINE_MAN",
    displayName: "LINE MAN",
    enabled: true,
    acceptsOrders: true,
    menuSyncState: "PENDING",
    lastSyncAt: "2026-03-25T18:12:00.000Z",
    commissionRate: 0.28
  },
  {
    platform: "FOODPANDA",
    displayName: "foodpanda",
    enabled: false,
    acceptsOrders: false,
    menuSyncState: "FAILED",
    lastSyncAt: "2026-03-25T17:05:00.000Z",
    commissionRate: 0.32
  },
  {
    platform: "ROBINHOOD",
    displayName: "Robinhood",
    enabled: true,
    acceptsOrders: true,
    menuSyncState: "SYNCED",
    lastSyncAt: "2026-03-25T18:41:00.000Z",
    commissionRate: 0.18
  }
];

export const deliveryOrders: DeliveryOrder[] = [
  {
    id: "DLV-1001",
    platform: "GRAB_FOOD",
    externalOrderNo: "GF-582190",
    customerName: "Aom",
    status: "PREPARING",
    placedAt: "2026-03-25T18:34:00.000Z",
    etaMinutes: 22,
    totalAmount: 545,
    commissionAmount: 163.5,
    branchStatus: "IN_KITCHEN",
    items: [
      { name: "Truffle Fried Rice", quantity: 1 },
      { name: "Spicy Chicken Karaage", quantity: 1 }
    ]
  },
  {
    id: "DLV-1002",
    platform: "LINE_MAN",
    externalOrderNo: "LM-103845",
    customerName: "Mint",
    status: "READY_FOR_PICKUP",
    placedAt: "2026-03-25T18:20:00.000Z",
    etaMinutes: 8,
    totalAmount: 285,
    commissionAmount: 79.8,
    branchStatus: "READY",
    items: [{ name: "Truffle Fried Rice", quantity: 1 }]
  },
  {
    id: "DLV-1003",
    platform: "ROBINHOOD",
    externalOrderNo: "RB-74420",
    customerName: "Peak",
    status: "OUT_FOR_DELIVERY",
    placedAt: "2026-03-25T18:05:00.000Z",
    etaMinutes: 15,
    totalAmount: 450,
    commissionAmount: 81,
    branchStatus: "DISPATCHED",
    items: [{ name: "Spicy Chicken Karaage", quantity: 2 }]
  }
];

export const customerMembers: CustomerMember[] = [
  {
    id: "MBR-001",
    fullName: "Nina Somchai",
    phone: "081-234-5678",
    tier: "GOLD",
    pointsBalance: 420,
    totalSpend: 18450,
    lastVisitAt: "2026-03-24T20:30:00.000Z",
    favoriteItems: ["Truffle Fried Rice", "Lychee Negroni"],
    preferredLanguage: "th",
    birthDate: "1994-03-28",
    lineUserId: "line-nina-001"
  },
  {
    id: "MBR-002",
    fullName: "Aiko Tanaka",
    phone: "082-345-6789",
    tier: "SILVER",
    pointsBalance: 180,
    totalSpend: 6200,
    lastVisitAt: "2026-03-20T19:10:00.000Z",
    favoriteItems: ["Spicy Chicken Karaage"],
    preferredLanguage: "ja",
    birthDate: "1996-03-25"
  }
];

export const inventoryItems: StockItem[] = [
  {
    id: "INV-001",
    name: "Jasmine Rice",
    category: "Dry Goods",
    unit: "kg",
    onHand: 18,
    minLevel: 6,
    reorderQty: 20,
    avgUnitCost: 58,
    supplierName: "Bangkok Pantry Co.",
    linkedMenuItems: ["M1"],
    recipeUsage: [{ menuItemId: "M1", quantityPerOrder: 0.25 }],
    status: "IN_STOCK",
    lastUpdatedAt: "2026-03-25T17:50:00.000Z"
  },
  {
    id: "INV-002",
    name: "Chicken Thigh",
    category: "Protein",
    unit: "kg",
    onHand: 4.2,
    minLevel: 5,
    reorderQty: 12,
    avgUnitCost: 112,
    supplierName: "Fresh Farm Proteins",
    linkedMenuItems: ["M2"],
    recipeUsage: [{ menuItemId: "M2", quantityPerOrder: 0.18 }],
    status: "LOW_STOCK",
    lastUpdatedAt: "2026-03-25T18:05:00.000Z"
  },
  {
    id: "INV-003",
    name: "Lychee Syrup",
    category: "Bar",
    unit: "bottle",
    onHand: 1,
    minLevel: 2,
    reorderQty: 6,
    avgUnitCost: 145,
    supplierName: "Night Bar Supply",
    linkedMenuItems: ["M3"],
    recipeUsage: [{ menuItemId: "M3", quantityPerOrder: 0.25 }],
    status: "LOW_STOCK",
    lastUpdatedAt: "2026-03-25T18:08:00.000Z"
  },
  {
    id: "INV-004",
    name: "Parmesan Cheese",
    category: "Dairy",
    unit: "kg",
    onHand: 0.8,
    minLevel: 1,
    reorderQty: 4,
    avgUnitCost: 420,
    supplierName: "Euro Deli Partners",
    linkedMenuItems: ["M1"],
    recipeUsage: [{ menuItemId: "M1", quantityPerOrder: 0.03 }],
    status: "LOW_STOCK",
    lastUpdatedAt: "2026-03-25T17:40:00.000Z"
  }
];

export const stockMovements: StockMovement[] = [
  {
    id: "STK-1",
    itemId: "INV-002",
    itemName: "Chicken Thigh",
    type: "PURCHASE",
    quantity: 8,
    unit: "kg",
    note: "Emergency supplier top-up",
    createdAt: "2026-03-25T15:20:00.000Z",
    actorName: "Night Shift Manager"
  },
  {
    id: "STK-2",
    itemId: "INV-003",
    itemName: "Lychee Syrup",
    type: "WASTE",
    quantity: 1,
    unit: "bottle",
    note: "Bottle broken during service",
    createdAt: "2026-03-25T17:10:00.000Z",
    actorName: "Kitchen Station"
  }
];

export const staffNotifications: StaffNotification[] = [
  {
    id: "NTF-1",
    type: "CHECK_BILL",
    title: "Check bill requested",
    message: "Table A1 requested check bill from QR",
    createdAt: "2026-03-25T18:42:00.000Z",
    read: false,
    audienceRole: "STAFF",
    tableLabel: "A1"
  }
];

export const kitchenChatMessages: KitchenChatMessage[] = [
  {
    id: "CHAT-1",
    fromName: "Kitchen Station",
    fromRole: "KITCHEN",
    target: "FLOOR",
    tableLabel: "A1",
    message: "Karaage ready for pickup",
    createdAt: "2026-03-25T18:38:00.000Z"
  }
];
