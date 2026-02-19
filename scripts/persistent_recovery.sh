#!/bin/bash
# 🦾 Gibson's Persistent Recovery Daemon
# Goal: Force-sync permanent SSH and verify Kibana Dash
# Idempotent & Robust

REMOTE_HOST="10.144.118.159"
REMOTE_PASS="Lamborghini"
LOG_DIR="/home/africool/.openclaw/workspace/projects/members/Gibson/logs"
STAB_LOG="$LOG_DIR/infrastructure_stabilization.log"
mkdir -p "$LOG_DIR"

# Cleanup on exit
trap "echo 'PERSISTENT RETRY STOPPED' >> $STAB_LOG; exit" SIGINT SIGTERM

echo "[$(date)] Persistent recovery daemon started." >> "$STAB_LOG"

while true; do
    # Check if we already have passwordless access
    if ssh -o BatchMode=yes -o ConnectTimeout=5 gibson-stack "uptime" &>/dev/null; then
        echo "[$(date)] ✅ Permanent SSH access confirmed. Monitoring..." >> "$STAB_LOG"
        
        # Verify and Fix Dashboard if needed
        KIBANA_STATUS=$(ssh gibson-stack "docker inspect -f '{{.State.Status}}' kibana" 2>/dev/null)
        if [ "$KIBANA_STATUS" != "running" ]; then
             echo "[$(date)] 🛠️ Restarting Kibana..." >> "$STAB_LOG"
             ssh gibson-stack "docker compose -f /opt/microservices-stack/docker-compose.yml up -d kibana" &>/dev/null
        fi
        
        sleep 300 # Sleep 5m if healthy
    else
        # Attempt sync using password
        echo "[$(date)] 🔄 Attempting SSH sync using password..." >> "$STAB_LOG"
        if nc -zv -w 2 "$REMOTE_HOST" 22 &>/dev/null; then
            sshpass -p "$REMOTE_PASS" ssh-copy-id -o StrictHostKeyChecking=no -o ConnectTimeout=10 gibson-stack &>> "$STAB_LOG"
        fi
        sleep 30 # Retry every 30s if flaky
    fi
done
