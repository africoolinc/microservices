/**
 * DNS Resolver Gateway
 * Resolves .crypto domains via blockchain queries
 * Exposes REST API only
 */

const { ethers } = require('ethers');
const Redis = require('ioredis');
const express = require('express');
require('dotenv').config();

const REGISTRY_ADDRESS = process.env.REGISTRY_ADDRESS || '0xD1E5b0FF1287aA9f9A268759062E4Ab08b9Dacbe';

// Minimal ABI for resolution
const REGISTRY_ABI = [
  "function resolverOf(uint256 tokenId) external view returns (address)",
  "function uri(uint256 tokenId) external view returns (string memory)"
];

class CryptoDNSResolver {
  constructor() {
    this.provider = new ethers.JsonRpcProvider(process.env.ETH_RPC_URL);
    this.registry = new ethers.Contract(REGISTRY_ADDRESS, REGISTRY_ABI, this.provider);
    this.redis = new Redis(process.env.REDIS_URL || 'redis://redis:6379');
  }

  // Convert domain to tokenId (labelhash)
  labelhash(label) {
    return ethers.keccak256(ethers.toUtf8Bytes(label));
  }

  async resolveDomain(domain) {
    // Check cache first
    const cached = await this.redis.get(`crypto:resolution:${domain}`);
    if (cached) {
      console.log(`📦 Cache hit for ${domain}`);
      return JSON.parse(cached);
    }

    console.log(`🔍 Resolving ${domain}...`);

    try {
      const labels = domain.split('.');
      
      // Only handle .crypto TLD
      if (labels[labels.length - 1] !== 'crypto') {
        return null;
      }

      // Calculate tokenId from domain name
      const tokenId = this.labelhash(labels[0]);
      
      // Get resolver address
      const resolverAddress = await this.registry.resolverOf(tokenId);
      
      if (resolverAddress === ethers.ZeroAddress) {
        console.log(`   ❌ No resolver for ${domain}`);
        return null;
      }

      const result = {
        domain,
        tokenId,
        resolver: resolverAddress,
        blockchain: 'ethereum',
        timestamp: Date.now()
      };

      // Cache for 5 minutes
      await this.redis.set(
        `crypto:resolution:${domain}`,
        JSON.stringify(result),
        'EX', 
        300
      );

      console.log(`   ✅ Resolved: ${resolverAddress}`);
      return result;

    } catch (error) {
      console.error(`   ❌ Error resolving ${domain}:`, error.message);
      return { error: error.message };
    }
  }
}

// Express REST API
function createRESTAPI(resolver) {
  const app = express();
  
  app.get('/resolve/:domain', async (req, res) => {
    const { domain } = req.params;
    const result = await resolver.resolveDomain(domain);
    res.json(result);
  });

  app.get('/health', (req, res) => {
    res.json({ status: 'ok', service: 'crypto-dns-resolver' });
  });

  return app;
}

// Start services
async function main() {
  console.log('🧊 Starting Crypto DNS Resolver...');
  
  const resolver = new CryptoDNSResolver();
  
  // Test connection
  try {
    const block = await resolver.provider.getBlockNumber();
    console.log(`   ✅ Connected to Ethereum (block: ${block})`);
  } catch (error) {
    console.log(`   ⚠️  Ethereum connection failed: ${error.message}`);
  }

  // Start REST API
  const app = createRESTAPI(resolver);
  const port = process.env.PORT || 3000;
  
  app.listen(port, () => {
    console.log(`   ✅ REST API listening on port ${port}`);
  });

  // Test resolution
  console.log('\n🧪 Testing resolution...');
  const testResult = await resolver.resolveDomain('mamaduka.crypto');
  console.log('   Result:', testResult);
}

if (require.main === module) {
  main().catch(console.error);
}

moduleDNSResolver, create.exports = { CryptoRESTAPI };
