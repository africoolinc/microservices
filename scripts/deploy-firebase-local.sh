#!/bin/bash
# Firebase Deployment Helper for Gibson Microservices
# Run this on your LOCAL machine (not the server)

echo "=========================================="
echo "  Gibson Microservices Firebase Deploy"
echo "=========================================="

# Check for Firebase CLI
if ! command -v firebase &> /dev/null; then
    echo "❌ Firebase CLI not found."
    echo "   Installing..."
    npm install -g firebase-tools
fi

# Login to Firebase (use africoolinc@gmail.com)
echo "📋 Please login with: africoolinc@gmail.com"
firebase login

# Go to the frontend directory
cd services/social-media/frontend

# Deploy to Firebase Hosting
echo "🚀 Deploying to Firebase..."
firebase deploy --only hosting --project africool-fd821

echo "✅ Done! Your app is live at:"
echo "   https://africool-fd821.web.app"
