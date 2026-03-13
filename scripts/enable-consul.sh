#!/bin/bash
#
# Enable Consul Service Discovery
# This script starts Consul and registers all Gibson services
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"
CONSUL_HTTP_ADDR="${CONSUL_HTTP_ADDR:-http://localhost:8500}"

echo "╔════════════════════════════════════════════════════════╗"
echo "║     Gibson Consul Service Discovery - Enable Script    ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Step 1: Start Consul
echo "📦 Step 1: Starting Consul..."
cd "$WORKSPACE_DIR"

if docker ps | grep -q "consul"; then
    echo "   ✅ Consul is already running"
else
    echo "   🔄 Starting Consul container..."
    docker compose up -d consul 2>/dev/null || {
        echo "   ⚠️  docker-compose not found, trying docker compose..."
        docker compose up -d consul
    }
    
    # Wait for Consul to be ready
    echo "   ⏳ Waiting for Consul to be ready..."
    for i in {1..30}; do
        if curl -s "$CONSUL_HTTP_ADDR/v1/status/leader" > /dev/null 2>&1; then
            echo "   ✅ Consul is ready!"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "   ❌ Consul failed to start"
            exit 1
        fi
        sleep 2
    done
fi

# Step 2: Register services from config
echo ""
echo "📦 Step 2: Registering services from config..."
if [ -f "$WORKSPACE_DIR/consul/config/services.json" ]; then
    curl -s -X PUT "$CONSUL_HTTP_ADDR/v1/catalog/services" \
      -H "Content-Type: application/json" \
      -d @"$WORKSPACE_DIR/consul/config/services.json" > /dev/null
    
    echo "   ✅ Services registered from config file"
else
    echo "   ⚠️  Config file not found, skipping bulk registration"
fi

# Step 3: Register live Docker services
echo ""
echo "📦 Step 3: Discovering and registering live Docker services..."

# Get list of running containers
SERVICES=(
    "crypto-register-api:3002:/health"
    "crypto-register-frontend:80:/"
    "bridge_api:3000:/health"
    "bridge_heartbeat:3001:/health"
    "bridge_tracker:3002:/health"
    "keycloak:8080:/health/ready"
    "crypto_stack-options-bot-1:5000:/health"
    "stack-duka-dao-app-1:3000:/health"
    "gibsons_dash:3000:/health"
    "dao_wallet:3000:/health"
)

for service_def in "${SERVICES[@]}"; do
    IFS=':' read -r name port health <<< "$service_def"
    
    if docker ps --format '{{.Names}}' | grep -q "^${name}$"; then
        echo "   🔄 Registering $name..."
        "$SCRIPT_DIR/consul-register.sh" "$name" "$port" "$health" > /dev/null 2>&1 && \
            echo "   ✅ $name registered" || \
            echo "   ⚠️  $name registration failed (may need network access)"
    else
        echo "   ⏭️  Skipping $name (not running)"
    fi
done

# Step 4: Show status
echo ""
echo "📦 Step 4: Consul Service Status"
echo "═══════════════════════════════════════════════════════════"

curl -s "$CONSUL_HTTP_ADDR/v1/catalog/services" | jq -r '
  to_entries[] | 
  "   \(.key): \(.value | length) instance(s)"
' 2>/dev/null || echo "   (Unable to fetch service list)"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "✅ Consul service discovery enabled!"
echo ""
echo "📊 Access the Consul UI: http://localhost:8500"
echo "🔍 Query services: curl $CONSUL_HTTP_ADDR/v1/catalog/services"
echo "🏥 Check health:   curl $CONSUL_HTTP_ADDR/v1/health/service/<service-name>"
echo "🌐 DNS query:      dig @127.0.0.1 -p 8600 <service>.service.consul"
echo ""
