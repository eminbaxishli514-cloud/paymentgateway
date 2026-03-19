# Payment Gateway Demo

A demonstration payment gateway with a Python backend and a Stripe-inspired frontend. No real payments are processed — this is for testing and learning.

## Features

- **Multiple payment methods**: Card, PayPal, Apple Pay
- **Saved cards**: Choose from demo saved cards or enter new card details
- **Promo codes**: DEMO10 (10% off), SAVE20 (20% off), HALFOFF (50% off)
- **SMS verification**: Card payments require 3D Secure–style verification (demo code: 123456)
- **Progress indicator**: Payment → Verify → Complete
- **Receipt**: View and download receipt after successful payment
- **Transaction history**: View all payments from the current session
- **Light/dark mode**: Theme toggle with persisted preference
- **Responsive layout**: Optimized for phones, tablets, and desktops

## Quick Start

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) for the checkout page.

## Test Data

| Item | Value |
|------|-------|
| Success card | 4242 4242 4242 4242 |
| Decline card | 0000 0000 0000 0000 |
| SMS code | 123456 |
| Promo codes | DEMO10, SAVE20, HALFOFF |

## Pages

- `/` — Checkout
- `/verify?payment_id=xxx` — SMS verification (opens after Pay for card)
- `/receipt?payment_id=xxx` — Receipt
- `/history` — Transaction history
- `/store` — Marketplace
- `/admin` — **SIEM / security dashboard** (in-memory demo: traffic, suspicious IPs, blocklist). Set `ADMIN_API_KEY` and paste it in the UI as the admin token.

### SIEM (demo)

Lightweight in-app SIEM: logs API and main page hits, aggregates per IP, flags high request rates (`SIEM_SUSPICIOUS_RPM` / `SIEM_CRITICAL_RPM`), and lets you block IPs (403 for blocked clients). Data is **in memory** only. For production, stream logs to Splunk, Elastic, Datadog, etc.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/payments/promo/{code}` | Validate promo code |
| GET | `/api/payments/saved-cards` | List saved cards |
| POST | `/api/payments/` | Process payment |
| POST | `/api/payments/verify` | Verify SMS and complete payment |
| GET | `/api/payments/history` | Transaction history |
| GET | `/api/payments/receipt/{id}` | Receipt data |
| GET | `/api/payments/{id}` | Payment details |
| POST | `/api/payments/refund` | Refund a payment |

**Admin (header `X-Admin-Token` = `ADMIN_API_KEY`):**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/siem/dashboard` | Summary, top IPs, thresholds |
| GET | `/api/admin/siem/events` | Recent request events |
| GET | `/api/admin/siem/blocked` | IP blocklist |
| POST | `/api/admin/siem/block` | Body `{"ip":"1.2.3.4"}` |
| POST | `/api/admin/siem/unblock` | Body `{"ip":"1.2.3.4"}` |

Payment and refund IDs use `secrets.token_hex(16)` (128-bit) with prefixes `pay_` / `ref_`.

## Project Structure

```
paymentgateway/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── schemas/
│   │   ├── routers/
│   │   └── services/
│   ├── static/
│   │   ├── index.html, verify.html, receipt.html, history.html
│   │   ├── css/style.css
│   │   └── js/
│   └── requirements.txt
└── README.md
```

## License

MIT
