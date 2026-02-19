/**
 * StackForge Service Monitor
 * Checks health of services on 10.144.118.159
 */

const { execSync } = require('child_process');

const STACKFORGE_HOST = process.env.STACKFORGE_HOST || '10.144.118.159';

class ServicesMonitor {
  constructor() {
    this.host = STACKFORGE_HOST;
  }
  
  exec(command) {
    try {
      const cmd = `ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no gibz@${this.host} "${command}"`;
      return execSync(cmd, { encoding: 'utf8', timeout: 15000 });
    } catch (e) {
      console.error(`SSH error: ${e.message}`);
      return null;
    }
  }
  
  getDockerContainers() {
    const output = this.exec('docker ps --format "{{.Names}}:{{.Status}}"');
    
    if (!output) return { error: 'SSH connection failed' };
    
    const containers = output.trim().split('\n').map(line => {
      const [name, status] = line.split(':');
      return { name, status: status || 'unknown', running: status?.includes('Up') };
    });
    
    const running = containers.filter(c => c.running).length;
    
    return {
      total: containers.length,
      running,
      containers
    };
  }
  
  getPublicServices() {
    const services = [
      { name: 'gateway', port: 18789, url: `http://${this.host}:18789/health` },
      { name: 'keycloak', port: 8080, url: `http://${this.host}:8080/health` },
      { name: 'kibana', port: 5601, url: `http://${this.host}:5601/api/status` },
      { name: 'kafka', port: 9092, url: null },
      { name: 'subservice', port: 5005, url: `http://${this.host}:5005/health` }
    ];
    
    // For now, return mock status - can integrate actual HTTP checks
    return services.map(s => ({
      ...s,
      status: 'unknown',
      checkedAt: new Date().toISOString()
    }));
  }
  
  getFullStatus() {
    const containers = this.getDockerContainers();
    
    return {
      host: this.host,
      name: 'StackForge',
      type: 'server',
      containers,
      publicServices: this.getPublicServices(),
      timestamp: new Date().toISOString()
    };
  }
}

module.exports = new ServicesMonitor();
