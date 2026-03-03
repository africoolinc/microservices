# 🔗 .crypto Domain Resolution Service

Blockchain-powered DNS resolution for .crypto domains with Cloudflare integration.

## Quick Start

```bash
# Navigate to stack directory
cd ~/projects/members/Gibson/crypto_stack

# Copy environment file
cp .env.example .env

# Edit .env with your ETH RPC URL
nano .env

# Start the stack
docker-compose up -d

# Check status
docker-compose ps
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| resolver | 3000 | Domain resolution API |
| dns | 8053 | DNS-over-HTTPS endpoint |
| api | 8888 | HTTP reverse proxy |
| cache | 6379 | Redis for caching |

## API Endpoints

### Resolve a .crypto domain
```bash
curl "http://localhost:3000/resolve?domain=mamaduka.crypto"
```

### DNS-over-HTTPS (Cloudflare-style)
```bash
curl "http://localhost:8053/dns-query?name=mamaduka.crypto&type=A"
```

### Via Nginx proxy
```http://localhost:bash
curl "8888/resolve?domain=mamaduka.crypto"
curl "http://localhost:8888/dns-query?name=mamaduka.crypto&type=A"
```

## Deployment to Cloudflare

### Option 1: Cloudflare Worker
1. Go to Cloudflare Dashboard → Workers
2. Create new worker
3. Copy contents from `worker/worker.js`
4. Deploy

### Option 2: Traditional DNS
Configure in Cloudflare:
- **A Record**: `dns.mamaduka.crypto` → Your server IP (proxied)
- **CNAME**: `mamaduka.crypto` → Your domain

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| ETH_RPC_URL | Ethereum JSON-RPC endpoint | https://eth.llamarpc.com |
| REGISTRY_ADDRESS | .Crypto registry contract | 0xD1E5b0FF1287aA9f9A268759062E4Ab08b9Dacbe |
| CACHE_TTL | Cache duration (seconds) | 300 |

## Architecture

```
Client Request
      ↓
   DNS Query
      ↓
┌─────────────┐
│  DNS (8053) │ ← Handles DoH queries
└─────────────┘
      ↓
┌─────────────┐
│ Resolver    │ ← Queries Ethereum blockchain
│   (3000)    │
└─────────────┘
      ↓
┌─────────────┐
│  Redis      │ ← Caches results
│  Cache      │
└─────────────┘
```

## Contract Information

- **Registry**: [0xD1E5b0FF1287aA9f9A268759062E4Ab08b9Dacbe](https://etherscan.io/token/0xD1E5b0FF1287aA9f9A268759062E4Ab08b9Dacbe)
- **Type**: ERC-721 (NFT)
- **Network**: Ethereum Mainnet
