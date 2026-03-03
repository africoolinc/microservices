# Crypto Stack - .crypto Domain Resolution Service

## Overview
A Docker-based stack to resolve .crypto domains (ENS) via Cloudflare DNS integration.

## Architecture
- **Registry Contract**: `0xD1E5b0FF1287aA9f9A268759062E4Ab08b9Dacbe` (ENS .crypto Registry)
- **Blockchain Listener**: Monitors Ethereum for .crypto registry events
- **Resolver Service**: Queries resolver contracts for DNS records
- **API Gateway**: Exposes DNS-over-HTTPS (DoH) endpoints
- **Cloudflare Worker**: Handles DNS routing

## Services
1. `listener` - Blockchain event listener (Go/Rust/Node)
2. `resolver` - Domain resolution engine
3. `api` - REST/DoH API gateway
4. `worker` - Cloudflare Worker scripts (deployed separately)
5. `nginx` - Reverse proxy

## Deployment
- Deploy to: Gibson's server (10.144.118.159)
- Domain: `mamaduka.crypto` (via Cloudflare)
- Ports: 443 (HTTPS), 53 (DNS)

## Security
- Rate limiting enabled
- Cache TTL: 5 minutes for A/AAAA, 1 hour for CNAME/TXT
- Fallback to traditional DNS on failure
