# Gibson Microservices - Live Services Directory

**Last Updated:** March 3, 2026 - 15:05 (Africa/Nairobi)

---

## 🔴 LIVE PRODUCTION SERVICES (Port 10000-11000)

| Service | Port | Local URL | Status |
|---------|------|-----------|--------|
| **Gibson's Dashboard** | 10000 | http://192.168.100.182:10000 | ✅ Running |
| **DAO Wallet** | 10002 | http://192.168.100.182:10002 | ✅ Running |
| **Lyrikali Social v3.1 (PROD)** | 10500 | http://192.168.100.182:10500 | ✅ Running |
| Portainer | 9443 | https://192.168.100.182:9443 | ✅ Running |
| Keycloak | 8080 | http://192.168.100.182:8080 | ✅ Running |

---

## 🟡 DEVELOPMENT SERVICES (Port 5000-6000)

| Service | Port | Local URL | Status |
|---------|------|-----------|--------|
| **Lyrikali Social v3.1 (DEV)** | 5003 | http://192.168.100.182:5003 | ✅ Running |
| Stack Duka DAO App | 3000 | http://192.168.100.182:3000 | ✅ Running |

---

## 🔐 Authentication Options (Both DEV & PROD)

| Method | Endpoint | Status |
|--------|----------|--------|
| **Keycloak** | POST /api/v1/auth/login | ✅ Available |
| **Firebase Google** | POST /api/v1/auth/firebase-login | ✅ Available |
| **Registration** | POST /api/v1/auth/register | ✅ Available |

---

## 📋 Health Check Links

```bash
# DEV Environment
curl http://192.168.100.182:5003/health

# PROD Environment  
curl http://192.168.100.182:10500/health
```

---

## 🔑 Keycloak Configuration

- **URL:** http://192.168.100.182:8080
- **Realm:** lyrikali
- **Client:** lyrikali-app
- **Admin:** admin / adminpass

---

## 📱 Lyrikali Social v3.1 Features

| Feature | Status |
|---------|--------|
| Keycloak Auth | ✅ |
| Firebase Google Sign-In | ✅ |
| BTC Lightning Payments | ✅ |
| Subscription Tiers | ✅ |
| PostHog Analytics | ✅ |
| Consul Service Discovery | ✅ |

---

## 📞 Service Discovery (Consul)

- **Consul UI:** http://192.168.100.182:8500/ui

---

## 🚀 Quick Test Commands

```bash
# Test DEV auth
curl -X POST http://localhost:5003/api/v1/auth/login -H "Content-Type: application/json" -d '{"username":"test","password":"test"}'

# Test PROD auth
curl -X POST http://localhost:10500/api/v1/auth/login -H "Content-Type: application/json" -d '{"username":"test","password":"test"}'

# Test Firebase login (both ports)
curl -X POST http://localhost:10500/api/v1/auth/firebase-login -H "Content-Type: application/json" -d '{"firebase_token":"test","email":"user@gmail.com","name":"Test User"}'
```
