# MyPOS — Production Checklist

Run `npx tsx scripts/prod-check.ts` to get a machine-readable status at any time.

---

## Blockers — must fix before go-live

### 1. Payment — PromptPay
- Set `PAYMENT_PROMPTPAY_PROVIDER=PROMPTPAY_REAL`
- Set `PROMPTPAY_MERCHANT_ID=<your merchant ID from PromptPay>`
- Set `PROMPTPAY_MERCHANT_PHONE=<registered phone number>`

### 2. Payment — Card gateway
Choose one and fill in the corresponding keys:

**Omise**
- Set `PAYMENT_CARD_PROVIDER=OMISE_REAL`
- Set `OMISE_PUBLIC_KEY=pkey_...`
- Set `OMISE_SECRET_KEY=skey_...`

**2C2P**
- Set `PAYMENT_CARD_PROVIDER=2C2P_REAL`
- Set `TWOC2P_MERCHANT_ID=...`
- Set `TWOC2P_SECRET_KEY=...`

### 3. Payment — Webhook secret
- Set `PAYMENT_WEBHOOK_SECRET=<secret from payment provider dashboard>`

### 4. LINE OA receipt
- Set `RECEIPT_LINE_PROVIDER=LINE_OA`
- Set `LINE_CHANNEL_ACCESS_TOKEN=<from LINE Developers console>`
- Verify `LINE_API_BASE=https://api.line.me`

### 5. CORS
- Set `CORS_ORIGIN=https://pos.yourstore.com,https://qr.yourstore.com,https://kds.yourstore.com`
  (comma-separated, exact origins — no trailing slash)

### 6. Database & JWT (if not already done)
- Set `DATABASE_URL=postgresql://user:pass@host:5432/mypos`
- Generate: `node -e "console.log(require('crypto').randomBytes(64).toString('hex'))"`
  → `JWT_SECRET=<64-char hex>`
  → `REFRESH_TOKEN_SECRET=<different 64-char hex>`

---

## Warnings — fix before go-live (non-fatal but affects features)

### 7. KDS API key
- Generate: `node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"`
- Set `KDS_API_KEY=<key>` in API env
- Set `VITE_KDS_TOKEN=<same key>` in KDS Vite env
- Without this: KDS cannot take kitchen actions and WS is rejected

### 8. Staff Mobile API URL
- Set `EXPO_PUBLIC_API_BASE_URL=https://pos-api.yourstore.com` in EAS Build env
- Set `EXPO_PUBLIC_EAS_PROJECT_ID=<UUID from expo.dev>` for push notifications
- Without this: mobile app falls back to hardcoded LAN IP `192.168.100.9:4000`

### 9. API HTTPS URL
- Set `VITE_API_BASE_URL=https://pos-api.yourstore.com` (must start with `https://`)

### 10. E-Tax (RD API) — warning only, not a day-1 blocker
- Set `ETAX_PROVIDER=RD_REAL`
- Set `RD_API_BASE=https://etax.rd.go.th`
- Set `RD_CLIENT_ID=<from RD portal>`
- Set `RD_CLIENT_SECRET=<from RD portal>`
- Without this: e-tax submission queued locally, not sent to RD

---

## SMTP (email receipts)
- Set `RECEIPT_EMAIL_PROVIDER=SMTP`
- Set `SMTP_HOST=smtp.yourprovider.com`
- Set `SMTP_PORT=587`
- Set `SMTP_USER=receipts@yourstore.com`
- Set `SMTP_PASS=<app password>`
- Set `SMTP_FROM=receipts@yourstore.com`

---

## Hardware testing required

| Device | What to verify |
|--------|---------------|
| POS terminal | Login → order → payment full flow |
| Receipt printer (TCP) | `PRINTER_TCP_MAP=main=<IP>:9100` responds; `PRINTER_TCP_MODE=ESCPOS` for thermal |
| KDS touchscreen | WS live updates arrive; kitchen actions (Ready/Ack/OOS) round-trip |
| Staff mobile device | GPS clock-in geofence passes; push notifications received |
| QR kiosk tablet | Customer QR flow: lock table → order → check bill |

---

## Infrastructure

| Item | Notes |
|------|-------|
| PostgreSQL | Run `npx prisma migrate deploy` before first start |
| Redis | Required for rate-limit state; standalone or managed (e.g. Upstash) |
| Reverse proxy (Nginx/Caddy) | Terminate TLS, proxy to port 4000; `trustProxy: true` already set in API |
| Process manager | `pm2 start` or Docker with `restart: unless-stopped` |
| Backup script | `scripts/backup.sh` — schedule via cron |

---

## Final go-live steps

```bash
# 1. Copy and fill in all values
cp .env.production.example .env

# 2. Run prod:check — must show 0 blockers
npx tsx scripts/prod-check.ts

# 3. Run DB migrations
npx prisma migrate deploy

# 4. Start API
npm run start -w apps/api

# 5. Build and deploy frontends
npm run build -w apps/pos-console
npm run build -w apps/customer-qr
npm run build -w apps/kds

# 6. Build Staff Mobile EAS build
cd apps/staff-mobile && eas build --platform all
```
