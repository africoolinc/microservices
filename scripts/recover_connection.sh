#!/bin/bash
# Gibson's Microservices Stack - IP Recovery Script
# Use this script when Gibson provides the new IP address for his machine

set -e

echo "========================================="
echo "Gibson's Microservices Stack - IP Recovery"
echo "========================================="
echo ""

if [ -z "$1" ]; then
    echo "ERROR: No IP address provided"
    echo ""
    echo "Usage: $0 <new_ip_address>"
    echo ""
    echo "Example: $0 192.168.100.108"
    echo ""
    echo "This script will:"
    echo "  1. Update the remote_details.txt file"
    echo "  2. Update SSH configuration"
    echo "  3. Test the connection"
    echo "  4. Run a health check if successful"
    exit 1
fi

NEW_IP="$1"
echo "Attempting to update remote IP to: $NEW_IP"
echo ""

# Validate IP format
if ! [[ $NEW_IP =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
    echo "ERROR: Invalid IP address format"
    exit 1
fi

echo "[1/4] Updating remote_details.txt..."
sed -i "s/REMOTE_HOST=.*/REMOTE_HOST=$NEW_IP/" projects/members/Gibson/config/remote_details.txt
sed -i "s/STATUS=.*/STATUS=updating/" projects/members/Gibson/config/remote_details.txt
echo "✓ Updated remote_details.txt"

echo ""
echo "[2/4] Updating SSH configuration..."
mkdir -p ~/.ssh

# Remove old gibson-stack entry if it exists
if [ -f ~/.ssh/config ]; then
    awk '!found && /^Host gibson-stack$/ { found=1; skip=1; next } skip && /^Host / { skip=0; found=0 } !skip' ~/.ssh/config > ~/.ssh/config.tmp
    mv ~/.ssh/config.tmp ~/.ssh/config
fi

# Add new entry
cat >> ~/.ssh/config << EOF

Host gibson-stack
    HostName $NEW_IP
    User gibz
    IdentityFile ~/.ssh/github_microservices
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
EOF
echo "✓ SSH configuration updated"

echo ""
echo "[3/4] Testing SSH connection..."
if ssh -o ConnectTimeout=10 gibson-stack "echo 'Connected to Gibson'\$(hostname)\$(uptime)" 2>/dev/null; then
    echo "✓ SSH connection successful!"
    echo ""
    echo "[4/4] Running quick service check..."
    ssh gibson-stack "docker ps -q | wc -l" > /tmp/container_count
    CONTAINER_COUNT=$(cat /tmp/container_count)
    echo "✓ Found $CONTAINER_COUNT running containers"
    
    # Update status to connected
    sed -i "s/STATUS=.*/STATUS=connected/" projects/members/Gibson/config/remote_details.txt
    echo "✓ Status updated to connected"
    
    echo ""
    echo "========================================="
    echo "SUCCESS: Gibson's machine is now reachable!"
    echo "========================================="
    echo ""
    echo "Next steps:"
    echo "1. Run full health check: ./scripts/check_services.sh"
    echo "2. Verify all services are operational"
    echo "3. Push pending GitHub commits if needed"
    echo "4. Resume normal operations"
    echo ""
else
    echo "✗ SSH connection failed"
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Verify the IP address is correct"
    echo "2. Check if Gibson's machine is powered on"
    echo "3. Confirm SSH service is running on the remote machine"
    echo "4. Check network connectivity between machines"
    echo ""
    # Update status to disconnected
    sed -i "s/STATUS=.*/STATUS=disconnected/" projects/members/Gibson/config/remote_details.txt
    exit 1
fi

echo "========================================="
echo "IP Recovery Complete!"
echo "========================================="