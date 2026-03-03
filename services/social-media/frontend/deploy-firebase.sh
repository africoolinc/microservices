#!/bin/bash
# Auto-deploy script for Lyrikali Firebase Hosting
# Run manually or set up cron for automated deployments

set -e

# Check for Firebase CLI
if ! command -v firebase &> /dev/null; then
    echo "❌ Firebase CLI not found. Install with: npm install -g firebase-tools"
    exit 1
fi

# Check if logged in
echo "🔐 Checking Firebase authentication..."
firebase projects:list &>/dev/null || {
    echo "❌ Not logged in to Firebase."
    echo "   Run: firebase login"
    echo "   Then re-run this script."
    exit 1
}

# Deploy
echo "🚀 Deploying to Firebase Hosting..."
firebase deploy --only hosting --project africool-fd821

echo "✅ Deployment complete!"
echo "🌐 https://africool-fd821.web.app"
