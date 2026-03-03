# Crypto Stack - .crypto Domain DNS Resolution

A Docker-based service for resolving .crypto domains via the Ethereum blockchain.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Cloudflare    │────▶│  DNS Resolver   │────▶│  Blockchain     │
│  Worker/Client │     │  Gateway        │     │  Listener       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │                        │
                               ▼                        ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │  Redis Cache    │◀────│  Ethereum       │
                        │                 │     │  Mainnet        │
                        └─────────────────┘     └─────────────────┘
```

## Services

1. **blockchain-listener** - Monitors .crypto registry events on Ethereum
2. **dns-resolver** - Handles DNS queries for .crypto domains (REST + DNS)
3. **redis** - Caches domain resolutions
4. **cf-worker-manager** - Manages Cloudflare Worker deployment

## Quick Start

### 1. Configure Environment

```bash
cp .env.example .env
# Edit .env with your values
```

Required variables:
- `ETH_RPC_URL` - Ethereum RPC endpoint
- `CLOUDFLARE_API_TOKEN` - For Cloudflare Worker deployment (optional)

### 2. Deploy to Remote Server

```bash
# Deploy to Gibson's server
./deploy.sh
```

### 3. Test Resolution

```bash
# REST API
curl http://localhost:3000/resolve/mamaduka.crypto

# Health check
curl http://localhost:3000/health
```

## Contract Information

- **Registry Address**: `0xD1E5b0FF1287aA9f9A268759062E4Ab08b9Dacbe`
- **Blockchain**: Ethereum Mainnet
- **Token Standard**: ERC-721 (UNS - Unstoppable Domains)

## Cloudflare Integration

### Deploy Cloudflare Worker

```bash
cd cf-worker
npm install
CLOUDFLARE_API_TOKEN=your_token CLOUDFLARE_ACCOUNT_ID=your_id npm run deploy
```

### Configure DNS

1. Create a CNAME record for `mamaduka.crypto`
2. Point it to your worker or the DNS resolver

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /resolve/:domain` | Resolve a .crypto domain |
| `GET /health` | Health check |
| `GET /dns-query?name=x.crypto` | DNS-over-HTTPS query |

## Development

```bash
# Local development
docker-compose up

# View logs
docker-compose logs -f

# Stop
docker-compose down
```
