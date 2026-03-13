#!/bin/bash
# Deploy Crypto Register Service to Port 3001

set -e

echo "=== Deploying Crypto Register Service ==="

# Check if running on remote or local
if [ -d "/opt/microservices-stack" ]; then
    echo "Running on remote machine..."
    cd /opt/microservices-stack/services/crypto-register
else
    echo "Running from local - will deploy via SSH..."
    # Copy files to remote
    scp -r ./services/crypto-register gibson-vpn:/opt/microservices-stack/services/
fi

# Build and start containers
echo "Building and starting containers..."
docker-compose -f /opt/microservices-stack/services/crypto-register/docker-compose.yml up -d --build

# Wait for service to be ready
echo "Waiting for service..."
sleep 5

# Check status
echo "=== Service Status ==="
docker ps | grep crypto-register

echo ""
echo "=== Service deployed on port 3001 ==="
echo "Frontend: http://<server-ip>:3001"
echo "API: http://<server-ip>:3002"