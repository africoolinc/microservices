# DAO Wallet Services - Deployment Plan

## Overview
- **Project Name**: DAO Wallet Services (Phone→Wallet DAO)
- **Target**: Port `5002` on `0.0.0.0`
- **Purpose**: Fintech app bridging mobile money with Ethereum for unbanked users in emerging markets

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    DAO Wallet Services                   │
│                    0.0.0.0:5002                         │
├─────────────────────────────────────────────────────────┤
│  Frontend: React/Vue (Static + API proxy)              │
│  Backend:  Flask/FastAPI                                │
│  Database: SQLite (dev) / PostgreSQL (prod)            │
└─────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React + Tailwind CSS |
| Backend | Flask (Python) |
| API | REST + Web3 (Ethereum) |
| Auth | JWT + Phone-based |
| Mobile Money | Mock integration (M-Pesa stub) |

---

## Page Structure (from Wireframe)

1. **Landing Page** (`/`)
   - Hero: "AI-Governed Phone→Wallet DAO"
   - Stats: $1T+ Market Size, 1M+ Target Users
   - CTA: "Join the DAO Today"

2. **Features** (`/features`)
   - Verticals: Fintech, DeFi, DAO, AI-Data, Gaming

3. **How It Works** (`/how-it-works`)
   - 3 Steps: Sign Up → Connect Mobile Money → Start Earning

4. **Pricing** (`/pricing`)
   - Starter: $100/mo
   - Pro: $200/mo (Most Popular)
   - Advanced: $300/mo

5. **FAQ** (`/faq`)

6. **Sign In / Get Started** (`/login`, `/register`)

---

## Deployment Steps

### Phase 1: Project Setup (Week 1)
- [ ] Initialize Flask project structure
- [ ] Set up React frontend with Vite
- [ ] Configure Tailwind CSS
- [ ] Create API routes

### Phase 2: Core Features (Week 2)
- [ ] User registration (phone-based)
- [ ] Mobile money mock integration
- [ ] Wallet generation (Ethereum)
- [ ] JWT authentication

### Phase 3: DeFi Integration (Week 3)
- [ ] Yield farming stubs
- [ ] Staking interface
- [ ] DAO voting UI

### Phase 4: Deployment (Week 4)
- [ ] Build frontend for production
- [ ] Configure Gunicorn/Nginx
- [ ] Deploy to `0.0.0.0:5002`

---

## File Structure

```
/projects/members/Gibson/microservices/dao-wallet/
├── app/
│   ├── __init__.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── wallet.py
│   │   └── mobile_money.py
│   ├── models/
│   │   └── user.py
│   └── utils/
│       └── web3_helpers.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── App.jsx
│   ├── public/
│   └── package.json
├── requirements.txt
├── docker-compose.yml
└── README.md
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register with phone number |
| POST | `/api/auth/login` | Login and get JWT |
| GET | `/api/wallet/balance` | Get wallet balance |
| POST | `/api/wallet/connect-momo` | Link mobile money |
| GET | `/api/defi/yields` | Get yield farming options |
| POST | `/api/dao/vote` | Cast DAO vote |

---

## Success Metrics

- [ ] App loads on `http://0.0.0.0:5002`
- [ ] User can register with phone number
- [ ] Mock mobile money connection works
- [ ] Wallet address generated
- [ ] Landing page matches wireframe

---

## Next Actions

1. **Initialize project** in `projects/members/Gibson/microservices/dao-wallet/`
2. **Create Flask backend** with auth + wallet routes
3. **Build React frontend** matching the wireframe
4. **Test locally** on port 5002

---

*Plan created: 2026-02-15*
