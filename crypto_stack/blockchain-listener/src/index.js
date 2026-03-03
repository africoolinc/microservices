/**
 * Blockchain Listener Service
 * Monitors .crypto registry events on Ethereum mainnet
 * Contract: 0xD1E5b0FF1287aA9f9A268759062E4Ab08b9Dacbe
 */

const { ethers } = require('ethers');
const Redis = require('ioredis');
require('dotenv').config();

// Registry ABI (minimal for event listening)
const REGISTRY_ABI = [
  "event Resolve(uint256 indexed tokenId, address indexed to)",
  "event Sync(address indexed resolver, uint256 indexed updateId, uint256 indexed tokenId)",
  "event NewURI(uint256 indexed tokenId, string uri)",
  "function resolverOf(uint256 tokenId) external view returns (address)",
  "function uri(uint256 tokenId) external view returns (string)"
];

// Resolver ABI (for getting DNS records)
const RESOLVER_ABI = [
  "function resolve(bytes calldata name, bytes calldata data) external view returns (bytes)",
  "function resolveForContract(bytes calldata name) external view returns (address)"
];

const REGISTRY_ADDRESS = process.env.REGISTRY_ADDRESS || '0xD1E5b0FF1287aA9f9A268759062E4Ab08b9Dacbe';

class BlockchainListener {
  constructor() {
    this.provider = new ethers.JsonRpcProvider(process.env.ETH_RPC_URL);
    this.registry = new ethers.Contract(REGISTRY_ADDRESS, REGISTRY_ABI, this.provider);
    this.redis = new Redis(process.env.REDIS_URL || 'redis://redis:6379');
    this.isRunning = false;
  }

  async start() {
    console.log('🔗 Starting Blockchain Listener for .crypto domains...');
    console.log(`   Registry: ${REGISTRY_ADDRESS}`);
    console.log(`   RPC: ${process.env.ETH_RPC_URL}`);

    // Listen for Sync events
    this.registry.on('Sync', async (resolver, updateId, tokenId, event) => {
      console.log(`📡 Sync event: tokenId=${tokenId}, resolver=${resolver}`);
      await this.handleSync(resolver, updateId, tokenId);
    });

    // Listen for Resolve events  
    this.registry.on('Resolve', async (tokenId, to, event) => {
      console.log(`📡 Resolve event: tokenId=${tokenId}, to=${to}`);
      await this.handleResolve(tokenId, to);
    });

    // Listen for NewURI events
    this.registry.on('NewURI', async (tokenId, uri, event) => {
      console.log(`📡 NewURI event: tokenId=${tokenId}, uri=${uri}`);
      await this.handleNewURI(tokenId, uri);
    });

    this.isRunning = true;
    console.log('✅ Blockchain Listener running');

    // Initial sync - get recent events
    await this.initialSync();
  }

  async handleSync(resolver, updateId, tokenId) {
    try {
      // Cache resolver address
      await this.redis.hset('crypto:resolvers', tokenId.toString(), resolver);
      
      // Invalidate cache for this domain
      const domain = await this.getDomainFromTokenId(tokenId);
      if (domain) {
        await this.redis.del(`crypto:domain:${domain}`);
        console.log(`   🔄 Cache invalidated for: ${domain}`);
      }
    } catch (error) {
      console.error('Error handling Sync event:', error);
    }
  }

  async handleResolve(tokenId, to) {
    try {
      // Store resolution
      await this.redis.hset('crypto:resolutions', tokenId.toString(), to);
      
      const domain = await this.getDomainFromTokenId(tokenId);
      if (domain) {
        console.log(`   ✅ Domain ${domain} resolves to ${to}`);
      }
    } catch (error) {
      console.error('Error handling Resolve event:', error);
    }
  }

  async handleNewURI(tokenId, uri) {
    try {
      // Store URI
      await this.redis.hset('crypto:uris', tokenId.toString(), uri);
      
      // Extract domain from URI and cache
      const domain = this.extractDomainFromURI(uri);
      if (domain) {
        await this.redis.set(`crypto:domain:${domain}`, JSON.stringify({
          tokenId: tokenId.toString(),
          uri: uri,
          updated: Date.now()
        }), 'EX', 3600);
        
        console.log(`   ✅ New domain: ${domain}`);
      }
    } catch (error) {
      console.error('Error handling NewURI event:', error);
    }
  }

  extractDomainFromURI(uri) {
    // URI format: "https://api.unstoppabledomain.com/api/v2/metadata/budz.crypto"
    try {
      const parts = uri.split('/');
      const domainPart = parts[parts.length - 1];
      if (domainPart && domainPart.endsWith('.crypto')) {
        return domainPart;
      }
    } catch (e) {
      // Ignore
    }
    return null;
  }

  async getDomainFromTokenId(tokenId) {
    // Try to find domain from cached URIs
    const uri = await this.redis.hget('crypto:uris', tokenId.toString());
    if (uri) {
      return this.extractDomainFromURI(uri);
    }
    return null;
  }

  async initialSync() {
    console.log('📥 Performing initial sync...');
    try {
      // Get the current block and sync recent events
      const block = await this.provider.getBlockNumber();
      const fromBlock = Math.max(0, block - 1000); // Last 1000 blocks

      console.log(`   Scanning blocks ${fromBlock} to ${block}...`);
      
      // Query past Sync events
      const syncFilter = this.registry.filters.Sync();
      const syncEvents = await this.registry.queryFilter(syncFilter, fromBlock, block);
      
      for (const event of syncEvents) {
        await this.handleSync(
          event.args.resolver,
          event.args.updateId,
          event.args.tokenId
        );
      }

      // Query past Resolve events
      const resolveFilter = this.registry.filters.Resolve();
      const resolveEvents = await this.registry.queryFilter(resolveFilter, fromBlock, block);
      
      for (const event of resolveEvents) {
        await this.handleResolve(
          event.args.tokenId,
          event.args.to
        );
      }

      console.log(`   ✅ Synced ${syncEvents.length} sync events, ${resolveEvents.length} resolve events`);
    } catch (error) {
      console.error('Initial sync error:', error.message);
    }
  }

  async stop() {
    this.isRunning = false;
    console.log('🛑 Blockchain Listener stopped');
  }
}

// Start if run directly
if (require.main === module) {
  const listener = new BlockchainListener();
  
  listener.start().catch(console.error);
  
  process.on('SIGINT', async () => {
    await listener.stop();
    process.exit(0);
  });
}

module.exports = BlockchainListener;
