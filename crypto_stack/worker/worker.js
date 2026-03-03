/**
 * Cloudflare Worker - .crypto Domain Resolution
 * 
 * Resolves .crypto (ENS) domains through the crypto_stack API
 * Falls back to traditional DNS for non-.crypto domains
 * 
 * Usage:
 *   Deploy to Cloudflare Workers
 *   Set CRYPTO_API_URL environment variable to your API endpoint
 *   Configure DNS to point to worker
 */

const API_URL = CRYPTO_API_URL || 'http://localhost:8080';
const CACHE_TTL = 300; // 5 minutes

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // Handle DNS-over-HTTPS queries
    if (url.pathname === '/dns-query' || url.pathname === '/resolve') {
      return await handleDNSQuery(request, url);
    }

    // Handle REST API
    if (url.pathname.startsWith('/api/')) {
      return await handleAPIRequest(request, url);
    }

    // Serve worker info
    if (url.pathname === '/' || url.pathname === '/worker.js') {
      return new Response(WORKER_JS, {
        headers: { 'Content-Type': 'application/javascript' }
      });
    }

    return new Response('Not Found', { status: 404 });
  }
};

async function handleDNSQuery(request, url) {
  const name = url.searchParams.get('name');
  const type = url.searchParams.get('type') || 'A';

  if (!name) {
    return new Response(JSON.stringify({ error: 'Missing name parameter' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' }
    });
  }

  // Check if it's a .crypto domain
  if (name.endsWith('.crypto')) {
    return await resolveCryptoDomain(name, type, url);
  }

  // Fallback to Cloudflare DNS for non-.crypto domains
  return await fetch(`https://cloudflare-dns.com/dns-query?name=${name}&type=${type}`, {
    headers: { 'Accept': 'application/dns-json' }
  });
}

async function resolveCryptoDomain(name, type, url) {
  const cacheKey = `crypto:${name}:${type}`;
  
  // Check KV cache if available
  if (typeof CRYPTO_CACHE !== 'undefined') {
    const cached = await CRYPTO_CACHE.get(cacheKey);
    if (cached) {
      return new Response(cached, {
        headers: { 
          'Content-Type': 'application/dns-json',
          'X-Cache': 'HIT'
        }
      });
    }
  }

  try {
    // Query our resolver API
    const response = await fetch(`${API_URL}/api/resolve?domain=${name}&type=${type}`);
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    const dnsResponse = convertToDNSJSON(data, name, type);

    // Cache the result
    if (typeof CRYPTO_CACHE !== 'undefined') {
      await CRYPTO_CACHE.put(cacheKey, JSON.stringify(dnsResponse), { expirationTtl: CACHE_TTL });
    }

    return new Response(JSON.stringify(dnsResponse), {
      headers: { 
        'Content-Type': 'application/dns-json',
        'X-Cache': 'MISS'
      }
    });

  } catch (error) {
    // Fallback to cached error response
    return new Response(JSON.stringify({
      Status: 2, // SERVFAIL
      TC: false,
      RD: true,
      RA: true,
      AD: false,
      CD: false,
      Question: [{ name, type, class: 'IN' }],
      Answer: []
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/dns-json' }
    });
  }
}

async function handleAPIRequest(request, url) {
  const path = url.pathname.replace('/api/', '');
  
  if (path === 'resolve' || path === 'domain') {
    const domain = url.searchParams.get('domain');
    if (!domain) {
      return new Response(JSON.stringify({ error: 'Missing domain parameter' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // Forward to resolver service
    const response = await fetch(`${API_URL}/api/resolve?domain=${domain}`);
    return new Response(response.body, {
      headers: { 
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      }
    });
  }

  return new Response(JSON.stringify({ 
    service: '.crypto Resolver Worker',
    version: '1.0.0',
    endpoints: [
      '/dns-query - DNS-over-HTTPS endpoint',
      '/api/resolve?domain=x.crypto - REST API'
    ]
  }), {
    headers: { 'Content-Type': 'application/json' }
  });
}

// Convert resolver response to DNS JSON format
function convertToDNSJSON(data, name, type) {
  const answer = [];
  
  if (data.records && data.records.A) {
    data.records.A.forEach(addr => {
      answer.push({
        name,
        type: 1, // A
        TTL: CACHE_TTL,
        data: addr
      });
    });
  }

  if (data.records && data.records.AAAA) {
    data.records.AAAA.forEach(addr => {
      answer.push({
        name,
        type: 28, // AAAA
        TTL: CACHE_TTL,
        data: addr
      });
    });
  }

  return {
    Status: 0, // NOERROR
    TC: false,
    RD: true,
    RA: true,
    AD: false,
    CD: false,
    Question: [{ name, type: typeToNumber(type), class: 'IN' }],
    Answer: answer,
    Authority: [],
    Additional: []
  };
}

function typeToNumber(type) {
  const types = { A: 1, AAAA: 28, CNAME: 5, TXT: 16, MX: 15, NS: 2, ANY: 255 };
  return types[type.toUpperCase()] || 1;
}

// Worker info constant
const WORKER_JS = `
// .crypto Resolver Worker Client
// Include this script in your HTML to resolve .crypto domains

class CryptoDNS {
  static async resolve(domain, type = 'A') {
    const response = await fetch(
      \`\${WORKER_URL}/dns-query?name=\${domain}&type=\${type}\`,
      { headers: { 'Accept': 'application/dns-json' } }
    );
    return response.json();
  }
}
`;
