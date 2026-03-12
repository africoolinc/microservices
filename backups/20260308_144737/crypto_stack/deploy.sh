#!/bin/bash
# Deploy crypto_stack to remote server

STACK_DIR="/home/africool/.openclaw/workspace/projects/members/Gibson/crypto_stack"
REMOTE_HOST="10.144.118.159"
REMOTE_USER="gibz"
REMOTE_DIR="~/crypto_stack"

echo "🚀 Deploying crypto_stack to $REMOTE_HOST..."

# Sync files
echo "📁 Syncing files..."
rsync -avz --progress \
  --exclude 'node_modules' \
  --exclude '.env' \
  "$STACK_DIR/" \
  "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"

echo "✅ Files synced!"

echo "🔧 Running remote setup..."
ssh "$REMOTE_USER@$REMOTE_HOST" << 'EOF'
  cd ~/crypto_stack
  
  # Copy environment file (will need manual config)
  if [ ! -f .env ]; then
    cp .env.example .env
  fi
  
  # Start the stack
  docker-compose up -d
  
  echo "✅ Stack deployed!"
  docker-compose ps
EOF

echo "🎉 Deployment complete!"
