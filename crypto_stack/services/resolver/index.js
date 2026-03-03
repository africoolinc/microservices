/**
 * .crypto Domain Resolution Service (Standalone Server)
 * Provides both resolution logic and HTTP API
 */

const express = require('express');
const cors = require('cors');
const { ethers } = require('ethers');

const app = express();
const PORT = process.env.PORT || 3000;

// Configuration
const REGISTRY_ADDRESS = process.env.REGISTRY_ADDRESS || '0xD1E5b0FF1287aA9f9A268759062E4Ab08b9Dacbe';
const ETH_RPC_URL = process.env.ETH_RPC_URL || 'https://eth-mainnet.g.alchemy.com/v2/demo';

// ABI fragments
const REGISTRY_ABI = [
  "function resolverOf(uint256 tokenId) view returns (address)"
];

const RESOLVER_ABI = [
  "function addr(bytes32 node) view returns (address)",
  "function contenthash(bytes32 node) view returns (bytes)",
  "function name(bytes32 node) view returns (string)"
];

// Initialize provider and contract
const provider = new ethers.JsonRpcProvider(ETH_RPC_URL);
const registry = new ethers.Contract(REGISTRY_ADDRESS, REGISTRY_ABI, provider);

// Cache
const cache = new Map();
const CACHE_TTL = parseInt(process.env.CACHE_TTL) || 300;

// Middleware
app.use(cors());
app.use(express.json());

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

// Resolve domain
async function resolveDomain(domain) {
  // Check cache
  const cached = cache.get(domain);
  if (cached && Date.now() - cached.timestamp < CACHE_TTL * 1000) {
    return cached;
  }

  const tokenId = namehash(domain);
  const resolverAddress = await registry.resolverOf(tokenId);
  
  let aRecord = null;
  let contentHash = null;

  if (resolverAddress !== ethers.ZeroAddress) {
    const resolver = new ethers.Contract(resolverAddress, RESOLVER_ABI, provider);
    try {
      aRecord = await resolver.addr(tokenId);
    } catch (e) {}
    try {
      contentHash = await resolver.contenthash(tokenId);
    } catch (e) {}
  }

  const result = {
    domain,
    tokenId,
    resolver: resolverAddress,
    records: {
      A: aRecord && aRecord !== ethers.ZeroAddress ? [aRecord] : [],
      contenthash: contentHash || null
    },
    timestamp: Date.now()
  };

  cache.set(domain, result);
  return result;
}

// Routes
app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'crypto-resolver' });
});

app.get('/resolve', async (req, res) => {
  const { domain } = req.query;
  if (!domain) {
    return res.status(400).json({ error: 'Missing domain parameter' });
  }
  
  try {
    const result = await resolveDomain(domain);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`🚀 Crypto Resolver running on port ${PORT}`);
  console.log(`📡 Registry: ${REGISTRY_ADDRESS}`);
});
