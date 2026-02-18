# RESOURCE_POLICY.md - Resource Management Rules

## 1. Memory Thresholds for Docker Microservices
- **Target Maintenance**: 70% Memory Usage.
- **Intervention Trigger**: 80% Memory/Load Usage.

## 2. Enforcement Protocols (Automated/Agent-Led)
- **At 70% (Maintenance Mode)**:
    - Run `docker system prune -f` (dangling images/containers).
    - Clear cache/temp files in microservice volumes.
    - Check for memory leaks in logs.
- **At 80% (Intervention Mode)**:
    - Identify top memory-consuming containers.
    - Scale down non-essential services (e.g., test environments, monitoring redundancy).
    - If specific containers exceed 2GB individually, restart them.
    - Notify Gibson immediately with a "Resource Intervention Report."

## 3. Implementation
- Monitored by: **Workspace Manager Core Orchestrator**.
- Frequency: Every 15 minutes via cron/heartbeat.
- Logging: All interventions are logged in `workspace_manager/logs/resource_interventions.log`.

## 4. Compliance
- This rule is **STRICT**. Any bypass requires explicit user override documented in the logs.
