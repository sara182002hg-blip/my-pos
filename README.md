# MyPOS Platform

Production-oriented monorepo for a restaurant and nightlife POS platform built around three primary apps:

1. `POS Console` for cashier, manager, QR ordering, delivery control and backoffice modules
2. `Staff Mobile` for geofenced check-in, table service and live order handling
3. `Kitchen Display System` for touchscreen kitchen operations

The repo also includes a central `API` workspace, a customer-facing `QR Web App`, shared domain models, Prisma schema, and local infrastructure for PostgreSQL + Redis.

## Workspace layout

```text
apps/
  api/            Fastify API + websocket starter
  customer-qr/    Next.js guest ordering PWA shell
  pos-console/    React + Vite web console
  kds/            React + Vite kitchen board
  staff-mobile/   Expo React Native starter
packages/
  domain/         Shared types and mock fixtures
  ui-web/         Placeholder for shared web UI components
prisma/
  schema.prisma   Core schema for POS operations
docs/
  architecture.md System design and delivery roadmap
  production-runbook.md Production release and pilot checklist
```

## Why this structure

- Supports multi-branch growth without splitting business rules across separate repos
- Keeps order, menu, payment, table, HR and audit concepts in one shared domain package
- Allows QR, delivery and backoffice to start as POS Console modules, then break out later if traffic grows
- Makes offline-first branch edge deployment possible through a future sync worker without rewriting app boundaries

## Suggested rollout

### Phase 1

- POS Console floor management, dine-in orders, payments, receipts
- Staff Mobile login, geofence attendance, order taking
- KDS with station queues and ready notifications
- PostgreSQL + Redis + websocket event layer

### Phase 2

- QR ordering, multi-language menu and check bill flow
- Delivery aggregation and platform menu sync
- Loyalty, CRM and scheduled alerts

### Phase 3

- e-Tax integration, payroll exports, advanced forecasting and branch benchmarking

## Getting started

1. Copy `.env.example` to `.env`
   - or run `npm run env:init` for a local dev `.env`
2. Start infrastructure with `npm run infra:up`
3. Install dependencies with `npm install`
4. For a fast UAT stack, run `npm run uat:start`
5. Check readiness with `npm run uat:health`
6. Or run each app from the root:
   - `npm run dev:api`
   - `npm run dev:qr`
   - `npm run dev:pos`
   - `npm run dev:kds`
   - `npm run dev:staff`

## Demo accounts

- `cashier01 / 1234` for POS payment and order actions
- `manager01 / 5678` for broader operational access
- `owner01 / 9999` reserved for future owner console flows
- `staff01 / 2468` and `kitchen01 / 1357` reserved for staff-specific surfaces

## Demo operational flow

1. Start `API` and `POS Console`
2. Login from the POS page as `cashier01`
3. Click `Create Sample Order` to push a dine-in order into the live snapshot
4. Open `KDS` to see the station cards update
5. Open `QR Web App` at `/table/T2` to place an order or request check bill from the guest side
6. Use `Settle Cash` in POS or kitchen action buttons in KDS to trigger live state changes

## Demo launcher

- Open `http://127.0.0.1:5173/demo.html` after `npm run uat:start`
- Use it to check API/POS/KDS/QR health, open each demo app, create a sample order, or reset the in-memory demo state

## API flows included now

- `POST /api/auth/login` for username + PIN
- `POST /api/auth/verify-2fa` for owner and manager 2FA challenges
- `POST /api/auth/refresh` and `POST /api/auth/logout`
- `GET /api/auth/me` for access-token validation
- `POST /api/system/reset-demo` to restore in-memory demo state for repeatable UAT runs
- `POST /api/orders` with role-checked order creation
- `POST /api/orders/:orderId/pay` with receipt issuance
- `POST /api/orders/:orderId/payment-session` to create PromptPay or hosted-checkout payment sessions
- `POST /api/orders/:orderId/split-pay` for equal or mixed-method split billing with multiple receipts
- `POST /api/payment-sessions/:sessionId/capture` to convert a successful gateway session into the normal receipt flow
- `POST /api/payment-sessions/:sessionId/retry` to regenerate a new QR or checkout session from a failed or expired one
- `POST /api/payment-sessions/webhook` with `x-payment-webhook-secret` for provider callbacks that auto-capture, fail, or expire gateway sessions
- `GET /api/receipts`, `GET /api/receipts/dispatch-attempts`, and `GET /api/audit` for protected operational feeds
- `GET /api/reports/backoffice/export.csv`, `GET /api/receipts/export.csv`, `GET /api/receipts/dispatch-attempts/export.csv`, `GET /api/payment-sessions/export.csv`, `GET /api/audit/export.csv`, and `GET /api/inventory/export.csv` for operational CSV exports
- `GET /api/members/export.csv` and `GET /api/delivery/export.csv` for CRM and delivery CSV exports
- `GET /api/tables/export.csv`, `GET /api/menu/export.csv`, `GET /api/security/export.csv`, and `GET /api/exceptions/export.csv` for floor, menu, security, and exception CSV exports
- `GET /api/orders/export.csv` and `GET /api/kitchen/export.csv` for order and kitchen CSV exports
- `GET /api/payment-sessions` for recent gateway QR and checkout sessions
- `GET /api/reports/backoffice` for sales, payment mix, top items, audit summary, and HR-aware reporting
- `GET /api/delivery/overview` for aggregated delivery orders, platform status, commission totals, and ETA summary
- `POST /api/delivery/platforms/:platform/toggle`
- `POST /api/delivery/platforms/:platform/sync-menu`
- `POST /api/menu`
- `POST /api/menu/:menuItemId`
- `GET /api/inventory/overview`
- `POST /api/inventory/movements`
- `GET /api/security/users`
- `GET /api/security/policy`
- `POST /api/security/users`
- `POST /api/security/users/:userId`
- `POST /api/security/users/:userId/force-logout`
- `POST /api/security/policy`
- `GET /api/hr/overview`
- `GET /api/hr/export.csv`
- `GET /api/hr/payroll/export.csv`
- `GET /api/staff/notifications/export.csv`
- `GET /api/staff/chat/export.csv`
- `POST /api/hr/schedules`
- `POST /api/hr/leave-requests/:requestId`
- `POST /api/hr/swap-requests/:requestId`
- `POST /api/tables/:tableId/layout`
- `POST /api/tables/:tableId/reserve`
- `POST /api/tables/:tableId/clear-reservation`
- `POST /api/orders/:orderId/void`
- `POST /api/receipts/:receiptId/refund`
- `POST /api/receipts/:receiptId/tax-invoice`
- `POST /api/receipts/:receiptId/e-tax-submit`
- `POST /api/receipts/dispatch-attempts/:attemptId/retry`
- `GET /api/exceptions`
- `GET /api/members`
- `POST /api/members`
- `POST /api/orders/:orderId/assign-member`
- `GET /api/crm/overview`
- `POST /api/kitchen/:ticketId/acknowledge|ready|out-of-stock`
- `POST /api/staff/clock-in`, `POST /api/staff/clock-out`, `GET /api/staff/current-shift`, `GET /api/staff/my-orders`
- `GET /api/staff/hr`, `POST /api/staff/leave-requests`, `POST /api/staff/swap-requests`
- `GET /api/staff/notifications`, `GET /api/staff/chat`, `POST /api/staff/chat`, `POST /api/staff/request-help`
- `GET /api/public/tables/:tableId`
- `POST /api/public/tables/:tableId/lock`
- `POST /api/public/tables/:tableId/orders`
- `POST /api/public/tables/:tableId/check-bill`

## Database scripts

- CI runs the same pilot gate in `.github/workflows/ci.yml`: install, Prisma client generation, typecheck, POS/KDS/QR builds, smoke checks, and a non-blocking production readiness report
- `npm run db:generate`
- `npm run db:push`
- `npm run db:seed`
- `npm run env:init`
- `npm run doctor`
- `npm run pilot:links`
- `npm run prod:check`
- `npm run prod:check:example`
- `npm run prod:data:check`
- `npm run prod:data:check:example`
- `npm run prod:compose:config`
- `npm run release:check`
- `npm run uat:start`
- `npm run uat:stop`
- `npm run uat:health`
- `npm run smoke:all`
- `npm run smoke:pilot`
- `npm run smoke:reset-demo`
- `npm run smoke:db`

`npm run env:init` creates a local `.env` from `.env.example` with non-placeholder development secrets for JWT and payment webhook testing.
`npm run doctor` checks local readiness for pilot use: `.env`, JWT secrets, database URL, provider modes, Docker availability, and whether the API/POS/KDS/QR endpoints are already reachable.
`npm run pilot:links` prints LAN URLs for POS, KDS, QR, Demo Launcher, and API health so tablets or phones on the same Wi-Fi can open the demo stack.
`npm run prod:check` reports production blockers such as stub payment providers, missing SMTP/LINE credentials, placeholder secrets, and non-production URLs.
`npm run prod:check:example` validates `.env.production.example` as a checklist template and should fail until real production values replace placeholders.
`npm run prod:data:check` verifies that configured Postgres and Redis endpoints are reachable.
`npm run prod:data:check:example` runs the same data check against `.env.production.example` and should fail until real infrastructure URLs replace placeholders.
`npm run prod:compose:config` validates the example production compose file for `API`, `POS Console`, `KDS`, `QR Web App`, Postgres, and Redis.
`npm run release:check` runs the pilot release gate: typecheck, POS/KDS/QR builds, smoke checks, and a non-blocking production readiness report.
`npm run uat:start` launches the local UAT stack for `API`, `POS Console`, `KDS`, and `QR Web App` on fixed ports `4000`, `5173`, `5174`, and `3000`.
`npm run uat:health` checks those local endpoints and returns a compact JSON readiness report.
`npm run uat:stop` stops the background PowerShell processes started by `uat:start`.
`npm run smoke:all` runs both in-process smoke checks in sequence: the payment pilot flow and the owner reset-demo recovery flow.
`npm run smoke:pilot` runs a no-browser pilot smoke flow against the in-process API: cashier login, create dine-in order, create PromptPay session, webhook auto-capture, receipt issuance, and backoffice gateway-report checks.
`npm run smoke:reset-demo` runs a second in-process smoke flow that creates a dine-in order, signs in as the owner through 2FA, calls `POST /api/system/reset-demo`, and verifies the baseline demo state is restored.
`npm run smoke:db` runs `db push`, seeds Postgres, then executes the same pilot smoke flow against the DB-backed app state.

This machine currently has no Docker installed, so PostgreSQL bootstrap was not executed here. Prisma schema and client generation were validated, and the seed script is ready for an environment with Postgres available.

## Current data-source behavior

- API now boots through a repository layer instead of mutating route-local state directly
- If `DATABASE_URL` is available and Prisma can connect, app state can bootstrap users, tables, reservations, floorplan layouts, and menu from Postgres
- Prisma schema now also includes customer members, inventory items and movements, shift plans, leave requests, swap requests, and security configuration for the next stage of full persistence rollout
- Operational records for `shift sessions`, `staff notifications`, and `kitchen chat` are now also represented in Prisma so staff-side activity can survive API restarts in database-backed mode
- Delivery platform connections and delivery-order metadata are now represented in Prisma as well, so delivery dashboards can bootstrap from Postgres instead of resetting to mock-only state
- Receipt persistence now carries split-bill metadata and refund fields in schema so payment reconciliation can keep guest-level split context and refund status
- When Prisma is connected, auth events, order creation, table status, table layout, reservations, menu updates, kitchen updates, payments, receipts, shift sessions, staff notifications, kitchen chat, delivery platform config, and audit logs also have a persistence sync path, and the repository now has bootstrap coverage ready for CRM, inventory, HR, security policy, and delivery center flows
- Public QR table locks and `check bill` state now ride the same table-status persistence path as cashier-side table actions
- `Exception` records for voids and refunds now have a dedicated Prisma model so `/api/exceptions` can bootstrap from database-backed state instead of relying only on runtime memory
- Audit persistence is now closer to runtime parity for staff HR, shift clocking, chat/help, security admin, and related backoffice actions, reducing drift between in-memory and Postgres-backed audit feeds
- QR-specific table events now preserve their original audit names in persistence as well, so `table.qr_lock` and `table.check_bill_requested` no longer collapse into generic status-change entries
- Auth persistence now updates account activity timestamps on real login flows too, so `lastLoginAt` stays useful in security admin views under database-backed mode
- Delivery operator actions and member settlement events now keep their original audit names in persistence too, including `delivery.platform_toggle`, `delivery.menu_sync`, and `member.points_earned`
- The Prisma seed now covers more of the live demo state too, including reservations, dine-in open orders, shift sessions, staff notifications, and kitchen chat, so database-backed demos start closer to the in-memory experience
- Prisma bootstrap now derives table `currentAmount` and `occupiedMinutes` from active dine-in orders, so DB-backed floorplan cards reflect open checks more accurately
- Prisma seed now also includes a historical paid split-bill transaction with payments, receipts, and audit entries, so cashier and backoffice views have receipt/payment activity immediately in database-backed demos
- Prisma bootstrap now restores order-line modifiers from `modifiersJson` and sorts payment/receipt relations more deterministically, so split-bill and add-on data survive database-backed reloads more faithfully
- Menu modifier groups and option pricing are now also seeded, persisted, and bootstrapped from Prisma, so QR/POS add-on selection stays aligned with the in-memory demo model
- Menu translations for `th/en/zh/ja` now persist in Prisma too, so multilingual QR ordering no longer falls back to base-language-only data after a database-backed reload
- Receipt refunds now persist their own `refundReason` field in Prisma instead of reusing `voidReason`, and refund writes no longer mark receipts as voided under the hood
- Split-bill persistence now guards member loyalty settlement from being applied multiple times across multiple receipts, and payment records keep the receipt `paidAt` timestamp for more accurate reconciliation
- Payment persistence is now more retry-safe as well: payment rows use deterministic ids per receipt and order-level member settlement is guarded by `memberSettledAt`, reducing duplicate financial side effects if a sync path replays
- Shift sessions now persist role, distance, tips, and orders handled in Prisma too, so HR and staff-performance views no longer degrade to placeholder values after a database-backed reload
- Active shift sessions now increment `ordersHandled` whenever a logged-in cashier or floor staff member creates an order, and the updated shift state is pushed through the Prisma sync path as well
- Payment flows now support `tipAmount` on both single-pay and split-bill requests, and the tip is added back into the active waiter shift plus persisted through the payment/receipt sync path
- Backoffice reporting now separates net food sales, refunded totals, net tips, and collected totals, and payment-method breakdowns split receipt money into sales vs tip components
- POS Console cashier actions now let operators choose the payment method used for both single-pay and equal split-bill flows instead of hard-coding cash only
- Split-bill UI now also supports mixed payment methods per guest, while the console still auto-balances equal food-share and tip-share amounts for cashiers
- Payment gateway sessions now support non-cash cashier flows too, with PromptPay QR payloads or hosted-checkout URLs plus manual capture into the standard receipt/audit pipeline
- Receipts can now be shared from the POS Console through Email or LINE targets, with recipient details stored on the receipt record and `receipt.share` captured in the audit trail
- Receipts can now also be marked as printed from the POS Console, storing `printedAt` and `printerName` on the receipt plus `receipt.print` audit events as a clean bridge toward real Epson/Star adapter work
- Backoffice now also tracks receipt lifecycle counts such as issued, printed, emailed, LINE-shared, and pending receipt actions, while individual receipts keep channel-specific sent timestamps
- Receipt operations now emit dedicated dispatch-attempt records with channel, target, provider, status, and timestamp so later real adapters can plug into a delivery log instead of ad-hoc state flags
- Receipt share/print routes now run through a dispatch adapter layer first, so invalid or unavailable targets can produce explicit failed attempts instead of silently marking the receipt as delivered
- Failed receipt dispatch attempts can now be retried from the API and POS Console, reusing the original channel/target while creating a fresh success or failure attempt for ops visibility
- Email dispatch can now use a real SMTP adapter when `RECEIPT_EMAIL_PROVIDER=SMTP` and the `SMTP_*` variables are set; otherwise it falls back to the internal queue stub used by the demo stack
- LINE receipt dispatch can now also use a real LINE Messaging API push adapter when `RECEIPT_LINE_PROVIDER=LINE_OA` and `LINE_CHANNEL_ACCESS_TOKEN` are set; otherwise it falls back to the stub path used in local demos
- Receipt printing can now use a real raw TCP network printer adapter when `RECEIPT_PRINT_PROVIDER=TCP_PRINTER`; operators can pass `printerName` as `host:port` directly or resolve it from `PRINTER_TCP_MAP`
- The TCP printer adapter now supports both plain `TEXT` and basic `ESCPOS` output through `PRINTER_TCP_MODE`, including initialize, centered header, bold title, and paper cut commands for Epson/Star-style devices
- Security policy now also carries receipt-template settings, so operators can customize business name, branch label, footer/contact lines, and whether QR lookup or tip lines appear across print, email, and LINE dispatch flows
- Receipts can now also be upgraded into `TAX_INVOICE` or `E_TAX` documents with taxpayer metadata, and backoffice receipt ops now tracks how many tax documents have been issued
- E-Tax receipts now also have a submission flow with `PENDING_SUBMISSION / SUBMITTED / FAILED` state, submission references, and backoffice counts for pending vs submitted e-tax documents
- If Prisma is unavailable, API falls back to the in-memory seed state and keeps the same HTTP contract

## Staff app demo

- Login from the mobile app with `staff01 / 2468`
- Use `Clock In` for an in-range demo geofence
- Use `Outside Fence` to test geofence rejection on a fresh session
- Use `Clock Out` to close the current shift
- Select a table, tap menu items, and use `Send Order To POS` to create a live dine-in order from the staff app
- Use `เรียกผู้จัดการ` to create a manager notification tied to the selected table
- Use `แจ้งครัว` to send a short chat message into the kitchen feed
- Open `My Schedule & HR` to review assigned shifts and submit leave or swap requests from the same staff session
- Staff notifications now also receive `check bill` alerts from the public QR flow and `kitchen ready` alerts from KDS actions

## QR app demo

- Start `API` and `QR Web App`
- Open `http://localhost:3000` to see demo table links
- Open `http://localhost:3000/table/T2` for a table-scoped guest ordering session
- The QR app locks the table, loads in-stock menu items, supports Thai/English/Chinese/Japanese labels, lets guests choose modifiers and special notes, refreshes order status every 5 seconds, and can request check bill without login
- Modifier pricing is resolved server-side from the menu definition, so client payloads cannot override add-on prices
- The QR app is installable as a PWA from Chrome/Edge/mobile browsers through `Install` or `Add to Home screen`

## Backoffice reporting demo

- Login to `POS Console` as `cashier01` to see sales and payment reporting for today
- Login as `manager01` to unlock HR-aware staff performance in the same report feed
- The report endpoint aggregates paid orders, receipts, top-selling items, hourly sales buckets, and audit counts from the live repository state
- Managers and cashiers can now export CSV directly from `Backoffice Summary`, `Gateway Ops`, `Receipt Ops`, and `Inventory Control`
- Managers can also export the full alerts feed and kitchen-floor chat log from the POS console without staff-level audience scoping

## Delivery center demo

- Login to `POS Console` as `manager01`
- View aggregated marketplace orders, ETA, commission total, and active delivery workload in the `Delivery Center` panel
- Toggle a platform on or off and push a menu sync from the same console
- Export delivery summary, platform status, and active marketplace orders with `Export Delivery CSV`
- Delivery sales now also feed the `Delivery Mix` metric from live repository data

## Inventory demo

- Login to `POS Console` as `manager01` or `cashier01`
- Open the `Inventory Control` panel to review stock value, low-stock count, waste value, and reorder suggestions
- Create a dine-in order to auto-consume linked stock items from recipe rules
- Use `Receive Reorder` or `Log Waste` to append stock movements and update on-hand levels immediately
- Low-stock or out-of-stock transitions raise manager-facing alerts through the shared notification system

## Menu hub demo

- Login to `POS Console` as `manager01`, `cashier01`, or another role with `menu.manage`
- Use the `Menu Hub` form to create a new menu item with base price and optional happy-hour price
- Select a menu card and use `Pause Sale` or `Resume Sale` to toggle availability in real time
- Use `Export Menu CSV` to download the current catalog, multilingual labels, and modifier-group names
- Price updates are applied from the same panel, and out-of-stock menu items are blocked from new order creation on the backend

## Table management demo

- Login to `POS Console` as `manager01` or `cashier01`
- Drag a table on the floorplan board to update its live layout position
- Select a table to create or clear a reservation with guest name, party size, phone, and note
- Use `Export Tables CSV` to download live table, floorplan, and reservation state
- Use `Export Orders CSV` and `Export Kitchen CSV` to download live tickets and kitchen queue snapshots
- Reservation state is reflected in the shared table snapshot and clears automatically when a dine-in order is opened on that table

## Void and refund demo

- Login to `POS Console` as `manager01`
- Set a reason, then void an unpaid order or refund an issued receipt from the console
- Exception activity appears in the `Exceptions` panel and is also written into the audit feed
- Use `Export Exceptions CSV` to download the current incident feed
- Backoffice reporting now subtracts refunded amounts, tracks voided order count, and shows refund totals

## Split bill demo

- Login to `POS Console` as `cashier01` or `manager01`
- Select an open order and set `Split guests` above the service tickets
- Use `Split Bill` to issue multiple receipts against the same order in one transaction
- Receipt feed shows split markers like `1/2`, `2/2` and keeps refund flow per receipt

## Gateway payment demo

- Login to `POS Console` as `cashier01` or `manager01`
- Select an unpaid order and change the payment method to `PROMPTPAY`, `CARD`, `RABBIT LINE PAY`, or `TRUE MONEY`
- Use `Create Gateway Session` to create either a PromptPay QR payload or a hosted checkout URL in the `Gateway Sessions` panel
- Use `Capture` when the external payment is confirmed to turn the session into a normal paid receipt and audit event
- For provider-style callbacks, send `POST /api/payment-sessions/webhook` with header `x-payment-webhook-secret: <PAYMENT_WEBHOOK_SECRET>` and payload like `{ "reference": "...", "event": "PAID" }`
- Webhook callbacks are idempotent and can mark sessions as `CAPTURED`, `FAILED`, or `EXPIRED`
- Expired sessions are normalized automatically when the feed is loaded, and `FAILED / EXPIRED` sessions can be retried from the POS UI with `Retry`
- Backoffice reporting now includes a `Gateway Ops` summary for pending, captured, failed, expired, and pending gateway amount

## Tax invoice demo

- Login to `POS Console` as `manager01` or `cashier01`
- Pay an order first so a standard receipt exists
- In `Receipt Ops`, fill in taxpayer name, tax id, optional branch address, and optional e-tax email
- Choose `Tax Invoice` or `E-Tax`, then issue the document from the target receipt row
- `E-Tax` requires an email target, and receipt ops now shows both tax-document counts and taxpayer metadata on recent receipts
- After issuing `E-Tax`, use `Submit E-Tax` to simulate submission by email or RD portal and watch the receipt status update to `SUBMITTED` or `FAILED`

## Security admin demo

- Login to `POS Console` as `manager01`
- Manager and owner logins now require a second 2FA step; the demo challenge returns a local test code in the console UI
- Use the `Security Admin` panel to create accounts, block or unblock users, reset PIN, and force logout live sessions
- Use the same panel to manage the admin IP whitelist and choose whether 2FA applies to owner only or owner plus manager
- Use `Export Security CSV` to download managed users plus current policy and receipt-template settings
- The same panel now lets managers customize receipt branding and footer text used by printer, email, and LINE receipt dispatch
- Blocked or expired users cannot log in, force logout invalidates both refresh sessions and older access tokens, and non-whitelisted IPs are blocked from admin-grade routes

## HR desk demo

- Login to `POS Console` as `manager01`
- Use `HR Schedule Desk` to assign a new shift, review leave requests, and approve or reject swap requests
- Use `Export HR CSV` to download schedules, leave requests, and swap requests
- Use `Export Payroll CSV` to download hours worked, OT, orders handled, and tip totals from recorded shift sessions
- Staff members can open the mobile app, review their own schedule, and submit leave or swap requests back into the same shared repository state

## CRM and loyalty demo

- Login to `POS Console` as `manager01` or `cashier01`
- Create a member with phone, language, birthday, and optional LINE user id
- Select an open order and assign the member before payment
- Use `Export CRM CSV` to download member balances, top members, and birthday segments
- After payment, the member earns loyalty points automatically, total spend and last visit are updated, and CRM summary reflects the change

## Notes

- Current UI uses shared mock data to demonstrate the product direction and core flows
- Prisma schema is designed for PostgreSQL production deployment
- `Customer QR` currently targets the public API using `NEXT_PUBLIC_API_BASE_URL` and defaults to `http://127.0.0.1:4000`
- Real integrations like Omise, PromptPay, LINE OA, delivery APIs and printer drivers should be added as infrastructure adapters in later iterations
