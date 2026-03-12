/**
 * Cloudflare Worker API
 * Manages Cloudflare Workers for .crypto domain resolution
 */

const express = require('express');
const axios = require('axios');
const cors = require('cors');
const winston = require('winston');
const fs = require('fs');
const path = require('path');

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [new winston.transports.Console()]
});

const CONFIG = {
  resolverUrl: process.env.RESOLVER_URL || 'http://localhost:8080',
  cloudflareAccountId: process.env.CLOUDFLARE_ACCOUNT_ID || '',
  cloudflareApiToken: process.env.CLOUDFLARE_API_TOKEN || '',
  domain: process.env.DOMAIN || 'mamaduka.crypto',
  port: parseInt(process.env.PORT || '3000')
};

class WorkerAPI {
  constructor() {
    this.app = express();
    this.cloudflareBaseUrl = 'https://api.cloudflare.com/client/v4';
  }

  async initialize() {
    this.app.use(cors());
    this.app.use(express.json());
    this.setupRoutes();
    logger.info('Worker API initialized');
  }

  setupRoutes() {
    // Health check
    this.app.get('/health', (req, res) => {
      res.json({ status: 'ok', service: 'worker-api', domain: CONFIG.domain });
    });

    // Get worker script
    this.app.get('/worker/script', (req, res) => {
      const script = this.generateWorkerScript();
      res.type('application/javascript').send(script);
    });

    // Deploy worker to Cloudflare
    this.app.post('/worker/deploy', async (req, res) => {
      try {
        const result = await this.deployWorker();
        res.json(result);
      } catch (error) {
        logger.error('Worker deployment failed', { error: error.message });
        res.status(500).json({ error: error.message });
      }
    });

    // Get worker status
    this.app.get('/worker/status', async (req, res) => {
      try {
        const status = await this.getWorkerStatus();
        res.json(status);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    // Resolve domain (API endpoint)
    this.app.get('/resolve/:domain', async (req, res) => {
      try {
        const { domain } = req.params;
        const response = await axios.get(`${CONFIG.resolverUrl}/resolve/${domain}`, {
          timeout: 10000
        });
        res.json(response.data);
      } catch (error) {
        logger.error('Resolution failed', { error: error.message });
        res.status(500).json({ error: error.message });
      }
    });

    // Dashboard view
    this.app.get('/', (req, res) => {
      res.send(this.generateDashboard());
    });
  }

  /**
   * Generate Cloudflare Worker script for .crypto resolution
   */
  generateWorkerScript() {
    return `
/**
 * .crypto Domain Resolution Worker
 * Deploys to Cloudflare Workers for DNS resolution
 */

const RESOLVER_URL = '${CONFIG.resolverUrl}';
const CACHE_TTL = 300;

// DNS type codes
const DNS_TYPES = {
  1: 'A',
  28: 'AAAA',
  5: 'CNAME',
  16: 'TXT',
  15: 'MX',
  2: 'NS'
};

const TYPE_CODES = {
  A: 1,
  AAAA: 28,
  CNAME: 5,
  TXT: 16,
  MX: 15,
  NS: 2
};

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // Handle DNS-over-HTTPS requests
    if (url.pathname === '/dns-query' || url.pathname === '/dns-query/') {
      return handleDOH(request);
    }
    
    // Handle resolution API
    if (url.pathname.startsWith('/resolve/')) {
      const domain = url.pathname.split('/resolve/')[1];
      return handleResolve(domain);
    }
    
    // Default: serve dashboard or 404
    if (url.pathname === '/' || url.pathname === '/index.html') {
      return new Response(DASHBOARD_HTML, {
        headers: { 'Content-Type': 'text/html' }
      });
    }
    
    return new Response('Not Found', { status: 404 });
  }
};

async function handleDOH(request) {
  const url = new URL(request.url);
  const name = url.searchParams.get('name');
  const type = url.searchParams.get('type') || 'A';
  
  if (!name) {
    return new Response(JSON.stringify({ error: 'Missing name parameter' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' }
    });
  }
  
  // Check if .crypto domain
  if (name.endsWith('.crypto')) {
    return await resolveCryptoDomain(name, type);
  }
  
  // Fallback to Cloudflare DNS
  return await fetch(\`https://cloudflare-dns.com/dns-query?name=\${name}&type=\${type}\`, {
    headers: { 'Accept': 'application/dns-json' }
  });
}

async function resolveCryptoDomain(domain, type) {
  // Check cache first
  const cacheKey = \`crypto:resolve:\${domain}:\${type}\`;
  const cached = await CRYPTO_RESOLVER.get(cacheKey);
  
  if (cached) {
    return new Response(cached, {
      headers: { 
        'Content-Type': 'application/dns-json',
        'X-Cache': 'HIT'
      }
    });
  }
  
  // Resolve from blockchain
  try {
    const response = await fetch(\`\${RESOLVER_URL}/dns/\${domain}?type=\${type}\`);
    const data = await response.json();
    
    const dnsResponse = formatDNSResponse(domain, type, data);
    const jsonResponse = JSON.stringify(dnsResponse);
    
    // Cache the result
    await CRYPTO_RESOLVER.put(cacheKey, jsonResponse, { expirationTtl: CACHE_TTL });
    
    return new Response(jsonResponse, {
      headers: { 
        'Content-Type': 'application/dns-json',
        'X-Cache': 'MISS'
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({
      Status: 2,
     error: error.message
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

async function handleResolve(domain) {
  if (!domain.endsWith('.crypto')) {
    return new Response(JSON.stringify({ error: 'Only .crypto domains supported' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' }
    });
  }
  
  try {
    const response = await fetch(\`\${RESOLVER_URL}/resolve/\${domain}\`);
    const data = await response.json();
    return new Response(JSON.stringify(data), {
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

function formatDNSResponse(domain, type, data) {
  const records = [];
  
  if (data.records && data.records.data) {
    const typeCode = TYPE_CODES[type] || 1;
    records.push({
      name: domain,
      type: typeCode,
      TTL: 300,
      data: data.records.data
    });
  }
  
  return {
    Status: 0,
    TC: false,
    RD: true,
    RA: true,
    AD: false,
    CD: false,
    Question: [{ name: domain, type: TYPE_CODES[type] || 1, class: 'IN' }],
    Answer: records
  };
}

const DASHBOARD_HTML = \`
<!DOCTYPE html>
<html>
<head>
  <title>.crypto Resolver - \${CONFIG.domain}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
           max-width: 800px; margin: 50px auto; padding: 20px; background: #0d1117; color: #c9d1d9; }
    h1 { color: #58a6ff; }
    .card { background: #161b22; padding: 20px; border-radius: 8px; margin: 20px 0; }
    .status { color: #3fb950; }
    input { padding: 10px; width: 60%; background: #0d1117; border: 1px solid #30363d; 
            color: #c9d1d9; border-radius: 4px; }
    button { padding: 10px 20px; background: #238636; color: white; border: none; 
             border-radius: 4px; cursor: pointer; }
    button:hover { background: #2ea043; }
    #result { margin-top: 20px; white-space: pre-wrap; font-family: monospace; }
  </style>
</head>
<body>
  <h1>🔗 .crypto Domain Resolver</h1>
  <p>Service: \${CONFIG.domain}</p>
  <div class="card">
    <h3>Resolve Domain</h3>
    <input type="text" id="domain" placeholder="example.crypto">
    <button onclick="resolve()">Resolve</button>
    <div id="result"></div>
  </div>
  <div class="card">
    <h3>Status</h3>
    <p class="status">● Service Active</p>
  </div>
  <script>
    async function resolve() {
      const domain = document.getElementById('domain').value;
      if (!domain) return;
      const res = await fetch('/resolve/' + domain);
      document.getElementById('result').textContent = JSON.stringify(await res.json(), null, 2);
    }
  </script>
</body>
</html>
\`;
`;
  }

  /**
   * Deploy worker to Cloudflare
   */
  async deployWorker() {
    if (!CONFIG.cloudflareAccountId || !CONFIG.cloudflareApiToken) {
      return { error: 'Cloudflare credentials not configured' };
    }

    const script = this.generateWorkerScript();
    const workerName = 'crypto-resolver';

    try {
      // Upload worker script
      await axios.put(
        `${this.cloudflareBaseUrl}/accounts/${CONFIG.cloudflareAccountId}/workers/scripts/${workerName}`,
        script,
        {
          headers: {
            'Content-Type': 'application/javascript',
            'Authorization': `Bearer ${CONFIG.cloudflareApiToken}`
          }
        }
      );

      return { success: true, worker: workerName, domain: CONFIG.domain };
    } catch (error) {
      throw new Error(`Deployment failed: ${error.message}`);
    }
  }

  /**
   * Get worker status
   */
  async getWorkerStatus() {
    if (!CONFIG.cloudflareAccountId || !CONFIG.cloudflareApiToken) {
      return { deployed: false, reason: 'No credentials' };
    }

    const workerName = 'crypto-resolver';

    try {
      const response = await axios.get(
        `${this.cloudflareBaseUrl}/accounts/${CONFIG.cloudflareAccountId}/workers/scripts/${workerName}`,
        {
          headers: {
            'Authorization': `Bearer ${CONFIG.cloudflareApiToken}`
          }
        }
      );

      return { deployed: true, worker: workerName, version: response.data.version };
    } catch (error) {
      return { deployed: false, error: error.message };
    }
  }

  /**
   * Generate simple dashboard HTML
   */
  generateDashboard() {
    return `
<!DOCTYPE html>
<html>
<head>
  <title>.crypto Resolver - ${CONFIG.domain}</title>
  <meta charset="utf-8">
  <style>
    body { 
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
      max-width: 800px; margin: 50px auto; padding: 20px; 
      background: #0d1117; color: #c9d1d9; 
    }
    h1 { color: #58a6ff; }
    .card { background: #161b22; padding: 20px; border-radius: 8px; margin: 20px 0; }
    .status { color: #3fb950; }
    input { 
      padding: 10px; width: 60%; background: #0d1117; 
      border: 1px solid #30363d; color: #c9d1d9; border-radius: 4px; 
    }
    button { 
      padding: 10px 20px; background: #238636; color: white; 
      border: none; border-radius: 4px; cursor: pointer; 
    }
    button:hover { background: #2ea043; }
    #result { margin-top: 20px; white-space: pre-wrap; font-family: monospace; 
              background: #161b22; padding: 15px; border-radius: 4px; }
    code { background: #30363d; padding: 2px 6px; border-radius: 3px; }
  </style>
</head>
<body>
  <h1>🔗 .crypto Domain Resolution Service</h1>
  <p>Managed by <code>crypto_stack</code> | Domain: <code>${CONFIG.domain}</code></p>
  
  <div class="card">
    <h3>📡 Resolve Domain</h3>
    <input type="text" id="domain" placeholder="mamaduka.crypto">
    <button onclick="resolve()">Resolve</button>
    <div id="result"></div>
  </div>
  
  <div class="card">
    <h3>🔧 Service Status</h3>
    <p class="status">● Active</p>
    <p>Blockchain: Ethereum Mainnet</p>
    <p>Registry: 0xD1E5b0FF1287aA9f9A268759062E4Ab08b9Dacbe</p>
  </div>
  
  <script>
    async function resolve() {
      const domain = document.getElementById('domain').value;
      if (!domain) return;
      const res = await fetch('/resolve/' + domain);
      document.getElementById('result').textContent = JSON.stringify(await res.json(), null, 2);
    }
  </script>
</body>
</html>
    `;
  }

  async start() {
    this.app.listen(CONFIG.port, () => {
      logger.info(`Worker API listening on port ${CONFIG.port}`);
    });
  }
}

if (require.main === module) {
  const api = new WorkerAPI();
  api.initialize()
    .then(() => api.start())
    .catch(err => {
      logger.error('Failed to start Worker API', { error: err.message });
      process.exit(1);
    });
}

module.exports = WorkerAPI;
