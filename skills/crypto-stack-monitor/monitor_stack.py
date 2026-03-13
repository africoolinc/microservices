#!/usr/bin/env python3
"""
Crypto Stack Monitor
Monitors and audits crypto_stack services on Gibson's machine
Client query support for account status checks
"""

import json
import subprocess
import os
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import hashlib

# Configuration
WORKSPACE = Path("/home/africool/.openclaw/workspace/projects/members/Gibson")
LOGS_DIR = WORKSPACE / "logs"
MEMORY_DIR = WORKSPACE / "memory"
STACK_CONFIG = {
    "ssh_host": "gibson-vpn",
    "services": [
        {"name": "BTC Options Bot", "port": 5000, "critical": True, "tier": "core"},
        {"name": "Bridge API", "port": 3100, "critical": True, "tier": "core"},
        {"name": "Bridge Heartbeat", "port": 3101, "critical": False, "tier": "support"},
        {"name": "Bridge Tracker", "port": 3102, "critical": False, "tier": "support"},
        {"name": "Crypto Resolver", "port": 8080, "critical": False, "tier": "support"},
        {"name": "CF Worker Sim", "port": 8888, "critical": False, "tier": "support"},
    ],
    "containers": [
        "crypto_stack-options-bot-1",
        "bridge_api",
        "bridge_heartbeat",
        "bridge_tracker",
        "crypto_resolver",
        "bridge_db",
        "crypto_redis"
    ]
}

LOGS_DIR.mkdir(exist_ok=True)
MEMORY_DIR.mkdir(exist_ok=True)

# Client database (simulated - in production would be real DB)
CLIENTS_DB = LOGS_DIR / "clients.json"
if not CLIENTS_DB.exists():
    with open(CLIENTS_DB, 'w') as f:
        json.dump({}, f)

def ssh_exec(command):
    """Execute command on remote via SSH"""
    try:
        result = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=10", "-o", "BatchMode=yes", 
             STACK_CONFIG["ssh_host"], command],
            capture_output=True, text=True, timeout=30
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "SSH timeout"
    except Exception as e:
        return False, "", str(e)

def check_docker_containers():
    """Check Docker container status"""
    success, stdout, stderr = ssh_exec("docker ps -a --format '{{.Names}}\t{{.Status}}'")
    
    containers = []
    if success and stdout:
        for line in stdout.strip().split('\n'):
            if line:
                parts = line.split('\t')
                name = parts[0] if len(parts) > 0 else "unknown"
                status = parts[1] if len(parts) > 1 else "unknown"
                
                is_running = "Up" in status
                containers.append({
                    "container": name,
                    "status": "running" if is_running else "stopped",
                    "detail": status
                })
    
    return containers

def check_service_health(service, port):
    """Check HTTP service health"""
    try:
        result = subprocess.run(
            ["curl", "-s", "-w", "\n%{time_total}", 
             f"http://10.144.118.159:{port}/health", 
             "-o", "/dev/null"],
            capture_output=True, text=True, timeout=10
        )
        
        # Parse time from last line
        lines = result.stdout.strip().split('\n')
        time_ms = 0
        for line in reversed(lines):
            try:
                time_ms = float(line) * 1000
                break
            except:
                continue
        
        if result.returncode == 0:
            return {"status": "healthy", "ms": time_ms}
        elif result.returncode == 22:  # HTTP error
            return {"status": "down", "ms": time_ms, "error": "HTTP Error"}
        else:
            return {"status": "down", "ms": time_ms, "error": "Connection failed"}
    except Exception as e:
        return {"status": "down", "ms": 0, "error": str(e)}

def hash_phone(phone):
    """Hash phone number for privacy"""
    return hashlib.sha256(phone.encode()).hexdigest()[:12]

def quick_status():
    """Quick status check - local only"""
    print("=== Crypto Stack Quick Status ===\n")
    
    # Check docker status locally
    result = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
        capture_output=True, text=True
    )
    
    if result.returncode == 0:
        print("Local Docker Containers:")
        for line in result.stdout.strip().split('\n')[:10]:
            if line:
                print(f"  {line}")
    
    # Check remote status log
    status_file = LOGS_DIR / "crypto_stack_status.json"
    if status_file.exists():
        print("\nLast Remote Status:")
        with open(status_file) as f:
            data = json.load(f)
            print(f"  Timestamp: {data.get('timestamp', 'N/A')}")
            print(f"  Health Score: {data.get('summary', {}).get('health_score', 'N/A')}/10")
    
    return True

def full_audit(quiet=False):
    """Full stack audit via SSH"""
    if not quiet:
        print("=== Crypto Stack Full Audit ===\n")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Target: gibson-vpn (10.144.118.159)\n")
    
    # Check containers
    containers = check_docker_containers()
    
    # Check services
    service_status = []
    for svc in STACK_CONFIG["services"]:
        health = check_service_health(svc["name"], svc["port"])
        service_status.append({
            "port": svc["port"],
            "name": svc["name"],
            "status": health["status"],
            "ms": health.get("ms", 0),
            "error": health.get("error"),
            "critical": svc.get("critical", False),
            "tier": svc.get("tier", "support")
        })
    
    # Calculate health score
    healthy = sum(1 for s in service_status if s["status"] == "healthy")
    total = len(service_status)
    health_score = round((healthy / total) * 10, 1) if total > 0 else 0
    
    # Check critical services specifically
    critical_services = [s for s in service_status if s.get("critical")]
    critical_healthy = sum(1 for s in critical_services if s["status"] == "healthy")
    critical_score = round((critical_healthy / len(critical_services)) * 10, 1) if critical_services else 10
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "services": service_status,
        "containers": containers,
        "summary": {
            "healthy": healthy,
            "total": total,
            "health_score": health_score,
            "critical_healthy": critical_healthy,
            "critical_total": len(critical_services),
            "critical_score": critical_score
        }
    }
    
    # Save report
    status_file = LOGS_DIR / "crypto_stack_status.json"
    with open(status_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Generate public status
    generate_public_status(report)
    
    # Update memory ledger
    update_memory_ledger(report)
    
    if not quiet:
        print(f"\nHealth Score: {health_score}/10")
        print(f"Critical Services: {critical_healthy}/{len(critical_services)} ({critical_score}/10)")
        
        # Alert if critical issues
        critical_down = [s for s in service_status if s["status"] != "healthy" and s.get("critical")]
        
        if critical_down:
            print(f"\n⚠️  CRITICAL: {len(critical_down)} critical service(s) down!")
            for s in critical_down:
                print(f"  - {s['name']} ({s.get('error', 'unknown error')})")
        else:
            print("\n✅ All critical services operational")
    
    # Append to history
    history_file = LOGS_DIR / "crypto_stack_history.jsonl"
    with open(history_file, 'a') as f:
        f.write(json.dumps(report) + '\n')
    
    if not quiet:
        print(f"\nReport saved to: {status_file}")
    
    return report

def generate_public_status(report):
    """Generate client-accessible status page"""
    summary = report.get("summary", {})
    
    # Public status (no internal details)
    public_report = {
        "status": "operational" if summary.get("critical_score", 0) >= 8 else "degraded",
        "updated": report["timestamp"],
        "health_score": summary.get("critical_score", 0),
        "services": [
            {
                "name": s["name"],
                "status": "up" if s["status"] == "healthy" else "down",
                "latency_ms": s.get("ms", 0)
            }
            for s in report["services"] if s.get("tier") == "core"
        ]
    }
    
    public_file = LOGS_DIR / "public_status.json"
    with open(public_file, 'w') as f:
        json.dump(public_report, f, indent=2)
    
    return public_report

def update_memory_ledger(report):
    """Update daily memory ledger"""
    today = datetime.now().strftime("%Y-%m-%d")
    ledger_file = MEMORY_DIR / f"{today}.md"
    
    summary = report.get("summary", {})
    services = report.get("services", [])
    
    health = summary.get("health_score", 0)
    critical = summary.get("critical_score", 0)
    
    # Determine status emoji
    if critical >= 9:
        status = "✅"
    elif critical >= 7:
        status = "⚠️"
    else:
        status = "🔴"
    
    entry = f"""## {datetime.now().strftime("%H:%M")} - Crypto Stack Scan
{status} Health: {health}/10 | Critical: {critical}/10

### Services Status
"""
    
    for s in services:
        emoji = "✅" if s["status"] == "healthy" else "❌"
        latency = f"{s.get('ms', 0)}ms"
        entry += f"- {emoji} {s['name']}: {s['status']} ({latency})\n"
    
    entry += f"\n*Full report: `logs/crypto_stack_status.json`*\n"
    
    # Append to existing or create new
    if ledger_file.exists():
        with open(ledger_file, 'a') as f:
            f.write(entry + "\n")
    else:
        with open(ledger_file, 'w') as f:
            f.write(f"# Memory Ledger - {today}\n\n")
            f.write(entry + "\n")
    
    # Generate public summary for clients
    generate_public_status(report)
    
    return entry

def client_query(phone):
    """Query account status by phone number"""
    # Load client database
    with open(CLIENTS_DB) as f:
        clients = json.load(f)
    
    phone_hash = hash_phone(phone)
    
    # Check if client exists
    if phone_hash not in clients:
        return {
            "found": False,
            "message": "Phone number not registered. Sign up to access services."
        }
    
    client = clients[phone_hash]
    
    # Get current stack status
    status_file = LOGS_DIR / "crypto_stack_status.json"
    if status_file.exists():
        with open(status_file) as f:
            status = json.load(f)
        health = status.get("summary", {}).get("critical_score", 0)
    else:
        health = "Unknown"
    
    # Build response
    return {
        "found": True,
        "client": {
            "tier": client.get("tier", "Bronze"),
            "registered": client.get("created_at", "Unknown"),
            "last_active": client.get("last_active", "Unknown")
        },
        "system_status": {
            "health_score": health,
            "status": "operational" if health >= 7 else "degraded"
        },
        "services": status.get("services", []) if status_file.exists() else []
    }

def scheduled_scan():
    """Run scheduled 4-hour scan"""
    import argparse
    print(f"🔄 Running scheduled scan at {datetime.now().isoformat()}")
    
    report = full_audit(quiet=True)
    
    summary = report.get("summary", {})
    critical = summary.get("critical_score", 0)
    
    # Alert if issues
    if critical < 7:
        print(f"⚠️ ALERT: Critical services degraded! Score: {critical}/10")
        # Could send SMS/email alert here
    
    print(f"✅ Scan complete. Health: {summary.get('health_score', 0)}/10")
    return report

def main():
    parser = argparse.ArgumentParser(description="Crypto Stack Monitor")
    parser.add_argument("--quick", action="store_true", help="Quick local status")
    parser.add_argument("--audit", action="store_true", help="Full audit via SSH")
    parser.add_argument("--client", type=str, help="Query client by phone number")
    parser.add_argument("--schedule", action="store_true", help="Run scheduled 4-hour scan")
    parser.add_argument("--alert", action="store_true", help="Enable alerting")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    
    args = parser.parse_args()
    
    if args.schedule:
        scheduled_scan()
    elif args.client:
        result = client_query(args.client)
        print(json.dumps(result, indent=2))
    elif args.quick:
        quick_status()
    elif args.audit:
        full_audit()
    else:
        full_audit(quiet=args.quiet)

if __name__ == "__main__":
    main()