# Production Runbook

## Release Gate

Run this before every pilot or release candidate:

```powershell
npm run release:check
```

Expected result:

- `readyForPilot = true`
- `readyForProduction = false` is acceptable until real provider credentials are installed

## Production Env

Create `.env.production` from `.env.production.example` and replace every placeholder.

Required before production:

- `NODE_ENV=production`
- `VITE_API_BASE_URL=https://...`
- `DATABASE_URL=postgresql://...`
- `REDIS_URL=redis://...`
- `JWT_SECRET`
- `REFRESH_TOKEN_SECRET`
- `PAYMENT_WEBHOOK_SECRET`
- `PAYMENT_PROMPTPAY_PROVIDER=PROMPTPAY_REAL`
- `PROMPTPAY_MERCHANT_ID`
- `PROMPTPAY_MERCHANT_PHONE`
- `PAYMENT_CARD_PROVIDER=OMISE_REAL` or `2C2P_REAL`
- `OMISE_PUBLIC_KEY / OMISE_SECRET_KEY` or `TWOC2P_MERCHANT_ID / TWOC2P_SECRET_KEY`
- `RECEIPT_EMAIL_PROVIDER=SMTP`
- `SMTP_HOST / SMTP_FROM / SMTP_USER / SMTP_PASS`
- `RECEIPT_LINE_PROVIDER=LINE_OA`
- `LINE_CHANNEL_ACCESS_TOKEN`

Recommended before production:

- `RECEIPT_PRINT_PROVIDER=TCP_PRINTER`
- `PRINTER_TCP_MAP`
- `ETAX_PROVIDER=RD_REAL`
- `RD_API_BASE / RD_CLIENT_ID / RD_CLIENT_SECRET`

## Readiness Checks

```powershell
npm run prod:check -- --env .env.production
npm run prod:data:check -- --env .env.production
npm run prod:compose:config
```

Expected result:

- `prod:check` has no blockers
- `prod:data:check` returns Postgres and Redis reachable
- `prod:compose:config` renders without compose errors

## Database Bootstrap

For a fresh production database:

```powershell
npm run db:generate
npm run db:push
npm run db:seed
```

For a real rollout, run seed only for demo or initial branch setup. Do not reseed over live production data.

## Backup And Restore

Create a manual Postgres backup:

```powershell
npm run db:backup
```

Restore from a backup file:

```powershell
npm run db:restore -- backups/mypos-YYYY.sql
```

Backups are written to `backups/`, which is intentionally ignored by git.

## Docker Compose Deploy

```powershell
docker compose -f docker-compose.prod.example.yml --env-file .env.production up -d --build
```

Health checks:

```powershell
curl https://your-api-domain.example/health
npm run prod:data:check -- --env .env.production
```

## Pilot Closeout

After a pilot day:

- Export sales, receipts, gateway sessions, audit, inventory, payroll, CRM, delivery, tables, orders, kitchen, alerts, and chat CSVs from POS Console
- Review failed receipt dispatch attempts
- Review payment gateway pending/failed/expired sessions
- Review void/refund exception feed
- Confirm backup snapshot exists from `npm run db:backup` or the managed database provider
