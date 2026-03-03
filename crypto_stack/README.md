# .crypto Domain Resolution Stack

A Docker-based service for resolving Unstoppable Domains (.crypto) with Cloudflare DNS integration.

## Architecture

```
┌─────────────────┐
│   DNS Client    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Nginx Proxy   │ :80, :443
└────────┬────────┘
         │
    ┌────┴────┐
   ┌──────── ▼         ▼
┐ ┌──────────────┐
│DNS Proxy│ │CF Worker    │
│ :8053  │ │Sim: :8888   │
└───┬────┘ └──────┬───────┘
    │             │
    └──────┬──────┘
           ▼
┌─────────────────┐
│ Resolver Gateway│ :8080
│ (Blockchain)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Blockchain Node │
│ (Ethereum)      │
└─────────────────┘
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| blockchain-listener | - | Monitors .crypto registry events |
| resolver-gateway | 8080 | Queries resolver contracts for DNS records |
| doh-proxy | 8053 | DNS-over-HTTPS proxy |
| cf-worker-sim | 8888 | Cloudflare Worker simulator |
| nginx | 80, 443 | Reverse proxy & load balancer |
| redis | 6379 | Caching layer |

## Quick Start

### 1. Prerequisites

- Docker & Docker Compose
- Ethereum RPC URL (Infura/Alchemy)

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your Ethereum RPC URL
```

### 3. Deploy

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### 4. Test

```bash
# Resolve a .crypto domain
curl http://localhost:8888/resolve/vitalik.crypto

# DNS query
curl "http://localhost:8888/dns-query?name=vitalik.crypto&type=A"

# Health check
curl http://localhost:8888/health
```

## Endpoints

- `GET /resolve/{domain}` - Full domain resolution
- `GET /dns-query?name={domain}&type={A|AAAA|TXT}` - DNS-over-HTTPS style
- `GET /health` - Health check
- `GET /` - Service info

## Cloudflare Integration

For production Cloudflare Worker deployment:

1. Deploy the resolver logic as a Cloudflare Worker
2. Configure DNS to point to your worker
3. Use Workers KV for caching

## Contract Information

- **Registry**: `0xD1E5b0FF1287aA9f9A268759062E4Ab08b9Dacbe`
- **Network**: Ethereum Mainnet

## License

MIT
