#!/bin/bash
# SSH Keepalive Script for Gibson's Remote Machine
# Maintains uninterrupted SSH connection by keeping the tunnel alive
# Run via cron every 4 hours

REMOTE_HOST="${REMOTE_HOST:-192.168.84.108}"
REMOTE_USER="${REMOTE_USER:-gibz}"
SSH_KEY_PATH="$HOME/.ssh/github_microservices"
SSH_CONFIG="$HOME/.ssh/config"
LOG_FILE="$HOME/.ssh/keepalive.log"

# Best practices configured:
# - ServerAliveInterval: 60 seconds (send keepalive to server)
# - ServerAliveCountMax: 3 (disconnect after 3 failed keepalives)
# - TCPKeepAlive: yes (TCP-level keepalives)
# - Compression: yes (faster over slow links)
# - Reconnect: automatic on failure

setup_keepalive() {
    echo "$(date): Setting up SSH keepalive configuration..."
    
    # Ensure .ssh directory exists
    mkdir -p "$HOME/.ssh"
    chmod 700 "$HOME/.ssh"
    
    # Create/update SSH config with keepalive settings
    cat > "$SSH_CONFIG" << 'EOF'
# SSH Keepalive Configuration for Gibson's Stack
# Best practices for maintaining reliable SSH connections:
# - ServerAliveInterval: Send keepalive every 60s to detect dead connections
# - ServerAliveCountMax: Allow 3 failures before disconnecting
# - TCPKeepAlive: Use TCP-level keepalives
# - Compression: Enable for better performance over slow links
# - Reconnect: Enable automatic reconnection

Host gibson-stack
    HostName 192.168.84.108
    User gibz
    IdentityFile ~/.ssh/github_microservices
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    
    # Keepalive settings (best practice)
    ServerAliveInterval 60
    ServerAliveCountMax 3
    TCPKeepAlive yes
    
    # Performance & reliability
    Compression yes
    ServerAliveInterval 60
    
    # Reconnection settings
    ConnectionAttempts 3
    ConnectTimeout 10

# Global SSH client settings for all connections
Host *
    # Enable keepalive globally
    ServerAliveInterval 60
    ServerAliveCountMax 3
    TCPKeepAlive yes
    Compression yes
    
    # Security best practices
    HashKnownHosts yes
    AddKeysToAgent yes
EOF

    chmod 600 "$SSH_CONFIG"
    echo "$(date): SSH config updated with keepalive settings" >> "$LOG_FILE"
}

test_connection() {
    echo "$(date): Testing SSH connection to $REMOTE_USER@$REMOTE_HOST..."
    
    if ssh -o ConnectTimeout=10 -o BatchMode=yes gibson-stack "echo 'Connection OK' && date" 2>/dev/null; then
        echo "$(date): ✓ SSH connection successful" >> "$LOG_FILE"
        return 0
    else
        echo "$(date): ✗ SSH connection failed - attempting reconnect..." >> "$LOG_FILE"
        
        # Try with explicit parameters
        if ssh -o ConnectTimeout=15 -o StrictHostKeyChecking=no \
            -i "$SSH_KEY_PATH"" \
            "$REMOTE_USER@$REMOTE_HOST" "echo 'Reconnect OK' && date" 2>/dev/null; then
            echo "$(date): ✓ Reconnection successful" >> "$LOG_FILE"
            return 0
        else
            echo "$(date): ✗ Reconnection failed" >> "$LOG_FILE"
            return 1
        fi
    fi
}

# Main execution
case "${1:-run}" in
    setup)
        setup_keepalive
        ;;
    test)
        test_connection
        ;;
    run|*)
        setup_keepalive
        test_connection
        ;;
esac
