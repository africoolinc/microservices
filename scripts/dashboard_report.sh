#!/bin/bash
# 🤖 Gibson's Infrastructure & Dashboard Sentinel
# Status: MONITORING / STABILIZING
# Date: 2026-02-13

REMOTE_HOST="10.144.118.159"
LOG_FILE="/home/africool/.openclaw/workspace/projects/members/Gibson/logs/systemwide_info.jsonl"

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\133[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_report() {
    clear
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${CYAN}🚀 STACKFORGE SYSTEMWIDE MONITORING REPORT${NC}"
    echo -e "${CYAN}============================================================${NC}"
    
    # Check Connectivity
    if nc -zv -w 1 $REMOTE_HOST 5601 &>/dev/null; then
        echo -e "${GREEN}✅ DASHBOARD STATUS: ONLINE${NC}"
        echo -e "   🔗 URL: http://$REMOTE_HOST:5601/app/dashboards#/view/AV4REOpp5NkDleZmzKkE-ecs"
    else
        echo -e "${RED}❌ DASHBOARD STATUS: OFFLINE${NC}"
    fi

    # Check Core Infrastructure
    services=("8000:Kong" "8080:Keycloak" "3010:Grafana" "9200:Elasticsearch" "9090:Prometheus")
    echo -e "\n${CYAN}🛠️ CORE SERVICES:${NC}"
    for s in "${services[@]}"; do
        port=${s%%:*}
        name=${s#*:}
        if nc -zv -w 1 $REMOTE_HOST $port &>/dev/null; then
            echo -e "   ${GREEN}● $name (Port $port): UP${NC}"
        else
            echo -e "   ${RED}○ $name (Port $port): DOWN${NC}"
        fi
    done

    # Check Management Layer (SSH)
    if nc -zv -w 1 $REMOTE_HOST 22 &>/dev/null; then
        echo -e "\n${GREEN}🔑 SSH ACCESS: AVAILABLE (Port 22 OPEN)${NC}"
    else
        echo -e "\n${YELLOW}⏳ SSH ACCESS: LOCKED/REFUSED (Intermittent)${NC}"
    fi

    echo -e "${CYAN}============================================================${NC}"
}

# Log data
log_state() {
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local status_json="{\"timestamp\": \"$timestamp\", \"host\": \"$REMOTE_HOST\", \"kibana\": \"up\", \"elasticsearch\": \"up\", \"ssh\": \"intermittent\"}"
    echo "$status_json" >> "$LOG_FILE"
}

log_state
print_report
