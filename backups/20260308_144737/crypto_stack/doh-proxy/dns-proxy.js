const dgram = require('dgram');
const http = require('http');
const dns = require('dns');
const { URL } = require('url');

const UPSTREAM_RESOLVER = process.env.UPSTREAM_RESOLVER || 'http://resolver-gateway:8080';
const CLOUDFLARE_DNS = process.env.CLOUDFLARE_DNS || '1.1.1.1';
const PORT = 8053;

class DNSProxy {
  constructor() {
    this.server = dgram.createSocket('udp4');
    this.setupHandlers();
  }

  setupHandlers() {
    this.server.on('message', (msg, rinfo) => {
      this.handleDNSQuery(msg, rinfo);
    });

    this.server.on('error', (err) => {
      console.error('DNS Server error:', err);
      this.server.close();
    });
  }

  async handleDNSQuery(msg, rinfo) {
    try {
      // Parse DNS query (simplified - just extract domain)
      const domain = this.extractDomainFromQuery(msg);
      
      if (domain && domain.endsWith('.crypto')) {
        // Resolve .crypto via our resolver gateway
        await this.resolveCryptoDomain(domain, msg, rinfo);
      } else {
        // Forward to traditional DNS
        await this.forwardToDNS(msg, rinfo);
      }
    } catch (error) {
      console.error('Query handling error:', error);
      // Send NXDOMAIN on error
      this.sendResponse(msg, Buffer.from([0x00, 0x81, 0x80, 0x00, 0x01, 0x00, 0x00, 0x01, 0x00, 0x00]), rinfo);
    }
  }

  extractDomainFromQuery(msg) {
    try {
      // Very basic DNS query parsing
      const buffer = msg;
      // Skip header (12 bytes) and extract domain from question section
      let pos = 12;
      let domain = '';
      
      while (buffer[pos] !== 0) {
        const len = buffer[pos];
        if (len > 63) {
          // Compression pointer - skip for now
          break;
        }
        if (domain) domain += '.';
        domain += buffer.slice(pos + 1, pos + 1 + len).toString();
        pos += 1 + len;
      }
      
      return domain || null;
    } catch (e) {
      return null;
    }
  }

  async resolveCryptoDomain(domain, originalMsg, rinfo) {
    try {
      // Call our resolver gateway
      const url = `${UPSTREAM_RESOLVER}/resolve/${domain}`;
      const response = await fetch(url);
      const data = await response.json();

      // Build DNS response
      const responseBuffer = this.buildDNSResponse(domain, data, originalMsg);
      this.sendResponse(originalMsg, responseBuffer, rinfo);
    } catch (error) {
      console.error('Crypto resolution error:', error);
      // Fallback to traditional DNS
      await this.forwardToDNS(originalMsg, rinfo);
    }
  }

  buildDNSResponse(domain, data, originalMsg) {
    // Build a basic DNS response with A records if available
    const response = Buffer.alloc(512);
    
    // Copy transaction ID from query
    originalMsg.copy(response, 0, 0, 2);
    
    // Flags: Response, Authoritative
    response[2] = 0x81; // QR=1, Opcode=0, AA=1, TC=0, RD=1
    response[3] = 0x80; // RA=1, Z=0, RCODE=0
    
    // Question count
    response[4] = 0x00;
    response[5] = 0x01;
    
    // Answer count (0 for now - can be populated with actual records)
    response[6] = 0x00;
    response[7] = 0x00;
    
    // Authority/Additional counts
    response[8] = 0x00;
    response[9] = 0x00;
    response[10] = 0x00;
    response[11] = 0x00;

    return response.slice(0, 12);
  }

  async forwardToDNS(msg, rinfo) {
    // Use Node's built-in DNS to resolve
    try {
      const domain = this.extractDomainFromQuery(msg);
      if (!domain) {
        this.sendErrorResponse(msg, rinfo);
        return;
      }

      dns.resolve4(domain, (err, addresses) => {
        if (err) {
          this.sendErrorResponse(msg, rinfo);
          return;
        }

        // Build response with A records
        const response = this.buildARecordResponse(domain, addresses, msg);
        this.sendResponse(msg, response, rinfo);
      });
    } catch (e) {
      this.sendErrorResponse(msg, rinfo);
    }
  }

  buildARecordResponse(domain, addresses, query) {
    // Build DNS response with A records
    const numAnswers = addresses.length;
    const buffer = Buffer.alloc(512);
    
    // Copy transaction ID
    query.copy(buffer, 0, 0, 2);
    
    // Flags
    buffer[2] = 0x81;
    buffer[3] = 0x80;
    
    // Counts
    buffer[4] = 0x00; buffer[5] = 0x01; // Questions
    buffer[6] = (numAnswers >> 8) & 0xFF; buffer[7] = numAnswers & 0xFF; // Answers
    buffer[8] = 0x00; buffer[9] = 0x00; // Authority
    buffer[10] = 0x00; buffer[11] = 0x00; // Additional
    
    // Copy question section
    let pos = 12;
    const questionStart = 12;
    while (query[pos] !== 0) {
      const len = query[pos];
      query.copy(buffer, pos, pos, pos + 1 + len);
      pos += 1 + len;
    }
    buffer[pos] = 0;
    pos++;
    buffer[pos] = 0x00; buffer[pos+1] = 0x01; // Type A
    pos += 2;
    buffer[pos] = 0x00; buffer[pos+1] = 0x01; // Class IN
    
    // Add answer records
    pos += 2;
    const answerStart = pos;
    
    for (const ip of addresses) {
      // Name pointer to question
      buffer[pos] = 0xC0; buffer[pos+1] = questionStart;
      pos += 2;
      
      // Type A, Class IN, TTL
      buffer[pos] = 0x00; buffer[pos+1] = 0x01;
      pos += 2;
      buffer[pos] = 0x00; buffer[pos+1] = 0x01;
      pos += 2;
      buffer[pos] = 0x00; buffer[pos+1] = 0x00; buffer[pos+2] = 0x00; buffer[pos+3] = 0xE8; // TTL 232
      pos += 4;
      
      // Data length (4 for A record)
      buffer[pos] = 0x00; buffer[pos+1] = 0x04;
      pos += 2;
      
      // IP address
      const parts = ip.split('.');
      buffer[pos] = parseInt(parts[0]);
      buffer[pos+1] = parseInt(parts[1]);
      buffer[pos+2] = parseInt(parts[2]);
      buffer[pos+3] = parseInt(parts[3]);
      pos += 4;
    }
    
    return buffer.slice(0, pos);
  }

  sendResponse(query, response, rinfo) {
    this.server.send(response, 0, response.length, rinfo.port, rinfo.address);
  }

  sendErrorResponse(msg, rinfo) {
    // NXDOMAIN response
    const response = Buffer.alloc(12);
    msg.copy(response, 0, 0, 2);
    response[2] = 0x81; // Response
    response[3] = 0x83; // NXDOMAIN
    response[4] = 0x00; response[5] = 0x01; // QDCOUNT
    response[6] = 0x00; response[7] = 0x00; // ANCOUNT
    this.sendResponse(msg, response, rinfo);
  }

  start() {
    this.server.bind(PORT);
    console.log(`DNS Proxy listening on port ${PORT}`);
    console.log(`.crypto domains will be resolved via: ${UPSTREAM_RESOLVER}`);
    console.log(`Other domains will use: ${CLOUDFLARE_DNS}`);
  }
}

// Start the DNS proxy
const proxy = new DNSProxy();
proxy.start();
