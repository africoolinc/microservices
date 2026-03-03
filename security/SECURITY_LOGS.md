# 🔥 Firefly Security Logs - Network Scan History

**Last Updated:** March 2, 2026  
**Log Source:** `~/Documents/netscan/logs/`  
**Status:** ✅ Parsed

---

## 📊 Scan History Summary

| Date | Target Network | Hosts Up | Notes |
|------|---------------|----------|-------|
| 2025-09-06 | 192.168.1.1 | 0 | Wrong subnet |
| 2025-10-13 | 192.168.1.1 | 0 | Wrong subnet |
| 2025-10-17 | 192.168.1.1 | 0 | Wrong subnet |
| 2025-10-18 | 192.168.1.1 | 0 | Wrong subnet |
| 2025-10-27 | 192.168.1.1 | 0 | Wrong subnet |
| 2025-10-30 | 192.168.1.1 | 0 | Wrong subnet |
| **2025-11-27** | **192.168.0.1/24** | **1** | ✅ Correct subnet! |
| 2026-01-18 | 192.168.1.1 | 0 | Wrong subnet |
| 2026-01-19 | 192.168.0.1/24 | 0 | No hosts |
| 2026-01-20 | 192.168.1.1 | 0 | Wrong subnet |
| 2026-01-21 | 192.168.1.1 | 0 | Wrong subnet |
| 2026-01-23 | 192.168.1.1 | 0 | Wrong subnet |
| 2026-01-24 | 192.168.1.1 | 0 | Wrong subnet |

---

## ⚠️ CRITICAL FINDING: Wrong Network Range

**The scanner has been targeting the WRONG network!**

- **Default in script:** `192.168.1.1/24`
- **Actual family network:** `192.168.100.0/24`

### Only Successful Scan (2025-11-27):
```
Target: 192.168.0.1/24
Host found: 192.168.0.3
Ports: 80 (closed), 443 (closed)
```

This is likely the router or an old device.

---

## 🔧 Required Fix

Update the netscan02.sh script to use correct network:

```bash
# Current (WRONG):
NETWORK="192.168.1.1/24"

# Should be:
NETWORK="192.168.100.0/24"
TARGET="192.168.100.1"  # Router gateway
```

---

## 📁 Available Log Types

| File Pattern | Count | Status |
|--------------|-------|--------|
| `nmap_target_*.txt.gz` | 16 | Port scans (empty results) |
| `nmap_web_*.xml` | 10 | Web scans (80/443) |
| `nmap_topology_*.txt` | 0 | Missing |
| `msf_vuln_*.txt` | 0 | Missing |
| `packet_dump_*.pcap` | 0 | Missing |

---

## 🎯 Recommended Next Scans

1. **Fix network range** to `192.168.100.0/24`
2. **Run topology scan** to discover all live hosts
3. **Full port scan** on known devices:
   - 192.168.100.1 (Router)
   - 192.168.100.122 (Allan)
   - 192.168.100.238 (Gibson)
   - 192.168.100.182 (Ahie)
   - 192.168.100.224 (V20)

---

## 🛡️ Family Network Assets

| Device | IP | Expected Services |
|--------|-----|-------------------|
| Router | 192.168.100.1 | HTTP, HTTPS, SSH? |
| Allan | 192.168.100.122 | SSH, dev services |
| Gibson | 192.168.100.238 | SSH, Docker |
| Ahie | 192.168.100.182 | OpenClaw, development |
| V20 | 192.168.100.224 | ADB, SSH |

---

## 🚀 Action Items

- [ ] Update netscan02.sh NETWORK to 192.168.100.0/24
- [ ] Re-run network topology scan
- [ ] Scan all known family devices
- [ ] Set up periodic scans (weekly)
- [ ] Enable Metasploit vulnerability checks

---
