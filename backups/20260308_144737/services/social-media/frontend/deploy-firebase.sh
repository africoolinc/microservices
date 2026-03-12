#!/bin/bash
# Firebase Deploy Script for Lyrikali Social
# Updated: March 6, 2026

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR"

echo "=== Lyrikali Firebase Deployment ==="
echo ""

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Install from https://nodejs.org"
    exit 1
fi

# Check npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm not found"
    exit 1
fi

echo "📦 Installing dependencies..."
cd "$FRONTEND_DIR"
npm install 2>/dev/null || true

# Check for Firebase CLI
if ! command -v firebase &> /dev/null; then
    echo "📦 Installing Firebase CLI..."
    npm install -g firebase-tools
fi

# Check Firebase login
echo "🔐 Checking Firebase authentication..."
if ! firebase projects:list &>/dev/null 2>&1; then
    echo "⚠️  Not logged in to Firebase. Run: firebase login"
    echo "   Then re-run this script."
    exit 1
fi

# Create production config
echo "⚙️  Configuring production build..."

# Detect API endpoint
API_ENDPOINT=""
if [ -f /home/africool/.openclaw/workspace/projects/members/Gibson/ngrok/.env ]; then
    source /home/africool/.openclaw/workspace/projects/members/Gibson/ngrok/.env
fi

# Check if ngrok is running
NGROK_URL=$(curl -s localhost:4040/api/tunnels 2>/dev/null | grep -o '"public_url":"https://[^"]*"' | head -1 | cut -d'"' -f4)
if [ -n "$NGROK_URL" ]; then
    API_ENDPOINT="$NGROK_URL"
    echo "✅ Ngrok detected: $API_ENDPOINT"
else
    # Use local IP as fallback
    LOCAL_IP=$(hostname -I | awk '{print $1}')
    API_ENDPOINT="http://$LOCAL_IP:10500"
    echo "⚠️  Ngrok not running. Using local: $API_ENDPOINT"
    echo "   For public access, start ngrok: ngrok http 10500"
fi

# Update app.js with correct API URL
sed -i "s|const API_BASE = '';|const API_BASE = '$API_ENDPOINT';|g" "$FRONTEND_DIR/app.js"
sed -i "s|const KEYCLOAK_URL = 'http://localhost:8080'|const KEYCLOAK_URL = '$API_ENDPOINT'|g" "$FRONTEND_DIR/app.js"

echo "📝 API Endpoint set to: $API_ENDPOINT"

# Deploy to Firebase
echo ""
echo "🚀 Deploying to Firebase Hosting..."
firebase deploy --only hosting --project africool-fd821

echo ""
echo "✅ Deployment complete!"
echo "🌐 Live URL: https://africool-fd821.web.app"
echo "🔗 API: $API_ENDPOINT"
