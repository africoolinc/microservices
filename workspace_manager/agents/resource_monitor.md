# Resource Monitor Agent

## Role
Automated resource monitoring agent for Gibson's microservices stack. Enforces memory, CPU, and disk thresholds per RESOURCE_POLICY.md.

## Targets
- **Host**: 10.144.118.159 (StackForge)
- **Stack**: Docker microservices managed by docker-compose

## Thresholds (Per RESOURCE_POLICY.md)

### Memory
- **Maintenance**: 70% Docker container memory usage
- **Intervention**: 80% Docker container memory usage

### CPU
- **Maintenance**: 70% average over 5 min
- **Intervention**: 85% average over 5 min

### Disk I/O
- **Maintenance**: <10ms I/O wait
- **Intervention**: >50ms I/O wait OR disk queue >2

## Checks

### 1. Container Memory Check
```bash
docker stats --no-stream --format '{{.Name}}\t{{.MemPerc}}'
```
Alert if ANY container exceeds threshold.

### 2. Host Memory Check
```bash
free | awk '/^Mem:/{printf "%.0f", $3/$2*100}'
```
Alert if host memory exceeds threshold.

### 3. CPU Load Check
```bash
uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ','
```
Alert if 5-min average exceeds threshold.

## Actions

### At 70% (Maintenance Mode)
1. Run `docker system prune -f`
2. Log to `workspace_manager/logs/resource_interventions.log`
3. Monitor for sustained high usage

### At 80% (Intervention Mode)
1. Identify top memory-consuming containers
2. Restart containers exceeding 2GB individually
3. Create "Resource Intervention Report"
4. Notify Gibson immediately

## Execution
- **Frequency**: Every 15 minutes via cron
- **Logging**: All actions logged with timestamps
- **Alerting**: Push notification on intervention triggers

## Example Cron Entry
```bash
*/15 * * * * /home/africool/.openclaw/workspace/projects/members/Gibson/workspace_manager/agents/resource_monitor.sh
```

## Output Format
```markdown
# Resource Intervention Report
**Timestamp**: 2026-02-19 02:30 EAT
**Trigger**: Memory > 80%
**Host**: 10.144.118.159

## Affected Containers
| Container | Memory % |
|-----------|----------|
| elasticsearch | 85% |
| keycloak | 82% |

## Actions Taken
1. Restarted elasticsearch
2. Pruned Docker system

## Recommendation
Consider adding more memory or optimizing ES queries.
```
