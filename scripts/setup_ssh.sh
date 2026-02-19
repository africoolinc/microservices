#!/bin/bash
# SSH Configuration and Setup for Gibson's Remote Machine
# Sets up passwordless SSH access

set -e

REMOTE_HOST="${1:-192.168.84.108}"
REMOTE_USER="${2:-gibz}"
REMOTE_PASS="${3:-Lamborghini}"
SSH_KEY_PATH="$HOME/.ssh/github_microservices"

echo "========================================="
echo "SSH Setup for Gibson's Remote Machine"
echo "========================================="
echo ""

# Step 1: Check if sshpass is installed
if ! command -v sshpass &> /dev/null; then
    echo "Installing sshpass..."
    sudo apt-get update && sudo apt-get install -y sshpass
fi

# Step 2: Ensure SSH key exists locally
if [ ! -f "$SSH_KEY_PATH" ]; then
    echo "Creating SSH key pair..."
    mkdir -p ~/.ssh
    ssh-keygen -t ed25519 -C "gibson-microservices@juma.family" -f "$SSH_KEY_PATH" -N ""
    echo "✓ SSH key created at $SSH_KEY_PATH"
else
    echo "✓ SSH key already exists at $SSH_KEY_PATH"
fi

# Step 3: Copy public key to remote
echo ""
echo "Copying SSH key to remote machine..."
sshpass -p "$REMOTE_PASS" ssh-copy-id -o StrictHostKeyChecking=no -i "$SSH_KEY_PATH.pub" "$REMOTE_USER@$REMOTE_HOST" 2>/dev/null || {
    echo "ssh-copy-id failed, trying manual copy..."
    # Manual approach
    PUB_KEY=$(cat "$SSH_KEY_PATH.pub")
    sshpass -p "$REMOTE_PASS" ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "mkdir -p ~/.ssh && echo '$PUB_KEY' >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"
}
echo "✓ SSH key copied to remote"

# Step 4: Create SSH config entry
echo ""
echo "Creating SSH config entry..."
mkdir -p ~/.ssh
if ! grep -q "Host gibson-stack" ~/.ssh/config 2>/dev/null; then
    cat >> ~/.ssh/config << EOF

Host gibson-stack
    HostName $REMOTE_HOST
    User $REMOTE_USER
    IdentityFile $SSH_KEY_PATH
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
EOF
    echo "✓ SSH config added (use: ssh gibson-stack)"
else
    echo "✓ SSH config already exists"
fi

# Step 5: Test connection
echo ""
echo "Testing SSH connection..."
if ssh -o ConnectTimeout=5 gibson-stack "echo 'SSH connection successful'" 2>/dev/null; then
    echo "✓ SSH connection working!"
    echo ""
    echo "========================================="
    echo "SSH Setup Complete!"
    echo "========================================="
    echo ""
    echo "You can now connect with:"
    echo "  ssh gibson-stack"
    echo ""
    echo "Or use in scripts:"
    echo '  ssh gibson-stack "docker ps"'
    echo ""
else
    echo "✗ SSH connection failed"
    echo ""
    echo "Possible issues:"
    echo "  - Remote host is offline"
    echo "  - IP address has changed (check info.txt)"
    echo "  - SSH service not running on remote"
    echo "  - Firewall blocking port 22"
    echo ""
    echo "Current settings:"
    echo "  Host: $REMOTE_HOST"
    echo "  User: $REMOTE_USER"
    echo "  Key:  $SSH_KEY_PATH"
    exit 1
fi
