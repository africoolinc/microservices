# RESOURCE_POLICY.md - Resource Management Rules

## 1. Memory Thresholds for Docker Microservices
- **Target Maintenance**: 70% Memory Usage.
- **Intervention Trigger**: 80% Memory Usage.

## 2. CPU Thresholds
- **Target Maintenance**: 70% Average CPU Usage (over 5 min window).
- **Intervention Trigger**: 85% Average CPU Usage (over 5 min window).

## 3. Disk I/O Thresholds
- **Target Maintenance**: Average I/O Wait Time < 10ms.
- **Intervention Trigger**: Average I/O Wait Time > 50ms OR High Disk Queue Depth (> 2 per disk).

## 4. Enforcement Protocols (Automated/Agent-Led)
- **At 70% Memory (Maintenance Mode)**:
    - Run `docker system prune -f`.
    - Clear cache/temp files in microservice volumes.
    - Check for memory leaks in logs.
- **At 80% Memory (Intervention Mode)**:
    - Identify top memory-consuming containers.
    - Restart containers exceeding 2GB memory individually.
    - **Notify Gibson immediately** with a "Resource Intervention Report" (memory).
- **Below CPU/Disk Intervention Triggers**:
    - Identify top CPU/IO consuming processes/containers.
    - Throttle or restart misbehaving processes/containers.
    - **Notify Gibson immediately** with a "Resource Intervention Report" (CPU/IO).
- **Below CPU/Disk Maintenance Triggers**:
    - Monitor for sustained high load.
    - Log potential performance bottlenecks.

## 5. Implementation
- Monitored by: **Workspace Manager Core Orchestrator**.
- Frequency: Checks run every 15 minutes.
- Logging: All interventions are logged in `workspace_manager/logs/resource_interventions.log` and summarized in `workspace_manager/logs/workspace_ops.log`.

## 6. Compliance
- This rule is **STRICT**. Any bypass requires explicit user override documented in the logs.
