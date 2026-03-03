# Lyrikali Firebase Integration Guide

## ✅ Configured (Ready to Deploy)

### Firebase Config (`firebase-config.js`)
```javascript
const firebaseConfig = {
  apiKey: "AIzaSyAmS0qOzT2QIfw_4pvGjdK9zRDUNYrX41s",
  authDomain: "lyrikali-app.firebaseapp.com",
  projectId: "lyrikali-app",
  storageBucket: "lyrikali-app.appspot.com",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID",
  measurementId: "YOUR_MEASUREMENT_ID"
};
```

### Firebase Hosting (`firebase.json`)
- **Site:** lyrikali-app
- **Public:** Current directory
- **Rewrites:** API → Cloud Function, SPA fallback to index.html

---

## ⚠️ Missing Values

Before deploying, fill in these values in `firebase-config.js`:

1. **messagingSenderId** - Get from Firebase Console → Project Settings → Cloud Messaging
2. **appId** - Get from Firebase Console → Project Settings → General → Your apps
3. **measurementId** - Get from Firebase Console → Project Settings → Analytics

---

## 🚀 Deployment Steps

### 1. Install Firebase CLI
```bash
npm install -g firebase-tools
```

### 2. Login to Firebase
```bash
firebase login
```

### 3. Initialize Project (if not already)
```bash
cd services/social-media/frontend
firebase init hosting
```

### 4. Deploy to Firebase
```bash
firebase deploy --only hosting
```

### 5. Deploy Cloud Functions (optional)
```bash
firebase deploy --only functions
```

---

## 🔄 Firebase Fallback Logic

The app already has fallback logic in `app.js`:

```javascript
const FirebaseFallback = {
    enabled: false,
    firebaseUrl: 'https://lyrikali-app.web.app',
    
    async checkHealth() {
        try {
            const response = await fetch('/api/health', { 
                method: 'HEAD',
                signal: controller.signal 
            });
            return response.ok;
        } catch (e) {
            this.enabled = true;
            // Use Firebase fallback
            return false;
        }
    }
};
```

**How it works:**
1. App tries to connect to Gibson API (port 10500)
2. If fails, switches to Firebase-hosted version
3. Mixpanel tracks fallback activation

---

## 📦 Features Enabled

| Feature | Status | Config |
|---------|--------|--------|
| Firebase Hosting | ✅ Ready | firebase.json |
| Firebase Analytics | ✅ Ready | firebase-config.js |
| Firebase Auth | ⚠️ Needs appId | firebase-config.js |
| Firebase Firestore | ⚠️ Needs setup | firebase.json |
| Cloud Functions | ⚠️ Needs init | firebase.json |
| Mixpanel | ✅ Configured | index.html, app.js |

---

## 🌐 URLs

| Service | URL |
|---------|-----|
| Firebase Hosting | https://lyrikali-app.web.app |
| Firebase Console | https://console.firebase.google.com/project/lyrikali-app |

---

## 📝 Next Steps

1. [ ] Fill in missing Firebase config values (Sender ID, App ID)
2. [ ] Run `firebase login`
3. [ ] Run `firebase deploy --only hosting`
4. [ ] Verify site loads at https://lyrikali-app.web.app
5. [ ] Test fallback: Stop Gibson API → Refresh page → Should load from Firebase
