# Gibson SSH Tunnel Setup - Complete Guide

## Current Situation
- **Direct SSH to 10.144.118.159**: Hangs at authentication (port 22 TCP works)
- **Cloudflare Tunnel (trusting_beaver)**: Running but unstable/quic issues
- **Ngrok**: Free tier can't do TCP tunnels without card
- **Ping**: Works (~500ms latency)

---

## Option 1: Add SSH to Cloudflare Tunnel (RECOMMENDED)

The cloudflared container (`trusting_beaver`) is already running. To add SSH access:

### On Gibson's Machine (when you can access it):

1. **Create/update cloudflared config:**
```bash
docker exec trusting_beaver sh -c 'cat > /etc/cloudflared/config.yml << EOF
tunnel: 2c995659-7d0a-4ef8-b9af-8aa4a37b0237
credentials-file: /etc/cloudflared/credentials.json
ingress:
  - hostname: ssh-gibson.africoolinc.com
    service: tcp://localhost:22
  - service: http_status:404
EOF'
```

2. **Restart the tunnel:**
```bash
docker restart trusting_beaver
```

3. **Then access SSH via:**
```bash
ssh -o StrictHostKeyChecking=no gibz@ssh-gibson.africoolinc.com
```

---

## Option 2: Create New Cloudflare Tunnel (LOCAL - For This Machine)

Since the remote tunnel has issues, we can create a NEW tunnel from THIS machine to reach the remote:

### Step 1: Install cloudflared on THIS machine
```bash
# On this machine (already done - cloudflared in docker)
docker pull cloudflare/cloudflared:latest
```

### Step 2: Create tunnel
```bash
docker run -d --name gibson-ssh-tunnel \
  -v ~/.cloudflared:/etc/cloudflared \
  cloudflare/cloudflared:latest tunnel --url ssh://host.docker.internal:22 \
  --token eyJhIjoiY2NiZmNjMDE3ZmE0ZGFlNThjNTA1N2NlZTA0MjhiOTkiLCJ0IjoiMmM5OTU2NTktN2QwYS00ZWY4LWI5YWYtOGFhNGEzN2IwMjM3IiwicyI6IlpXSTBZemcwWlRNdE5XRTBOaTAwWmpsaExXRTRNV1l0TjJVNU1qSTJOemMxWXpNNCJ9
```

Note: This requires remote machine to connect BACK to us, which won't work since remote SSH is broken.

---

## Option 3: Fix Remote SSH (ROOT CAUSE)

### If you have physical/console access to Gibson's machine:

```bash
# Check SSH service
sudo systemctl status ssh

# Restart SSH
sudo systemctl restart ssh

# Check authorized_keys
cat ~/.ssh/authorized_keys

# If empty, add our key:
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHlS8V2LmK1JnK3xJnK3xJnK3xJnK3xJnK3xJnK3x AfricoolMicroservices" >> ~/.ssh/authorized_keys
```

---

## Option 4: ZeroTier VPN (ALTERNATIVE)

Check if ZeroTier is running on both machines:
- Remote: `zerotier-cli status` 
- Local: Would need to join same network

Network ID needed: Check `Connections/status.json` or ask Gibson

---

## Quick Diagnostic - What's Working?

| Service | Status |
|---------|--------|
| Ping 10.144.118.159 | ✅ Works |
| Port 22 TCP | ✅ Open |
| SSH Auth | ❌ Hangs |
| Cloudflare Tunnel | ⚠️ Unstable |
| Web Services (ecommerce.africoolinc.com) | ❌ 502 (service down) |

---

## Action Items

1. **Immediate**: Try SSH again - sometimes remote sshd recovers
2. **If fails**: Ask Gibson to check his machine's SSH service
3. **Long-term**: Set up backup tunnel with SSH ingress

---

*Created: 2026-02-26 14:15 EAT*
