/**
 * Cloudflare Worker - .crypto Domain DNS Resolution
 * 
 * This worker handles DNS-over-HTTPS (DoH) queries for .crypto domains
 * by resolving them through the Ethereum blockchain.
 * 
 * Deploy to Cloudflare Workers and configure mamaduka.crypto as the domain.
 */

const REGISTRY_ADDRESS = '0xD1E5b0FF1287aA9f9A268759062E4Ab08b9Dacbe';

// Minimal ABI for registry
const REGISTRY_ABI = [
  "function resolverOf(uint256 tokenId) external view returns (address)",
  "function uri(uint256 tokenId) external view returns (string memory)"
];

// DNS record types
const DNS_TYPES = {
  A: 1,
  AAAA: 28,
  CNAME: 5,
  TXT: 16,
  MX: 15,
  NS: 2,
  CONTENTHASH: 64
};

/**
 * Calculate namehash for ENS-style domains
 */
function namehash(domain) {
  let node = '0x0000000000000000000000000000000000000000000000000000000000000000';
  const labels = domain.split('.').reverse();
  
  for (const label of labels) {
    const labelHash = ethereumjsUtils.keccak256(Buffer.from(label)).toString('hex').slice(2);
    node = ethereumjsUtils.keccak256(Buffer.from(node + labelHash, 'hex')).toString('hex');
  }
  return '0x' + node;
}

/**
 * Convert domain to tokenId (labelhash)
 */
function labelhash(label) {
  return ethereumjsUtils.keccak256(Buffer.from(label)).toString('hex');
}

/**
 * Fetch resolver address from registry
 */
async function getResolver(tokenId) {
  const data = encodeFunctionCall('resolverOf(uint256)', ['uint256'], [tokenId]);
  
  const response = await fetch(`https://eth-mainnet.g.alchemy.com/v2/demo`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      jsonrpc: '2.0',
      method: 'eth_call',
      params: [{ to: REGISTRY_ADDRESS, data }, 'latest'],
      id: 1
    })
  });
  
  const result = await response.json();
  return decodeResult(result.result);
}

/**
 * Encode function call
 */
function encodeFunctionCall(signature, types, args) {
  const iface = new ethers.utils.Interface([`function ${signature}`]);
  return iface.encodeFunctionData(signature, args);
}

/**
 * Decode result
 */
function decodeResult(data) {
  if (!data || data === '0x') return null;
  return data;
}

/**
 * Build DNS response in application/dns-json format
 */
function buildDNSResponse(domain, records) {
  const response = {
    Status: 0, // NOERROR
    TC: false,
    RD: true,
    RA: true,
    AD: false,
    CD: false,
    Question: [{
      name: domain,
      type: 1 // A record
    }],
    Answer: records.map(r => ({
      name: domain,
      type: DNS_TYPES[r.type] || 1,
      TTL: 300,
      data: r.data
    }))
  };
  
  return response;
}

/**
 * Handle DNS query
 */
async function handleDNSQuery(domain) {
  console.log(`Resolving: ${domain}`);
  
  // Only handle .crypto domains
  if (!domain.endsWith('.crypto')) {
    return null;
  }
  
  const labels = domain.split('.');
  const label = labels[0];
  const tld = labels[labels.length - 1];
  
  if (tld !== 'crypto') {
    return null;
  }
  
  try {
    // Get tokenId (labelhash)
    const tokenId = labelhash(label);
    
    // Get resolver address
    const resolver = await getResolver(tokenId);
    
    if (!resolver || resolver === '0x0000000000000000000000000000000000000000000000') {
      return { Status: 3, error: 'NXDOMAIN' };
    }
    
    // Build DNS response
    // For now, return a placeholder IP - in production, query resolver for contenthash
    const records = [
      { type: 'A', data: '185.199.108.153' } // GitHub Pages placeholder
    ];
    
    return buildDNSResponse(domain, records);
    
  } catch (error) {
    console.error('Resolution error:', error);
    return { Status: 2, error: 'SERVFAIL' };
  }
}

/**
 * Main worker fetch handler
 */
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  const url = new URL(request.url);
  
  // Handle DNS-over-HTTPS
  if (url.pathname === '/dns-query' || url.pathname === '/resolve') {
    const domain = url.searchParams.get('name') || url.searchParams.get('domain');
    
    if (!domain) {
      return new Response(JSON.stringify({ error: 'Missing domain parameter' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    const result = await handleDNSQuery(domain);
    
    if (!result) {
      // Not a .crypto domain, return 404
      return new Response(JSON.stringify({ error: 'Not a .crypto domain' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    return new Response(JSON.stringify(result), {
      headers: { 
        'Content-Type': 'application/dns-json',
        'Cache-Control': 'public, max-age=300'
      }
    });
  }
  
  // Health check
  if (url.pathname === '/health') {
    return new Response(JSON.stringify({
      status: 'ok',
      service: 'crypto-dns-resolver',
      blockchain: 'ethereum',
      registry: REGISTRY_ADDRESS
    }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }
  
  // Root info
  if (url.pathname === '/' || url.pathname === '/info') {
    return new Response(JSON.stringify({
      name: 'Crypto DNS Resolver',
      version: '1.0.0',
      description: 'DNS resolution for .crypto domains via Ethereum blockchain',
      endpoints: {
        'GET /dns-query?name=example.crypto': 'Resolve DNS',
        'GET /resolve?domain=example.crypto': 'Resolve domain JSON',
        'GET /health': 'Health check'
      },
      registry: REGISTRY_ADDRESS,
      supportedTLD: '.crypto'
    }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }
  
  return new Response('Not Found', { status: 404 });
}

// Export for testing
module.exports = { handleDNSQuery, namehash, labelhash };
