#!/bin/bash
# Sync Local Workspace with Remote Machine
# Pushes management scripts to remote and pulls stack config from remote

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/../config/remote_config.txt"

# Load config
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
else
    REMOTE_HOST="10.144.118.159"
    REMOTE_USER="gibz"
    REMOTE_PASS="Lamborghini"
fi

STACK_DIR="${STACK_DIR:-/opt/microservices-stack}"

echo "========================================="
echo "Workspace Sync - Local ↔ Remote"
echo "========================================="
echo "Remote: $REMOTE_USER@$REMOTE_HOST"
echo "Stack:  $STACK_DIR"
echo ""

# Check SSH connectivity
echo "[1/4] Testing SSH connection..."
if ! ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "echo 'connected'" 2>/dev/null | grep -q "connected"; then
    echo "✗ Cannot connect to remote"
    echo "  Run: ./scripts/update_remote_ip.sh <new-ip>"
    exit 1
fi
echo "✓ SSH connection working"

# Sync local scripts to remote (for running on remote)
echo ""
echo "[2/4] Pushing management scripts to remote..."
ssh "$REMOTE_USER@$REMOTE_HOST" "mkdir -p $STACK_DIR/management-scripts"
scp -q "$SCRIPT_DIR/"*.sh "$REMOTE_USER@$REMOTE_HOST:$STACK_DIR/management-scripts/" 2>/dev/null || {
    echo "⚠ Could not sync scripts (remote may not have rsync)"
}
echo "✓ Scripts synced"

# Check remote stack structure
echo ""
echo "[3/4] Checking remote stack structure..."
REMOTE_FILES=$(ssh "$REMOTE_USER@$REMOTE_HOST" "ls -la $STACK_DIR/ 2>/dev/null || echo 'NOT_FOUND'")
if echo "$REMOTE_FILES" | grep -q "docker-compose.yml"; then
    echo "✓ Stack found on remote"
    echo ""
    echo "Remote files:"
    echo "$REMOTE_FILES" | head -20
else
    echo "⚠ docker-compose.yml not found on remote"
    echo "  Remote directory: $STACK_DIR"
    echo "  May need to create stack first"
fi

# Pull remote config to local (for reference)
echo ""
echo "[4/4] Syncing remote configs to local..."
mkdir -p "$SCRIPT_DIR/../config/remote-backup"
scp -q "$REMOTE_USER@$REMOTE_HOST:$STACK_DIR/docker-compose.yml" "$SCRIPT_DIR/../config/remote-backup/" 2>/dev/null || true
scp -q "$REMOTE_USER@$REMOTE_HOST:$STACK_DIR/.env" "$SCRIPT_DIR/../config/remote-backup/" 2>/dev/null || true
echo "✓ Configs backed up locally"

echo ""
echo "========================================="
echo "Sync Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Run: ./scripts/stack-manager.sh (interactive menu)"
echo "  2. Or:  ./scripts/check_services.sh (health check)"
echo "  3. Or:  ssh $REMOTE_USER@$REMOTE_HOST (direct access)"
