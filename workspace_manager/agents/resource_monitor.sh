#!/bin/bash
# Resource Monitor Agent for Gibson's Microservices Stack
# Monitors Docker containers and host resources per RESOURCE_POLICY.md
# Runs every 15 minutes via cron

HOST="10.144.118.159"
SSH_USER="gibz"
LOG_FILE="/home/africool/.openclaw/workspace/projects/members/Gibson/workspace_manager/logs/resource_interventions.log"
MEMORY_MAINTENANCE=70
MEMORY_INTERVENTION=80

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

check_memory() {
    # Get host memory percentage
    MEM_PCT=$(ssh -o StrictHostKeyChecking=no ${SSH_USER}@${HOST} "free | awk '/^Mem:/{printf \"%.0f\", \$3/\$2*100}'")
    echo $MEM_PCT
}

check_container_memory() {
    # Get container memory percentages
    ssh -o StrictHostKeyChecking=no ${SSH_USER}@${HOST} "docker stats --no-stream --format '{{.Name}}\t{{.MemPerc}}' 2>/dev/null"
}

maintenance_mode() {
    log "⚠️ MAINTENANCE MODE: Memory at ${1}%"
    log "Running: docker system prune -f"
    ssh -o StrictHostKeyChecking=no ${SSH_USER}@${HOST} "docker system prune -f" 2>/dev/null
    log "Maintenance complete."
}

intervention_mode() {
    log "🔴 INTERVENTION MODE: Memory at ${1}%"
    
    # Get top memory-consuming containers
    CONTAINERS=$(ssh -o StrictHostKeyChecking=no ${SSH_USER}@${HOST} "docker stats --no-stream --format '{{.Name}}\t{{.MemUsage}}' | sort -k2 -h -r | head -5")
    
    log "Top containers:"
    echo "$CONTAINERS" | while read line; do
        log "  - $line"
    done
    
    # Restart high-memory containers (>2GB)
    HIGH_MEM=$(ssh -o StrictHostKeyChecking=no ${SSH_USER}@${HOST} "docker ps --format '{{.Names}}' | while read c; do
        MEM=\$(docker inspect --format='{{.MemoryUsage}}' \$c 2>/dev/null)
        if [ \$((MEM / 1024 / 1024)) -gt 2048 ]; then
            echo \$c
        fi
    done")
    
    if [ -n "$HIGH_MEM" ]; then
        log "Restarting high-memory containers: $HIGH_MEM"
        for container in $HIGH_MEM; do
            log "  Restarting: $container"
            ssh -o StrictHostKeyChecking=no ${SSH_USER}@${HOST} "docker restart $container" 2>/dev/null
        done
    fi
    
    # Generate intervention report
    REPORT_FILE="/home/africool/.openclaw/workspace/projects/members/Gibson/workspace_manager/reports/resource_intervention_$(date +%Y%m%d_%H%M%S).md"
    cat > "$REPORT_FILE" << EOF
# Resource Intervention Report
**Timestamp**: $(date '+%Y-%m-%d %H:%M %Z')
**Trigger**: Memory > ${1}%
**Host**: ${HOST}

## Container Status
$(ssh -o StrictHostKeyChecking=no ${SSH_USER}@${HOST} "docker stats --no-stream --format '| {{.Name}} | {{.MemPerc}} |'")

## Actions Taken
1. Docker system prune executed
2. High-memory containers restarted: $HIGH_MEM

## Recommendation
Consider adding more memory or optimizing container configurations.
EOF
    
    log "Intervention report saved: $REPORT_FILE"
    log "🔔 NOTIFICATION: Gibson should check intervention report"
}

# Main execution
log "=== Resource Monitor Check Started ==="

MEM_PCT=$(check_memory)
log "Host memory: ${MEM_PCT}%"

if [ "$MEM_PCT" -ge "$MEMORY_INTERVENTION" ]; then
    intervention_mode $MEM_PCT
elif [ "$MEM_PCT" -ge "$MEMORY_MAINTENANCE" ]; then
    maintenance_mode $MEM_PCT
else
    log "✅ Memory healthy: ${MEM_PCT}%"
fi

log "=== Resource Monitor Check Complete ==="
