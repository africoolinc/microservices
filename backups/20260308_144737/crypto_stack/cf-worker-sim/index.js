const http = require('http');

const RESOLVER_URL = process.env.RESOLVER_URL || 'http://resolver-gateway:8080';
const DOMAIN = process.env.DOMAIN || 'mamaduka.crypto';
const PORT = 8888;

class CFWorkerSimulator {
  constructor() {
    this.server = http.createServer(this.handleRequest.bind(this));
  }

  async handleRequest(req, res) {
    const url = new URL(req.url, `http://${req.headers.host}`);
    
    // Set CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    
    if (req.method === 'OPTIONS') {
      res.writeHead(204);
      res.end();
      return;
    }

    // Health check
    if (url.pathname === '/health') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ 
        status: 'ok', 
        service: 'cf-worker-sim',
        domain: DOMAIN,
        resolver: RESOLVER_URL 
      }));
      return;
    }

    // DNS-over-HTTPS style endpoint
    if (url.pathname === '/dns-query' || url.pathname === '/dns-query/') {
      const name = url.searchParams.get('name');
      const type = url.searchParams.get('type') || 'A';
      
      if (!name) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Missing name parameter' }));
        return;
      }

      try {
        const dnsResult = await this.resolveDNS(name, type);
        res.writeHead(200, { 'Content-Type': 'application/dns-json' });
        res.end(JSON.stringify(dnsResult));
      } catch (error) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: error.message }));
      }
      return;
    }

    // API endpoint to resolve domain
    if (url.pathname === '/resolve' || url.pathname.startsWith('/resolve/')) {
      const domain = url.pathname.replace('/resolve/', '') || url.searchParams.get('domain');
      
      if (!domain) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Missing domain parameter' }));
        return;
      }

      try {
        const result = await this.resolveCryptoDomain(domain);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(result));
      } catch (error) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: error.message }));
      }
      return;
    }

    // Root - serve info about this worker
    if (url.pathname === '/' || url.pathname === '') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        service: '.crypto DNS Resolution Worker',
        domain: DOMAIN,
        endpoints: {
          'GET /health': 'Health check',
          'GET /dns-query?name=domain.crypto&type=A': 'DNS-over-HTTPS style query',
          'GET /resolve/domain.crypto': 'Full domain resolution',
          'GET /': 'This info'
        }
      }));
      return;
    }

    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Not found' }));
  }

  async resolveDNS(name, type) {
    // If not .crypto, return empty (would need traditional DNS)
    if (!name.endsWith('.crypto')) {
      return { Status: 3, TC: false, RD: true, RA: true, AD: false, CD: false, Question: [{ name, type }], Answer: [] };
    }

    // Resolve .crypto via our gateway
    const domainData = await this.resolveCryptoDomain(name);
    
    // Convert to DNS JSON response format
    const answers = [];
    
    if (type === 'A' && domainData.records && domainData.records._custom) {
      // Would need to parse records - simplified
      answers.push({
        name,
        type: 1,
        TTL: 300,
        data: domainData.records._custom.content || ''
      });
    }

    return {
      Status: 0,
      TC: false,
      RD: true,
      RA: true,
      AD: false,
      CD: false,
      Question: [{ name, type }],
      Answer: answers
    };
  }

  async resolveCryptoDomain(domain) {
    const url = `${RESOLVER_URL}/resolve/${domain}`;
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`Resolver returned ${response.status}`);
    }
    
    return await response.json();
  }

  start() {
    this.server.listen(PORT, () => {
      console.log(`Cloudflare Worker Simulator running on port ${PORT}`);
      console.log(`Serving domain: ${DOMAIN}`);
      console.log(`Resolver URL: ${RESOLVER_URL}`);
    });
  }
}

const worker = new CFWorkerSimulator();
worker.start();
