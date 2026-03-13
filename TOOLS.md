# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## Crypto Stack Monitor

- **Skill Location:** `skills/crypto-stack-monitor/`
- **Main Script:** `monitor_stack.py`
- **Usage:** 
  - `--quick` for local status
  - `--audit` for full remote check
- **Outputs:** `logs/crypto_stack_status.json`

### Gibson Connection

- **VPN IP:** 10.144.118.159 (use `gibson-vpn` alias)
- **Local IP:** 192.168.100.238 (not reachable from gateway)
- **SSH User:** gibz
- **SSH Key:** `~/.ssh/id_rsa_gibson`

---

## Business Intelligence

- **Phone Signup Blueprint:** `docs/BUSINE` (incomplete reference)
