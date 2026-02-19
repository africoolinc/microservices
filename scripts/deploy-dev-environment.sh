#!/bin/bash
# Deploy Development Environment to Remote
# Sets up all 3 microservices for developer access

set -e

REMOTE_HOST="${1:-10.144.118.159}"
REMOTE_USER="gibz"
REMOTE_PASS="Lamborghini"
STACK_DIR="/opt/dev-stack"

echo "========================================="
echo "Deploying Development Environment"
echo "Remote: $REMOTE_USER@$REMOTE_HOST"
echo "========================================="
echo ""

# Test connection
echo "[1/5] Testing SSH connection..."
if ! sshpass -p "$REMOTE_PASS" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$REMOTE_USER@$REMOTE_HOST" "echo 'connected'" 2>/dev/null | grep -q "connected"; then
    echo "✗ Cannot connect to $REMOTE_HOST"
    echo "  Possible issues:"
    echo "    - Wrong IP address"
    echo "    - Remote machine is offline"
    echo "    - SSH service not running"
    echo ""
    echo "  To update IP: ./update_remote_ip.sh <new-ip>"
    exit 1
fi
echo "✓ SSH connection successful"

# Create directory structure on remote
echo ""
echo "[2/5] Creating directory structure..."
sshpass -p "$REMOTE_PASS" ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "
    sudo mkdir -p $STACK_DIR
    sudo chown $REMOTE_USER:$REMOTE_USER $STACK_DIR
    mkdir -p $STACK_DIR/{services/{ecommerce-platform,fintech-app,social-media},scripts,config,logs}
    echo 'Directories created'
"
echo "✓ Directory structure ready"

# Copy service files
echo ""
echo "[3/5] Deploying microservices..."

# E-commerce
sshpass -p "$REMOTE_PASS" scp -o StrictHostKeyChecking=no -r \
    services/ecommerce-platform/* \
    "$REMOTE_USER@$REMOTE_HOST:$STACK_DIR/services/ecommerce-platform/" 2>/dev/null || echo "⚠ E-commerce service copy incomplete"

# FinTech
sshpass -p "$REMOTE_PASS" scp -o StrictHostKeyChecking=no -r \
    services/fintech-app/* \
    "$REMOTE_USER@$REMOTE_HOST:$STACK_DIR/services/fintech-app/" 2>/dev/null || echo "⚠ FinTech service copy incomplete"

# Social Media  
sshpass -p "$REMOTE_PASS" scp -o StrictHostKeyChecking=no -r \
    services/social-media/* \
    "$REMOTE_USER@$REMOTE_HOST:$STACK_DIR/services/social-media/" 2>/dev/null || echo "⚠ Social Media service copy incomplete"

echo "✓ Services deployed"

# Copy docker-compose and scripts
echo ""
echo "[4/5] Copying orchestration files..."
sshpass -p "$REMOTE_PASS" scp -o StrictHostKeyChecking=no \
    docker-compose.dev.yml \
    "$REMOTE_USER@$REMOTE_HOST:$STACK_DIR/docker-compose.yml" 2>/dev/null || echo "⚠ Compose file copy incomplete"

sshpass -p "$REMOTE_PASS" scp -o StrictHostKeyChecking=no \
    scripts/*.sh \
    "$REMOTE_USER@$REMOTE_HOST:$STACK_DIR/scripts/" 2>/dev/null || echo "⚠ Scripts copy incomplete"

echo "✓ Orchestration files ready"

# Start services
echo ""
echo "[5/5] Starting services..."
sshpass -p "$REMOTE_PASS" ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "
    cd $STACK_DIR
    
    # Check if docker is running
    if ! docker info > /dev/null 2>&1; then
        echo '⚠ Docker not running. Starting Docker...'
        sudo systemctl start docker 2>/dev/null || echo 'Could not start Docker'
    fi
    
    # Build and start services
    echo 'Building microservices...'
    docker-compose build --parallel 2>&1 | tail -20
    
    echo 'Starting services...'
    docker-compose up -d
    
    echo ''
    echo 'Service Status:'
    docker-compose ps
    
    echo ''
    echo '========================================='
    echo 'Development Environment Ready!'
    echo '========================================='
    echo ''
    echo 'Service URLs:'
    echo '  E-Commerce:    http://localhost:5001'
    echo '  FinTech:       http://localhost:5002'
    echo '  Social Media:  http://localhost:5003'
    echo '  Kong Gateway:  http://localhost:8000'
    echo '  Consul:        http://localhost:8500'
    echo '  Grafana:       http://localhost:3000'
    echo ''
    echo 'Developer Access:'
    echo '  ssh $REMOTE_USER@$REMOTE_HOST'
    echo '  cd $STACK_DIR'
    echo '  docker-compose logs -f [service-name]'
"

echo ""
echo "✓ Deployment complete!"
echo ""
echo "Next steps for developers:"
echo "  1. SSH to remote: ssh gibz@$REMOTE_HOST"
echo "  2. Edit code in: $STACK_DIR/services/"
echo "  3. Restart service: docker-compose restart [service-name]"
echo "  4. View logs: docker-compose logs -f [service-name]"
