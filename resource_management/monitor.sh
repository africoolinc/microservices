#!/bin/bash
# Gibson Stack Resource Monitor
# Thresholds: WARNING 70%, CRITICAL 80%
# Usage: Run via cron or manually on remote machine

LOG_DIR="$HOME/microservices/resource_management/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/status_$(date +%Y-%m-%d).log"
ALERT_LOG="$LOG_DIR/alerts_$(date +%Y-%m-%d).log"

# Thresholds
MEM_WARNING=70
MEM_CRITICAL=80
DISK_WARNING=80
DISK_CRITICAL=90
CPU_WARNING=60
CPU_CRITICAL=80

log_msg() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

alert_msg() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ALERT] $1" | tee -a "$ALERT_LOG"
}

# Get current metrics
MEM_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
DISK_USAGE=$(df -h / | tail -1 | awk '{print int($5)}')
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print int($2)}')

log_msg "=== Resource Check ==="
log_msg "Memory: ${MEM_USAGE}% | Disk: ${DISK_USAGE}% | CPU: ${CPU_USAGE}%"

# Memory Checks
if [ "$MEM_USAGE" -ge "$MEM_CRITICAL" ]; then
    alert_msg "CRITICAL: Memory at ${MEM_USAGE}% - Attempting auto-remediation"
    # Restart non-essential containers
    docker restart kibana grafana 2>/dev/null
    log_msg "Action: Restarted kibana, grafana"
elif [ "$MEM_USAGE" -ge "$MEM_WARNING" ]; then
    log_msg "WARNING: Memory at ${MEM_USAGE}% - Monitoring closely"
fi

# Disk Checks  
if [ "$DISK_USAGE" -ge "$DISK_CRITICAL" ]; then
    alert_msg "CRITICAL: Disk at ${DISK_USAGE}% - Manual intervention required"
elif [ "$DISK_USAGE" -ge "$DISK_WARNING" ]; then
    log_msg "WARNING: Disk at ${DISK_USAGE}% - Consider cleanup"
fi

# CPU Checks
if [ "$CPU_USAGE" -ge "$CPU_CRITICAL" ]; then
    alert_msg "CRITICAL: CPU at ${CPU_USAGE}% - High load detected"
elif [ "$CPU_USAGE" -ge "$CPU_WARNING" ]; then
    log_msg "WARNING: CPU at ${CPU_USAGE}% - Elevated load"
fi

# Container Status
CONTAINER_COUNT=$(docker ps --format "{{.Names}}" | wc -l)
log_msg "Running Containers: $CONTAINER_COUNT"

if [ "$CONTAINER_COUNT" -lt 15 ]; then
    alert_msg "WARNING: Low container count ($CONTAINER_COUNT) - possible failure"
fi

log_msg "=== Check Complete ==="
echo "" >> "$LOG_FILE"
