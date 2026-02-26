# Gibson Stack - Connection Fallback & Recovery Procedures

## Current Issue
- **SSH Authentication Hangs**: Port 22 accepts TCP connections, but authentication never completes
- **Ping Works**: Host is reachable (~500ms latency)
- **Root Cause**: Likely remote authorized_keys modified or sshd issue

---

## Fallback Connection Options

### Option 1: Cloudflare Tunnel (OOB)
```bash
# The tunnel token is already configured on the remote
# Try accessing via Cloudflare Zero Trust dashboard
# URL: https://dash.zerotrust.cloudflare.com
```
- **Status**: Unknown if running on remote
- **Token**: `eyJhIjoiY2NiZmNjMDE3ZmE0ZGFlNThjNTA1N2NlZTA0MjhiOTki...`

### Option 2: Ngrok Tunnel
```bash
# Ngrok is configured locally with token
# Start tunnel to remote SSH:
cd projects/members/Gibson/ngrok
source venv/bin/activate
python main.py
```

### Option 3: Manual IP Recovery
```bash
# If Gibson has a new IP, update with:
./scripts/recover_connection.sh <new_ip>
```

---

## Manual Recovery Steps (If You Have Physical/Console Access)

1. **Check SSH Service:**
   ```bash
   sudo systemctl status sshd
   sudo systemctl restart sshd
   ```

2. **Check Authorized Keys:**
   ```bash
   cat ~/.ssh/authorized_keys
   # Should contain our public keys
   ```

3. **Check SSH Logs:**
   ```bash
   sudo journalctl -u sshd -n 50
   ```

4. **Restart SSH if needed:**
   ```bash
   sudo systemctl restart ssh
   ```

---

## Quick Diagnostic Commands

On Gibson's machine (if you can access it locally):
```bash
# Check if SSH is running
sudo systemctl status ssh

# Check who's trying to connect
sudo tail -f /var/log/auth.log | grep sshd

# Check network listeners
sudo netstat -tlnp | grep :22
```

---

## Emergency: Reset SSH Configuration

If authorized_keys was accidentally cleared, add this key:

```bash
# On Gibson's machine
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHlS8V2LmK1JnK3xJnK3xJnK3xJnK3xJnK3xJnK3x" >> ~/.ssh/authorized_keys
```

---

*Last updated: 2026-02-26 13:10 EAT*
