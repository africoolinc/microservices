const Web3 = require('web3');
const Redis = require('ioredis');

// Configuration
const REGISTRY_ADDRESS = process.env.REGISTRY_ADDRESS || '0xD1E5b0FF1287aA9f9A268759062E4Ab08b9Dacbe';
const ETHEREUM_RPC_URL = process.env.ETHEREUM_RPC_URL || 'https://mainnet.infura.io/v3/YOUR_INFURA_KEY';
const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';

// .crypto Registry ABI (simplified for events)
const REGISTRY_ABI = [
  {
    "anonymous": false,
    "inputs": [
      { "indexed": true, "name": "resolver", "type": "address" },
      { "indexed": true, "name": "updateId", "type": "uint256" },
      { "indexed": true, "name": "tokenId", "type": "uint256" }
    ],
    "name": "Sync",
    "type": "event"
  },
  {
    "anonymous": false,
    "inputs": [
      { "indexed": true, "name": "tokenId", "type": "uint256" },
      { "indexed": true, "name": "to", "type": "address" }
    ],
    "name": "Resolve",
    "type": "event"
  },
  {
    "anonymous": false,
    "inputs": [
      { "indexed": true, "name": "tokenId", "type": "uint256" },
      { "name": "uri", "type": "string" }
    ],
    "name": "NewURI",
    "type": "event"
  },
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
  }
];

// Resolver ABI
const RESOLVER_ABI = [
  {
    "constant": true,
    "inputs": [{ "name": "name", "type": "bytes" }],
    "name": "resolve",
    "outputs": [{ "name": "", "type": "bytes" }],
    "type": "function"
  },
  {
    "constant": true,
    "inputs": [{ "name": "name", "type": "bytes" }],
    "name": "namehash",
    "outputs": [{ "name": "", "type": "bytes32" }],
    "type": "function"
  },
  {
    "constant": true,
    "inputs": [{ "name": "node", "type": "bytes32" }, { "name": "coinType", "type": "uint256" }],
    "name": "addr",
    "outputs": [{ "name": "", "type": "bytes" }],
    "type": "function"
  },
  {
    "constant": true,
    "inputs": [{ "name": "node", "type": "bytes32" }],
    "name": "getText",
    "outputs": [{ "name": "", "type": "string" }],
    "type": "function"
  }
];

class BlockchainListener {
  constructor() {
    this.web3 = new Web3(new Web3.providers.WebsocketProvider(ETHEREUM_RPC_URL.replace('https', 'wss')));
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

  async handleSync(event) {
    const { resolver, updateId, tokenId } = event.returnValues;
    console.log(`[Sync] TokenId: ${tokenId}, Resolver: ${resolver}, UpdateId: ${updateId}`);
    
    // Cache resolver address
    await this.redis.setex(`resolver:${tokenId}`, 86400, resolver);
    await this.redis.publish('resolver-update', JSON.stringify({ tokenId, resolver }));
  }

  async handleResolve(event) {
    const { tokenId, to } = event.returnValues;
    console.log(`[Resolve] TokenId: ${tokenId}, To: ${to}`);
    
    await this.redis.setex(`resolve:${tokenId}`, 86400, to);
  }

  async startListening() {
    console.log('Starting .crypto blockchain listener...');
    
    // Listen for Sync events
    this.registry.events.Sync({ fromBlock: 'latest' })
      .on('data', (event) => this.handleSync(event))
      .on('error', (error) => console.error('Sync event error:', error));

    // Listen for Resolve events
    this.registry.events.Resolve({ fromBlock: 'latest' })
      .on('data', (event) => this.handleResolve(event))
      .on('error', (error) => console.error('Resolve event error:', error));

    console.log('Listening for .crypto registry events...');
  }

  async getResolverAddress(tokenId) {
    const cached = await this.redis.get(`resolver:${tokenId}`);
    if (cached) return cached;
    
    const resolver = await this.registry.methods.resolverOf(tokenId).call();
    await this.redis.setex(`resolver:${tokenId}`, 3600, resolver);
    return resolver;
  }

  async getOwner(tokenId) {
    return await this.registry.methods.ownerOf(tokenId).call();
  }
}

// Export for testing
module.exports = { BlockchainListener, REGISTRY_ADDRESS, RESOLVER_ABI };

// Start if main
if (require.main === module) {
  const listener = new BlockchainListener();
  listener.startListening().catch(console.error);
}
