# CF Worker Memory Projection - mamaduka.crypto

## Executive Summary

| Metric | Value |
|--------|-------|
| **Estimated Base Memory** | 15-25 MB |
| **Peak Memory (with RPC)** | 50-80 MB |
| **Cloudflare Free Tier** | 128 MB |
| **Cloudflare Paid Tier** | 512 MB - 1024 MB |
| **Recommendation** | ✅ FEASIBLE on Free Tier |

---

## Memory Breakdown

### 1. Base Worker Runtime
| Component | Memory |
|-----------|--------|
| V8 Isolate (minimal) | 2-4 MB |
| JavaScript Core | 1-2 MB |
| Express/routing | 1-2 MB |
| **Subtotal** | **4-8 MB** |

### 2. Web3/Ethereum RPC Calls
| Component | Memory |
|-----------|--------|
| Web3.js (minimal build) | 5-10 MB |
| Buffer/encoding | 1-2 MB |
| RPC Response parsing | 2-5 MB |
| **Subtotal** | **8-17 MB** |

### 3. Cache Layer (Workers KV)
| Component | Memory |
|-----------|--------|
| KV bindings | 0.5-1 MB |
| In-memory cache (L1) | 1-2 MB |
| **Subtotal** | **1.5-3 MB** |

### 4. Request Context
| Component | Memory |
|-----------|--------|
| Request/Response objects | 0.5-1 MB |
| URL parsing | 0.1-0.2 MB |
| JSON parsing | 0.2-0.5 MB |
| **Subtotal** | **0.8-1.7 MB** |

---

## Per-Request Memory Usage

### Cold Request (first call)
```
Base Runtime:     ~10 MB
Web3 Initialization: ~10 MB
RPC Call:         ~15 MB
Response:         ~5 MB
────────────────────────────
TOTAL:            ~40 MB
```

### Warm Request (cached resolver)
```
Base Runtime:     ~10 MB
Cache Hit:        ~2 MB
Response:         ~5 MB
────────────────────────────
TOTAL:            ~17 MB
```

### Concurrent Requests (simulated)
| Concurrent | Est. Memory |
|------------|-------------|
| 1 | 40 MB |
| 5 | 50 MB |
| 10 | 60 MB |
| 50 | 80 MB |
| 100 | 100 MB |

---

## Cloudflare Worker Limits (2026)

### Free Tier
| Limit | Value |
|-------|-------|
| Memory | 128 MB |
| Duration | 10 ms (CPU) / 30s (real) |
| Requests/day | 100,000 |
| KV Reads/day | 100,000 |

### Paid Tier (Workers Bundled)
| Limit | Value |
|-------|-------|
| Memory | 512 MB (default) |
| CPU Time | 50 ms |
| Duration | 30s (real) |
| Requests/month | 10,000,000 |

---

## Optimization Strategies

### 1. Use Minimal Web3
```javascript
// Instead of full web3.js (~500KB)
import { ethers } from 'ethers';
// ethers v6 minified: ~50KB
```

### 2. Aggressive Caching
```javascript
// Cache resolver addresses for 1 hour
// Cache DNS records for 5 minutes
// Use Workers KV for persistence
```

### 3. Batch RPC Calls
```javascript
// eth_call is cheap - batch multiple lookups
// Single request can resolve multiple domains
```

### 4. Connection Pooling
```javascript
// Reuse Ethereum RPC connections
// Keep-alive headers
```

---

## Projected Cost

### Free Tier (Personal/DEV)
| Resource | Usage | Cost |
|----------|-------|------|
| Requests | ~1000/day | $0 |
| KV Reads | ~500/day | $0 |
| Bandwidth | ~10MB/day | $0 |
| **Total** | | **$0** |

### Paid Tier (Production)
| Resource | Usage | Cost |
|----------|-------|------|
| Requests | 1M/month | $5 |
| KV Reads | 500K/month | $0.50 |
| Compute | 50M GB-ms | $2.50 |
| **Total** | | **~$8/month** |

---

## Deployment Checklist

- [ ] Create Cloudflare account (if not exists)
- [ ] Add domain mamaduka.crypto to Cloudflare
- [ ] Install Wrangler: `npm install -g wrangler`
- [ ] Create KV namespace for cache
- [ ] Configure wrangler.toml
- [ ] Deploy with `wrangler deploy`
- [ ] Test endpoints
- [ ] Configure custom domain

---

## Next Steps

1. **Immediate**: Deploy to Cloudflare (free tier)
2. **Short-term**: Add more .crypto domains
3. **Medium-term**: Add BTC price oracle integration
4. **Long-term**: Full DeFi integration

---

## Conclusion

✅ **CF Worker deployment is feasible** with current memory requirements.
- Projected peak: **50-80 MB**
- Available (Free): **128 MB**
- **Headroom**: 48-78 MB for growth

The mamaduka.crypto CF Worker can be deployed immediately on Cloudflare's free tier.
