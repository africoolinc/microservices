# crypto_stack - Deployment Status

## Summary
The .crypto domain resolution stack has been prepared and is ready for deployment.

## What's Ready
- ✅ Docker Compose stack with 6 services
- ✅ Ethereum RPC configured (using public endpoint)
- ✅ SSL certificates generated
- ✅ Cloudflare Worker documentation created
- ✅ Deploy script configured

## Current Status
- **Remote Host**: Gibson's machine (10.144.118.159) - **UNREACHABLE** (no network route)
- **Local Deployment**: Possible

## Files Created/Modified
- `.env` - Environment configuration with Ethereum RPC
- `deploy.sh` - Fixed deployment script
- `CLOUDFLARE_WORKER.md` - Cloudflare Worker deployment guide

## Deployment Options

### Option 1: Remote (when Gibson's machine is online)
```bash
cd projects/members/Gibson/crypto_stack
./deploy.sh
```

### Option 2: Local Development
```bash
cd projects/members/Gibson/crypto_stack
docker-compose up -d
```

### Option 3: Cloudflare Workers
See `CLOUDFLARE_WORKER.md` for full instructions.

## Services
| Service | Port | Description |
|---------|------|-------------|
| cf-worker-sim | 8888 | Main API endpoint |
| resolver-gateway | 8080 | Blockchain resolver |
| doh-proxy | 8053 | DNS proxy |
| blockchain-listener | - | Event listener |
| redis | 6379 | Cache |
| nginx | 80/443 | Reverse proxy |

## Test Endpoints
- `http://localhost:8888/resolve/mamaduka.crypto`
- `http://localhost:8888/health`
- `http://localhost:8888/dns-query?name=mamaduka.crypto&type=A`

## Contract Info
- **Registry**: `0xD1E5b0FF1287aA9f9A268759062E4Ab08b9Dacbe`
- **Network**: Ethereum Mainnet
- **RPC**: `https://eth.llamarpc.com`
