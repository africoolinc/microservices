# Crypto Register Service

Phone number registration with .crypto domain allocation.

## Deployment

**Ports:**
- Frontend: `3001` (http://<server>:3001)
- API: `3002` (http://<server>:3002)

## Quick Start

```bash
# Deploy locally
cd services/crypto-register
./deploy.sh

# Or manually
docker-compose up -d
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/register` | POST | Register phone + domain |
| `/api/check-domain` | GET | Check domain availability |
| `/api/client` | GET | Get client by phone hash |
| `/api/status` | GET | System status |
| `/health` | GET | Health check |

## Registration Flow

1. User enters phone number (+254...)
2. User chooses .crypto domain name
3. User selects services (Signals free, API $29/mo)
4. Registration saved to `/data/registrations.json`
5. User receives confirmation with domain

## Data Storage

Registrations stored in Docker volume: `crypto-register-data`

Schema:
```json
{
  "id": "uuid",
  "phoneHash": "sha256-first12chars",
  "domain": "name.crypto",
  "email": "optional",
  "services": ["signals", "api"],
  "createdAt": "ISO8601",
  "status": "active"
}
```

## Integration

### Check Client Status
```bash
curl http://localhost:3002/api/client?phone=<phone_hash>
```

### Register New Client
```bash
curl -X POST http://localhost:3002/api/register \
  -H "Content-Type: application/json" \
  -d '{"phone":"+2547XX","domain":"name.crypto","services":["signals"]}'
```

## Status

- **Created:** 2026-03-12
- **Port:** 3001 (frontend), 3002 (API)
- **Network:** microservices-stack_backend
- **Status:** ✅ Running