# Analytics Platform Comparison: Mixpanel vs Open Source Alternatives

**Date:** March 3, 2026  
**Purpose:** Evaluate analytics platforms for Lyrikali social media app

---

## Current Setup ✅
- **Mixpanel Token:** `6f1822434e5fe7491b6acf4efe9a0b5d` (configured)
- **Firebase:** API Key configured (`AIzaSyAmS0qOzT2QIfw_4pvGjdK9zRDUNYrX41s`)
- **Features:** Autocapture enabled, 100% session recording

---

## Option 1: Mixpanel (Current)

### Pros
- ✅ Industry standard for product analytics
- ✅ Powerful cohort analysis & funnels
- ✅ Session recording (100% configured)
- ✅ Easy SDK integration
- ✅ Free tier: 100K events/month

### Cons
- ❌ Proprietary - data leaves your infrastructure
- ❌ Pricing can scale quickly
- ❌ Limited customization

### Cost
- Free: 100K events/month
- $0.25/1K events after (Growth plan)

---

## Option 2: PostHog (Open Source)

### Overview
- **License:** MIT (self-hosted) / Proprietary (cloud)
- **Deployment:** Docker Compose, Kubernetes
- **Requirements:** 4 vCPU, 16GB RAM, 30GB+ storage

### Pros
- ✅ Full product suite: Analytics + CDP + Data Warehouse + SQL Editor
- ✅ Open source & self-hostable
- ✅ Feature flags built-in
- ✅ Session recordings
- ✅ AI-powered insights
- ✅ No event limits on self-hosted

### Cons
- ❌ Heavy infrastructure requirements
- ❌ Self-hosted = you manage scaling
- ❌ Paid features only on cloud (=$)
- ❌ Complex setup vs Mixpanel

### Self-Hosted Requirements
```
- 4 vCPU, 16GB RAM minimum
- PostgreSQL, ClickHouse, Redis, Kafka (or managed)
- Regular backups & maintenance
```

---

## Option 3: Plausible Analytics

### Overview
- **License:** Proprietary (no self-hosted option)
- **Focus:** Simple website analytics (like GA alternative)

### Pros
- ✅ Lightweight (75x smaller than GA script)
- ✅ No cookie consent needed (privacy-first)
- ✅ Simple, easy to understand
- ✅ EU-based servers

### Cons
- ❌ No self-hosted option
- ❌ Less product-focused (more for website analytics)
- ❌ No session recordings
- ❌ No cohort/funnel analysis like Mixpanel

### Cost
- €9/month for 10K visits
- €69/month for 100K visits

---

## Option 4: Umami (Open Source)

### Overview
- **License:** MIT
- **Focus:** Simple, privacy-focused web analytics

### Pros
- ✅ Lightweight & fast
- ✅ Self-hostable (Docker)
- ✅ No cookie consent needed
- ✅ Very low resource usage (can run on $5 VPS)
- ✅ Simple dashboard

### Cons
- ❌ Basic features vs Mixpanel
- ❌ No session recordings
- ❌ Limited cohort analysis
- ❌ No advanced funnel tools

### Requirements
```
- 1 vCPU, 1GB RAM
- MySQL or PostgreSQL
- ~10GB storage
```

---

## Option 5: Ackee (Open Source)

### Overview
- **License:** MPL-2.0
- **Focus:** Privacy-focused analytics

### Pros
- ✅ Very lightweight
- ✅ Privacy-first (no tracking cookies)
- ✅ Docker deployment
- ✅ Node.js based (familiar stack)

### Cons
- ❌ Very basic features
- ❌ Limited integrations
- ❌ Small community
- ❌ No session recordings

---

## Comparison Matrix

| Feature | Mixpanel | PostHog | Plausible | Umami | Ackee |
|---------|----------|---------|-----------|-------|-------|
| Session Recording | ✅ | ✅ | ❌ | ❌ | ❌ |
| Funnels | ✅ | ✅ | ❌ | ❌ | ❌ |
| Cohorts | ✅ | ✅ | ❌ | ❌ | ❌ |
| Feature Flags | ❌ | ✅ | ❌ | ❌ | ❌ |
| Self-Hostable | ❌ | ✅ | ❌ | ✅ | ✅ |
| Free Tier | 100K/mo | Unlimited* | 30K/mo | Unlimited | Unlimited |
| Privacy-First | ⚠️ | ⚠️ | ✅ | ✅ | ✅ |
| Setup Complexity | Easy | Hard | Easy | Easy | Easy |
| Resource Needs | Managed | High | Managed | Low | Low |

*PostHog self-hosted = unlimited, cloud = limited

---

## Recommendation

### For Now: Keep Mixpanel ✅
Mixpanel is already configured and working. Best choice if:
- You want quick setup
- You need advanced product analytics
- You're okay with data on external servers

### Future: Consider PostHog Self-Hosted
If you need:
- Full data ownership
- No per-event costs at scale
- Feature flags + analytics in one

**Migration path:** Export Mixpanel data → Import to PostHog (they have migration tools)

### Quick Win: Add Umami for Website Analytics
Deploy Umami alongside Mixpanel for simple website analytics as a lightweight alternative to Google Analytics.

---

## Implementation Status

| Task | Status |
|------|--------|
| Mixpanel Token Configured | ✅ Done |
| Firebase API Key Configured | ✅ Done |
| Firebase Fallback Logic | ✅ Updated |
| PostHog Research | ✅ Complete |
| PostHog Deployment | ⏳ Not Started |

---

## Next Steps

1. **Deploy to Firebase Hosting** (test fallback):
   ```bash
   cd services/social-media/frontend
   firebase init
   firebase deploy --only hosting
   ```

2. **Test Mixpanel tracking** - Visit dashboard at posthog.com

3. **Optional: Deploy Umami** for lightweight analytics:
   ```bash
   # Docker compose example
   docker run -d --name umami -p 3000:3000 -e DATABASE_URL=postgresql://... ghcr.io/umami-software/umami:postgresql-latest
   ```
