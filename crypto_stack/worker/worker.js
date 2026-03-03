/**
 * Cloudflare Worker for .crypto Domain Resolution
 * Deploy at: dns.mamaduka.crypto
 */

// .Crypto Registry Contract
const REGISTRY_ADDRESS = '0xD1E5b0FF1287aA9f9A268759062E4Ab08b9Dacbe';

// ABI for registry
const REGISTRY_ABI = [
  'function resolverOf(uint256 tokenId) view returns (address)',
  'function ownerOf(uint256 tokenId) view returns (address)'
];

// Resolver ABI
const RESOLVER_ABI = [
  'function addr(bytes32 node) view returns (address)',
  'function contenthash(bytes32 node) view returns (bytes)',
  'function text(bytes32 node, string calldata key) view returns (string)'
];

// DNS record types
const DNS_TYPES = {
  A: 1,
  AAAA: 28,
  CNAME: 5,
  TXT: 16,
  MX: 15,
  NS: 2,
  CAA: 257
};

// ENS namehash algorithm
function namehash(domain) {
  let node = '0x0000000000000000000000000000000000000000000000000000000000000000';
  const labels = domain.split('.').reverse();

  for (const label of labels) {
    const labelHash = ethers.keccak256(ethers.toUtf8Bytes(label));
    node = ethers.keccak256(
      Buffer.concat([
        Buffer.from(node.slice(2), 'hex'),
        Buffer.from(labelHash.slice(2), 'hex')
      ])
    );
  }
  return node;
}

// Parse query string
function getQueryParams(url) {
  const params = {};
  const urlObj = new URL(url);
  urlObj.searchParams.forEach((value, key) => {
    params[key] = value;
  });
  return params;
}

// Build DNS JSON response
function buildDNSResponse(domain, type, resolution) {
  const response = {
    Status: 0,
    TC: false,
    RD: true,
    RA: true,
    AD: false,
    CD: false,
    Question: [{ name: domain, type: DNS_TYPES[type] || 1 }],
    Answer: []
  };

  if (!resolution) {
    response.Status = 2;
    return response;
  }

  // Add ETH address as A record
  if (resolution.records?.A?.[0]) {
    response.Answer.push({
      name: domain,
      type: 1,
      TTL: 300,
      data: resolution.records.A[0]
    });
  }

  // Add contenthash
  if (resolution.records?.contenthash) {
    response.Answer.push({
      name: domain,
      type: 16,
      TTL: 300,
      data: resolution.records.contenthash
    });
  }

  return response;
}

// Main fetch handler
export default {
  async fetch(request) {
    const url = new URL(request.url);
    const params = getQueryParams(request.url);

    // Handle DNS-over-HTTPS
    if (url.pathname === '/dns-query' || url.pathname === '/dns') {
      const name = params.name;
      const type = params.type || 'A';

      if (!name) {
        return new Response(JSON.stringify({ Status: 1, error: 'Missing name' }), {
          headers: { 'Content-Type': 'application/dns-json' }
        });
      }

      // Only handle .crypto domains
      if (!name.endsWith('.crypto')) {
        // Forward to Cloudflare DNS
        const cfResponse = await fetch(`https://cloudflare-dns.com/dns-query?${url.searchParams}`, {
          headers: { 'Accept': 'application/dns-json' }
        });
        return cfResponse;
      }

      // Resolve .crypto domain via Ethereum
      try {
        // Use public RPC
        const provider = new ethers.JsonRpcProvider('https://eth.llamarpc.com');
        
        const registry = new ethers.Contract(REGISTRY_ADDRESS, REGISTRY_ABI, provider);
        const tokenId = namehash(name);
        
        const resolverAddress = await registry.resolverOf(tokenId);
        
        const resolution = {
          domain: name,
          resolver: resolverAddress,
          records: {}
        };

        if (resolverAddress && resolverAddress !== ethers.ZeroAddress) {
          const resolver = new ethers.Contract(resolverAddress, RESOLVER_ABI, provider);
          
          try {
            const ethAddress = await resolver.addr(tokenId);
            if (ethAddress && ethAddress !== ethers.ZeroAddress) {
              resolution.records.A = [ethAddress];
            }
          } catch (e) {}

          try {
            const contenthash = await resolver.contenthash(tokenId);
            if (contenthash && contenthash !== '0x') {
              resolution.records.contenthash = contenthash;
            }
          } catch (e) {}
        }

        const dnsResponse = buildDNSResponse(name, type, resolution);
        return new Response(JSON.stringify(dnsResponse), {
          headers: { 'Content-Type': 'application/dns-json' }
        });

      } catch (error) {
        return new Response(JSON.stringify({ 
          Status: 2, 
          error: error.message 
        }), {
          headers: { 'Content-Type': 'application/dns-json' }
        });
      }
    }

    // Health check
    if (url.pathname === '/health') {
      return new Response(JSON.stringify({ 
        status: 'ok', 
        worker: 'crypto-dns',
        domain: 'mamaduka.crypto'
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // Default response
    return new Response(`
      <html>
        <head><title>mamaduka.crypto DNS</title></head>
        <body>
          <h1>🔗 mamaduka.crypto DNS Worker</h1>
          <p>Blockchain-powered DNS resolution</p>
          <ul>
            <li><a href="/dns-query?name=mamaduka.crypto&type=A">Test Resolution</a></li>
            <li><a href="/health">Health Check</a></li>
          </ul>
        </body>
      </html>
    `, {
      headers: { 'Content-Type': 'text/html' }
    });
  }
};
