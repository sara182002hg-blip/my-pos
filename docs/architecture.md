# Architecture Overview

## Core decision

Build one platform with four technical layers:

1. Client apps: POS Console, Staff Mobile, KDS
2. Domain layer: shared types, validation, workflow contracts
3. Core backend: API, auth, real-time, queue workers
4. Infrastructure adapters: payment, delivery, notifications, printers, tax, storage

This keeps the product aligned with the user's request for three main apps while still supporting QR ordering, delivery and backoffice as first-class modules.

## Operational boundaries

### POS Console

- Dine-in order creation and editing
- Floorplan and reservation management
- Payment, receipt, refund and void workflows
- Menu management and stock flags
- Delivery control center and backoffice dashboards
- Security admin, roles and audit browsing

### Staff Mobile

- Username + PIN login
- Biometric unlock
- GPS geofence check before shift
- Order taking from floorplan
- Personal performance, OT, tips and shift schedule
- Alerts from kitchen and check-bill requests

### KDS

- Station-specific queue board
- Large touch-first controls
- Allergen and priority emphasis
- SLA timer and delay reason capture
- Ready / out-of-stock signals back to POS and staff

## Backend modules

### Identity & Access

- JWT access token with 8-hour expiry
- Refresh token rotation and logout path
- Role policy matrix for owner, manager, cashier, staff, kitchen
- Append-only audit log
- Current scaffold includes demo login/session and permission contracts so UI and API already share role semantics

### Order orchestration

- `OrderService` as the source of truth for line items and state transitions
- Event publication when orders are sent, acknowledged, prepared, served, paid, voided
- Redis-backed job queues for notifications, delivery sync and scheduled summaries
- Current starter already covers login, order creation, kitchen acknowledge/ready/out-of-stock, and payment settlement with websocket snapshot broadcasts
- Payment settlement now issues receipt records and protected receipt/audit feeds for cashier or manager workflows

### Branch edge strategy

- Recommended production topology is hybrid edge + cloud
- Branch devices talk to a local edge service for low-latency and offline continuity
- Edge syncs with the cloud control plane for central reporting and multi-branch management
- Current code now has a repository/data-source layer so swapping between memory seed data and Prisma bootstrap does not affect route contracts
- Write-side events now also have a Prisma persistence adapter path, while memory remains the safe fallback in local environments without Postgres

## Data model highlights

- `Order` keeps source channel, guest count, totals and lifecycle state
- `OrderItem` stores kitchen station, allergen flags and modifier JSON
- `DiningTable` handles QR lock and reservation links
- `ShiftSession` stores GPS, device ID, IP and OT
- `AuditLog` is append-only for security-sensitive activity
- `DeliveryOrder` isolates marketplace-specific metadata from dine-in flows

## Recommended next implementation steps

1. Add Zod schemas and repository interfaces to `packages/domain`
2. Split API into modules: auth, orders, tables, kitchen, payments, shifts, reports
3. Replace mock fixtures with Prisma repositories and seed scripts
4. Add Socket.IO or event broadcasting abstraction for live updates
5. Introduce Tailwind + shadcn/ui in web apps and Expo Router in the mobile app
6. Add contract tests for order state transitions and payment settlement flows
