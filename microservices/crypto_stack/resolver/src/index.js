/**
 * .crypto Resolver Gateway
 * Resolves .crypto domains to DNS records via blockchain
 */

const { ethers } = require('ethers');
const Redis = require('ioredis');
const express = require('express');
const cors = require('cors');
const winston = require('winston');

// Logger
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [new winston.transports.Console()]
});

// Registry & Resolver ABIs
const REGISTRY_ABI = [
  "function resolverOf(uint256 tokenId) external view returns (address)",
  "function ownerOf(uint256 tokenId) external view returns (address)"
];

const RESOLVER_ABI = [
  "function addr(bytes32 node) external view returns (address)",
  "function setAddr(bytes32 node, address addr) external",
  "function dnsRecord(bytes32 node, bytes32 name, uint16 resource) external view returns (bytes)",
  "function dnsRecord(bytes32 node, bytes32 name, uint16 resource, uint64 cache) external view returns (bytes)"
];

// Configuration
const CONFIG = {
  registryAddress: process.env.REGISTRY_ADDRESS || '0xD1E5b0FF1287aA9f9A268759062E4Ab08b9Dacbe',
  ethRpcUrl: process.env.ETH_RPC_URL || 'https://eth-mainnet.g.alchemy.com/v2/demo',
  redisUrl: process.env.RECIS_URL || 'redis://localhost:6379',
  cacheTTL: parseInt(process.env.CACHE_TTL || '300'),
  port: parseInt(process.env.PORT || '8080')
};

class CryptoResolver {
  constructor() {
    this.provider = null;
    this.registry = null;
    this.redis = null;
    this.app = express();
  }

  async initialize() {
    logger.info('Initializing resolver...');

    // Connect to Ethereum
    this.provider = new ethers.providers.JsonRpcProvider(CONFIG.ethRpcUrl);

    // Create registry contract
    this.registry = new ethers.Contract(
      CONFIG.registryAddress,
      REGISTRY_ABI,
      this.provider
    );

    // Redis for caching
    this.redis = new Redis(CONFIG.redisUrl, {
      retryStrategy: (times) => Math.min(times * 50, 2000)
    });

    // Express setup
    this.app.use(cors());
    this.app.use(express.json());

    // Routes
    this.setupRoutes();

    logger.info('Resolver initialized');
  }

  setupRoutes() {
    // Health check
    this.app.get('/health', async (req, res) => {
      res.json({ status: 'ok', service: 'crypto-resolver' });
    });

    // Resolve domain
    this.app.get('/resolve/:domain', async (req, res) => {
      try {
        const { domain } = req.params;
        const result = await this.resolveDomain(domain);
        res.json(result);
      } catch (error) {
        logger.error('Resolution failed', { error: error.message });
        res.status(500).json({ error: error.message });
      }
    });

    // Get owner
    this.app.get('/owner/:domain', async (req, res) => {
      try {
        const { domain } = req.params;
        const owner = await this.getOwner(domain);
        res.json({ domain, owner });
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    // Get resolver
    this.app.get('/resolver/:domain', async (req, res) => {
      try {
        const { domain } = req.params;
        const resolver = await this.getResolverAddress(domain);
        res.json({ domain, resolver });
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    // DNS record query
    this.app.get('/dns/:domain', async (req, res) => {
      try {
        const { domain } = req.params;
        const type = req.query.type || 'A';
        const records = await this.getDNSRecords(domain, type);
        res.json({ domain, type, records });
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });
  }

  /**
   * Compute namehash
   */
  namehash(domain) {
    let node = '0x0000000000000000000000000000000000000000000000000000000000000000';
    const labels = domain.split('.').reverse();

    for (const label of labels) {
      const labelHash = ethers.utils.keccak256(ethers.utils.toUtf8Bytes(label));
      node = ethers.utils.keccak256(Buffer.concat([
        Buffer.from(node.slice(2), 'hex'),
        Buffer.from(labelHash.slice(2), 'hex')
      ]));
    }
    return node;
  }

  /**
   * Get resolver address for domain
   */
  async getResolverAddress(domain) {
    const hash = this.namehash(domain);
    const tokenId = ethers.BigNumber.from(hash);

    // Check cache
    const cached = await this.redis.get(`resolver:${tokenId}`);
    if (cached) return cached;

    const resolver = await this.registry.resolverOf(tokenId);
    await this.redis.set(`resolver:${tokenId}`, resolver, 'EX', CONFIG.cacheTTL);
    return resolver;
  }

  /**
   * Get domain owner
   */
  async getOwner(domain) {
    const hash = this.namehash(domain);
    const tokenId = ethers.BigNumber.from(hash);

    const owner = await this.registry.ownerOf(tokenId);
    return owner;
  }

  /**
   * Get DNS records from resolver
   */
  async getDNSRecords(domain, recordType = 'A') {
    const resolverAddress = await this.getResolverAddress(domain);

    if (resolverAddress === ethers.constants.AddressZero) {
      return { error: 'No resolver set' };
    }

    const resolver = new ethers.Contract(resolverAddress, RESOLVER_ABI, this.provider);
    const node = this.namehash(domain);

    // DNS record type codes
    const recordTypes = { A: 1, AAAA: 28, CNAME: 5, TXT: 16, MX: 15 };
    const resource = recordTypes[recordType] || 1;
    const nameHash = ethers.utils.keccak256(ethers.utils.toUtf8Bytes(recordType.toLowerCase()));

    try {
      const record = await resolver.dnsRecord(node, nameHash, resource);
      return { type: recordType, data: record };
    } catch (error) {
      return { type: recordType, error: 'No record found' };
    }
  }

  /**
   * Full domain resolution
   */
  async resolveDomain(domain) {
    if (!domain.endsWith('.crypto')) {
      throw new Error('Only .crypto domains supported');
    }

    const owner = await this.getOwner(domain);
    const resolverAddress = await this.getResolverAddress(domain);

    // Get common records
    const [aRecord, aaaaRecord, txtRecord] = await Promise.all([
      this.getDNSRecords(domain, 'A'),
      this.getDNSRecords(domain, 'AAAA'),
      this.getDNSRecords(domain, 'TXT')
    ]);

    return {
      domain,
      owner,
      resolver: resolverAddress,
      records: {
        A: aRecord,
        AAAA: aaaaRecord,
        TXT: txtRecord
      },
      resolvedAt: new Date().toISOString()
    };
  }

  /**
   * Start server
   */
  async start() {
    this.app.listen(CONFIG.port, () => {
      logger.info(`Resolver listening on port ${CONFIG.port}`);
    });
  }
}

// Run if executed directly
if (require.main === module) {
  const resolver = new CryptoResolver();
  resolver.initialize()
    .then(() => resolver.start())
    .catch(err => {
      logger.error('Failed to start resolver', { error: err.message });
      process.exit(1);
    });
}

module.exports = CryptoResolver;
