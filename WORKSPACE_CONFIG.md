# Workspace Configuration

## Default Accounts

| Service | Account | Status |
|---------|---------|--------|
| GitHub | africoolinc@gmail.com | ✅ Configured |
| Firebase | africoolinc@gmail.com | ⚠️ Needs manual setup |
| GCP | africoolinc@gmail.com | ⚠️ Needs manual setup |

## Firebase Setup (Manual Required)

Since interactive browser login is limited, please set up Firebase manually:

1. **On your local machine with browser access:**
   ```bash
   # Install Firebase CLI if needed
   npm install -g firebase-tools
   
   # Login with africoolinc@gmail.com
   firebase login
   ```

2. **Then copy credentials to this machine OR deploy directly from local**

3. **Alternatively - Deploy from local machine:**
   ```bash
   cd services/trading-api
   firebase init hosting
   # Select "Use an existing project" or create new
   # Deploy: firebase deploy --only hosting
   ```

## GitHub Token

Stored in: `.secrets/github_token`

## Notes

- The previous account (swahilisafarifame@gmail.com) has been deauthorized
- gcloud auth currently has no credentialed accounts
- Firebase projects need to be accessed via Firebase Console at https://console.firebase.google.com/

---

*Updated: March 10, 2026*
