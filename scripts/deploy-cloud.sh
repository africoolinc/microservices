#!/bin/bash
# Deploy StackForge to Cloud VPS
# Supports: DigitalOcean, AWS EC2, Linode, Vultr

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SSH_KEY="~/.ssh/id_rsa"
REMOTE_USER="root"
STACK_DIR="/opt/stackforge"

echo -e "${BLUE}=== StackForge Cloud Deployment ===${NC}"
echo ""

# Parse arguments
PROVIDER=""
REGION=""
SERVER_IP=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --provider)
            PROVIDER="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --ip)
            SERVER_IP="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --provider    Cloud provider (digitalocean, aws, linode, vultr)"
            echo "  --region      Region/datacenter (e.g., nyc1, us-east-1)"
            echo "  --ip          IP of existing server (skips provisioning)"
            echo "  --help        Show this help"
            echo ""
            echo "Examples:"
            echo "  $0 --provider digitalocean --region nyc1"
            echo "  $0 --ip 165.227.123.45"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Get server IP
if [ -z "$SERVER_IP" ]; then
    if [ -z "$PROVIDER" ]; then
        read -p "Enter cloud provider (digitalocean/aws/linode/vultr): " PROVIDER
    fi
    if [ -z "$REGION" ]; then
        read -p "Enter region (e.g., nyc1, us-east-1): " REGION
    fi
    
    echo -e "${YELLOW}Provisioning new $PROVIDER server in $REGION...${NC}"
    echo -e "${RED}Note: Automated provisioning not yet implemented.${NC}"
    echo "Please create a server manually with:"
    echo "  - Ubuntu 22.04 LTS"
    echo "  - 4GB RAM minimum (8GB recommended)"
    echo "  - 2 vCPUs"
    echo "  - 50GB SSD"
    echo "  - SSH key authentication"
    echo ""
    read -p "Enter the server IP address: " SERVER_IP
else
    echo -e "${GREEN}Using existing server at $SERVER_IP${NC}"
fi

# Verify SSH access
echo -e "${BLUE}Testing SSH connection...${NC}"
if ! ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new "${REMOTE_USER}@${SERVER_IP}" "echo 'Connection successful'" 2>/dev/null; then
    echo -e "${RED}Cannot connect to $SERVER_IP via SSH${NC}"
    echo "Please ensure:"
    echo "  1. Server is running"
    echo "  2. SSH port 22 is open"
    echo "  3. Your SSH key is added to the server"
    exit 1
fi

echo -e "${GREEN}SSH connection verified${NC}"
echo ""

# Server setup
echo -e "${BLUE}Setting up server...${NC}"
ssh "${REMOTE_USER}@${SERVER_IP}" << 'REMOTE_SCRIPT'
    # Update system
    apt-get update && apt-get upgrade -y
    
    # Install dependencies
    apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release \
        git \
        ufw \
        fail2ban \
        nginx
    
    # Install Docker
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Start Docker
    systemctl enable docker
    systemctl start docker
    
    # Create stack user
    useradd -m -s /bin/bash -G docker stackforge || true
    
    # Create directory
    mkdir -p /opt/stackforge
    chown stackforge:stackforge /opt/stackforge
    
    # Configure firewall
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable
    
    # Install fail2ban
    systemctl enable fail2ban
    systemctl start fail2ban
    
    echo "Server setup complete"
REMOTE_SCRIPT

echo -e "${GREEN}Server setup complete${NC}"
echo ""

# Deploy stack
echo -e "${BLUE}Deploying StackForge...${NC}"

# Create local tarball of stack (excluding secrets and data)
tar czf /tmp/stackforge-deploy.tar.gz \
    --exclude='.git' \
    --exclude='.secrets' \
    --exclude='postgres-data' \
    --exclude='pgdata' \
    --exclude='elasticsearch-data' \
    --exclude='*.db' \
    --exclude='logs' \
    --exclude='volumes' \
    --exclude='*.log' \
    --exclude='tmp' \
    --exclude='.DS_Store' \
    .

# Copy to server
scp /tmp/stackforge-deploy.tar.gz "${REMOTE_USER}@${SERVER_IP}:/opt/stackforge/"

# Extract and start
ssh "${REMOTE_USER}@${SERVER_IP}" << REMOTE_SCRIPT
    cd /opt/stackforge
    tar xzf stackforge-deploy.tar.gz
    rm stackforge-deploy.tar.gz
    chown -R stackforge:stackforge .
    
    # Create env file for secrets
    cat > .env << 'EOF'
# Database passwords (CHANGE THESE!)
POSTGRES_USER=appuser
POSTGRES_PASSWORD=$(openssl rand -base64 32)
POSTGRES_DB=appdb
KONG_DB_USER=kong
KONG_DB_PASS=$(openssl rand -base64 32)
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=$(openssl rand -base64 32)
GRAFANA_ADMIN=admin
GRAFANA_PASS=$(openssl rand -base64 32)

# App configuration
SERVICE_A_ID=service-a
SERVICE_B_ID=service-b
SERVICE_C_ID=service-c
CONSUL_HOST=consul
KAFKA_BROKER=kafka:9092
EOF
    
    # Start the stack
    docker compose up -d
    
    # Wait for services
    echo "Waiting for services to start..."
    sleep 30
    
    # Check status
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    echo ""
    echo "StackForge deployed!"
REMOTE_SCRIPT

# Setup nginx reverse proxy with SSL
echo -e "${BLUE}Setting up reverse proxy...${NC}"
ssh "${REMOTE_USER}@${SERVER_IP}" << REMOTE_SCRIPT
    # Install certbot
    snap install core
    snap refresh core
    snap install --classic certbot
    ln -s /snap/bin/certbot /usr/bin/certbot
    
    # Create nginx config (will be customized per domain)
    cat > /etc/nginx/sites-available/stackforge << 'EOF'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    
    ln -sf /etc/nginx/sites-available/stackforge /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    nginx -t && systemctl restart nginx
REMOTE_SCRIPT

echo ""
echo -e "${GREEN}=== Deployment Complete! ===${NC}"
echo ""
echo "Server: $SERVER_IP"
echo "SSH: ssh ${REMOTE_USER}@${SERVER_IP}"
echo ""
echo "Admin UIs (via SSH tunnel):"
echo "  ssh -L 8001:localhost:8001 -L 8500:localhost:8500 -L 3000:localhost:3000 ${REMOTE_USER}@${SERVER_IP}"
echo ""
echo "Next steps:"
echo "  1. Configure DNS to point to $SERVER_IP"
echo "  2. Run certbot for SSL: certbot --nginx"
echo "  3. Update .env with production secrets"
echo "  4. Configure Kong routes for your APIs"
echo "  5. Set up monitoring alerts"
echo ""
echo "To check status:"
echo "  ssh ${REMOTE_USER}@${SERVER_IP} 'cd /opt/stackforge && docker compose ps'"
