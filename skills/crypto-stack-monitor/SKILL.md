# Crypto Stack Monitor Skill

Monitor, audit, and document the crypto_stack microservices running on Gibson's machine. Provides real-time health monitoring, logging, and alerting.

## Overview

This skill provides tools to:
- Monitor Docker containers in crypto_stack
- Check service health endpoints
- Log container statuses and performance metrics
- Generate audit reports
- Alert on service failures
- Document vital statistics

## Target Stack

| Service | Port | Container | Purpose |
|---------|------|-----------|---------|
| BTC Options Bot | 5000 | crypto_stack-options-bot-1 | Automated options trading |
| Bridge API | 3100 | bridge_api | API gateway |
| Bridge Heartbeat | 3101 | bridge_heartbeat | Health monitoring |
| Bridge Tracker | 3102 | bridge_tracker | Activity tracking |
| Crypto Resolver | 8080 | crypto_resolver | DNS/API resolver |
| CF Worker Sim | 8888 | cf-worker-sim | Cloudflare worker sim |
| Bridge DB | 5432 | bridge_db | PostgreSQL database |
| Redis | 6379 | crypto_redis | Cache layer |

## Prerequisites

```bash
# Required tools (already available on Gibson's machine)
docker
curl
jq
```

## Configuration

Connection is via VPN to Gibson's machine:
- **VPN IP:** `10.144.118.159`
- **SSH User:** `gibz`
- **SSH Key:** `~/.ssh/id_rsa_gibson`

## Core Functions

### 1. Docker Container Status

```bash
# SSH into Gibson's machine and check containers
ssh gibson-vpn "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"
```

### 2. Service Health Check

```bash
# Check specific service endpoints
curl -s -w "\nTime: %{time_total}s\n" http://10.144.118.159:5000/health
curl -s -w "\nTime: %{time_total}s\n" http://10.144.118.159:3000/health
```

### 3. Full Stack Audit

```bash
python3 skills/crypto-stack-monitor/stack_auditor.py
```

This generates:
- Container status report
- Service health metrics
- Resource usage (CPU/Memory)
- Error logs snapshot
- Health score calculation

### 4. Automated Monitoring

```bash
# Run monitor (outputs to logs/crypto_stack_status.json)
python3 skills/crypto-stack-monitor/monitor_stack.py

# Run with alerting
python3 skills/crypto-stack-monitor/monitor_stack.py --alert
```

## Script Usage

### Quick Status Check
```bash
python3 skills/crypto-stack-monitor/monitor_stack.py --quick
```

### Full Audit Report
```bash
python3 skills/crypto-stack-monitor/monitor_stack.py --audit
```

### Continuous Monitoring (cron)
```bash
# Add to crontab -e
*/15 * * * * cd /home/africool/.openclaw/workspace/projects/members/Gibson && python3 skills/crypto-stack-monitor/monitor_stack.py --quiet
```

## Output Files

| File | Description |
|------|-------------|
| `logs/crypto_stack_status.json` | Current status snapshot |
| `logs/crypto_stack_audit.json` | Detailed audit report |
| `logs/crypto_stack_history.jsonl` | Historical log (appended) |

## Health Score Calculation

```
Health Score = (Healthy Services / Total Services) × 10

Score Guidelines:
- 9-10: Excellent
- 7-8: Good (minor issues)
- 5-6: Fair (attention needed)
- <5: Critical (immediate action)
```

## Alert Conditions

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Service Down | Any service returns 404/500 | Alert |
| High Latency | >500ms response | Warning |
| Container Unhealthy | Docker health check fails | Critical |
| Disk Space | >90% used | Warning |

## Container Management (with permissions)

### Restart Service
```bash
ssh gibson-vpn "docker restart bridge_api"
```

### View Logs
```bash
ssh gibson-vpn "docker logs crypto_stack-options-bot-1 --tail 50"
```

### Stop/Start Stack
```bash
ssh gibson-vpn "cd /opt/microservices-stack && docker-compose restart"
```

### Update Container
```bash
ssh gibson-vpn "docker pull ghcr.io/username/container:latest && docker-compose up -d"
```

## Security & Audit

### Access Logs
```bash
ssh gibson-vpn "docker logs --since 1h bridge_api 2>&1 | grep -i error"
```

### Failed Connections
```bash
ssh gibson-vpn "docker logs crypto_resolver 2>&1 | grep -i 'connection refused'"
```

### Resource Usage
```bash
ssh gibson-vpn "docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}'"
```

## Business Intelligence

Track service usage patterns:

```bash
# API call counts (from logs)
ssh gibson-vpn "docker logs bridge_api 2>&1 | grep 'GET /' | wc -l"

# Options bot signals generated
ssh gibson-vpn "docker logs crypto_stack-options-bot-1 2>&1 | grep 'SIGNAL' | tail -20"
```

## Integration with Heartbeat

Add to `HEARTBEAT.md` for periodic checks:

```markdown
## Crypto Stack Monitor

- [ ] Check service health on startup
- [ ] Review logs for errors
- [ ] Verify backup completed
- [ ] Log to history
```

## Skill Status

- **Created**: 2026-03-12
- **Location**: `projects/members/Gibson/skills/crypto-stack-monitor/`
- **Main Script**: `monitor_stack.py`
- **Permissions**: SSH access to gibson-vpn, Docker management

## Required SSH Keys

Ensure SSH is configured:
```bash
cat ~/.ssh/config | grep -A5 gibson-vpn
```

Should show:
```
Host gibson-vpn
    HostName 10.144.118.159
    User gibz
    IdentityFile ~/.ssh/id_rsa_gibson
```

## Client Query Support

Clients can query their account status using phone number:

```bash
# Query by phone number (client-facing)
python3 skills/crypto-stack-monitor/monitor_stack.py --client "+2547XXXXXXXX"
```

Response includes:
- Account tier (Platinum/Gold/Silver/Bronze/Free)
- Registration date
- Last active
- System health score
- Service status

## Public Status Endpoint

Clients can access public status at:
```
logs/public_status.json
```

Contains:
- Overall status (operational/degraded)
- Health score
- Core service status only

## Cron Job Setup

**Current Schedule:** Every 4 hours (via crontab)

```bash
0 */4 * * * cd projects/members/Gibson && python3 skills/crypto-stack-monitor/monitor_stack.py --schedule
```

## Memory Ledger

Daily scan results logged to:
```
memory/YYYY-MM-DD.md
```

## Best Practices

1. **Always SSH first** to verify connection before running commands
2. **Check logs** for context before restart decisions
3. **Document changes** in logs/crypto_stack_audit.json
4. **Alert on critical** services only (Options Bot, Bridge API)
5. **Keep backups** before major changes

## Troubleshooting

### Can't connect to VPN
- Check internet connection
- Verify VPN is running on Gibson's machine
- Use local IP if on same network

### Container won't start
- Check logs: `docker logs <container>`
- Verify .env file exists
- Check port conflicts: `ss -tuln | grep <port>`

### High memory usage
- Restart non-critical services
- Clear Docker cache: `docker system prune`
- Check for memory leaks in app logs