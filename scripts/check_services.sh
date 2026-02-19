#!/bin/bash
# Service Status Monitor for Gibson's Microservices Stack
# Checks all services and reports health status

set -e

REMOTE_HOST="${1:-10.144.118.159}"
REMOTE_USER="${2:-gibz}"
REMOTE_PASS="${3:-Lamborghini}"
USE_SSH=true

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Service definitions with health check endpoints
# Format: "Service Name|Port|Health Endpoint|Health Check Type"
SERVICES=(
    "Kong Gateway|8000|/status|http"
    "Kong Admin|8001|/status|http"
    "Consul|8500|/v1/status/leader|http"
    "Service A|5001|/health|http"
    "Service B|5002|/health|http"
    "Service C|5003|/health|http"
    "Keycloak|8080|/health/ready|http"
    "PostgreSQL (app)|5432|pg_isready|command"
    "PostgreSQL (kong)|5433|pg_isready|command"
    "PostgreSQL (keycloak)|5434|pg_isready|command"
    "Redis|6379|redis-cli ping|command"
    "Zookeeper|2181|ruok|tcp"
    "Kafka|9092|kafka-topics|command"
    "Prometheus|9090|/-/healthy|http"
    "Grafana|3000|/api/health|http"
    "Elasticsearch|9200|/_cluster/health|http"
    "Kibana|5601|/api/status|http"
    "Logstash|9600|/_node/stats|http"
    "Portainer|9443|/api/status|http"
)

HEALTHY_COUNT=0
UNHEALTHY_COUNT=0
TOTAL_COUNT=${#SERVICES[@]}

echo "========================================="
echo "Microservices Stack Health Monitor"
echo "Target: $REMOTE_HOST"
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================="
echo ""

# Function to check if running locally or remotely
check_local_or_remote() {
    if [ -f /opt/microservices-stack/docker-compose.yml ]; then
        echo "local"
    else
        echo "remote"
    fi
}

# Function to check HTTP endpoint
check_http() {
    local host=$1
    local port=$2
    local endpoint=$3
    
    if command -v curl &> /dev/null; then
        if curl -sf "http://$host:$port$endpoint" > /dev/null 2>&1; then
            echo "healthy"
        else
            echo "unhealthy"
        fi
    else
        # Fallback using wget or bash
        timeout 2 bash -c "exec 3<>/dev/tcp/$host/$port && echo -e 'GET $endpoint HTTP/1.1\r\nHost: $host\r\nConnection: close\r\n\r\n' >&3 && cat <&3" > /dev/null 2>&1 && echo "healthy" || echo "unhealthy"
    fi
}

# Function to check TCP port
check_tcp() {
    local host=$1
    local port=$2
    
    timeout 2 bash -c "exec 3<>/dev/tcp/$host/$port" 2>/dev/null && echo "healthy" || echo "unhealthy"
}

# Function to check command (for docker exec)
check_command() {
    local container=$1
    local cmd=$2
    
    if docker ps --format "{{.Names}}" | grep -q "$container"; then
        if docker exec "$container" sh -c "$cmd" > /dev/null 2>&1; then
            echo "healthy"
        else
            echo "unhealthy"
        fi
    else
        echo "not-running"
    fi
}

# Main check loop
LOCATION=$(check_local_or_remote)

if [ "$LOCATION" == "local" ]; then
    echo -e "${BLUE}Running checks locally on $REMOTE_HOST...${NC}"
    echo ""
    
    # Check Docker is running
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}ERROR: Docker is not running or not accessible${NC}"
        exit 1
    fi
    
    # Get running containers
    RUNNING_CONTAINERS=$(docker ps --format "{{.Names}}")
    
    for service_def in "${SERVICES[@]}"; do
        IFS='|' read -r name port endpoint check_type <<< "$service_def"
        
        # Map service names to container names
        container_name=""
        case "$name" in
            "Kong Gateway"|"Kong Admin") container_name="kong" ;;
            "Consul") container_name="consul" ;;
            "Service A") container_name="service-a" ;;
            "Service B") container_name="service-b" ;;
            "Service C") container_name="service-c" ;;
            "Keycloak") container_name="keycloak" ;;
            "PostgreSQL (app)") container_name="app-db" ;;
            "PostgreSQL (kong)") container_name="kong-db" ;;
            "PostgreSQL (keycloak)") container_name="keycloak-db" ;;
            "Redis") container_name="redis" ;;
            "Zookeeper") container_name="zookeeper" ;;
            "Kafka") container_name="kafka" ;;
            "Prometheus") container_name="prometheus" ;;
            "Grafana") container_name="grafana" ;;
            "Elasticsearch") container_name="elasticsearch" ;;
            "Kibana") container_name="kibana" ;;
            "Logstash") container_name="logstash" ;;
            "Portainer") container_name="portainer" ;;
        esac
        
        # Check if container is running
        if echo "$RUNNING_CONTAINERS" | grep -q "^${container_name}$"; then
            container_status=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "unknown")
            
            if [ "$container_status" == "healthy" ] || [ "$container_status" == "unknown" ]; then
                status="healthy"
                ((HEALTHY_COUNT++))
                echo -e "${GREEN}✓${NC} $name (port $port) - ${GREEN}HEALTHY${NC}"
            else
                status="unhealthy"
                ((UNHEALTHY_COUNT++))
                echo -e "${RED}✗${NC} $name (port $port) - ${RED}UNHEALTHY${NC} (status: $container_status)"
            fi
        else
            ((UNHEALTHY_COUNT++))
            echo -e "${RED}✗${NC} $name (port $port) - ${RED}NOT RUNNING${NC}"
        fi
    done
else
    echo -e "${BLUE}Running checks remotely via SSH...${NC}"
    echo ""
    
    # Check if sshpass is available
    if ! command -v sshpass &> /dev/null; then
        echo -e "${YELLOW}WARNING: sshpass not installed. Installing...${NC}"
        sudo apt-get update && sudo apt-get install -y sshpass 2>/dev/null || true
    fi
    
    # SSH to remote and check services
    sshpass -p "$REMOTE_PASS" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$REMOTE_USER@$REMOTE_HOST" '
        # Check Docker
        if ! docker info > /dev/null 2>&1; then
            echo "DOCKER_NOT_RUNNING"
            exit 1
        fi
        
        RUNNING=$(docker ps --format "{{.Names}} {{.Status}} {{.Ports}}")
        echo "$RUNNING"
    ' 2>/dev/null || {
        echo -e "${RED}ERROR: Could not connect to remote host${NC}"
        echo "Host: $REMOTE_HOST"
        echo "User: $REMOTE_USER"
        echo ""
        echo "Possible issues:"
        echo "  - Host is offline"
        echo "  - IP address changed (check info.txt)"
        echo "  - SSH not enabled on remote"
        echo "  - Network connectivity issues"
        exit 1
    }
fi

# Summary
echo ""
echo "========================================="
echo "Health Check Summary"
echo "========================================="
echo -e "${GREEN}Healthy:${NC}    $HEALTHY_COUNT / $TOTAL_COUNT"
echo -e "${RED}Unhealthy:${NC}  $UNHEALTHY_COUNT / $TOTAL_COUNT"
echo ""

if [ $UNHEALTHY_COUNT -eq 0 ]; then
    echo -e "${GREEN}✓ All services are running optimally!${NC}"
    exit 0
else
    echo -e "${YELLOW}! Some services need attention${NC}"
    echo ""
    echo "To restart services:"
    echo "  cd /opt/microservices-stack"
    echo "  docker-compose down && docker-compose up -d"
    exit 1
fi
