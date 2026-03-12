/**
 * .crypto Domain Resolution API
 * REST API gateway for resolving .crypto domains
 */

const express = require('express');
const cors = require('cors');
const { ethers } = require('ethers');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

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

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    service: '.crypto Resolver API',
    version: '1.0.0',
    timestamp: new Date().toISOString()
  });
});

// Resolve domain endpoint
app.get('/api/resolve', async (req, res) => {
  const { domain, type } = req.query;

  if (!domain) {
    return res.status(400).json({ error: 'Missing domain parameter' });
  }

  if (!domain.endsWith('.crypto')) {
    return res.status(400).json({ error: 'Only .crypto domains are supported' });
  }

  try {
    const tokenId = namehash(domain);
    
    // Get resolver address
    const resolverAddress = await registry.resolverOf(tokenId);
    
    if (resolverAddress === ethers.ZeroAddress) {
      return res.json({
        domain,
        error: 'No resolver set',
        records: {}
      });
    }

    // Query resolver
    const resolver = new ethers.Contract(resolverAddress, RESOLVER_ABI, provider);
    
    let aRecord = null;
    let contentHash = null;

    try {
      aRecord = await resolver.addr(tokenId);
    } catch (e) {}

    try {
      contentHash = await resolver.contenthash(tokenId);
    } catch (e) {}

    const response = {
      domain,
      tokenId,
      resolver: resolverAddress,
      records: {
        A: aRecord && aRecord !== ethers.ZeroAddress ? [aRecord] : [],
        contenthash: contentHash || null
      },
      timestamp: new Date().toISOString()
    };

    res.json(response);

  } catch (error) {
    console.error(`Resolution error:`, error);
    res.status(500).json({ 
      error: error.message,
      domain 
    });
  }
});

// Get domain info
app.get('/api/domain/:name', async (req, res) => {
  const { name } = req.params;
  
  try {
    const domain = name.includes('.crypto') ? name : `${name}.crypto`;
    const tokenId = namehash(domain);
    const resolverAddress = await registry.resolverOf(tokenId);
    
    res.json({
      domain,
      tokenId,
      hasResolver: resolverAddress !== ethers.ZeroAddress,
      resolver: resolverAddress
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 .crypto Resolver API running on port ${PORT}`);
  console.log(`📡 Ethereum RPC: ${ETH_RPC_URL}`);
  console.log(`📋 Registry: ${REGISTRY_ADDRESS}`);
});
