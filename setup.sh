#!/bin/bash

# Optimized script to install Docker (with Compose plugin), Portainer, and deploy the microservices architecture stack.
# Designed for Debian-based systems (e.g., Ubuntu). Run with sudo if not root.
# Current date: September 01, 2025. Uses latest versions: Docker Compose v2.39.2, Portainer CE 2.33.1.

set -e  # Exit on error

# Check if running on a Debian-based system
if ! command -v apt-get &> /dev/null; then
    echo "Error: This script is designed for Debian-based systems (e.g., Ubuntu)."
    exit 1
fi

# Function to check if sudo is needed
use_sudo() {
    if [ "$(id -u)" -ne 0 ]; then
        sudo "$@"
    else
        "$@"
    fi
}

# Install prerequisites if needed
echo "Installing prerequisites..."
use_sudo apt-get update -y
use_sudo apt-get install -y ca-certificates curl

# Install Docker using official convenience script (includes Compose plugin)
if ! command -v docker &> /dev/null; then
    echo "Installing Docker via official script..."
    curl -fsSL https://get.docker.com | use_sudo sh
    echo "Docker installed: $(docker --version)"
    echo "Docker Compose installed: $(docker compose version)"
else
    echo "Docker is already installed: $(docker --version)"
    if ! docker compose version &> /dev/null; then
        echo "Error: Docker Compose plugin missing. Reinstalling Docker..."
        curl -fsSL https://get.docker.com | use_sudo sh
    else
        echo "Docker Compose is already installed: $(docker compose version)"
    fi
fi

# Add current user to docker group if not already added
if ! groups "${USER}" | grep -q docker; then
    use_sudo usermod -aG docker "${USER}"
    echo "Added ${USER} to docker group. Please log out and log back in for changes to take effect."
    # Note: Changes won't apply in this session; user must relog. Deployment below may require sudo if not relogged.
fi

# Start and enable Docker service
use_sudo systemctl start docker
use_sudo systemctl enable docker

# Install Portainer if not already running
if ! docker ps --format '{{.Names}}' | grep -q '^portainer$'; then
    echo "Installing Portainer CE 2.33.1..."
    docker volume create portainer_data || true
    docker run -d \
        -p 8000:8000 \
        -p 9443:9443 \
        --name portainer \
        --restart=unless-stopped \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v portainer_data:/data \
        portainer/portainer-ce:2.33.1
    # Wait for Portainer to be healthy
    for i in {1..30}; do
        if curl -k -s https://localhost:9443/api/status &> /dev/null; then
            echo "Portainer is up."
            break
        fi
        sleep 2
    done
else
    echo "Portainer is already running."
fi

# Deploy the microservices architecture stack
echo "Deploying microservices stack..."
PROJECT_DIR="microservices-stack"
mkdir -p "${PROJECT_DIR}"
cd "${PROJECT_DIR}"

# Create app.py for Flask services
cat << EOF > app.py
from flask import Flask
import consul
import os

app = Flask(__name__)
service_id = os.environ.get('SERVICE_ID', 'unknown')
c = consul.Consul(host='consul', port=8500)

# Register service with Consul
c.agent.service.register(
    name=service_id,
    service_id=service_id,
    address=service_id,
    port=5000,
    check=consul.Check.http(url='http://localhost:5000/health', interval='10s')
)

@app.route('/')
def hello():
    return f'Hello from {service_id}'

@app.route('/health')
def health():
    return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
EOF

# Create Dockerfile for services
cat << EOF > Dockerfile.service
FROM python:3.12-slim
RUN pip install --no-cache-dir flask python-consul
COPY app.py /app.py
CMD ["python", "/app.py"]
EOF

# Create configs directory and files
mkdir -p configs
cat << EOF > configs/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  - job_name: 'consul'
    static_configs:
      - targets: ['consul:8500']
  - job_name: 'services'
    static_configs:
      - targets: ['service-a:5000', 'service-b:5000', 'service-c:5000']  # Add /metrics endpoint in real services
EOF

cat << EOF > configs/logstash.conf
input { beats { port => 5044 } }
output { elasticsearch { hosts => ["elasticsearch:9200"] } }
EOF

# Create docker-compose.yml (updated to version 3.9)
cat << EOF > docker-compose.yml
version: '3.9'

services:
  consul:
    image: hashicorp/consul:1.17
    container_name: consul
    command: agent -server -bootstrap-expect=1 -ui -client=0.0.0.0
    ports:
      - '8500:8500'
      - '8600:8600/udp'
    networks:
      - backend
    healthcheck:
      test: ["CMD", "consul", "info"]
      interval: 10s
      retries: 3

  kong-db:
    image: postgres:16
    container_name: kong-db
    environment:
      POSTGRES_USER: kong
      POSTGRES_PASSWORD: kongpass
      POSTGRES_DB: kong
    volumes:
      - kong-db-data:/var/lib/postgresql/data
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U kong"]
      interval: 10s
      retries: 5

  kong:
    image: kong:3.7
    container_name: kong
    environment:
      KONG_DATABASE: postgres
      KONG_PG_HOST: kong-db
      KONG_PG_USER: kong
      KONG_PG_PASSWORD: kongpass
      KONG_PROXY_ACCESS_LOG: /dev/stdout
      KONG_ADMIN_ACCESS_LOG: /dev/stdout
      KONG_PROXY_ERROR_LOG: /dev/stderr
      KONG_ADMIN_ERROR_LOG: /dev/stderr
      KONG_ADMIN_LISTEN: '0.0.0.0:8001'
    depends_on:
      kong-db:
        condition: service_healthy
    ports:
      - '8000:8000'  # Proxy
      - '8001:8001'  # Admin
    networks:
      - backend
    command: sh -c "kong migrations bootstrap && kong start"
    healthcheck:
      test: ["CMD", "kong", "health"]
      interval: 10s
      retries: 5

  keycloak-db:
    image: postgres:16
    container_name: keycloak-db
    environment:
      POSTGRES_USER: keycloak
      POSTGRES_PASSWORD: keycloakpass
      POSTGRES_DB: keycloak
    volumes:
      - keycloak-db-data:/var/lib/postgresql/data
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U keycloak"]
      interval: 10s
      retries: 5

  keycloak:
    image: quay.io/keycloak/keycloak:25.0
    container_name: keycloak
    environment:
      KC_DB: postgres
      KC_DB_URL_HOST: keycloak-db
      KC_DB_URL_DATABASE: keycloak
      KC_DB_USERNAME: keycloak
      KC_DB_PASSWORD: keycloakpass
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: adminpass
      KC_HEALTH_ENABLED: true
    command: start-dev
    depends_on:
      keycloak-db:
        condition: service_healthy
    ports:
      - '8080:8080'
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8080/health/ready"]
      interval: 30s
      retries: 5

  app-db:
    image: postgres:16
    container_name: app-db
    environment:
      POSTGRES_USER: appuser
      POSTGRES_PASSWORD: apppass
      POSTGRES_DB: appdb
    volumes:
      - app-db-data:/var/lib/postgresql/data
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U appuser"]
      interval: 10s
      retries: 5

  redis:
    image: redis:7
    container_name: redis
    ports:
      - '6379:6379'
    networks:
      - backend
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      retries: 3

  zookeeper:
    image: confluentinc/cp-zookeeper:7.6.1
    container_name: zookeeper
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    ports:
      - '2181:2181'
    networks:
      - backend

  kafka:
    image: confluentinc/cp-kafka:7.6.1
    container_name: kafka
    depends_on:
      - zookeeper
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092,PLAINTEXT_HOST://localhost:29092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    ports:
      - '9092:9092'
      - '29092:29092'
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "kafka-topics.sh --bootstrap-server localhost:9092 --list"]
      interval: 30s
      retries: 5

  prometheus:
    image: prom/prometheus:v2.53.0
    container_name: prometheus
    volumes:
      - ./configs/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - '9090:9090'
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "wget --quiet --tries=1 --spider http://localhost:9090/-/healthy || exit 1"]
      interval: 10s
      retries: 3

  grafana:
    image: grafana/grafana:11.1.0
    container_name: grafana
    depends_on:
      - prometheus
    environment:
      GF_SECURITY_ADMIN_USER: admin
      GF_SECURITY_ADMIN_PASSWORD: adminpass
    ports:
      - '3000:3000'
    volumes:
      - grafana-data:/var/lib/grafana
    networks:
      - backend

  elasticsearch:
    image: elasticsearch:8.14.1
    container_name: elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - ES_JAVA_OPTS=-Xms512m -Xmx512m
    volumes:
      - es-data:/usr/share/elasticsearch/data
    ports:
      - '9200:9200'
      - '9300:9300'
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9200/_cat/health?h=status"]
      interval: 30s
      retries: 5

  logstash:
    image: logstash:8.14.1
    container_name: logstash
    depends_on:
      - elasticsearch
    volumes:
      - ./configs/logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    environment:
      LS_JAVA_OPTS: -Xmx256m -Xms256m
    ports:
      - '5001:5000'  # Example input port
      - '9600:9600'
    networks:
      - backend

  kibana:
    image: kibana:8.14.1
    container_name: kibana
    depends_on:
      elasticsearch:
        condition: service_healthy
    environment:
      ELASTICSEARCH_URL: http://elasticsearch:9200
      ELASTICSEARCH_HOSTS: '["http://elasticsearch:9200"]'
    ports:
      - '5601:5601'
    networks:
      - backend

  service-a:
    build:
      context: .
      dockerfile: Dockerfile.service
    container_name: service-a
    environment:
      SERVICE_ID: service-a
    depends_on:
      consul:
        condition: service_healthy
    ports:
      - '5001:5000'
    networks:
      - backend

  service-b:
    build:
      context: .
      dockerfile: Dockerfile.service
    container_name: service-b
    environment:
      SERVICE_ID: service-b
    depends_on:
      consul:
        condition: service_healthy
    ports:
      - '5002:5000'
    networks:
      - backend

  service-c:
    build:
      context: .
      dockerfile: Dockerfile.service
    container_name: service-c
    environment:
      SERVICE_ID: service-c
    depends_on:
      consul:
        condition: service_healthy
    ports:
      - '5003:5000'
    networks:
      - backend

networks:
  backend:
    driver: bridge

volumes:
  kong-db-data:
  keycloak-db-data:
  app-db-data:
  prometheus-data:
  grafana-data:
  es-data:
EOF

# Build and deploy (use sudo if group not effective yet)
if [ "$(id -u)" -ne 0 ] && ! docker info &> /dev/null; then
    echo "Using sudo for deployment (relog for non-sudo access)."
    use_sudo docker compose build
    use_sudo docker compose up -d
else
    docker compose build
    docker compose up -d
fi

echo "Installation and deployment complete!"
echo "Access Portainer at https://localhost:9443 (initial setup required; use for monitoring/scaling the stack)."
echo "Microservices access points:"
echo "- Consul UI: http://localhost:8500"
echo "- Kong Admin: http://localhost:8001"
echo "- Keycloak: http://localhost:8080 (admin/adminpass)"
echo "- Grafana: http://localhost:3000 (admin/adminpass)"
echo "- Kibana: http://localhost:5601"
echo "- Services: http://localhost:5001, :5002, :5003"
echo "To add DB replication or customize, edit docker-compose.yml and run 'docker compose up -d'."
echo "Docker version: $(docker --version)"
echo "Docker Compose version: $(docker compose version)"
