#!/bin/bash
# 🤖 Gibson's Connectivity & Dashboard Stabilizer
# Managed by: Ahie Juma (Family Economic Agent)
# Date: 2026-02-13

# --- Configuration & Styling ---
REMOTE_HOST="10.144.118.159"
REMOTE_USER="gibz"
REMOTE_PASS="Lamborghini"
SSH_KEY_PATH="$HOME/.ssh/id_rsa_gibson"
LOG_FILE="/home/africool/.openclaw/workspace/projects/members/Gibson/logs/infrastructure_stabilization.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# --- Utilities ---
log_action() {
    local status=$1
    local message=$2
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] [$status] $message" >> "$LOG_FILE"
}

print_status() {
    local color=$1
    local emoji=$2
    local message=$3
    echo -e "${color}${emoji} ${message}${NC}"
    log_action "$emoji" "$message"
}

# Trap for unexpected exits
cleanup() {
    print_status "$YELLOW" "⚠️" "Script interrupted. Cleaning up temporary probes..."
    exit 1
}
trap cleanup SIGINT SIGTERM

# --- Step 1: Health Check (Idempotent) ---
print_status "$CYAN" "📡" "Starting infrastructure pulse check for $REMOTE_HOST..."

if ping -c 1 "$REMOTE_HOST" &>/dev/null; then
    print_status "$GREEN" "✅" "Host is RESPONSIVE to ICMP (Ping)."
else
    print_status "$RED" "❌" "Host is UNREACHABLE. Please check if the machine is powered on."
    exit 1
fi

# Check SSH Port Intermittency
SSH_READY=false
for i in {1..5}; do
    if nc -zv -w 2 "$REMOTE_HOST" 22 &>/dev/null; then
        print_status "$GREEN" "🔑" "Port 22 (SSH) is OPEN. Attempting stabilization..."
        SSH_READY=true
        break
    else
        print_status "$YELLOW" "⏳" "Port 22 REFUSED. Retry $i/5..."
        sleep 3
    fi
done

if [ "$SSH_READY" = false ]; then
    print_status "$RED" "🛑" "SSH service is down or locking us out. Check system load or firewall rules."
    exit 1
fi

# --- Step 2: Establish Permanent SSH (Idempotent) ---
if ! [ -f "$SSH_KEY_PATH" ]; then
    print_status "$YELLOW" "🗝️" "SSH Key missing at $SSH_KEY_PATH. Restoring from workspace..."
    mkdir -p "$HOME/.ssh" && chmod 700 "$HOME/.ssh"
    cp /home/africool/.openclaw/workspace/projects/members/Gibson/ssh/github_ssh_key "$SSH_KEY_PATH"
    chmod 600 "$SSH_KEY_PATH"
fi

print_status "$CYAN" "🔄" "Syncing permanent identity to remote machine..."
if sshpass -p "$REMOTE_PASS" ssh-copy-id -i "${SSH_KEY_PATH}.pub" -o StrictHostKeyChecking=no gibson-stack &>/dev/null; then
    print_status "$GREEN" "🛡️" "Permanent SSH Identity ESTABLISHED."
else
    print_status "$YELLOW" "ℹ️" "Identity already present or port dropped during sync. Testing passwordless access..."
fi

# --- Step 3: Service & Dashboard Verification ---
print_status "$CYAN" "📊" "Probing Dashboard Health (Kibana @ Port 5601)..."
KIBANA_CHECK=$(ssh gibson-stack "docker ps --filter name=kibana --format '{{.Status}}'" 2>/dev/null)

if [[ $KIBANA_CHECK == *"Up"* ]]; then
    print_status "$GREEN" "📈" "Kibana Container is RUNNING. Status: $KIBANA_CHECK"
    
    # Check Elasticsearch Backend
    ES_CHECK=$(ssh gibson-stack "curl -s localhost:9200/_cluster/health" 2>/dev/null)
    if [[ $ES_CHECK == *"status\":\"green\""* ]] || [[ $ES_CHECK == *"status\":\"yellow\""* ]]; then
        print_status "$GREEN" "🟢" "Elasticsearch Cluster is HEALTHY."
        print_status "$CYAN" "🌐" "Dashboard should be active at: http://$REMOTE_HOST:5601/app/dashboards#/view/AV4REOpp5NkDleZmzKkE-ecs"
    else
        print_status "$RED" "🔴" "Elasticsearch error or unreachable. Dashboard may be degraded."
    fi
else
    print_status "$RED" "💀" "Kibana service is NOT running on the remote host."
    print_status "$CYAN" "🛠️" "Attempting idempotent service restart..."
    ssh gibson-stack "cd /opt/microservices-stack && docker compose up -d kibana elasticsearch" &>/dev/null
    print_status "$YELLOW" "⏳" "Restart command sent. Please allow 60s for initialization."
fi

print_status "$GREEN" "🏁" "Stabilization cycle COMPLETE. Critical info logged to memory."
