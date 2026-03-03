#!/bin/bash
# Lyrikali Firebase Deploy Script
# Run: chmod +x deploy-firebase.sh && ./deploy-firebase.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Deploying Lyrikali to Firebase..."

# Check if logged in
if ! firebase projects:list >/dev/null 2>&1; then
    echo "❌ Not logged in. Run: firebase login"
    exit 1
fi

# Use correct project
firebase use africool-fd821 --project africool-fd821 2>/dev/null || true

# Deploy hosting
echo "📦 Deploying to Firebase Hosting..."
firebase deploy --only hosting --project africool-fd821

echo "✅ Deployment complete!"
echo "🌐 Live at: https://africool-fd821.web.app"
