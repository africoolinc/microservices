/**
 * .crypto Blockchain Listener Service
 * Monitors the .crypto registry contract for domain events
 * Contract: 0xD1E5b0FF1287aA9f9A268759062E4Ab08b9Dacbe
 */

const { ethers } = require('ethers');
const Redis = require('ioredis');
const winston = require('winston');

// Logger configuration
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console()
  ]
});

// Registry ABI - minimal interface for event listening
const REGISTRY_ABI = [
  "event NewURI(uint256 indexed tokenId, string uri)",
  "event NewURIPrefix(string prefix)",
  "event Resolve(uint256 indexed tokenId, address indexed to)",
  "event Sync(address indexed resolver, uint256 indexed updateId, uint256 indexed tokenId)",
  "function resolverOf(uint256 tokenId) external view returns (address)",
  "function ownerOf(uint256 tokenId) external view returns (address)",
  "function namehash(string calldata domain) external view returns (bytes32)"
];

// Configuration
const CONFIG = {
  registryAddress: process.env.REGISTRY_ADDRESS || '0xD1E5b0FF1287aA9f9A268759062E4Ab08b9Dacbe',
  ethRpcUrl: process.env.ETH_RPC_URL || 'https://eth-mainnet.g.alchemy.com/v2/demo',
  redisUrl: process.env.REDIS_URL || 'redis://localhost:6379'
};

class BlockchainListener {
  constructor() {
    this.provider = null;
    this.contract = null;
    this.redis = null;
    this.isRunning = false;
  }

  /**
   * Initialize connections
   */
  async initialize() {
    logger.info('Initializing blockchain listener...', { rpcUrl: CONFIG.ethRpcUrl });
    
    // Connect to Ethereum
    this.provider = new ethers.providers.JsonRpcProvider(CONFIG.ethRpcUrl);
    
    // Create contract instance
    this.contract = new ethers.Contract(
      CONFIG.registryAddress,
      REGISTRY_ABI,
      this.provider
    );
    
    // Connect to Redis
    this.redis = new Redis(CONFIG.redisUrl, {
      retryStrategy: (times) => Math.min(times * 50, 2000)
    });
    
    logger.info('Blockchain listener initialized', {
      registry: CONFIG.registryAddress,
      network: (await this.provider.getNetwork()).chainId
    });
  }

  /**
   * Compute namehash for .crypto domain
   * @param {string} domain - e.g., "mamaduka.crypto"
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
   * Convert namehash to token ID (bigint)
   */
  namehashToTokenId(namehash) {
    return ethers.BigNumber.from(namehash);
  }

  /**
   * Handle Sync event - resolver changed
   */
  async handleSync(event) {
    const { resolver, updateId, tokenId } = event.returnValues;
    logger.info('Sync event received', { resolver, updateId, tokenId: tokenId.toString() });
    
    // Invalidate cache for this token
    await this.redis.del(`resolver:${tokenId}`);
    await this.redis.publish('domain:update', JSON.stringify({ tokenId: tokenId.toString(), resolver }));
  }

  /**
   * Handle Resolve event - domain resolved to address
   */
  async handleResolve(event) {
    const { tokenId, to } = event.returnValues;
    logger.info('Resolve event received', { tokenId: tokenId.toString(), to });
    
    // Cache resolution
    await this.redis.set(`resolve:${tokenId}`, to, 'EX', 3600);
    await this.redis.publish('domain:resolve', JSON.stringify({ tokenId: tokenId.toString(), to }));
  }

  /**
   * Handle NewURI event - domain metadata updated
   */
  async handleNewURI(event) {
    const { tokenId, uri } = event.returnValues;
    logger.info('NewURI event received', { tokenId: tokenId.toString(), uri });
    
    // Store URI
    await this.redis.set(`uri:${tokenId}`, uri, 'EX', 86400);
  }

  /**
   * Start listening to events
   */
  async startListening() {
    if (this.isRunning) {
      logger.warn('Listener already running');
      return;
    }

    this.isRunning = true;
    logger.info('Starting blockchain event listener...');

    // Subscribe to Sync events (most important for DNS resolution)
    this.contract.on('Sync', (resolver, updateId, tokenId, event) => {
      this.handleSync({ returnValues: { resolver, updateId, tokenId } });
    });

    // Subscribe to Resolve events
    this.contract.on('Resolve', (tokenId, to, event) => {
      this.handleResolve({ returnValues: { tokenId, to } });
    });

    // Subscribe to NewURI events
    this.contract.on('NewURI', (tokenId, uri, event) => {
      this.handleNewURI({ returnValues: { tokenId, uri } });
    });

    logger.info('Blockchain listener started, listening for events...');
  }

  /**
   * Query resolver address for a domain
   */
  async getResolver(domain) {
    const hash = this.namehash(domain);
    const tokenId = this.namehashToTokenId(hash);
    
    try {
      const resolver = await this.contract.resolverOf(tokenId);
      await this.redis.set(`resolver:${tokenId}`, resolver, 'EX', 3600);
      return resolver;
    } catch (error) {
      logger.error('Failed to get resolver', { domain, error: error.message });
      return null;
    }
  }

  /**
   * Query owner of a domain
   */
  async getOwner(domain) {
    const hash = this.namehash(domain);
    const tokenId = this.namehashToTokenId(hash);
    
    try {
      const owner = await this.contract.ownerOf(tokenId);
      return owner;
    } catch (error) {
      logger.error('Failed to get owner', { domain, error: error.message });
      return null;
    }
  }

  /**
   * Health check
   */
  async healthCheck() {
    const network = await this.provider.getNetwork();
    const blockNumber = await this.provider.getBlockNumber();
    
    return {
      status: 'healthy',
      network: network.chainId,
      blockNumber,
      registry: CONFIG.registryAddress
    };
  }
}

// Export for use in other modules
module.exports = BlockchainListener;

// Run if executed directly
if (require.main === module) {
  const listener = new BlockchainListener();
  
  listener.initialize()
    .then(() => listener.startListening())
    .catch(err => {
      logger.error('Failed to start listener', { error: err.message });
      process.exit(1);
    });

  process.on('SIGINT', () => {
    logger.info('Shutting down...');
    process.exit(0);
  });
}
