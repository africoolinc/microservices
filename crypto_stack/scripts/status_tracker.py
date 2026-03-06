#!/usr/bin/env python3
"""
Crypto Stack Status Tracker
Runs every 3 hours to verify service health
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

STATUS_FILE = "/home/africool/.openclaw/workspace/projects/members/Gibson/crypto_stack/logs/status.json"
LOG_FILE = "/home/africool/.openclaw/workspace/projects/members/Gibson/crypto_stack/logs/tracker.log"

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def check_port(port, name):
    """Check if a port is responding"""
    import urllib.request
    import time
    start = time.time()
    try:
        req = urllib.request.Request(f"http://localhost:{port}/")
        with urllib.request.urlopen(req, timeout=10) as r:
            elapsed = (time.time() - start) * 1000
            return {"port": port, "name": name, "status": "healthy", "ms": round(elapsed, 1)}
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        return {"port": port, "name": name, "status": "down", "ms": round(elapsed, 1), "error": str(e)[:50]}

def check_docker_container(name):
    """Check if docker container is running"""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={name}", "--format", "{{.Status}}"],
            capture_output=True, text=True, timeout=5
        )
        status = result.stdout.strip()
        if status:
            return {"container": name, "status": "running", "detail": status}
        return {"container": name, "status": "stopped"}
    except Exception as e:
        return {"container": name, "status": "error", "error": str(e)}

def run_status_check():
    """Run full status check"""
    log("=" * 50)
    log("CRYPTO STACK STATUS CHECK")
    log("=" * 50)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "services": [],
        "containers": [],
        "summary": {"healthy": 0, "total": 0}
    }
    
    # Check ports
    ports = [
        (5000, "BTC Options Bot"),
        (3000, "Bridge API"),
        (3001, "Bridge Heartbeat"),
        (8080, "Crypto Resolver"),
        (8888, "CF Worker Sim")
    ]
    
    for port, name in ports:
        log(f"Checking {name} on port {port}...")
        svc = check_port(port, name)
        results["services"].append(svc)
        results["summary"]["total"] += 1
        if svc["status"] == "healthy":
            results["summary"]["healthy"] += 1
            log(f"  ✅ {name}: HEALTHY ({svc['ms']}ms)")
        else:
            log(f"  ❌ {name}: DOWN - {svc.get('error', 'No response')}")
    
    # Check containers
    containers = ["crypto_resolver", "crypto_stack-options-bot-1", "bridge_api", "redis"]
    for c in containers:
        log(f"Checking container {c}...")
        cont = check_docker_container(c)
        results["containers"].append(cont)
        if cont["status"] == "running":
            log(f"  ✅ {c}: RUNNING")
        else:
            log(f"  ⚠️  {c}: {cont['status']}")
    
    # Calculate health score
    score = round((results["summary"]["healthy"] / results["summary"]["total"]) * 100, 1) if results["summary"]["total"] > 0 else 0
    results["summary"]["health_score"] = score
    
    log("-" * 50)
    log(f"HEALTH SCORE: {score}%")
    log("=" * 50)
    
    # Save results
    os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)
    with open(STATUS_FILE, "w") as f:
        json.dump(results, f, indent=2)
    
    return results

if __name__ == "__main__":
    run_status_check()
