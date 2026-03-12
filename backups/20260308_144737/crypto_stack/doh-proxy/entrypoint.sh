#!/bin/bash
# DNS Proxy - Handles DNS-over-HTTPS and traditional DNS queries

UPSTREAM_RESOLVER=${UPSTREAM_RESOLVER:-http://resolver-gateway:8080}
CLOUDFLARE_DNS=${CLOUDFLARE_DNS:-1.1.1.1}

echo "Starting DNS Proxy..."
echo "Upstream Resolver: $UPSTREAM_RESOLVER"
echo "Fallback DNS: $CLOUDFLARE_DNS"

# Simple DNS proxy using Node.js
node /app/dns-proxy.js
