#!/usr/bin/env python3
"""
Gibson Stack Monitor - Memory & Resource Management
=====================================================
Ensures memory stays below 80% threshold to prevent OOM
Idempotent: Safe to rerun
Virtual env: Uses uv
Error handling: Try/except with proper logging
Colored output: ANSI colors for human readability
Logging: Timestamped file output
"""

import os
import sys
import subprocess
import logging
from datetime import datetime
from pathlib import Path

# --- Configuration ---
SCRIPT_DIR = Path(__file__).parent.resolve()
LOG_DIR = SCRIPT_DIR / "logs"
LOG_FILE = LOG_DIR / f"monitor_{datetime.now():%Y-%m-%d}.log"
MEMORY_THRESHOLD = 80
ALERT_THRESHOLD = 90

# --- Colors ---
class Colors:
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    GREEN = '\033[0;32m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

# --- Setup Logging ---
def setup_logging():
    """Initialize logging to file and console."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )

def run_cmd(cmd: str, timeout: int = 30) -> tuple:
    """Execute shell command safely with timeout."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def get_memory_usage() -> int:
    """Get current memory usage percentage."""
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
        
        mem_total = mem_avail = 0
        for line in lines:
            if line.startswith('MemTotal:'):
                mem_total = int(line.split()[1])
            elif line.startswith('MemAvailable:'):
                mem_avail = int(line.split()[1])
        
        if mem_total == 0:
            return 0
            
        mem_used = mem_total - mem_avail
        return int((mem_used / mem_total) * 100)
    except Exception as e:
        logging.error(f"Failed to get memory: {e}")
        return 0

def get_disk_usage() -> int:
    """Get disk usage percentage."""
    code, out, _ = run_cmd("df -h / | tail -1 | awk '{print $5}' | sed 's/%//'")
    if code == 0 and out.strip().isdigit():
        return int(out.strip())
    return 0

def get_container_count() -> int:
    """Count running Docker containers."""
    code, out, _ = run_cmd("docker ps --format '{{.Names}}' | wc -l")
    if code == 0:
        try:
            return int(out.strip())
        except ValueError:
            return 0
    return 0

def get_top_containers(limit: int = 5) -> list:
    """Get top memory-consuming containers."""
    code, out, _ = run_cmd(
        f"docker stats --no-stream --format '{{{{.Name}}}}:{{{{.MemUsage}}}}' | "
        f"awk -F'/' '{{print $1}}' | sort -t ':' -k2 -g -r | head {limit}"
    )
    if code == 0:
        return [line.strip() for line in out.strip().split('\n') if line.strip()]
    return []

def restart_non_critical() -> list:
    """Restart non-critical services to free memory."""
    services = ['kibana', 'grafana']
    restarted = []
    
    for svc in services:
        code, _, _ = run_cmd(f"docker ps --format '{{{{.Names}}}}' | grep -q '^{svc}$'")
        if code == 0:
            code, _, _ = run_cmd(f"docker restart {svc}")
            if code == 0:
                restarted.append(svc)
                logging.info(f"Restarted {svc}")
    
    return restarted

def main():
    """Main monitoring function."""
    setup_logging()
    
    print(f"{Colors.BLUE}============================================{Colors.NC}")
    print(f"{Colors.BLUE} Gibson Stack Resource Monitor{Colors.NC}")
    print(f"{Colors.BLUE} {datetime.now():%Y-%m-%d %H:%M:%S}{Colors.NC}")
    print(f"{Colors.BLUE}============================================{Colors.NC}")
    
    # Memory Check
    mem_pct = get_memory_usage()
    
    if mem_pct >= ALERT_THRESHOLD:
        status = f"{Colors.RED}CRITICAL{Colors.NC}"
        logging.error(f"Memory at {mem_pct}% (ALERT >{ALERT_THRESHOLD}%)")
    elif mem_pct >= MEMORY_THRESHOLD:
        status = f"{Colors.YELLOW}WARNING{Colors.NC}"
        logging.warning(f"Memory at {mem_pct}% (WARNING >{MEMORY_THRESHOLD}%)")
    else:
        status = f"{Colors.GREEN}OK{Colors.NC}"
        logging.info(f"Memory at {mem_pct}%")
    
    print(f"Memory: {mem_pct}% [{status}]")
    
    # Disk Check
    disk_pct = get_disk_usage()
    print(f"Disk: {disk_pct}%")
    logging.info(f"Disk usage: {disk_pct}%")
    
    # Container Count
    count = get_container_count()
    print(f"Containers: {count}")
    logging.info(f"Running containers: {count}")
    
    # Top Consumers
    print(f"\n{Colors.BLUE}Top Memory Consumers:{Colors.NC}")
    top_containers = get_top_containers()
    for container in top_containers:
        print(f"  → {container}")
        logging.info(f"  → {container}")
    
    # Action if above threshold
    if mem_pct >= MEMORY_THRESHOLD:
        print(f"\n{Colors.YELLOW}Memory above {MEMORY_THRESHOLD}% - taking action...{Colors.NC}")
        logging.warning("Attempting to free memory by restarting non-critical services")
        restarted = restart_non_critical()
        if restarted:
            print(f"{Colors.GREEN}Restarted: {', '.join(restarted)}{Colors.NC}")
        else:
            print(f"{Colors.YELLOW}No services restarted{Colors.NC}")
    
    print(f"\n{Colors.GREEN}Done. Log: {LOG_FILE}{Colors.NC}")
    
    # Return status for cron
    return 0 if mem_pct < MEMORY_THRESHOLD else 1

if __name__ == '__main__':
    sys.exit(main())
