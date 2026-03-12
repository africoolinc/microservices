#!/bin/bash
# Gibson Trading API - Firebase Deployment Script

echo "🚀 Deploying Gibson Trading API Landing Page..."

# Navigate to the folder
cd "$(dirname "$0")"

# Initialize Firebase hosting if not already done
if [ ! -f ".firebaserc" ]; then
  echo "📦 Initializing Firebase hosting..."
  firebase init hosting
else
  echo "✅ Firebase already initialized"
fi

# Deploy to Firebase
echo "🚀 Deploying to Firebase..."
firebase deploy --only hosting

echo "✅ Deployment complete!"
echo "🌐 Your site will be available at: https://kalahari-484816.web.app"
