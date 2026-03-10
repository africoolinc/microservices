# Gibson Trading API Documentation

## Overview

**Gibson Trading API** is a unified API-as-a-Service platform that provides programmatic access to:
- BTC Options trading signals and predictions
- Portfolio management
- Bridge API workflows and payments

### Base URL
```
http://<host>:5200/api/v1/
```

---

## Authentication

All endpoints (except `/health`, `/`, `/api/v1/tiers`, `/api/v1/auth/*`) require an API key.

### Getting Your API Key

1. **Register**: `POST /api/v1/auth/register`
2. **Login**: `POST /api/v1/auth/login`

Include your API key in requests:
```bash
curl -H "X-API-Key: gib_live_xxxxxxxxxxxx" http://localhost:5200/api/v1/price
```

---

## Subscription Tiers

| Tier | Price | Requests/min | Features |
|------|-------|--------------|----------|
| FREE | $0 | 100 | price, health |
| STARTER | $29/mo | 500 | + predictions, options chain, signals, portfolio |
| PRO | $59/mo | 2000 | + trade execution |
| ENTERPRISE | $99/mo | 10000 | + dedicated, webhooks |

---

## Endpoints

### Public Endpoints

#### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "service": "gibson-trading-api",
  "version": "1.0.0",
  "timestamp": "2026-03-10T18:00:00.000Z",
  "uptime": 3600
}
```

#### `GET /api/v1/tiers`
Get available subscription tiers.

---

### Authentication

#### `POST /api/v1/auth/register`
Register a new account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "name": "John Doe"
}
```

**Response:**
```json
{
  "message": "Registration successful",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "John Doe"
  },
  "apiKey": "gib_live_xxxxxxxxxxxx",
  "tier": "FREE"
}
```

#### `POST /api/v1/auth/login`
Login to get account info.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

#### `GET /api/v1/auth/key`
Get API key info and usage.

**Headers:** `X-API-Key: gib_live_xxxxxxxxxxxx`

#### `POST /api/v1/subscription/upgrade`
Upgrade your subscription.

**Request:**
```json
{
  "tier": "STARTER"
}
```

---

### Trading Endpoints

#### `GET /api/v1/price`
Get current BTC price.

**Headers:** `X-API-Key: gib_live_xxxxxxxxxxxx`

**Response:**
```json
{
  "price": 85000,
  "timestamp": "2026-03-10T18:00:00.000Z"
}
```

#### `GET /api/v1/predictions`
Get BTC options predictions. **STARTER+**

**Response:**
```json
{
  "btc": {
    "currentPrice": 85000,
    "predictedChange24h": 0.062,
    "predictedChange72h": 0.098,
    "confidence": 0.78,
    "surgeProbability": 0.82,
    "recommendation": "BUY_CALL"
  },
  "generatedAt": "2026-03-10T18:00:00.000Z"
}
```

#### `GET /api/v1/options/chain`
Get options chain. **STARTER+**

**Query Parameters:**
- `expiry` (optional): Expiry date (default: 7d)

#### `GET /api/v1/signals`
Get trading signals. **STARTER+**

**Query Parameters:**
- `limit` (optional): Number of signals (default: 20)

#### `GET /api/v1/portfolio`
Get portfolio positions. **STARTER+**

#### `POST /api/v1/trade/execute`
Execute a trade (dry run). **PRO+**

**Request:**
```json
{
  "action": "BUY_CALL",
  "strike": 88000,
  "expiry": "7d",
  "size": 0.01,
  "dryRun": true
}
```

---

### Bridge API Endpoints

#### `GET /api/v1/bridge/workflows`
Get Bridge workflows.

#### `GET /api/v1/bridge/payments`
Get Bridge payments.

#### `GET /api/v1/bridge/stats`
Get Bridge statistics.

---

## Rate Limits

| Tier | Requests/min |
|------|-------------|
| FREE | 100 |
| STARTER | 500 |
| PRO | 2000 |
| ENTERPRISE | 10000 |

When rate limited, you'll receive:
```json
{
  "error": "Rate limit exceeded",
  "retryAfter": 60
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request |
| 401 | Unauthorized (invalid/missing API key) |
| 403 | Forbidden (tier upgrade required) |
| 429 | Rate limit exceeded |
| 500 | Internal Server Error |

---

## SDK Examples

### JavaScript
```javascript
const API_KEY = 'gib_live_xxxxxxxxxxxx';

async function getPrice() {
  const res = await fetch('http://localhost:5200/api/v1/price', {
    headers: { 'X-API-Key': API_KEY }
  });
  return res.json();
}
```

### Python
```python
import requests

API_KEY = 'gib_live_xxxxxxxxxxxx'
HEADERS = {'X-API-Key': API_KEY}

def get_price():
    return requests.get(
        'http://localhost:5200/api/v1/price',
        headers=HEADERS
    ).json()
```

### cURL
```bash
curl -H "X-API-Key: gib_live_xxxxxxxxxxxx" \
  http://localhost:5200/api/v1/price
```

---

## Webhooks (ENTERPRISE)

Configure webhooks for real-time signals:

```json
{
  "webhookUrl": "https://your-app.com/webhook",
  "events": ["signal", "trade_executed"]
}
```

---

## Support

- Email: support@gibson.trade
- Discord: [Gibson API Community](https://discord.gg/gibson-trade)

---

*Last Updated: March 10, 2026*
