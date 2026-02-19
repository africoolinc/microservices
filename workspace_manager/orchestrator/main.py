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

# --- Thresholds from RESOURCE_POLICY.md ---
# Memory
TARGET_MEM = 70.0
INTERVENE_MEM = 80.0

# CPU (Average over 5 min window)
TARGET_CPU = 70.0
INTERVENE_CPU = 85.0

# Disk I/O
TARGET_IO_WAIT_MS = 10.0
INTERVENE_IO_WAIT_MS = 50.0
INTERVENE_IO_QUEUE = 2.0 # per disk

# --- Setup Logging ---
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
    """Service to monitor and enforce RESOURCE_POLICY.md for Memory, CPU, and Disk I/O."""

    def __init__(self):
        self.checked_iostat = None
        self.iostat_available = False
        self._check_iostat_availability()

    def _check_iostat_availability(self):
        """Check if iostat command is available on the remote host."""
        iostat_check = self._run_remote_command("command -v iostat")
        if iostat_check is not None and "iostat" in iostat_check:
            self.iostat_available = True
            logging.info("iostat command found on remote host.")
        else:
            logging.warning("iostat command not found on remote. Disk I/O checks will be skipped.")
            self.iostat_available = False

    def _run_remote_command(self, command):
        """Helper to run a command on the remote host via SSH."""
        try:
            # Escape $ signs to prevent local shell expansion
            escaped_command = command.replace("$", "\\$")
            ssh_command = f"ssh gibson-vpn \"{escaped_command}\""
            result = subprocess.run(ssh_command, shell=True, capture_output=True, text=True, check=True, timeout=15)
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            logging.error(f"Remote command timed out: {command}")
            return None
        except subprocess.CalledProcessError as e:
            # Ignore non-zero exit codes if output is valid, but log stderr for debugging
            if e.stderr:
                # Filter out known harmless warnings like "Warning: Permanently added..."
                stderr_lines = [l for l in e.stderr.splitlines() if "Warning:" not in l]
                if stderr_lines:
                    logging.error(f"Remote command error for '{command}': {' '.join(stderr_lines)}")
            return e.stdout.strip() if e.stdout else None
        except Exception as e:
            logging.error(f"Unexpected error running remote command '{command}': {e}")
            return None

    def get_memory_usage(self):
        """Fetches memory usage percentage from the remote host."""
        # Using awk to calculate percentage
        output = self._run_remote_command("free -m | grep Mem | awk '{print $3/$2*100}'")
        if output:
            try:
                return float(output)
            except ValueError:
                logging.error(f"Could not parse memory usage: {output}")
        return None

    def get_cpu_usage(self):
        """Fetches average CPU usage percentage from the remote host."""
        # Use top in batch mode, calculate busy percentage from idle
        # top -bn1 | grep "Cpu(s)" -> "Cpu(s):  1.5 us, ..."
        # We want 100 - idle%
        output = self._run_remote_command("top -bn1 | grep 'Cpu(s)' | awk '{print 100 - $8}'")
        if output:
            try:
                val = float(output)
                return val
            except ValueError:
                logging.error(f"Could not parse CPU usage: {output}")
        return None

    def get_disk_io_stats(self):
        """Fetches disk I/O stats (await, queue size) from the remote host."""
        if not self.iostat_available:
            return None, None

        try:
            # Capture r_await, w_await, aqu-sz ($9, $10, $11) for relevant devices
            output = self._run_remote_command("iostat -dx 1 1 | awk '/^[svh]d|^nvme|^mmcblk/ {print $9,$10,$11}'")
            
            avg_await_time = 0.0
            max_queue_depth = 0.0
            count = 0
            
            if output:
                for line in output.splitlines():
                    parts = line.split()
                    if len(parts) >= 3:
                        try:
                            r_await = float(parts[0])
                            w_await = float(parts[1])
                            aqu_sz = float(parts[2])
                            
                            avg_await_time += (r_await + w_await) / 2.0
                            max_queue_depth = max(max_queue_depth, aqu_sz)
                            count += 1
                        except ValueError:
                            logging.warning(f"Could not parse disk I/O line: {line}")
                if count > 0:
                    return avg_await_time / count, max_queue_depth
        except Exception as e:
            logging.error(f"Failed to get disk I/O stats: {e}")
        return None, None

    def enforce_policy(self, mem_usage, cpu_usage, disk_io_await, disk_io_queue):
        """Checks thresholds and triggers actions."""
        timestamp = datetime.datetime.now().isoformat()
        
        # Memory check
        if mem_usage is not None:
            if mem_usage >= INTERVENE_MEM:
                logging.warning(f"CRITICAL MEMORY: {mem_usage:.2f}% (Threshold: {INTERVENE_MEM}%). Intervening...")
                self._log_intervention(timestamp, "CRITICAL_MEM", mem_usage=mem_usage)
                self._run_intervention_actions(reason="High Memory")
            elif mem_usage >= TARGET_MEM:
                logging.info(f"MAINTENANCE MEMORY: {mem_usage:.2f}% (Threshold: {TARGET_MEM}%). Running maintenance...")
                self._log_intervention(timestamp, "MAINTENANCE_MEM", mem_usage=mem_usage)
                self._run_maintenance_actions()
            else:
                logging.info(f"Memory healthy at {mem_usage:.2f}%")
        
        # CPU check
        if cpu_usage is not None:
            if cpu_usage >= INTERVENE_CPU:
                logging.warning(f"CRITICAL CPU: {cpu_usage:.2f}% (Threshold: {INTERVENE_CPU}%). Intervening...")
                self._log_intervention(timestamp, "CRITICAL_CPU", cpu_usage=cpu_usage)
                self._run_intervention_actions(reason="High CPU")
            elif cpu_usage >= TARGET_CPU:
                logging.info(f"MAINTENANCE CPU: {cpu_usage:.2f}% (Threshold: {TARGET_CPU}%). Performing checks...")
                self._log_intervention(timestamp, "MAINTENANCE_CPU", cpu_usage=cpu_usage)
        else:
            logging.warning("CPU usage not available or error parsing.")

        # Disk I/O check
        if disk_io_await is not None and disk_io_queue is not None:
            if disk_io_await >= INTERVENE_IO_WAIT_MS or disk_io_queue >= INTERVENE_IO_QUEUE:
                logging.warning(f"CRITICAL DISK I/O: Await={disk_io_await:.2f}ms, Queue={disk_io_queue:.2f}. Intervening...")
                self._log_intervention(timestamp, "CRITICAL_DISK_IO", disk_io_await=disk_io_await, disk_io_queue=disk_io_queue)
                self._run_intervention_actions(reason="High Disk I/O")
            elif disk_io_await < TARGET_IO_WAIT_MS and disk_io_queue < INTERVENE_IO_QUEUE:
                 logging.info(f"Disk I/O healthy: Await={disk_io_await:.2f}ms, Queue={disk_io_queue:.2f}")
        elif self.checked_iostat and not self.iostat_available:
             pass 

    def _log_intervention(self, ts, level, **kwargs):
        """Structured logging for interventions."""
        entry = {"timestamp": ts, "level": level, **kwargs}
        try:
            with open(INT_LOG_FILE, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except IOError as e:
            logging.error(f"Failed to write to intervention log {INT_LOG_FILE}: {e}")

    def _run_maintenance_actions(self):
        """Run general maintenance tasks."""
        logging.info("Running general maintenance actions (Docker prune)...")
        try:
            self._run_remote_command("docker system prune -f")
            logging.info("Maintenance: Docker system prune completed.")
        except Exception as e:
            logging.error(f"Maintenance actions failed: {e}")

    def _run_intervention_actions(self, reason="Resource issue"):
        """Run critical intervention actions."""
        logging.warning(f"Executing critical intervention actions due to: {reason}")
        try:
            self._run_remote_command("docker system prune -af")
            logging.info("Intervention: Aggressive Docker cleanup (prune -af) completed.")
        except Exception as e:
            logging.error(f"Intervention actions failed: {e}")

class WorkspaceOrchestrator:
    def __init__(self):
        setup_logging()
        self.monitor = ResourceMonitor()
        logging.info("Core Orchestrator starting cycle...")

    def run_cycle(self):
        mem_usage = self.monitor.get_memory_usage()
        cpu_usage = self.monitor.get_cpu_usage()
        disk_io_await, disk_io_queue = self.monitor.get_disk_io_stats()
        
        if mem_usage is not None: logging.info(f"Measured Memory Usage: {mem_usage:.2f}%")
        if cpu_usage is not None: logging.info(f"Measured CPU Usage: {cpu_usage:.2f}%")
        if disk_io_await is not None and disk_io_queue is not None:
            logging.info(f"Measured Disk I/O: Avg Await={disk_io_await:.2f}ms, Max Queue={disk_io_queue:.2f}")

        self.monitor.enforce_policy(mem_usage, cpu_usage, disk_io_await, disk_io_queue)

if __name__ == "__main__":
    orchestrator = WorkspaceOrchestrator()
    orchestrator.run_cycle()
