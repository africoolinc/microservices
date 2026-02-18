import os
import json
import logging
import datetime
import subprocess
from pathlib import Path

# --- Configuration ---
WORKSPACE_ROOT = Path("/home/africool/.openclaw/workspace/projects/members/Gibson")
MANAGER_ROOT = WORKSPACE_ROOT / "workspace_manager"
LOG_DIR = MANAGER_ROOT / "logs"
LOG_FILE = LOG_DIR / "workspace_ops.log"
INT_LOG_FILE = LOG_DIR / "resource_interventions.log"

# --- Thresholds ---
TARGET_MEM = 70.0
INTERVENE_MEM = 80.0

def setup_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )

class ResourceMonitor:
    """Service to monitor and enforce RESOURCE_POLICY.md"""

    def check_remote_resources(self):
        """Fetch memory stats from remote Gibson machine."""
        try:
            # Using the established 'gibson-vpn' SSH alias from ~/.ssh/config
            cmd = "ssh gibson-vpn \"free | grep Mem | awk '{print \\$3/\\$2 * 100.0}'\""
            usage = float(subprocess.check_output(cmd, shell=True).decode().strip())
            return usage
        except Exception as e:
            logging.error(f"ResourceMonitor failed to reach remote: {e}")
            return None

    def enforce_policy(self, usage):
        if usage is None: return

        timestamp = datetime.datetime.now().isoformat()
        
        if usage >= INTERVENE_MEM:
            msg = f"CRITICAL: Memory at {usage:.2f}% (Threshold: {INTERVENE_MEM}%). Intervening..."
            logging.warning(msg)
            self._log_intervention(timestamp, "INTERVENTION", usage)
            self._run_intervention_actions()
        elif usage >= TARGET_MEM:
            msg = f"NOTICE: Memory at {usage:.2f}% (Threshold: {TARGET_MEM}%). Maintaining..."
            logging.info(msg)
            self._log_intervention(timestamp, "MAINTENANCE", usage)
            self._run_maintenance_actions()
        else:
            logging.info(f"Memory healthy at {usage:.2f}%")

    def _log_intervention(self, ts, level, usage):
        entry = {"timestamp": ts, "level": level, "usage_percent": usage}
        with open(INT_LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def _run_maintenance_actions(self):
        # Phase 1: Clean up docker
        try:
            subprocess.run("ssh gibson-vpn \"docker system prune -f\"", shell=True)
            logging.info("Maintenance: Docker system prune completed.")
        except Exception as e:
            logging.error(f"Maintenance actions failed: {e}")

    def _run_intervention_actions(self):
        # Phase 1: Critical cleanup and restart high-mem containers
        try:
            # Example: Find top consumer and restart it (careful with this in production)
            logging.info("Intervention: Identifying high-resource containers...")
            # For now, just prune and log. In Phase 2, we will scale down.
            subprocess.run("ssh gibson-vpn \"docker system prune -af\"", shell=True)
        except Exception as e:
            logging.error(f"Intervention actions failed: {e}")

class WorkspaceOrchestrator:
    def __init__(self):
        setup_logging()
        self.monitor = ResourceMonitor()
        logging.info("Core Orchestrator starting cycle...")

    def run_cycle(self):
        usage = self.monitor.check_remote_resources()
        self.monitor.enforce_policy(usage)

if __name__ == "__main__":
    orchestrator = WorkspaceOrchestrator()
    orchestrator.run_cycle()
