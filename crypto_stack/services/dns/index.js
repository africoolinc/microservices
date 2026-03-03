/**
 * DNS-over-HTTPS Service for .crypto domains
 * Handles DNS queries and proxies to blockchain resolver
 */

const express = require('express');
const axios = require('axios');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 8053;
const RESOLVER_URL = process.env.RESOLVER_URL || 'http://resolver:3000';
const DOMAIN = process.env.DOMAIN || 'mamaduka.crypto';

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

app.use(cors());
app.use(express.json());

// Forward to resolver service
async function resolveFromResolver(domain, type = 'A') {
  try {
    const response = await axios.get(`${RESOLVER_URL}/resolve`, {
      params: { domain },
      timeout: 10000
    });
    return response.data;
  } catch (error) {
    console.error('Resolver error:', error.message);
    return null;
  }
}

// Build DNS JSON response
function buildDNSResponse(domain, type, resolution) {
  const response = {
    Status: 0, // NOERROR
    TC: false,
    RD: true,
    RA: true,
    AD: false,
    CD: false,
    Question: [{ name: domain, type: DNS_TYPES[type] || 1 }],
    Answer: []
  };

  if (!resolution || !resolution.records) {
    return response;
  }

  // Add A records (ETH addresses)
  if (resolution.records.A && resolution.records.A.length > 0) {
    response.Answer.push({
      name: domain,
      type: 1, // A
      TTL: 300,
      data: resolution.records.A[0]
    });
  }

  // Add contenthash as TXT record
  if (resolution.records.contenthash) {
    response.Answer.push({
      name: domain,
      type: 16, // TXT
      TTL: 300,
      data: resolution.records.contenthash
    });
  }

  // Set status if no records found
  if (response.Answer.length === 0) {
    response.Status = 3; // NXDOMAIN
  }

  return response;
}

// Main DNS query endpoint (Cloudflare-style)
app.get('/dns-query', async (req, res) => {
  const { name, type = 'A' } = req.query;
  
  if (!name) {
    return res.status(400).json({ 
      Status: 1, // FORMERROR
      error: 'Missing name parameter' 
    });
  }

  // Check if .crypto domain
  if (name.endsWith('.crypto')) {
    const resolution = await resolveFromResolver(name, type);
    const response = buildDNSResponse(name, type, resolution);
    res.set('Content-Type', 'application/dns-json');
    return res.json(response);
  }

  // For non-.crypto domains, return error
  res.set('Content-Type', 'application/dns-json');
  return res.json({
    Status: 2, // SERVFAIL - we only handle .crypto
    error: 'Not a .crypto domain'
  });
});

// Alternative endpoint
app.get('/resolve', async (req, res) => {
  const { domain, type = 'A' } = req.query;
  
  if (!domain) {
    return res.status(400).json({ error: 'Missing domain parameter' });
  }

  const resolution = await resolveFromResolver(domain, type);
  res.json(resolution);
});

// Simple JSON endpoint
app.get('/api/resolve/:domain', async (req, res) => {
  const { domain } = req.params;
  const resolution = await resolveFromResolver(domain);
  res.json(resolution);
});

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    service: 'crypto-dns',
    domain: DOMAIN,
    resolver: RESOLVER_URL
  });
});

// Status page
app.get('/', (req, res) => {
  res.send(`
    <html>
      <head>
        <title>mamaduka.crypto DNS Service</title>
        <style>
          body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
          h1 { color: #f7931a; }
          .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }
          code { background: #e0e0e0; padding: 2px 6px; border-radius: 3px; }
        </style>
      </head>
      <body>
        <h1>🔗 mamaduka.crypto DNS Service</h1>
        <p>Blockchain-powered DNS resolution for .crypto domains</p>
        
        <h2>Endpoints</h2>
        <div class="endpoint">
          <code>GET /dns-query?name=mamaduka.crypto&type=A</code>
          <p>DNS-over-HTTPS (Cloudflare-style)</p>
        </div>
        <div class="endpoint">
          <code>GET /resolve?domain=mamaduka.crypto</code>
          <p>Simple resolution API</p>
        </div>
        <div class="endpoint">
          <code>GET /health</code>
          <p>Health check</p>
        </div>
        
        <h2>Test</h2>
        <p><a href="/dns-query?name=mamaduka.crypto&type=A">Test resolution</a></p>
      </body>
    </html>
  `);
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`🌍 DNS-over-HTTPS service running on port ${PORT}`);
  console.log(`📡 Resolver: ${RESOLVER_URL}`);
  console.log(`🏠 Domain: ${DOMAIN}`);
});

module.exports = app;
