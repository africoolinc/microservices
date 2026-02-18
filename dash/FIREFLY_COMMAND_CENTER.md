# 🔥 FIREFLY Command Center: Gibson's Dash
## Blueprint v1.0 - Docker Container on Port 10000

---

## 1. Vision

**Gibson's Dash** is a unified command center that aggregates data from all Juma family devices and services into a single, actionable dashboard. It keeps Gibson informed in real-time about:

- 🔴 **Threats** - Security alerts, suspicious activities, device anomalies
- 🟢 **Opportunities** - Trading signals, market intelligence, revenue leads
- 💡 **Actionable Data** - Business metrics, family updates, system health

---

## 2. Data Sources

### 📱 Mobile Devices
| Device | Source | Data Points |
|--------|--------|-------------|
| Gibson's V20 | ADB (10.144.180.80:5555) | Battery, storage, network, apps, location |
| Allan's Phone | ADB (pending) | Battery, status |
| Other Family | ADB (future) | Status, location |

### 🖥️ Infrastructure
| Service | Endpoint | Data |
|---------|----------|------|
| StackForge | 10.144.118.159 | Docker containers, services, health |
| Kibana | 10.144.118.159:5601 | Market intelligence trends |
| Kafka | 10.144.118.159:9092 | Event streams |
| Keycloak | 10.144.118.159:8080 | Auth status, user sessions |

### 💰 Business
| Source | Data |
|--------|------|
| Hyperliquid API | Portfolio balance, PnL, signals |
| Lyrikali | Subscriptions, user growth, trends |
| Bitsoko | Transaction volume, revenue |

### 👨‍👩‍👧‍👦 Family
| Source | Data |
|--------|------|
| Android Sync | Device status, battery, storage |
| Notification System | Family alerts, messages |

---

## 3. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GIBSON'S DASH (Port 10000)              │
│                    Docker Container: gibsons_dash           │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  ADB Gateway  │    │  API Gateway  │    │  Data Store   │
│  (Device      │    │  (Services    │    │  (SQLite/     │
│   Polling)    │    │   Fetching)   │    │   InfluxDB)   │
└───────────────┘    └───────────────┘    └───────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  V20 (ADB)   │    │  StackForge   │    │  Hyperliquid  │
│  10.144.180.80│    │  10.144.118.159│    │  API         │
└───────────────┘    └───────────────┘    └───────────────┘
```

---

## 4. Tech Stack

| Layer | Technology |
|-------|------------|
| **Container** | Docker + Docker Compose |
| **Backend** | Node.js / Express |
| **Frontend** | React + Tailwind CSS |
| **Database** | SQLite (embedded) or InfluxDB (time-series) |
| **Device Comm** | ADB (Android Debug Bridge) via ADBKit |
| **API Client** | Axios + Prometheus metrics |

---

## 5. Features

### 🔴 Threat Monitoring
- [ ] Device offline alerts
- [ ] Low battery warnings (<20%)
- [ ] Storage full warnings (>90%)
- [ ] Suspicious app installs detection
- [ ] Failed login attempts (Keycloak)
- [ ] Container health failures (StackForge)

### 🟢 Opportunity Tracking
- [ ] Hyperliquid PnL changes
- [ ] New subscription alerts (Lyrikali)
- [ ] Market trend summaries
- [ ] Revenue milestones

### 💡 Actionable Data
- [ ] Family device status overview
- [ ] StackForge service health matrix
- [ ] Quick actions (reboot services, sync device)
- [ ] Daily/weekly summaries

---

## 6. API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/status` | Full system status |
| GET | `/api/devices` | All device statuses |
| GET | `/api/devices/:id` | Single device details |
| GET | `/api/services` | StackForge services |
| GET | `/api/trading` | Hyperliquid portfolio |
| GET | `/api/threats` | Active threat alerts |
| GET | `/api/opportunities` | Opportunity feed |
| POST | `/api/devices/:id/sync` | Trigger device sync |
| POST | `/api/actions/reboot` | Reboot service |

---

## 7. UI Layout

```
╔═══════════════════════════════════════════════════════════╗
║  🔥 GIBSON'S DASH          Last Updated: 15:52          ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  ┌──────────────┐ ┌────────────────────┐       ║
┐ ┌────────║  │ 🔴 THREATS   │ │ 🟢 OPPORTUN. │ │ 📊 QUICK    │       ║
║  │     2        │ │     5        │ │    STATS    │       ║
║  └──────────────┘ └──────────────┘ └──────────────┘       ║
║                                                           ║
║  ── DEVICES ─────────────────────────────────────────    ║
║  📱 V20 (Gibson)     🔋96%  📶 Online  🌍 VPN:10.144.180.80║
║  💻 StackForge       ✅ 20/24 Containers Running         ║
║                                                           ║
║  ── SERVICES ──────────────────────────────────────────    ║
║  🟢 Kibana    🟢 Keycloak    🟢 Kafka    🟢 Gateway      ║
║                                                           ║
║  ── TRADING ──────────────────────────────────────────    ║
║  Portfolio: $39.29   Daily PnL: +$2.14                   ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

---

## 8. Docker Configuration

### docker-compose.yml

```yaml
version: '3.8'

services:
  gibsons_dash:
    image: gibsons_dash:latest
    container_name: gibsons_dash
    ports:
      - "10000:3000"
    environment:
      - NODE_ENV=production
      - ADB_HOST=10.144.180.80
      - ADB_PORT=5555
      - STACKFORGE_HOST=10.144.118.159
      - HYPERLIQUID_PRIVATE_KEY=${HYPERLIQUID_KEY}
      - DB_PATH=/data/dash.db
    volumes:
      - ./data:/data
      - /var/run/docker.sock:/var/run/docker.sock
    restart: unless-stopped
    networks:
      - juma_network

networks:
  juma_network:
    external: true
```

### Dockerfile

```dockerfile
FROM node:20-alpine

WORKDIR /app

# Install ADB
RUN apk add --no-cache android-tools

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source
COPY . .

EXPOSE 3000

CMD ["node", "server.js"]
```

---

## 9. Implementation Phases

| Phase | Task | Priority |
|-------|------|----------|
| 1 | Basic device status polling (V20) | 🔴 High |
| 2 | StackForge service health check | 🔴 High |
| 3 | Web dashboard UI | 🔴 High |
| 4 | Hyperliquid integration | 🟡 Medium |
| 5 | Threat detection rules | 🟡 Medium |
| 6 | Opportunity alerts | 🟢 Low |
| 7 | Multi-device support | 🟢 Low |

---

## 10. Files Structure

```
projects/members/Gibson/dash/
├── docker-compose.yml
├── Dockerfile
├── package.json
├── src/
│   ├── index.js          # Express server
│   ├── routes/
│   │   ├── devices.js    # Device endpoints
│   │   ├── services.js   # Service health
│   │   └── trading.js    # Trading data
│   ├── services/
│   │   ├── adb.js        # ADB wrapper
│   │   ├── docker.js     # Docker API
│   │   └── hyperliquid.js
│   └── ui/
│       └── build/        # React frontend
└── data/
    └── dash.db           # SQLite storage
```

---

*Blueprint by Ahie Juma | 2026-02-16*
