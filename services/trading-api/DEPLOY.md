# Gibson Trading API Landing Page

## ⚠️ Firebase Setup Required

The Firebase project `africool-fd821` is not accessible from this machine. You need to:

### Option A: Run Firebase Deploy Locally

On a machine with Firebase access, run:

```bash
firebase deploy --only hosting --project africool-fd821
```

### Option B: Create New Project

1. Go to https://console.firebase.google.com/
2. Create project: `gibson-trading-api`
3. Enable Hosting
4. Update `.firebaserc` with new project ID
5. Run `firebase deploy`

### Option C: Alternative Hosting

Deploy to Vercel, Netlify, or any static host:

```bash
# Vercel
vercel --prod

# Netlify  
netlify deploy --prod
```

---

## Files Ready for Deployment

- `index.html` - Complete landing page with pricing tiers
- `firebase.json` - Firebase hosting config
- `.firebaserc` - Project configuration
- `server.js` - Trading API backend
- `README.md` - API documentation

---

*Last Updated: March 10, 2026*
