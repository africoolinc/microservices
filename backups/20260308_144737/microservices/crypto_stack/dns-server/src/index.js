/**
 * DNS Server with DNS-over-HTTPS support for .crypto domains
 */

const { UDPClientServer, TCPClientServer } = require('dns2');
const express = require('express');
const axios = require('axios');
const cors = require('cors');
const winston = require('winston');

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
  port: parseInt(process.env.PORT || '8053'),
  dohPort: parseInt(process.env.DOH_PORT || '8443')
};

class DNSServer {
  constructor() {
    this.resolverUrl = CONFIG.resolverUrl;
    this.app = express();
    this.setupRoutes();
  }

  setupRoutes() {
    this.app.use(cors());
    this.app.use(express.json());

    // DNS-over-HTTPS endpoint
    this.app.get('/dns-query', async (req, res) => {
      try {
        const { name, type } = req.query;
        
        if (!name) {
          return res.status(400).json({ error: 'Missing name parameter' });
        }

        // Check if .crypto domain
        if (name.endsWith('.crypto')) {
          const result = await this.resolveFromBlockchain(name, type || 'A');
          return res.set('Content-Type', 'application/dns-json').json(result);
        }

        // Fallback to traditional DNS (Cloudflare)
        const result = await this.fallbackDNS(name, type || 'A');
        return res.set('Content-Type', 'application/dns-json').json(result);
      } catch (error) {
        logger.error('DNS query failed', { error: error.message });
        res.status(500).json({ error: error.message });
      }
    });

    // POST method for DoH
    this.app.post('/dns-query', async (req, res) => {
      try {
        const { name, type } = req.body;
        
        if (name.endsWith('.crypto')) {
          const result = await this.resolveFromBlockchain(name, type || 'A');
          return res.json(result);
        }

        const result = await this.fallbackDNS(name, type || 'A');
        res.json(result);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    // Health
    this.app.get('/health', (req, res) => {
      res.json({ status: 'ok', service: 'dns-server' });
    });
  }

  /**
   * Resolve .crypto domain from blockchain
   */
  async resolveFromBlockchain(domain, recordType = 'A') {
    try {
      const response = await axios.get(`${this.resolverUrl}/dns/${domain}`, {
        params: { type: recordType },
        timeout: 5000
      });

      return this.formatDNSResponse(domain, recordType, response.data);
    } catch (error) {
      logger.error('Blockchain resolution failed', { domain, error: error.message });
      return {
        Status: 2, // SERVFAIL
        TC: false,
        RD: true,
        RA: true,
        AD: false,
        CD: false,
        Question: [{ name: domain, type: recordType, class: 'IN' }],
        Answer: []
      };
    }
  }

  /**
   * Fallback to traditional DNS
   */
  async fallbackDNS(domain, recordType = 'A') {
    try {
      const typeCode = this.getTypeCode(recordType);
      const response = await axios.get(`https://cloudflare-dns.com/dns-query`, {
        params: { name: domain, type: typeCode },
        headers: { 'Accept': 'application/dns-json' },
        timeout: 5000
      });
      return response.data;
    } catch (error) {
      return {
        Status: 2,
        Question: [{ name: domain, type: recordType, class: 'IN' }],
        Answer: []
      };
    }
  }

  /**
   * Format response to DNS JSON format
   */
  formatDNSResponse(domain, type, data) {
    const records = [];
    
    if (data.records && data.records.data) {
      records.push({
        name: domain,
        type: this.getTypeCode(type),
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
      Question: [{ name: domain, type: this.getTypeCode(type), class: 'IN' }],
      Answer: records
    };
  }

  getTypeCode(type) {
    const types = {
      A: 1,
      AAAA: 28,
      CNAME: 5,
      TXT: 16,
      MX: 15,
      NS: 2,
      SOA: 6,
      CAA: 257
    };
    return types[type] || 1;
  }

  /**
   * Start DNS-over-HTTPS server
   */
  async startDOH() {
    this.app.listen(CONFIG.dohPort, () => {
      logger.info(`DNS-over-HTTPS server listening on port ${CONFIG.dohPort}`);
    });
  }

  async start() {
    await this.startDOH();
    logger.info('DNS server started');
  }
}

if (require.main === module) {
  const server = new DNSServer();
  server.start().catch(err => {
    logger.error('Failed to start DNS server', { error: err.message });
    process.exit(1);
  });
}

module.exports = DNSServer;
