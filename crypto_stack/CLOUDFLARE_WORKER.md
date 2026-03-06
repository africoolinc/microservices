# Cloudflare Worker Configuration for mamaduka.crypto

## Overview
This document details how to deploy the .crypto resolution as a Cloudflare Worker.

## Prerequisites
1. Cloudflare account with Workers enabled
2. Workers KV namespace for caching
3. Wrangler CLI installed (`npm install -g wrangler`)

## Worker Code (worker.js)

```javascript
/**
 * .crypto Domain Resolution Worker
 * Deploys to: mamaduka.crypto
 */

const REGISTRY_ADDRESS = '0xD1E5b0FF1287aA9f9A268759062E4Ab08b9Dacbe';
const ETHEREUM_RPC_URL = 'https://eth.llamarpc.com';

// Registry ABI (simplified)
const REGISTRY_ABI = [
  {
    "constant": true,
    "inputs": [{ "name": "tokenId", "type": "uint256" }],
    "name": "resolverOf",
    "outputs": [{ "name": "", "type": "address" }],
    "type": "function"
  }
];

// Resolver ABI
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
  }
];

const COIN_TYPES = { ETH: 60, BTC: 0 };

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    
    // Handle DNS query
    if (url.pathname === '/dns-query') {
      return await handleDNSQuery(request, env);
    }
    
    // Handle resolution
    if (url.pathname.startsWith('/resolve/')) {
      const domain = url.pathname.replace('/resolve/', '');
      return await handleResolve(domain, env);
    }
    
    // Health check
    if (url.pathname === '/health') {
      return new Response(JSON.stringify({ status: 'ok', worker: 'mamaduka.crypto' }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    // Root
    return new Response(JSON.stringify({
      service: '.crypto Resolution Worker',
      domain: 'mamaduka.crypto',
      endpoints: ['/dns-query', '/resolve/:domain', '/health']
    }), { headers: { 'Content-Type': 'application/json' } });
  }
};

async function handleDNSQuery(request, env) {
  const url = new URL(request.url);
  const name = url.searchParams.get('name');
  const type = url.searchParams.get('type') || 'A';
  
  if (!name) {
    return new Response(JSON.stringify({ error: 'Missing name' }), { status: 400 });
  }
  
  // Check cache first
  const cacheKey = `crypto:${name}:${type}`;
  const cached = await env.CRYPTO_CACHE.get(cacheKey);
  if (cached) {
    return new Response(cached, { headers: { 'Content-Type': 'application/dns-json', 'Cache-Control': 'max-age=300' } });
  }
  
  // Resolve from blockchain
  const result = await resolveCryptoDomain(name);
  
  // Format as DNS response
  const dnsResponse = {
    Status: 0,
    TC: false,
    RD: true,
    RA: true,
    Question: [{ name, type }],
    Answer: result.records ? formatAnswer(result, type) : []
  };
  
  const response = JSON.stringify(dnsResponse);
  
  // Cache for 5 minutes
  await env.CRYPTO_CACHE.put(cacheKey, response, { expirationTtl: 300 });
  
  return new Response(response, { headers: { 'Content-Type': 'application/dns-json' } });
}

async function handleResolve(domain, env) {
  const cacheKey = `resolve:${domain}`;
  const cached = await env.CRYPTO_CACHE.get(cacheKey);
  if (cached) {
    return new Response(cached, { headers: { 'Content-Type': 'application/json' } });
  }
  
  const result = await resolveCryptoDomain(domain);
  const response = JSON.stringify(result);
  
  await env.CRYPTO_CACHE.put(cacheKey, response, { expirationTtl: 300 });
  
  return new Response(response, { headers: { 'Content-Type': 'application/json' } });
}

async function resolveCryptoDomain(domain) {
  // Calculate namehash
  const node = namehash(domain);
  const tokenId = domainToTokenId(domain);
  
  // Get resolver from registry
  const resolver = await callContract(REGISTRY_ADDRESS, REGISTRY_ABI, 'resolverOf', [tokenId]);
  
  if (!resolver || resolver === '0x0000000000000000000000000000000000000000') {
    return { error: 'Domain not found', domain };
  }
  
  // Get records from resolver
  const records = {};
  
  try {
    const ethAddr = await callContract(resolver, RESOLVER_ABI, 'addr', [node, COIN_TYPES.ETH]);
    if (ethAddr && ethAddr !== '0x') {
      records.ETH = ethAddr;
    }
  } catch (e) {}
  
  try {
    const url = await callContract(resolver, RESOLVER_ABI, 'getText', [node, 'url']);
    if (url) records.url = url;
  } catch (e) {}
  
  try {
    const email = await callContract(resolver, RESOLVER_ABI, 'getText', [node, 'email']);
    if (email) records.email = email;
  } catch (e) {}
  
  return { domain, tokenId, resolver, records };
}

async function callContract(to, abi, method, args) {
  const response = await fetch(ETHEREUM_RPC_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      jsonrpc: '2.0',
      method: 'eth_call',
      params: [{
        to,
        data: encodeABI(abi, method, args)
      }, 'latest'],
      id: 1
    })
  });
  
  const result = await response.json();
  return result.result;
}

function namehash(domain) {
  let node = '0x0000000000000000000000000000000000000000000000000000000000000000';
  const labels = domain.split('.').reverse();
  
  for (const label of labels) {
    const labelHash = sha3(label);
    node = sha3(node.slice(2) + labelHash.slice(2), 'hex');
  }
  return node;
}

function domainToTokenId(domain) {
  const hash = sha3(domain);
  return BigInt(hash).toString();
}

function sha3(data, encoding) {
  // Use Web Crypto API or a library
  const msgBuffer = new TextEncoder().encode(data);
  return '0x' + Array.from(new Uint8Array(crypto.subtle.digest('SHA-256', msgBuffer)))
    .map(b => b.toString(16).padStart(2, '0')).join('');
}

function formatAnswer(result, type) {
  if (type === 'A' && result.records.ETH) {
    return [{
      name: result.domain,
      type: 1,
      TTL: 300,
      data: result.records.ETH
    }];
  }
  return [];
}
```

## Wrangler Configuration (wrangler.toml)

```toml
name = "mamaduka-crypto"
main = "worker.js"
compatibility_date = "2023-12-01"

[[kv_namespaces]]
binding = "CRYPTO_CACHE"
id = "YOUR_KV_NAMESPACE_ID"
```

## Deployment Steps

1. **Create KV Namespace**:
```bash
wrangler kv:namespace create CRYPTO_CACHE
```

2. **Deploy Worker**:
```bash
wrangler deploy
```

3. **Configure DNS**:
   - Add CNAME record: `mamaduka.crypto` → `{your-worker}.workers.dev`

## Testing

```bash
# Test resolution
curl "https://mamaduka.crypto.workers.dev/resolve/vitalik.crypto"

# Test DNS query
curl "https://mamaduka.crypto.workers.dev/dns-query?name=vitalik.crypto&type=A"

# Health check
curl "https://mamaduka.crypto.workers.dev/health"
```
