#!/bin/bash
#
# Consul Service Registration Script
# Usage: ./consul-register.sh <service_name> <service_port> <health_endpoint>
#
# Example: ./consul-register.sh crypto-api 3002 /health
#

set -e

CONSUL_HTTP_ADDR="${CONSUL_HTTP_ADDR:-http://consul:8500}"
SERVICE_NAME="${1:-}"
SERVICE_PORT="${2:-}"
HEALTH_CHECK="${3:-/health}"
SERVICE_ID="${SERVICE_NAME}-$(hostname | cut -c1-8)"

# Validate arguments
if [ -z "$SERVICE_NAME" ] || [ -z "$SERVICE_PORT" ]; then
    echo "Usage: $0 <service_name> <service_port> [health_endpoint]"
    echo "Example: $0 crypto-api 3002 /health"
    exit 1
fi

# Get container/service IP
SERVICE_ADDRESS=$(hostname -i 2>/dev/null || hostname -f 2>/dev/null || echo "localhost")

echo "🔵 Registering service with Consul..."
echo "   Service: $SERVICE_NAME"
echo "   ID: $SERVICE_ID"
echo "   Port: $SERVICE_PORT"
echo "   Address: $SERVICE_ADDRESS"
echo "   Health: $HEALTH_CHECK"
echo "   Consul: $CONSUL_HTTP_ADDR"

# Create registration JSON
REGISTRATION=$(cat <<EOF
{
  "ID": "$SERVICE_ID",
  "Name": "$SERVICE_NAME",
  "Port": $SERVICE_PORT,
  "Address": "$SERVICE_ADDRESS",
  "Tags": ["docker", "auto-registered", "$(date +%Y%m%d)"],
  "Meta": {
    "registered_by": "consul-register.sh",
    "hostname": "$(hostname)",
    "timestamp": "$(date -Iseconds)"
  },
  "Check": {
    "ID": "${SERVICE_ID}-health",
    "Name": "HTTP Health Check",
    "HTTP": "http://${SERVICE_ADDRESS}:${SERVICE_PORT}${HEALTH_CHECK}",
    "Interval": "10s",
    "Timeout": "5s",
    "DeregisterCriticalServiceAfter": "60s"
  }
}
EOF
)

# Register with Consul
RESPONSE=$(curl -s -w "\n%{http_code}" -X PUT "$CONSUL_HTTP_ADDR/v1/agent/service/register" \
  -H "Content-Type: application/json" \
  -d "$REGISTRATION")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Service registered successfully!"
    
    # Verify registration
    echo ""
    echo "📋 Verifying registration..."
    curl -s "$CONSUL_HTTP_ADDR/v1/catalog/service/$SERVICE_NAME" | jq -r '.[] | "   Found: \(.ServiceID) on \(.ServiceAddress):\(.ServicePort)"' 2>/dev/null || echo "   (Verification pending...)"
else
    echo "❌ Failed to register service (HTTP $HTTP_CODE)"
    echo "Response: $(echo "$RESPONSE" | head -n-1)"
    exit 1
fi

# Keep script running for health check loop (optional)
if [ "$4" = "--watch" ]; then
    echo ""
    echo "👁️  Watching service health (Ctrl+C to stop)..."
    while true; do
        STATUS=$(curl -s "$CONSUL_HTTP_ADDR/v1/health/service/$SERVICE_NAME" | jq -r '.[] | select(.Checks[0].Status == "passing") | .Service.ID' | head -1)
        if [ -n "$STATUS" ]; then
            echo "✅ $(date +%H:%M:%S) - Service healthy"
        else
            echo "⚠️  $(date +%H:%M:%S) - Service not passing health checks"
        fi
        sleep 30
    done
fi
