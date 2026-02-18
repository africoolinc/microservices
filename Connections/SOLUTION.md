# Cloudflare Tunnel Solution: "Gibson Out-of-Band (OOB) Access"

## Overview
To eliminate the single point of failure (SSH daemon), we are implementing a Cloudflare Tunnel. This provides a persistent, secure, outbound connection to Cloudflare's edge, allowing for web-based SSH and terminal access even when local port 22 is unresponsive or blocked by firewalls/OOM events.

## Benefits
- **No Inbound Ports:** No need to open port 22 to the public internet.
- **Bypasses OOM-killed SSH:** If the local `sshd` dies, the `cloudflared` container (with proper restart policies) can remain active.
- **Web-Based Terminal:** Accessible via any browser via Cloudflare Zero Trust dashboard.
- **Free Tier:** Sufficient for management and emergency recovery.

## Deployment Strategy
1. **System Service (Native):** Recommended for maximum persistence across reboots.
2. **Containerized (Docker):** Run `cloudflared` as a Docker container within the existing stack as a secondary fallback.
3. **Auto-Restart:** Set `restart: always` in Docker or use systemd service management.
4. **Authentication:** Uses the Cloudflare Tunnel Token.

## Setup Instructions

### Option A: Native System Service (Recommended)
Run this command on the remote machine (requires root):
```bash
sudo cloudflared service install eyJhIjoiY2NiZmNjMDE3ZmE0ZGFlNThjNTA1N2NlZTA0MjhiOTkiLCJ0IjoiMmM5OTU2NTktN2QwYS00ZWY4LWI5YWYtOGFhNGEzN2IwMjM3IiwicyI6IlpXSTBZemcwWlRNdE5XRTBOaTAwWmpsaExXRTRNV1l0TjJVNU1qSTJOemMxWXpNNCJ9
```

### Option B: Docker Container
Add the following to Gibson's `docker-compose.yml`:

```yaml
  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: cloudflared
    command: tunnel --no-autoupdate run
    environment:
      - TUNNEL_TOKEN=eyJhIjoiY2NiZmNjMDE3ZmE0ZGFlNThjNTA1N2NlZTA0MjhiOTkiLCJ0IjoiMmM5OTU2NTktN2QwYS00ZWY4LWI5YWYtOGFhNGEzN2IwMjM3IiwicyI6IlpXSTBZemcwWlRNdE5XRTBOaTAwWmpsaExXRTRNV1l0TjJVNU1qSTJOemMxWXpNNCJ9
    restart: always
    networks:
      - stack-network
```

## Connection Flow
1. Agent/User checks SSH.
2. If SSH fails, use Cloudflare Tunnel URL (e.g., `ssh.juma.family`).
3. If both fail, manual console intervention is required.

## Automation
The `connection_manager.py` script should be run every 15-30 minutes via cron to maintain the journal and alert on status changes.

```bash
*/15 * * * * /home/africool/.openclaw/workspace/projects/members/Gibson/Connections/connection_manager.py
```
