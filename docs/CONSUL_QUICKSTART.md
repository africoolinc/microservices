# Consul Service Discovery - Quick Start

## 🚀 Enable in 3 Commands

```bash
# 1. Start Consul
cd /home/africool/.openclaw/workspace/projects/members/Gibson
./scripts/enable-consul.sh

# 2. Verify services
curl http://localhost:8500/v1/catalog/services | jq

# 3. Open UI
# http://localhost:8500
```

---

## 📁 Files Created

| File | Purpose |
|------|---------|
| `docs/CONSUL_SERVICE_DISCOVERY_ENHANCEMENTS.md` | Full implementation guide |
| `consul/config/services.json` | Service definitions |
| `consul/config/connect.hcl` | Service mesh config |
| `scripts/consul-register.sh` | Auto-registration script |
| `scripts/enable-consul.sh` | One-click enable script |
| `prometheus/rules/consul-alerts.yml` | Monitoring alerts |

---

## 🔍 Service Registration

Services are automatically registered with:
- **Health checks** (10s interval)
- **Auto-deregister** (60s after critical failure)
- **Metadata** (version, team, tier)
- **Tags** (for filtering)

### Registered Services

| Service | Port | Tier | Health Endpoint |
|---------|------|------|-----------------|
| crypto-register-api | 3002 | critical | /health |
| bridge-api | 3000 | critical | /health |
| keycloak | 8080 | critical | /health/ready |
| btc-options-bot | 5000 | standard | /health |
| stack-duka-dao | 3000 | standard | /health |
| gibsons-dash | 3000 | standard | /health |
| dao-wallet | 3000 | standard | /health |

---

## 🔧 Manual Registration

```bash
# Register a new service
./scripts/consul-register.sh my-service 8080 /health

# With health watch
./scripts/consul-register.sh my-service 8080 /health --watch
```

---

## 📊 Consul UI Features

- **Service Catalog** - View all registered services
- **Health Checks** - Monitor service health status
- **KV Store** - Configuration management
- **Connect** - Service mesh visualization
- **ACL** - Access control (when enabled)

---

## 🔗 Service Discovery Methods

### 1. HTTP API
```bash
# List services
curl http://localhost:8500/v1/catalog/services

# Get specific service
curl http://localhost:8500/v1/catalog/service/crypto-register-api

# Health status
curl http://localhost:8500/v1/health/service/crypto-register-api
```

### 2. DNS
```bash
# Query service
dig @127.0.0.1 -p 8600 crypto-register-api.service.consul

# SRV record (includes port)
dig @127.0.0.1 -p 8600 _http._tcp.crypto-register-api.service.consul SRV
```

### 3. Connect (Service Mesh)
```bash
# After enabling Connect, services communicate via mTLS
# Sidecar proxies handle encryption automatically
```

---

## 🚨 Monitoring & Alerts

Alerts configured in `prometheus/rules/consul-alerts.yml`:

| Alert | Severity | Trigger |
|-------|----------|---------|
| ConsulServiceDown | Critical | No healthy nodes |
| ConsulServiceDegraded | Warning | <50% healthy |
| ConsulHealthCheckFailing | Warning | Check failing 2m |
| ConsulAgentDown | Critical | Agent unresponsive |
| ConsulHighMemory | Warning | >80% memory |

---

## 🛡️ Security Recommendations

1. **Enable ACLs** for production
2. **Enable Connect** for mTLS between services
3. **Restrict Consul UI** access (firewall/auth)
4. **Use intentions** to control service-to-service access
5. **Enable gossip encryption** for cluster communication

---

## 📈 Next Steps

1. ✅ Enable Consul (run `./scripts/enable-consul.sh`)
2. 📅 Enable Consul Connect (service mesh)
3. 📅 Set up Prometheus + Grafana dashboards
4. 📅 Configure service intentions
5. 📅 Enable DNS-based discovery

---

## 🆘 Troubleshooting

```bash
# Check Consul status
curl http://localhost:8500/v1/status/leader

# Check agent health
curl http://localhost:8500/v1/agent/self

# View logs
docker logs consul

# Deregister a service
curl -X PUT http://localhost:8500/v1/agent/service/deregister/<service-id>
```

---

*Created: 2026-03-13*
