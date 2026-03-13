# Gibson's Microservices Stack - Long-Term Memory

## Project Overview
An AI-driven microservices ecosystem designed for e-commerce, fintech, and social networking. Hosted on `ahie` (host) with some remote components.

## Recent Decisions & Updates
- **2026-03-06**: 
    - Established Trading Desk with journal and ledger system
    - BTC market: $68,100 (-4.4% today) — Buy zone for DCA
    - Created profit-taking rules: 15% reinvest, 85% to reserve
    - BTC Options Bot running at port 5000 (healthy)
    - Insilico/Blofin API pending IP whitelist
- **2026-02-27**: 
    - Identified Kafka listener configuration error (port conflict) and updated `docker-compose.yml`.
    - Initiated rebuild of `ecommerce-service`, `fintech-service`, and `social-media-service`.
    - Discovered Keycloak unhealthy status due to `realm_attribute` missing in DB.
    - Proposed "StackDuka Connect" business model.

## Infrastructure
- **Host**: ahie
- **Project Name**: microservices-stack
- **Key Services**: Kong, Keycloak, Consul, Kafka, Redis, PostgreSQL.

## Todos
- [ ] Fix Keycloak DB schema.
- [ ] Verify Fintech service functionality.
- [ ] Implement automated backup script for volumes.
- [ ] Rotate admin passwords (currently `adminpass`).

---

## 2026-03-12 - Stack Optimization & Business Development

### Network & Connectivity
- Gibson's laptop reachable via VPN (10.144.118.159), local IP unreachable
- SSH access confirmed on port 22

### Microservices Status
- **Running:** crypto_resolver, options-bot-1, bridge_api, bridge_heartbeat, bridge_tracker, stack-duka-dao-app-1, gibsons_dash, dao_wallet, zerotier, portainer (11)
- **Stopped:** redis
- **Issues:** Bridge Heartbeat (404), Crypto Resolver (connection refused), CF Worker Sim (connection refused)

### Backup & Security
- Created backup: `local_backup_20260312_182412.tar.gz` (550KB)
- No unauthorized SSH access detected
- Report: `logs/backup_security_report_2026-03-12.md`

### New Skills
- **crypto-stack-monitor**: Full monitoring skill with client query support
  - Location: `skills/crypto-stack-monitor/`
  - Run: `python3 skills/crypto-stack-monitor/monitor_stack.py --audit`
  - Schedule: Every 4 hours (cron)
  - Client query: `--client +254XXXXXXXX`

### Business Intel
- Created `docs/BUSINESS_BLUEPRINT_PHONE_SIGNUP.md`
- Revenue: Signal subscriptions ($9.99-$49.99/mo), API access ($99-$499/mo)
- Client tiers: Platinum/Gold/Silver/Bronze/Free
- SMS campaigns: Welcome, deposit reminder, signal alerts, upsell, win-back
- Year 1 target: $48K MRR at 10,000 users

### Crypto Register Service (Port 3001-3002)
- **Created:** `services/crypto-register/`
- **Purpose:** Phone registration + .crypto domain allocation
- **Frontend:** Port 3001 (nginx)
- **API:** Port 3002 (Node.js)
- **Features:** Phone signup, .crypto domain, service selection
- **Status:** ✅ Running
- **Test Grade:** B (8/10)

### Sepolia Testnet Bot
- **Skill:** `skills/sepolia-testnet-bot/`
- **Test Address:** `0xcA2a481E128d8A1FCE636E0D4fe10fF5987f028F`
- **Usage:** `python3 skills/sepolia-testnet-bot/testnet_bot.py --all`
- **Results:** 8/10 (Grade B)

### Crypto Register Service - LIVE (Port 10110)
- **Deployed:** 2026-03-12
- **Frontend:** http://localhost:10110 ✅
- **API:** http://localhost:10112 ✅
- **Keycloak Realm:** crypto-register
- **Client:** crypto-register-app
- **Theme:** Green (#10b981) with gray backgrounds
