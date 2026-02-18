#!/bin/bash
# StackForge Auto-Deploy Script
# Managed by Ahie Juma

REMOTE_HOST="10.144.118.159"
REMOTE_USER="gibz"
REMOTE_PASS="Lamborghini"
STACK_DIR="/home/gibz/stackforge"

echo "🚀 Starting Deployment to $REMOTE_HOST..."

# 1. Clear conflicting containers (just in case)
echo "🛑 Clearing conflicting containers..."
echo "$REMOTE_PASS" | sshpass -p "$REMOTE_PASS" ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "cat | sudo -S bash -c \"docker stop redis app-db keycloak-db kong-db prometheus grafana 2>/dev/null; docker rm redis app-db keycloak-db kong-db prometheus grafana 2>/dev/null\""

# 2. Create directory structure
echo "📁 Preparing directory structure..."
sshpass -p "$REMOTE_PASS" ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "mkdir -p $STACK_DIR/services/{ecommerce-platform,fintech-app,social-media}/src"

# 4. Push new files
echo "📤 Uploading new configuration..."
sshpass -p "$REMOTE_PASS" scp -o StrictHostKeyChecking=no projects/members/Gibson/docker-compose.yml "$REMOTE_USER@$REMOTE_HOST:$STACK_DIR/docker-compose.yml"

# Upload E-commerce
sshpass -p "$REMOTE_PASS" scp -o StrictHostKeyChecking=no projects/members/Gibson/services/ecommerce-platform/Dockerfile "$REMOTE_USER@$REMOTE_HOST:$STACK_DIR/services/ecommerce-platform/"
sshpass -p "$REMOTE_PASS" scp -o StrictHostKeyChecking=no projects/members/Gibson/services/ecommerce-platform/src/main.py "$REMOTE_USER@$REMOTE_HOST:$STACK_DIR/services/ecommerce-platform/src/"

# Upload FinTech
sshpass -p "$REMOTE_PASS" scp -o StrictHostKeyChecking=no projects/members/Gibson/services/fintech-app/Dockerfile "$REMOTE_USER@$REMOTE_HOST:$STACK_DIR/services/fintech-app/"
sshpass -p "$REMOTE_PASS" scp -o StrictHostKeyChecking=no projects/members/Gibson/services/fintech-app/src/main.py "$REMOTE_USER@$REMOTE_HOST:$STACK_DIR/services/fintech-app/src/"

# Upload Social Media
sshpass -p "$REMOTE_PASS" scp -o StrictHostKeyChecking=no projects/members/Gibson/services/social-media/Dockerfile "$REMOTE_USER@$REMOTE_HOST:$STACK_DIR/services/social-media/"
sshpass -p "$REMOTE_PASS" scp -o StrictHostKeyChecking=no projects/members/Gibson/services/social-media/src/main.py "$REMOTE_USER@$REMOTE_HOST:$STACK_DIR/services/social-media/src/"

# 5. Start new stack
echo "🏗️ Starting new stack..."
echo "$REMOTE_PASS" | sshpass -p "$REMOTE_PASS" ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "cat | sudo -S bash -c \"cd $STACK_DIR && docker-compose up -d --build\""

echo "✅ Deployment complete!"
