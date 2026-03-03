# Gibson Microservices - Live Services Directory

**Last Updated:** March 3, 2026 - 12:06 PM (Africa/Nairobi)

---

## 🔴 LIVE PRODUCTION SERVICES (Port 10000-11000)

| Service | Port | Local URL | Public URL | Status |
|---------|------|-----------|------------|--------|
| **Gibson's Dashboard** | 10000 | http://192.168.100.182:10000 | http://ahie.africoolinc.com:10000 | ✅ Running |
| **DAO Wallet** | 10002 | http://192.168.100.182:10002 | http://ahie.africoolinc.com:10002 | ✅ Running |
| **Lyrikali Social (v3)** | 10500 | http://192.168.100.182:10500 | http://ahie.africoolinc.com:10500 | ✅ Running |
| Portainer | 8000/9443 | http://192.168.100.182:9443 | https://ahie.africoolinc.com:9443 | ✅ Running |

---

## 🟡 DEVELOPMENT SERVICES (Port 5000-6000)

| Service | Port | Local URL | Status |
|---------|------|-----------|--------|
| Stack Duka DAO App | 3000 | http://192.168.100.182:3000 | ✅ Running |
| DAO Wallet (Dev) | 5002 | http://192.168.100.182:5002 | ✅ Running |

---

## 📋 Service Health Check Links

### Production Services
```bash
# Dashboard
curl http://192.168.100.182:10000/health

# DAO Wallet  
curl http://192.168.100.182:10002/health

# Lyrikali Social v3.0 (BTC Lightning)
curl http://192.168.100.182:10500/health

# Subscription Plans API
curl http://192.168.100.182:10500/api/v1/subscriptions/plans

# Portainer
curl http://192.168.100.182:9000/health
```

### Development Services
```bash
# DAO App
curl http://192.168.100.182:3000/health
```

---

## 🌐 External Access

**Local Network:** http://192.168.100.182

**Public Domain:** ahie.africoolinc.com (via ngrok tunnel - currently reconnecting)

---

## 🔐 Portainer Access

- **URL:** https://192.168.100.182:9443
- **User:** admin
- **Password:** [Check .secrets/portainer.env]

---

## 📱 API Endpoints - Lyrikali Social v3.0

```
GET  /api/v1/subscriptions/plans                    - View plans
POST /api/v1/subscriptions/create-invoice           - Create BTC invoice
GET  /api/v1/subscriptions/check-payment/<id>      - Check payment
POST /api/v1/auth/register                          - Register user
POST /api/v1/auth/login                             - Login
POST /api/v1/meme/generate                          - Generate meme
GET  /api/v1/trends                                 - Get trends
GET  /health                                        - Service health
```

---

## 📞 Service Discovery (Consul)

- **Consul UI:** http://192.168.100.182:8500/ui
- **Service Catalog:** http://192.168.100.182:8500/v1/catalog/services
