#!/bin/bash
# Backup Script for Gibson's Microservices Stack
# Creates timestamped backups of all data volumes

set -e

BACKUP_DIR="${1:-./backups}"
REMOTE_HOST="${2:-10.144.118.159}"
REMOTE_USER="${3:-gibz}"
STACK_DIR="/opt/microservices-stack"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="microservices_backup_${TIMESTAMP}"

echo "========================================="
echo "Microservices Stack Backup"
echo "========================================="
echo "Backup Directory: $BACKUP_DIR"
echo "Timestamp: $TIMESTAMP"
echo ""

# Create backup directory locally
mkdir -p "$BACKUP_DIR"

# Function to backup from local machine
backup_local() {
    echo "[LOCAL] Creating backup..."
    
    cd "$STACK_DIR" || exit 1
    
    # Create backup archive name
    ARCHIVE="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
    
    # Stop services gracefully
    echo "Stopping services for consistent backup..."
    docker-compose down
    
    # Create compressed backup of volumes and configs
    echo "Compressing data..."
    tar -czf "$ARCHIVE" \
        docker-compose.yml \
        config/ \
        services/ \
        scripts/ \
        2>/dev/null || true
    
    # Backup Docker volumes
    echo "Backing up Docker volumes..."
    docker run --rm \
        -v kong-db-data:/source/kong-db:ro \
        -v keycloak-db-data:/source/keycloak-db:ro \
        -v app-db-data:/source/app-db:ro \
        -v redis-data:/source/redis:ro \
        -v es-data:/source/es:ro \
        -v grafana-data:/source/grafana:ro \
        -v prometheus-data:/source/prometheus:ro \
        -v portainer-data:/source/portainer:ro \
        -v "$(pwd)/${BACKUP_DIR}:/backup" \
        alpine:latest \
        tar -czf "/backup/${BACKUP_NAME}_volumes.tar.gz" -C /source . 2>/dev/null || {
        echo "Warning: Some volumes may not exist yet"
    }
    
    # Restart services
    echo "Restarting services..."
    docker-compose up -d
    
    echo "✓ Local backup complete!"
    echo "  Config: $ARCHIVE"
    echo "  Volumes: ${BACKUP_DIR}/${BACKUP_NAME}_volumes.tar.gz"
}

# Function to backup from remote via SSH
backup_remote() {
    echo "[REMOTE] Connecting to $REMOTE_HOST..."
    
    # Check SSH connection
    if ! ssh "$REMOTE_USER@$REMOTE_HOST" "echo 'connected'" 2>/dev/null | grep -q "connected"; then
        echo "ERROR: Cannot connect to remote host"
        echo "Run ./setup_ssh.sh first to configure SSH access"
        exit 1
    fi
    
    # Execute backup on remote
    ssh "$REMOTE_USER@$REMOTE_HOST" << EOF
        cd "$STACK_DIR"
        mkdir -p backups
        
        echo "[REMOTE] Stopping services..."
        docker-compose down 2>/dev/null || docker compose down 2>/dev/null || true
        
        echo "[REMOTE] Creating backup archive..."
        tar -czf "backups/${BACKUP_NAME}.tar.gz" \
            docker-compose.yml \
            config/ \
            services/ \
            scripts/ \
            .env 2>/dev/null || true
        
        echo "[REMOTE] Backing up volumes..."
        docker run --rm \
            -v kong-db-data:/source/kong-db:ro \
            -v keycloak-db-data:/source/keycloak-db:ro \
            -v app-db-data:/source/app-db:ro \
            -v redis-data:/source/redis:ro \
            -v es-data:/source/es:ro \
            -v grafana-data:/source/grafana:ro \
            -v prometheus-data:/source/prometheus:ro \
            -v portainer-data:/source/portainer:ro \
            -v "$(pwd)/backups:/backup" \
            alpine:latest \
            tar -czf "/backup/${BACKUP_NAME}_volumes.tar.gz" -C /source . 2>/dev/null || echo "Some volumes skipped"
        
        echo "[REMOTE] Restarting services..."
        docker-compose up -d 2>/dev/null || docker compose up -d 2>/dev/null || true
        
        echo "[REMOTE] Backup complete at: backups/${BACKUP_NAME}.tar.gz"
EOF
    
    # Download backups from remote
    echo "[LOCAL] Downloading backups from remote..."
    mkdir -p "$BACKUP_DIR"
    scp "$REMOTE_USER@$REMOTE_HOST:$STACK_DIR/backups/${BACKUP_NAME}*.tar.gz" "$BACKUP_DIR/" 2>/dev/null || {
        echo "Note: Could not download - backups remain on remote at $STACK_DIR/backups/"
    }
    
    echo "✓ Remote backup complete!"
}

# Check if running on remote or local
if [ -d "$STACK_DIR" ]; then
    echo "Detected: Running on local (remote) machine"
    backup_local
else
    echo "Detected: Running from management machine"
    backup_remote
fi

# Cleanup old backups (keep last 7)
echo ""
echo "Cleaning up old backups (keeping last 7)..."
cd "$BACKUP_DIR"
ls -t *.tar.gz 2>/dev/null | tail -n +8 | xargs -r rm -f

echo ""
echo "========================================="
echo "Backup Summary"
echo "========================================="
echo "Backup Location: $BACKUP_DIR"
echo "Files created:"
ls -lh "$BACKUP_DIR/${BACKUP_NAME}"*.tar.gz 2>/dev/null || echo "  (Check remote machine)"
echo ""
echo "To restore:"
echo "  tar -xzf ${BACKUP_NAME}.tar.gz"
echo "  docker-compose up -d"
echo "========================================="
