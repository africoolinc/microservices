/**
 * .crypto Domain Resolution Service
 * Provides REST API for resolving .crypto domains via Ethereum
 */

const express = require('express');
const cors = require('cors');
const { ethers } = require('ethers');
const Redis = require('ioredis');

const app = express();
const PORT = process.env.PORT || 3000;

// Configuration
const REGISTRY_ADDRESS = process.env.REGISTRY_ADDRESS || '0xD1E5b0FF1287aA9f9A268759062E4Ab08b9Dacbe';
const ETH_RPC_URL = process.env.ETH_RPC_URL || 'https://eth.llamarpc.com';
const CACHE_TTL = parseInt(process.env.CACHE_TTL) || 300;

// ABI fragments
const REGISTRY_ABI = [
  "function resolverOf(uint256 tokenId) view returns (address)",
  "function ownerOf(uint256 tokenId) view returns (address)"
];

const RESOLVER_ABI = [
  "function addr(bytes32 node) view returns (address)",
  "function contenthash(bytes32 node) view returns (bytes)",
  "function name(bytes32 node) view returns (string)",
  "function text(bytes32 node, string calldata key) view returns (string)"
];

// Initialize provider
const provider = new ethers.JsonRpcProvider(ETH_RPC_URL);
const registry = new ethers.Contract(REGISTRY_ADDRESS, REGISTRY_ABI, provider);

// Initialize Redis if available
let redis = null;
try {
  redis = new Redis(process.env.REDIS_URL || 'redis://cache:6379', {
    lazyConnect: true,
    maxRetriesPerRequest: 1
  });
  redis.on('error', (err) => {
    console.log('Redis not available, using in-memory cache');
    redis = null;
  });
} catch (e) {
  console.log('Redis not configured, using in-memory cache');
}

// In-memory cache fallback
const memoryCache = new Map();
const CACHE_CLEANUP_INTERVAL = 60000;

setInterval(() => {
  const now = Date.now();
  for (const [key, value] of memoryCache.entries()) {
    if (now > value.expires) {
      memoryCache.delete(key);
    }
  }
}, CACHE_CLEANUP_INTERVAL);

// Cached resolution
async function getCachedResolution(domain) {
  const cacheKey = `crypto:resolution:${domain}`;
  
  // Try Redis first
  if (redis) {
    try {
      const cached = await redis.get(cacheKey);
      if (cached) {
        return JSON.parse(cached);
      }
    } catch (e) {}
  }
  
  // Fallback to memory
  const cached = memoryCache.get(domain);
  if (cached && Date.now() < cached.expires) {
    return cached.data;
  }
  
  return null;
}

// Cache resolution
async function cacheResolution(domain, data) {
  const cacheKey = `crypto:resolution:${domain}`;
  const expires = Date.now() + CACHE_TTL * 1000;
  
  if (redis) {
    try {
      await redis.setex(cacheKey, CACHE_TTL, JSON.stringify(data));
    } catch (e) {}
  }
  
  memoryCache.set(domain, { data, expires });
}

// Standard ENS namehash
function namehash(domain) {
  let node = '0x0000000000000000000000000000000000000000000000000000000000000000';
  const labels = domain.split('.').reverse();

  for (const label of labels) {
    const labelHash = ethers.keccak256(ethers.toUtf8Bytes(label));
    node = ethers.keccak256(Buffer.concat([
      Buffer.from(node.slice(2), 'hex'),
      Buffer.from(labelHash.slice(2), 'hex')
    ]));
  }
  return node;
}

// Resolve domain from blockchain
async function resolveDomain(domain) {
  // Check cache first
  const cached = await getCachedResolution(domain);
  if (cached) {
    return { ...cached, cached: true };
  }

  const tokenId = namehash(domain);
  
  let resolverAddress, owner;
  try {
    resolverAddress = await registry.resolverOf(tokenId);
  } catch (e) {
    resolverAddress = ethers.ZeroAddress;
  }
  
  try {
    owner = await registry.ownerOf(tokenId);
  } catch (e) {
    owner = null;
  }

  const result = {
    domain,
    tokenId,
    owner,
    resolver: resolverAddress,
    records: {},
    timestamp: Date.now()
  };

  // If resolver exists, query it
  if (resolverAddress && resolverAddress !== ethers.ZeroAddress) {
    const resolver = new ethers.Contract(resolverAddress, RESOLVER_ABI, provider);
    
    // Try to get ETH address
    try {
      const ethAddress = await resolver.addr(tokenId);
      if (ethAddress && ethAddress !== ethers.ZeroAddress) {
        result.records.A = [ethAddress];
      }
    } catch (e) {}

    // Try to get contenthash
    try {
      const contentHash = await resolver.contenthash(tokenId);
      if (contentHash && contentHash !== '0x') {
        result.records.contenthash = contentHash;
      }
    } catch (e) {}

    // Try to get name
    try {
      const name = await resolver.name(tokenId);
      if (name) {
        result.records.name = name;
      }
    } catch (e) {}

    // Try common text records
    const textKeys = ['email', 'url', 'avatar', 'description', 'notice', 'keywords', 'com.twitter', 'com.github'];
    for (const key of textKeys) {
      try {
        const value = await resolver.text(tokenId, key);
        if (value) {
          result.records[key] = value;
        }
      } catch (e) {}
    }
  }

  // Cache the result
  await cacheResolution(domain, result);
  
  return { ...result, cached: false };
}

// Middleware
app.use(cors());
app.use(express.json());

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    service: 'crypto-resolver',
    registry: REGISTRY_ADDRESS,
    ethRpc: ETH_RPC_URL,
    cache: redis ? 'redis' : 'memory'
  });
});

// Main resolution endpoint
app.get('/resolve', async (req, res) => {
  const { domain } = req.query;
  
  if (!domain) {
    return res.status(400).json({ error: 'Missing domain parameter' });
  }
  
  if (!domain.endsWith('.crypto')) {
    return res.status(400).json({ error: 'Only .crypto domains are supported' });
  }
  
  try {
    const result = await resolveDomain(domain);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// API endpoint (for nginx)
app.get('/api/resolve/:domain', async (req, res) => {
  const { domain } = req.params;
  
  try {
    const result = await resolveDomain(domain);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Cache management
app.post('/cache/clear', async (req, res) => {
  const { domain } = req.body;
  
  if (domain) {
    // Clear specific domain
    const cacheKey = `crypto:resolution:${domain}`;
    if (redis) {
      await redis.del(cacheKey);
    }
    memoryCache.delete(domain);
    res.json({ cleared: domain });
  } else {
    // Clear all
    if (redis) {
      await redis.flushdb();
    }
    memoryCache.clear();
    res.json({ cleared: 'all' });
  }
});

// Metrics endpoint
app.get('/metrics', (req, res) => {
  res.set('Content-Type', 'text/plain');
  res.send(`
# HELP crypto_resolutions_total Total resolution requests
# TYPE crypto_resolutions_total counter
crypto_resolutions_total 0

# HELP crypto_cache_hits_total Total cache hits
# TYPE crypto_cache_hits_total counter
crypto_resolutions_total 0
  `);
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`🚀 Crypto Resolver running on port ${PORT}`);
  console.log(`📡 Registry: ${REGISTRY_ADDRESS}`);
  console.log(`🔗 ETH RPC: ${ETH_RPC_URL}`);
  console.log(`💾 Cache: ${redis ? 'Redis' : 'In-Memory'}`);
});

module.exports = app;
