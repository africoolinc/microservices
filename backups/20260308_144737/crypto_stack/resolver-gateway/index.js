const Web3 = require('web3');
const Redis = require('ioredis');
const express = require('express');
const crypto = require('crypto');

// Configuration
const REGISTRY_ADDRESS = process.env.REGISTRY_ADDRESS || '0xD1E5b0FF1287aA9f9A268759062E4Ab08b9Dacbe';
const ETHEREUM_RPC_URL = process.env.ETHEREUM_RPC_URL || 'https://mainnet.infura.io/v3/YOUR_INFURA_KEY';
const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';
const CACHE_TTL = parseInt(process.env.CACHE_TTL || '300');

// .crypto Registry ABI
const REGISTRY_ABI = [
  {
    "constant": true,
    "inputs": [{ "name": "tokenId", "type": "uint256" }],
    "name": "resolverOf",
    "outputs": [{ "name": "", "type": "address" }],
    "type": "function"
  },
  {
    "constant": true,
    "inputs": [{ "name": "tokenId", "type": "uint256" }],
    "name": "ownerOf",
    "outputs": [{ "name": "owner", "type": "address" }],
    "type": "function"
  },
  {
    "constant": true,
    "inputs": [{ "name": "tokenId", "type": "uint256" }],
    "name": "tokenURI",
    "outputs": [{ "name": "", "type": "string" }],
    "type": "function"
  }
];

// Resolver ABI for DNS records
const RESOLVER_ABI = [
  {
    "constant": true,
    "inputs": [{ "name": "node", "type": "bytes32" }, { "name": "coinType", "type": "uint256" }],
    "name": "addr",
    "outputs": [{ "name": "", "type": "bytes" }],
    "type": "function"
  },
  {
    "constant": true,
    "inputs": [{ "name": "node", "type": "bytes32" }, { "name": "key", "type": "string" }],
    "name": "getText",
    "outputs": [{ "name": "", "type": "string" }],
    "type": "function"
  },
  {
    "constant": true,
    "inputs": [{ "name": "node", "type": "bytes32" }, { "name": "key", "type": "string" }],
    "name": "get",
    "outputs": [{ "name": "", "type": "bytes" }],
    "type": "function"
  }
];

// Coin types for different blockchains
const COIN_TYPES = {
  ETH: 60,
  BTC: 0,
  LTC: 2,
  DOGE: 3,
  DOT: 354,
  MATIC: 966,
  SOL: 501
};

class CryptoDomainResolver {
  constructor() {
    this.web3 = new Web3(ETHEREUM_RPC_URL);
    this.redis = new Redis(REDIS_URL);
    this.registry = new this.web3.eth.Contract(REGISTRY_ABI, REGISTRY_ADDRESS);
  }

  // Calculate namehash for .crypto domains
  namehash(domain) {
    let node = '0x0000000000000000000000000000000000000000000000000000000000000000';
    const labels = domain.split('.').reverse();
    
    for (const label of labels) {
      const labelHash = this.web3.utils.sha3(label);
      node = this.web3.utils.sha3(node + labelHash.slice(2), { encoding: 'hex' });
    }
    return node;
  }

  // Convert domain to tokenId
  domainToTokenId(domain) {
    const hash = this.web3.utils.sha3(domain);
    return this.web3.utils.toBN(hash).toString();
  }

  async getResolverAddress(tokenId) {
    const cacheKey = `resolver:${tokenId}`;
    const cached = await this.redis.get(cacheKey);
    if (cached) return cached;
    
    const resolver = await this.registry.methods.resolverOf(tokenId).call();
    await this.redis.setex(cacheKey, 3600, resolver);
    return resolver;
  }

  async resolveDomain(domain) {
    // Check cache first
    const cacheKey = `resolution:${domain}`;
    const cached = await this.redis.get(cacheKey);
    if (cached) {
      return JSON.parse(cached);
    }

    const tokenId = this.domainToTokenId(domain);
    const resolverAddress = await this.getResolverAddress(tokenId);
    
    // If no resolver, domain might not exist
    if (resolverAddress === '0x0000000000000000000000000000000000000000') {
      return { error: 'Domain not found', domain };
    }

    // Create resolver contract instance
    const resolver = new this.web3.eth.Contract(RESOLVER_ABI, resolverAddress);
    const node = this.namehash(domain);
    
    const records = {
      domain,
      tokenId,
      resolver: resolverAddress,
      owner: await this.registry.methods.ownerOf(tokenId).call().catch(() => null),
      records: {}
    };

    // Fetch different record types
    try {
      // ETH address
      const ethAddr = await resolver.methods.addr(node, COIN_TYPES.ETH).call();
      if (ethAddr && ethAddr !== '0x') {
        records.records.ETH = ethAddr;
      }
    } catch (e) {}

    try {
      // BTC address
      const btcAddr = await resolver.methods.addr(node, COIN_TYPES.BTC).call();
      if (btcAddr && btcAddr !== '0x') {
        records.records.BTC = this.decodeBase58Address(btcAddr);
      }
    } catch (e) {}

    try {
      // URL/website
      const url = await resolver.methods.getText(node, 'url').call();
      if (url) {
        records.records.url = url;
      }
    } catch (e) {}

    try {
      // Email
      const email = await resolver.methods.getText(node, 'email').call();
      if (email) {
        records.records.email = email;
      }
    } catch (e) {}

    try {
      // Avatar
      const avatar = await resolver.methods.getText(node, 'avatar').call();
      if (avatar) {
        records.records.avatar = avatar;
      }
    } catch (e) {}

    // Cache result
    await this.redis.setex(cacheKey, CACHE_TTL, JSON.stringify(records));
    
    return records;
  }

  decodeBase58Address(hexBytes) {
    // Simple base58 decoding for BTC addresses
    try {
      const bytes = Buffer.from(hexBytes.slice(2), 'hex');
      // This is simplified - production would use proper base58
      return '0x' + bytes.slice(1).toString('hex');
    } catch (e) {
      return hexBytes;
    }
  }
}

// Express API
const app = express();
const resolver = new CryptoDomainResolver();

app.use(express.json());

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'crypto-resolver-gateway' });
});

// Resolve domain
app.get('/resolve/:domain', async (req, res) => {
  try {
    const { domain } = req.params;
    if (!domain.endsWith('.crypto')) {
      return res.status(400).json({ error: 'Not a .crypto domain' });
    }
    const result = await resolver.resolveDomain(domain);
    res.json(result);
  } catch (error) {
    console.error('Resolution error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get resolver address
app.get('/resolver/:tokenId', async (req, res) => {
  try {
    const { tokenId } = req.params;
    const resolverAddress = await resolver.getResolverAddress(tokenId);
    res.json({ tokenId, resolver: resolverAddress });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Invalidate cache
app.delete('/cache/:domain', async (req, res) => {
  try {
    const { domain } = req.params;
    await resolver.redis.del(`resolution:${domain}`);
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
  console.log(`Crypto Resolver Gateway running on port ${PORT}`);
});

module.exports = { CryptoDomainResolver, app };
