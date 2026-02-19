#!/bin/bash
# Gibson Stack Monitor - Memory & Resource Management
# Idempotent, colored output, logging

set -o pipefail

LOG_DIR="$HOME/.openclaw/workspace/projects/members/Gibson/logs"
LOG_FILE="$LOG_DIR/monitor_$(date +%Y-%m-%d).log"
MEMORY_THRESHOLD=80
ALERT_THRESHOLD=90

RED="\033[0;31m"
YELLOW="\033[1;33m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
NC="\033[0m"

log_msg() {
    local ts=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "$ts $*"
}

main() {
    mkdir -p "$LOG_DIR" 2>/dev/null || true
    
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE} Gibson Stack Resource Monitor${NC}"
    echo -e "${BLUE} $(date)${NC}"
    echo -e "${BLUE}============================================${NC}"
    
    # Memory
    mem_total=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    mem_avail=$(grep MemAvailable /proc/meminfo | awk '{print $2}')
    mem_used=$((mem_total - mem_avail))
    mem_pct=$((mem_used * 100 / mem_total))
    
    if [ "$mem_pct" -ge "$ALERT_THRESHOLD" ]; then
        log_msg "${RED}ERROR${NC}: Memory at ${mem_pct}% (ALERT >${ALERT_THRESHOLD}%)"
    elif [ "$mem_pct" -ge "$MEMORY_THRESHOLD" ]; then
        log_msg "${YELLOW}WARN${NC}: Memory at ${mem_pct}% (WARNING >${MEMORY_THRESHOLD}%)"
    else
        log_msg "${GREEN}OK${NC}: Memory at ${mem_pct}%"
    fi | tee -a "$LOG_FILE"
    
    # Disk
    disk_pct=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
    log_msg "Disk: ${disk_pct}%" | tee -a "$LOG_FILE"
    
    # Containers
    count=$(docker ps --format '{{.Names}}' | wc -l)
    log_msg "Containers running: $count" | tee -a "$LOG_FILE"
    
    # Top memory consumers
    echo -e "${BLUE}Top Memory Consumers:${NC}" | tee -a "$LOG_FILE"
    docker stats --no-stream --format '{{.Name}}: {{.MemUsage}}' 2>/dev/null | \
        awk -F'/' '{print $1}' | sort -t ':' -k2 -g -r | head -5 | \
        while read line; do echo -e "  → $line" | tee -a "$LOG_FILE"; done
    
    # Action if above threshold
    if [ "$mem_pct" -ge "$MEMORY_THRESHOLD" ]; then
        log_msg "${YELLOW}Memory above threshold - restarting non-critical services...${NC}" | tee -a "$LOG_FILE"
        for svc in kibana grafana; do
            if docker ps --format '{{.Names}}' | grep -q "^${svc}$"; then
                docker restart "$svc" 2>/dev/null && log_msg "Restarted $svc" | tee -a "$LOG_FILE" || true
            fi
        done
    fi
    
    echo -e "${GREEN}Done. Log: $LOG_FILE${NC}" | tee -a "$LOG_FILE"
}

main "$@"
