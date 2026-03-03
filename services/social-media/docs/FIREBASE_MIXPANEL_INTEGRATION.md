# Lyrikali Firebase & Mixpanel Integration Plan

**Created:** Monday, March 2nd, 2026  
**Purpose:** Ensure 99.99% uptime with automatic failover between Gibson infrastructure and Firebase

---

## 🎯 Executive Summary

This document outlines a hybrid deployment strategy for Lyrikali:
- **Primary:** Gibson infrastructure (current)
- **Backup/Scaling:** Firebase Hosting + Cloud Functions
- **Analytics:** Mixpanel for user tracking

---

## 🔄 Architecture Overview

```
                        ┌─────────────────────────────┐
                        │       DNS / CDN             │
                        │   (Cloudflare)             │
                        └──────────────┬──────────────┘
                                       │
              ┌────────────────────────┴────────────────────────┐
              │                                                 │
              ▼                                                 ▼
┌─────────────────────────────┐              ┌─────────────────────────────┐
│   PRIMARY (Gibson Server)   │              │   BACKUP (Firebase)         │
│   ahie / 10.144.118.159    │   FAILOVER   │   lyrikali.web.app          │
│                             │◄────────────►│                             │
│   - Keycloak Auth          │   AUTO/      │   - Firebase Auth           │
│   - Social Media Service   │   MANUAL     │   - Firebase Functions      │
│   - API Backend            │              │   - Cloud Firestore         │
│   - Kong API Gateway       │              │   - Firebase Hosting        │
└─────────────────────────────┘              └─────────────────────────────┘
                                       │
                                       ▼
                        ┌─────────────────────────────┐
                        │   Mixpanel Analytics        │
                        │   - User Events             │
                        │   - Funnels                 │
                        │   - A/B Tests               │
                        └─────────────────────────────┘
```

---

## 🔥 Firebase Deployment

### Step 1: Firebase Project Setup

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login to Firebase
firebase login

# Initialize Firebase in project
cd services/social-media/frontend
firebase init hosting
```

### Step 2: firebase.json Configuration

```json
{
  "hosting": {
    "public": ".",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**"
    ],
    "rewrites": [
      {
        "source": "/api/**",
        "function": "api"
      }
    ],
    "headers": [
      {
        "source": "**/*.@(jpg|jpeg|gif|png|svg|webp)",
        "headers": [{"key": "Cache-Control", "value": "max-age=31536000"}]
      }
    ],
    "site": "lyrikali-app"
  }
}
```

### Step 3: Deploy Commands

```bash
# Deploy to Firebase
firebase deploy --only hosting

# Deploy with Cloud Functions
firebase deploy

# Set up CI/CD
firebase hosting:channel:deploy staging
```

---

## 📊 Mixpanel Integration

### Step 1: Create Mixpanel Project

1. Go to [mixpanel.com](https://mixpanel.com)
2. Create new project: "Lyrikali"
3. Get Project Token from Project Settings

### Step 2: Install Mixpanel SDK

```html
<!-- In index.html - add before </body> -->
<script>
  mixpanel.init("YOUR_MIXPANEL_TOKEN", {
    track_pageview: true,
    persistence: "localStorage"
  });
</script>
```

### Step 3: Track Critical Events (app.js)

```javascript
// Lyrikali Mix - Mixpanel Integration
const MIXPANEL_TOKEN = 'YOUR_TOKEN_HERE';

// Initialize Mixpanel
function initMixpanel() {
    if (typeof mixpanel !== 'undefined') {
        mixpanel.init(MIXPANEL_TOKEN, {
            debug: true,
            track_pageview: true,
            persistence: 'localStorage'
        });
    }
}

// Track Authentication
function trackLogin(method, userId) {
    mixpanel.track('User Login', {
        'method': method, // 'email', 'google', 'keycloak'
        'user_id': userId,
        'timestamp': new Date().toISOString()
    });
}

function trackSignup(method, userId) {
    mixpanel.track('User Signup', {
        'method': method,
        'user_id': userId,
        'source': 'web_app'
    });
}

// Track Content Creation
function trackMemeCreated(platform) {
    mixpanel.track('Meme Created', {
        'platform': platform,
        'content_type': 'lyric_meme',
        'timestamp': new Date().toISOString()
    });
}

// Track Feature Usage
function trackFeatureUsed(featureName) {
    mixpanel.track('Feature Used', {
        'feature': featureName,
        'user_id': currentUser?.id
    });
}

// Track Errors
function trackError(errorType, errorMessage) {
    mixpanel.track('App Error', {
        'error_type': errorType,
        'message': errorMessage,
        'url': window.location.href
    });
}

// User Profile Setup
function setUserProfile(user) {
    if (typeof mixpanel !== 'undefined' && user) {
        mixpanel.people.set({
            '$email': user.email,
            '$name': user.username,
            '$created': user.createdAt,
            'platform': 'web',
            'subscription_tier': user.tier || 'free'
        });
    }
}
```

### Step 4: Update app.js with Firebase Auth + Mixpanel

```javascript
// Modified auth handlers for Firebase + Mixpanel
async function handleLogin(email, password) {
    try {
        // Try Firebase Auth first (for backup)
        const credential = await firebase.auth().signInWithEmailAndPassword(email, password);
        
        // Track in Mixpanel
        trackLogin('firebase_email', credential.user.uid);
        setUserProfile({
            id: credential.user.uid,
            email: credential.user.email,
            createdAt: credential.user.metadata.creationTime
        });
        
        showDashboard();
    } catch (error) {
        // Fallback to local/Keycloak auth
        console.log('Firebase auth failed, trying local...');
        // ... existing auth logic
    }
}
```

---

## ⚡ Automatic Failover Strategy

### Option A: Cloudflare DNS Failover (Recommended)

```yaml
# Cloudflare Load Balancing / Failover
- name: lyrikali-api
  type: A
  value: 10.144.118.159  # Primary Gibson
  proxy: true
  ttl: 60

- name: lyrikali-api-backup  
  type: A
  value: [firebase-url].web.app  # Firebase fallback
  proxy: true
  ttl: 30

# Health Check Configuration
health_check:
  url: /api/health
  interval: 30s
  timeout: 5s
  retries: 3
```

### Option B: Client-Side Fallback

```javascript
// API client with automatic fallback
const API_ENDPOINTS = {
    primary: 'http://10.144.118.159:8000/api',
    firebase: 'https://us-central1-lyrikali.cloudfunctions.net/api'
};

async function apiCall(endpoint, options = {}) {
    // Try primary first
    try {
        const response = await fetch(`${API_ENDPOINTS.primary}${endpoint}`, {
            ...options,
            timeout: 5000  // 5 second timeout
        });
        if (response.ok) return response;
    } catch (e) {
        console.warn('Primary API failed, trying Firebase...');
    }
    
    // Fallback to Firebase
    try {
        const response = await fetch(`${API_ENDPOINTS.firebase}${endpoint}`, options);
        mixpanel.track('API Fallback Used', { endpoint });
        return response;
    } catch (e) {
        trackError('API Fallback Failed', e.message);
        throw e;
    }
}
```

### Option C: Service Worker Caching (Offline Support)

```javascript
// sw.js - Service Worker for offline support
const CACHE_NAME = 'lyrikali-v1';
const OFFLINE_URL = '/offline.html';

self.addEventListener('fetch', (event) => {
    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request).catch(() => {
                return caches.match(OFFLINE_URL);
            })
        );
    }
});
```

---

## 📋 Implementation Checklist

### Firebase Setup
- [ ] Create Firebase project
- [ ] Enable Firebase Auth (Email/Password + Google)
- [ ] Set up Cloud Firestore
- [ ] Configure Firebase Hosting
- [ ] Set up custom domain (optional)

### Mixpanel Setup  
- [ ] Create Mixpanel project
- [ ] Get API token
- [ ] Update app.js with tracking
- [ ] Create dashboards

### Failover Setup
- [ ] Configure Cloudflare DNS
- [ ] Set up health checks
- [ ] Test failover manually
- [ ] Document failover procedures

### Monitoring
- [ ] Set up Firebase Crashlytics
- [ ] Configure Firebase Analytics
- [ ] Set up Mixpanel alerts

---

## 💰 Cost Estimation

| Service | Free Tier | Paid Tier |
|---------|-----------|-----------|
| Firebase Hosting | 1GB storage, 10GB bandwidth | $0.15/GB |
| Firebase Functions | 125K invocations | $0.10/100K |
| Cloud Firestore | 1GB stored data | $0.18/GB |
| Mixpanel | 100K events/month | $0/month (growth) |
| Cloudflare Pro | - | $20/month |

**Estimated Monthly Cost (with failover):** $5-20/month

---

## 🚀 Quick Start Commands

```bash
# 1. Deploy frontend to Firebase
cd services/social-media/frontend
firebase deploy --only hosting

# 2. Test deployment
firebase open hosting:site

# 3. Set up CI/CD (GitHub Actions)
# Create .github/workflows/firebase.yml
```

---

## 📞 Next Steps

1. **Confirm Firebase account** and project name
2. **Get Mixpanel token** or use existing project
3. **Decide failover method** (DNS vs client-side)
4. **Test deployment** on Firebase staging

