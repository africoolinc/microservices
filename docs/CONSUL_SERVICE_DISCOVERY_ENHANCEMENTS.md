# Consul Service Discovery Enhancements

## Current State Analysis

### Existing Infrastructure
- **Consul**: Defined in `docker-compose.yml` (hashicorp/consul:1.17) but **NOT running**
- **Kong API Gateway**: Configured with Consul dependency
- **Crypto Stack**: 10+ microservices without service discovery
- **Bridge Services**: 3 services (api, heartbeat, tracker) without registration
- **Keycloak**: Auth service without health-based discovery

### Problems Identified
1. ❌ Consul defined but not started
2. ❌ No automatic service registration
3. ❌ No health check integration with Consul
4. ❌ Services use static hostnames/ports
5. ❌ No service mesh for secure service-to-service communication
6. ❌ No automatic failover/load balancing

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CONSUL SERVICE MESH                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Consul     │  │   Consul     │  │   Consul     │          │
│  │   Server     │  │   Client     │  │   Client     │          │
│  │   (UI:8500)  │  │   (sidecar)  │  │   (sidecar)  │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│         └─────────────────┼─────────────────┘                   │
│                           │                                     │
│  ┌────────────────────────▼─────────────────────────┐           │
│  │              Consul Connect (mTLS)               │           │
│  └────────────────────────┬─────────────────────────┘           │
│                           │                                     │
│    ┌──────────┐  ┌────────┴───────┐  ┌──────────┐              │
│    │  Kong    │  │  Crypto Stack  │  │  Bridge  │              │
│    │ Gateway  │  │   Services     │  │ Services │              │
│    └──────────┘  └────────────────┘  └──────────┘              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Enable Consul & Basic Registration (Priority: HIGH)

#### 1.1 Start Consul Server

```yaml
# docker-compose.yml - Enhanced Consul Configuration
services:
  consul:
    image: hashicorp/consul:1.17
    container_name: consul
    command: >
      agent -server
      -bootstrap-expect=1
      -ui
      -client=0.0.0.0
      -bind=0.0.0.0
      -datacenter=gibson-dc
      -log-level=INFO
    ports:
      - '8500:8500'  # HTTP API
      - '8600:8600/udp'  # DNS
      - '8300:8300'  # Server RPC
      - '8301:8301'  # Serf LAN
      - '8302:8302'  # Serf WAN
    volumes:
      - consul-data:/consul/data
      - consul-config:/consul/config
    networks:
      - backend
    healthcheck:
      test: ["CMD", "consul", "info"]
      interval: 10s
      timeout: 5s
      retries: 3
    restart: unless-stopped

volumes:
  consul-data:
  consul-config:
```

#### 1.2 Service Registration Templates

Create `consul/config/services.json`:

```json
{
  "services": [
    {
      "name": "crypto-register-api",
      "id": "crypto-register-api-1",
      "port": 3002,
      "address": "crypto-register-api",
      "tags": ["api", "crypto", "v1"],
      "meta": {
        "version": "1.0.0",
        "team": "crypto"
      },
      "check": {
        "id": "crypto-register-api-health",
        "name": "HTTP Health Check",
        "http": "http://crypto-register-api:3002/health",
        "interval": "10s",
        "timeout": "5s",
        "deregister_critical_service_after": "60s"
      }
    },
    {
      "name": "bridge-api",
      "id": "bridge-api-1",
      "port": 3000,
      "address": "bridge_api",
      "tags": ["api", "bridge", "v1"],
      "check": {
        "http": "http://bridge_api:3000/health",
        "interval": "10s",
        "timeout": "5s"
      }
    },
    {
      "name": "keycloak",
      "id": "keycloak-1",
      "port": 8080,
      "address": "keycloak",
      "tags": ["auth", "oidc", "v25"],
      "check": {
        "http": "http://keycloak:8080/health/ready",
        "interval": "15s",
        "timeout": "10s"
      }
    }
  ]
}
```

---

### Phase 2: Consul Connect Service Mesh (Priority: MEDIUM)

#### 2.1 Enable Consul Connect

Add to `consul/config/connect.hcl`:

```hcl
connect {
  enabled = true
}

# Default service intentions
acl {
  enabled = true
  default_policy = "deny"
  down_policy = "extend-cache"
}
```

#### 2.2 Service Intentions (Zero Trust)

```json
{
  "Kind": "service-intentions",
  "Name": "crypto-register-api",
  "Sources": [
    {
      "Name": "kong",
      "Action": "allow"
    },
    {
      "Name": "bridge-api",
      "Action": "allow"
    }
  ]
}
```

---

### Phase 3: Automatic Registration (Priority: HIGH)

#### 3.1 Consul Template for Docker Services

Create `scripts/consul-register.sh`:

```bash
#!/bin/bash
# Automatic service registration with Consul

CONSUL_HTTP_ADDR="${CONSUL_HTTP_ADDR:-http://consul:8500}"
SERVICE_NAME="$1"
SERVICE_PORT="$2"
HEALTH_CHECK="$3"

# Register service
curl -s -X PUT "$CONSUL_HTTP_ADDR/v1/agent/service/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"ID\": \"${SERVICE_NAME}-$(hostname)\",
    \"Name\": \"$SERVICE_NAME\",
    \"Port\": $SERVICE_PORT,
    \"Address\": \"$(hostname -i | awk '{print $1}')\",
    \"Tags\": [\"docker\", \"$(date +%Y%m%d)\"],
    \"Check\": {
      \"HTTP\": \"http://localhost:$SERVICE_PORT$HEALTH_CHECK\",
      \"Interval\": \"10s\",
      \"Timeout\": \"5s\",
      \"DeregisterCriticalServiceAfter\": \"60s\"
    }
  }"

echo "Registered $SERVICE_NAME on port $SERVICE_PORT"
```

#### 3.2 Docker Compose Integration

```yaml
services:
  crypto-register-api:
    build:
      context: ./api
      dockerfile: Dockerfile
    environment:
      CONSUL_HTTP_ADDR: http://consul:8500
      SERVICE_NAME: crypto-register-api
      SERVICE_PORT: 3002
    entrypoint: ["/bin/sh", "-c"]
    command:
      - |
        /consul-register.sh crypto-register-api 3002 /health &
        exec node server.js
    networks:
      - backend
    depends_on:
      consul:
        condition: service_healthy
```

---

### Phase 4: Health Monitoring & Alerting (Priority: MEDIUM)

#### 4.1 Consul Health Dashboard

```yaml
# Add to docker-compose.yml
consul-exporter:
  image: prom/consul-exporter:latest
  container_name: consul-exporter
  command:
    - '--consul.server=consul:8500'
  ports:
    - '9107:9107'
  networks:
    - backend

grafana:
  image: grafana/grafana:latest
  environment:
    - GF_INSTALL_PLUGINS=grafana-clock-panel,grafana-piechart-panel
  volumes:
    - grafana-data:/var/lib/grafana
    - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
  ports:
    - '3000:3000'
  depends_on:
    - prometheus
```

#### 4.2 Alerting Rules

```yaml
# prometheus/rules/consul-alerts.yml
groups:
  - name: consul
    rules:
      - alert: ConsulServiceDown
        expr: consul_catalog_service_node_healthy == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.service_name }} is down"
          
      - alert: ConsulHealthCheckFailing
        expr: consul_health_check_status != 1
        for: 5m
        labels:
          severity: warning
```

---

### Phase 5: DNS-Based Service Discovery (Priority: LOW)

#### 5.1 Enable Consul DNS

```bash
# Services can now resolve via DNS
# crypto-register-api.service.consul
# bridge-api.service.consul
# keycloak.service.consul

# Example: curl http://crypto-register-api.service.consul:3002/health
```

---

## Quick Start Commands

```bash
# 1. Start Consul
docker compose up -d consul

# 2. Verify Consul is running
curl http://localhost:8500/v1/status/leader

# 3. Register a service
curl -X PUT http://localhost:8500/v1/agent/service/register \
  -H "Content-Type: application/json" \
  -d @consul/config/services.json

# 4. List all services
curl http://localhost:8500/v1/catalog/services

# 5. Check service health
curl http://localhost:8500/v1/health/service/crypto-register-api

# 6. Query service via DNS
dig @127.0.0.1 -p 8600 crypto-register-api.service.consul
```

---

## Benefits Summary

| Feature | Before | After |
|---------|--------|-------|
| Service Discovery | Manual/Static | Automatic/Dynamic |
| Health Checks | Basic Docker | Consul + Auto-deregister |
| Load Balancing | None | Consul DNS + Connect |
| Security | Plain HTTP | mTLS via Connect |
| Monitoring | Logs only | Consul UI + Prometheus |
| Failover | Manual | Automatic |

---

## Next Steps

1. ✅ **Immediate**: Enable Consul in docker-compose
2. ✅ **Day 1**: Register all crypto-stack services
3. ✅ **Week 1**: Implement health checks for all services
4. 📅 **Week 2**: Enable Consul Connect (service mesh)
5. 📅 **Week 3**: Set up monitoring dashboard
6. 📅 **Week 4**: Configure DNS-based discovery

---

## Files to Create

- [ ] `consul/config/services.json` - Service definitions
- [ ] `consul/config/connect.hcl` - Connect configuration
- [ ] `scripts/consul-register.sh` - Auto-registration script
- [ ] `monitoring/grafana/dashboards/consul.json` - Dashboard
- [ ] `prometheus/rules/consul-alerts.yml` - Alerting rules

---

*Generated: 2026-03-13*
*Author: Gibson AI Agent*
