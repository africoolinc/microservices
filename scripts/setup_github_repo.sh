#!/bin/bash
# GitHub Repository Setup Script for Gibson's Microservices Stack
# This script initializes a git repo and pushes the stack to GitHub

set -e

REPO_NAME="${1:-microservices-stack}"
GITHUB_USER="${2:-africoolinc}"
REMOTE_HOST="10.144.118.159"
REMOTE_USER="gibz"
STACK_DIR="/opt/microservices-stack"  # Adjust based on actual remote path

echo "========================================="
echo "GitHub Repository Setup for Microservices Stack"
echo "========================================="
echo ""

# Check if running on remote or local
if [ -d "$STACK_DIR" ]; then
    echo "✓ Running on remote machine"
    LOCAL_SETUP=true
else
    echo "ℹ Running locally - will connect to remote"
    LOCAL_SETUP=false
fi

# Step 1: Ensure git is installed
echo "[1/6] Checking git installation..."
if ! command -v git &> /dev/null; then
    echo "Installing git..."
    sudo apt-get update && sudo apt-get install -y git
fi
echo "✓ Git is ready"

# Step 2: Configure git identity
echo ""
echo "[2/6] Configuring git identity..."
git config --global user.email "africoolinc@gmail.com" || true
git config --global user.name "africoolinc" || true
echo "✓ Git identity configured"

# Step 3: Initialize repository
echo ""
echo "[3/6] Initializing git repository..."
if [ ! -d "$STACK_DIR/.git" ]; then
    cd "$STACK_DIR"
    git init
    git branch -M main
    echo "✓ Repository initialized"
else
    echo "✓ Repository already initialized"
fi

# Step 4: Create .gitignore
echo ""
echo "[4/6] Creating .gitignore..."
cat > "$STACK_DIR/.gitignore" << 'EOF'
# Environment files
.env
.env.local
.env.*.local

# Secrets
*.pem
*.key
secrets/
.secrets/
config/secrets/

# Database files
*.db
*.sqlite
*.sqlite3
postgres-data/
redis-data/
elasticsearch-data/

# Logs
logs/
*.log
npm-debug.log*

# Runtime
pids/
*.pid
*.seed
*.pid.lock

# Docker
.docker/
docker-compose.override.yml

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Temporary files
tmp/
temp/
*.tmp
EOF
echo "✓ .gitignore created"

# Step 5: Add all files and commit
echo ""
echo "[5/6] Adding files to repository..."
cd "$STACK_DIR"
git add -A
git commit -m "Initial commit: Production-ready microservices stack

Components:
- Kong API Gateway (routing, auth, rate limiting)
- Consul Service Registry (service discovery)
- Flask microservices (A, B, C)
- Keycloak (identity management)
- PostgreSQL databases
- Redis caching layer
- Kafka message broker
- Prometheus + Grafana monitoring
- ELK stack (logging)
- Portainer (container management)

This stack provides a complete, production-ready infrastructure
for scalable microservices deployments." || echo "No changes to commit"
echo "✓ Files committed"

# Step 6: Connect to GitHub
echo ""
echo "[6/6] Connecting to GitHub..."
echo ""
echo "INSTRUCTIONS TO COMPLETE SETUP:"
echo "================================"
echo ""
echo "1. Copy this SSH public key to GitHub:"
echo "----------------------------------------"
cat ~/.ssh/github_microservices.pub 2>/dev/null || echo "   (Generate with: ssh-keygen -t ed25519 -f ~/.ssh/github_microservices)"
echo "----------------------------------------"
echo ""
echo "   Add to GitHub: https://github.com/settings/keys"
echo ""
echo "2. Create a new repository on GitHub:"
echo "   https://github.com/new"
echo "   Name: $REPO_NAME"
echo "   Visibility: Private (recommended for now)"
echo ""
echo "3. Then run these commands:"
echo "   cd $STACK_DIR"
echo "   git remote add origin git@github.com:$GITHUB_USER/$REPO_NAME.git"
echo "   git push -u origin main"
echo ""
echo "✓ Setup complete!"
echo ""
echo "========================================="
echo "Your microservices stack is ready for GitHub!"
echo "========================================="
