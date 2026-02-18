#!/bin/bash
# Dynamic IP Update Script for Gibson's Remote Machine
# Run this when the remote machine IP changes

set -e

NEW_IP="$1"
CONFIG_FILE="${2:-$(dirname $0)/remote_config.txt}"

echo "========================================="
echo "Remote Machine IP Updater"
echo "========================================="
echo ""

if [ -z "$NEW_IP" ]; then
    echo "Usage: $0 <new_ip_address> [config_file]"
    echo ""
    echo "Example:"
    echo "  $0 192.168.84.109"
    echo ""
    echo "Current config file: $CONFIG_FILE"
    if [ -f "$CONFIG_FILE" ]; then
        echo ""
        echo "Current settings:"
        cat "$CONFIG_FILE"
    fi
    exit 1
fi

echo "Updating remote IP to: $NEW_IP"
echo ""

# Save config
cat > "$CONFIG_FILE" << EOF
# Gibson's Remote Machine Configuration
# Last updated: $(date)

REMOTE_HOST=$NEW_IP
REMOTE_USER=gibz
REMOTE_PASS=Lamborghini
STACK_DIR=/opt/microservices-stack
SSH_KEY=~/.ssh/github_microservices
EOF

echo "✓ Config saved to: $CONFIG_FILE"

# Update SSH config
SSH_CONFIG="$HOME/.ssh/config"
if [ -f "$SSH_CONFIG" ]; then
    # Remove old entry if exists
    sed -i '/Host gibson-stack/,/^Host /{ /^Host gibson-stack/d; /^Host /!d; }' "$SSH_CONFIG" 2>/dev/null || true
    
    # Add new entry
    cat >> "$SSH_CONFIG" << EOF

Host gibson-stack
    HostName $NEW_IP
    User gibz
    IdentityFile ~/.ssh/github_microservices
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
EOF
    echo "✓ SSH config updated"
else
    echo "⚠ SSH config not found - run setup_ssh.sh after updating IP"
fi

# Update scripts with new IP
SCRIPT_DIR="$(dirname $0)"
for script in check_services.sh backup_stack.sh; do
    if [ -f "$SCRIPT_DIR/$script" ]; then
        # Update default IP in scripts
        sed -i "s/192\.168\.84\.108/$NEW_IP/g" "$SCRIPT_DIR/$script" 2>/dev/null || true
        echo "✓ Updated $script"
    fi
done

# Update info.txt
if [ -f "$SCRIPT_DIR/info.txt" ]; then
    sed -i "s/host: 192\.168\.84\.108/host: $NEW_IP/g" "$SCRIPT_DIR/info.txt" 2>/dev/null || true
    echo "✓ Updated info.txt"
fi

echo ""
echo "========================================="
echo "IP Update Complete!"
echo "========================================="
echo ""
echo "New IP: $NEW_IP"
echo ""
echo "Next steps:"
echo "  1. Test connection: ssh gibson-stack"
echo "  2. Check services: ./check_services.sh"
echo "  3. Update GitHub webhooks if configured"
echo ""
echo "If SSH still fails, ensure:"
echo "  - Remote machine is powered on"
echo "  - SSH service is running (systemctl status ssh)"
echo "  - Firewall allows port 22"
echo "  - New IP is correct"
