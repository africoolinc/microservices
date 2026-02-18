# Gibson Stack Connection Journal

This journal tracks the health and availability of management channels for the StackForge host (`10.144.118.159`).

## Connection Methodology
1. **Primary:** SSH (Port 22) - Direct management via key-based authentication.
2. **Secondary/OOB:** Cloudflare Tunnel - Web-based terminal and browser SSH.
3. **Emergency:** Physical/Console access.

---

## [2026-02-17T22:48:58.857911] Connectivity Heartbeat
| Component | Status |
|-----------|--------|
| Ping      | UP |
| SSH Port  | CLOSED |
| SSH Auth  | FAILED |
| Cloudflare| UNKNOWN (Not yet deployed) |
| **Preferred** | **Cloudflare Tunnel (OOB)** |
| Health    | 5/10 |

## [2026-02-17T23:28:44.019189] Connectivity Heartbeat
| Component | Status |
|-----------|--------|
| Ping      | UP |
| SSH Port  | OPEN |
| SSH Auth  | SUCCESS |
| Cloudflare| TOKEN_READY & CONNECTED |
| **Preferred** | **SSH** |
| Health    | 10/10 |

---

## 🎯 Task Update: Cloudflare Tunnel RESTORED
The Cloudflare Tunnel has been updated with the new token (`eyJh...`) provided by Gibson. 
- **Method:** Standalone Docker container (`cloudflare`)
- **Status:** Connected to `nbo02` (Nairobi edge)
- **Config:** Version 18 (9 hostnames active)
- **Health:** ✅ Operational fallback established.

---

## [2026-02-17T23:29:52.547594] Connectivity Heartbeat
| Component | Status |
|-----------|--------|
| Ping      | UP |
| SSH Port  | OPEN |
| SSH Auth  | SUCCESS |
| Cloudflare| TOKEN_READY |
| **Preferred** | **SSH** |
| Health    | 10/10 |

## [2026-02-17T23:30:45.442407] Connectivity Heartbeat
| Component | Status |
|-----------|--------|
| Ping      | UP |
| SSH Port  | OPEN |
| SSH Auth  | SUCCESS |
| Cloudflare| TOKEN_READY |
| **Preferred** | **SSH** |
| Health    | 10/10 |
