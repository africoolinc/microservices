# Gibson Stack Resource Management

## Overview
Automated system for monitoring, alerting, and managing resources on the Gibson microservices stack (10.144.118.159).

## Thresholds
| Level | CPU | Memory | Disk | Action |
|-------|-----|--------|------|--------|
| **OK** | 0-60% | 0-70% | 0-80% | None |
| **WARNING** | 60-80% | 70-80% | 80-90% | Auto-action (notify + optional restart) |
| **CRITICAL** | 80-100% | 80-100% | 90-100% | Alert + emergency procedures |

## Components

### 1. Monitor Script (`monitor.sh`)
- Checks CPU, Memory, Disk every 5 minutes
- Logs to `resource_management/logs/status_<date>.log`
- Triggers WARNING/CRITICAL alerts based on thresholds

### 2. Alert System
- **WARNING**: Logs warning, attempts service optimization
- **CRITICAL**: Sends Discord notification, attempts service restart

### 3. Auto-Remediation Actions
- Auto-restart non-essential containers on WARNING
- Emergency shutdown of low-priority services on CRITICAL
- Preserve: PostgreSQL, Keycloak, Kong (core services)

## Usage
```bash
# Run manual check
bash projects/members/Gibson/resource_management/monitor.sh

# View today's status
tail -f projects/members/Gibson/resource_management/logs/status_$(date +%Y-%m-%d).log
```

## Last Run
Last checked: 2026-02-17 17:20 GMT+3
Status: 🔴 SSH UNREACHABLE - Cannot execute remote checks
