/**
 * .crypto Registry Event Listener
 * Monitors Sync and Resolve events from the ENS .crypto registry
 */

const { ethers } = require('ethers');
const fs = require('fs');
const path = require('path');

// Configuration
const REGISTRY_ADDRESS = process.env.REGISTRY_ADDRESS || '0xD1E5b0FF1287aA9f9A268759062E4Ab08b9Dacbe';
const ETH_RPC_URL = process.env.ETH_RPC_URL || 'https://eth-mainnet.g.alchemy.com/v2/demo';
const LOG_FILE = '/data/events.log';

// Minimal ABI for Registry events we care about
const REGISTRY_ABI = [
  "event Sync(address indexed resolver, uint256 indexed updateId, uint256 indexed tokenId)",
  "event Resolve(uint256 indexed tokenId, address indexed to)",
  "event NewURI(uint256 indexed tokenId, string uri)",
  "function resolverOf(uint256 tokenId) view returns (address)"
];

class CryptoListener {
  constructor() {
    this.provider = new ethers.JsonRpcProvider(ETH_RPC_URL);
    this.registry = new ethers.Contract(REGISTRY_ADDRESS, REGISTRY_ABI, this.provider);
    this.cache = {};
  }

  async start() {
    console.log(`🎧 Starting .crypto Registry Listener...`);
    console.log(`📡 Connected to: ${ETH_RPC_URL}`);
    console.log(`📋 Registry: ${REGISTRY_ADDRESS}`);

    // Listen for Sync events
    this.registry.on('Sync', async (resolver, updateId, tokenId, event) => {
      console.log(`🔄 Sync: tokenId=${tokenId} resolver=${resolver} updateId=${updateId}`);
      await this.handleSync(tokenId, resolver, updateId);
    });

    // Listen for Resolve events
    this.registry.on('Resolve', async (tokenId, to, event) => {
      console.log(`✅ Resolve: tokenId=${tokenId} to=${to}`);
      await this.handleResolve(tokenId, to);
    });

    // Listen for NewURI events
    this.registry.on('NewURI', async (tokenId, uri, event) => {
      console.log(`📝 NewURI: tokenId=${tokenId} uri=${uri}`);
      await this.handleNewURI(tokenId, uri);
    });

    console.log(`✅ Listener active! Monitoring for events...`);
  }

  async handleSync(tokenId, resolver, updateId) {
    const entry = {
      type: 'Sync',
      tokenId: tokenId.toString(),
      resolver,
      updateId: updateId.toString(),
      timestamp: Date.now()
    };
    this.logEvent(entry);
    this.cache[tokenId] = { resolver, lastUpdate: Date.now() };
  }

  async handleResolve(tokenId, to) {
    const entry = {
      type: 'Resolve',
      tokenId: tokenId.toString(),
      to,
      timestamp: Date.now()
    };
    this.logEvent(entry);
  }

  async handleNewURI(tokenId, uri) {
    const entry = {
      type: 'NewURI',
      tokenId: tokenId.toString(),
      uri,
      timestamp: Date.now()
    };
    this.logEvent(entry);
  }

  logEvent(entry) {
    const logLine = JSON.stringify(entry) + '\n';
    fs.appendFileSync(LOG_FILE, logLine);
    console.log(`💾 Logged: ${entry.type}`);
  }

  // Get resolver for a domain
  async getResolver(domain) {
    const tokenId = this.namehash(domain);
    try {
      const resolver = await this.registry.resolverOf(tokenId);
      return resolver;
    } catch (error) {
      console.error(`❌ Error getting resolver for ${domain}:`, error.message);
      return null;
    }
  }

  // Standard ENS namehash algorithm
  namehash(domain) {
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
}

// Start listener
const listener = new CryptoListener();
listener.start().catch(console.error);
