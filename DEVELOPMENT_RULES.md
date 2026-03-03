# Gibson Microservices Stack - Development Rules & Standards

**Effective Date:** March 3, 2026  
**Last Updated:** March 3, 2026

---

## 🎯 Port Allocation Standards

### Development & Testing Environment
**Port Range:** 5000 - 6000

| Service | Port | Purpose |
|---------|------|---------|
| stack-duka-dao-app | 3000 | DAO application (dev) |
| social-media-service | 5003 | Social media app (dev) |
| fintech-service | 5004 | Fintech service (dev) |
| ecommerce-service | 5005 | E-commerce service (dev) |
| social-media-service | 10500 | **PRODUCTION** - Social media live |

### Production Environment (Live/Paying Clients)
**Port Range:** 10000 - 11000

| Service | Port | Purpose |
|---------|------|---------|
| gibsons_dash | 10000 | Production dashboard |
| dao_wallet | 10002 | Production wallet |
| portainer | 10000-10001 | Container management |
| social-media | 10500 | **LIVE** - BTC Lightning subscriptions |
| trading_desk | 10010+ | Live trading services |

---

## 🔒 Security Rules

### 1. Environment Separation
- ✅ **Development** = Ports 5000-6000
  - Can be freely modified, restarted, tested
  - May contain debug features
  - Data may be reset periodically

- ✅ **Production** = Ports 10000  - Requires-11000
 approval before changes
  - Must have rollback plan
  - Stable, tested versions only
  - Customer data must be protected

### 2. Service Classification

| Classification | Port Range | Access | Monitoring |
|---------------|------------|--------|------------|
| Internal/Dev | 5000-6000 | Team only | Basic |
| Staging | 6001-6999 | Team + Beta | Standard |
| Production | 10000-11000 | Public + Clients | Enhanced |

### 3. Deployment Checklist

**Before deploying to Production (10000-11000):**
- [ ] Code reviewed and tested in Dev
- [ ] No debug/logging exposing secrets
- [ ] Health check endpoint available
- [ ] Backup strategy in place
- [ ] Rollback plan documented
- [ ] Customer notification prepared (if needed)

### 4. Database & Storage

| Environment | Database | Retention |
|-------------|----------|-----------|
| Dev | dev-db (local) | 7 days |
| Staging | staging-db | 30 days |
| Prod | prod-db | Per compliance |

---

## 📋 Development Workflow

```
1. Develop → Local/Port 5000-6000
       ↓
2. Test → Dev Environment (5000-6000)
       ↓
3. Staging → Port 6001-6999 (optional)
       ↓
4. Deploy → Production (10000-11000)
```

---

## 🔧 Current Port Mapping

### Active Services (Dev)
| Service | Port | Status |
|---------|------|--------|
| stack-duka-dao-app | 3000 | ✅ Running |
| social-media-service | 5003 | ✅ Running |
| social-media (v3) | 10500 | ✅ **PROD** |
| gibsons_dash | 10000 | ✅ Running |
| dao_wallet | 10002 | ✅ Running |
| portainer | 8000/9443 | ✅ Running |

---

## ⚡ Quick Reference

```bash
# Check what's running on dev ports
docker ps | grep -E ':5[0-9]{3}'

# Check what's running on prod ports
docker ps | grep -E ':1[0-1][0-9]{3}'
```

---

## 📝 Rule Enforcement

**This rule is automatically enforced:**
- All new services must specify port in correct range
- Production deployments require commit message: `[PROD]`
- Port conflicts should be resolved before deployment
- Review logs for any unauthorized port usage
