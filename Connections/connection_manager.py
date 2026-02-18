#!/usr/bin/env python3
import subprocess
import os
import json
import datetime
import socket

# Configuration
CONFIG = {
    "target_host": "10.144.118.159",
    "ssh_key": "/home/africool/.openclaw/workspace/projects/members/Gibson/ssh/github_ssh_key",
    "ssh_user": "gibz",
    "journal_file": "/home/africool/.openclaw/workspace/projects/members/Gibson/Connections/JOURNAL.md",
    "status_json": "/home/africool/.openclaw/workspace/projects/members/Gibson/Connections/status.json"
}

def check_ping(host):
    try:
        output = subprocess.check_output(["ping", "-c", "1", "-W", "2", host], stderr=subprocess.STDOUT, universal_newlines=True)
        return True, "Reachable"
    except subprocess.CalledProcessError:
        return False, "Unreachable"

def check_ssh_port(host, port=22):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def check_ssh_auth(host, user, key):
    try:
        cmd = ["ssh", "-i", key, "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=no", f"{user}@{host}", "echo AUTH_OK"]
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
        return "AUTH_OK" in output
    except Exception:
        return False

def get_current_status():
    host = CONFIG["target_host"]
    ping_ok, ping_msg = check_ping(host)
    port_ok = check_ssh_port(host)
    auth_ok = check_ssh_auth(host, CONFIG["ssh_user"], CONFIG["ssh_key"]) if port_ok else False
    
    # Cloudflare check
    cf_token_path = "/home/africool/.openclaw/workspace/.secrets/gibson_cloudflare_token.txt"
    cf_status = "TOKEN_READY" if os.path.exists(cf_token_path) else "MISSING_TOKEN"
    
    preferred = "SSH" if auth_ok else "Cloudflare Tunnel (OOB)" if ping_ok else "Physical/Console"
    
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "ping": "UP" if ping_ok else "DOWN",
        "ssh_port": "OPEN" if port_ok else "CLOSED",
        "ssh_auth": "SUCCESS" if auth_ok else "FAILED",
        "cloudflare": cf_status,
        "preferred_channel": preferred,
        "health_score": 10 if auth_ok else 5 if ping_ok else 0
    }

def update_journal(status):
    header = f"\n## [{status['timestamp']}] Connectivity Heartbeat\n"
    table = (
        f"| Component | Status |\n"
        f"|-----------|--------|\n"
        f"| Ping      | {status['ping']} |\n"
        f"| SSH Port  | {status['ssh_port']} |\n"
        f"| SSH Auth  | {status['ssh_auth']} |\n"
        f"| Cloudflare| {status['cloudflare']} |\n"
        f"| **Preferred** | **{status['preferred_channel']}** |\n"
        f"| Health    | {status['health_score']}/10 |\n"
    )
    
    with open(CONFIG["journal_file"], "a") as f:
        f.write(header + table)

def save_status(status):
    with open(CONFIG["status_json"], "w") as f:
        json.dump(status, f, indent=2)

if __name__ == "__main__":
    status = get_current_status()
    save_status(status)
    update_journal(status)
    print(f"Connection Check Complete. Preferred Channel: {status['preferred_channel']}")
