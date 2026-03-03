/**
 * Health Check Service
 */

const http = require('http');

const endpoints = [
  { name: 'resolver', url: 'http://resolver:8080/health', port: 8080 },
  { name: 'blockchain-listener', url: 'http://blockchain-listener:8080/health', port: 8080 },
  { name: 'dns-server', url: 'http://dns-server:8443/health', port: 8443 },
  { name: 'worker-api', url: 'http://worker-api:3000/health', port: 3000 }
];

async function checkEndpoint(endpoint) {
  try {
    const response = await fetch(endpoint.url);
    return { name: endpoint.name, status: response.ok ? 'healthy' : 'unhealthy' };
  } catch (error) {
    return { name: endpoint.name, status: 'unhealthy', error: error.message };
  }
}

const server = http.createServer(async (req, res) => {
  if (req.url === '/health') {
    const results = await Promise.all(endpoints.map(checkEndpoint));
    const allHealthy = results.every(r => r.status === 'healthy');
    
    res.writeHead(allHealthy ? 200 : 503, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: allHealthy ? 'healthy' : 'degraded', services: results }));
  } else {
    res.writeHead(404);
    res.end();
  }
});

server.listen(8081, () => {
  console.log('Health check listening on port 8081');
});
