/**
 * ADB Device Service
 * Fetches data from Android devices via ADB
 */

const { execSync } = require('child_process');

const ADB_HOST = process.env.ADB_HOST || '10.144.180.80';
const ADB_PORT = process.env.ADB_PORT || '5555';

class AdbService {
  constructor() {
    this.deviceIp = `${ADB_HOST}:${ADB_PORT}`;
  }
  
  exec(command) {
    try {
      const cmd = `adb -s ${this.deviceIp} ${command}`;
      return execSync(cmd, { encoding: 'utf8', timeout: 10000 }).trim();
    } catch (e) {
      console.error(`ADB error: ${e.message}`);
      return null;
    }
  }
  
  getDeviceInfo() {
    return {
      model: this.exec('shell getprop ro.product.model'),
      manufacturer: this.exec('shell getprop ro.product.manufacturer'),
      android: this.exec('shell getprop ro.build.version.release'),
      serial: this.exec('shell getprop ro.serialno'),
      ip: this.exec("shell ifconfig wlan0 | grep 'inet addr' | cut -d: -f2 | awk '{print $1}'")
    };
  }
  
  getBattery() {
    const output = this.exec('shell dumpsys battery');
    const data = {};
    
    if (!output) return { level: 0, status: 'unknown' };
    
    for (const line of output.split('\n')) {
      if (line.includes('level:')) data.level = parseInt(line.split(':')[1]);
      if (line.includes('status:')) data.status = line.split(':')[1].trim();
      if (line.includes('temperature:')) data.temperature = parseFloat(line.split(':')[1]) / 10;
      if (line.includes('health:')) data.health = line.split(':')[1].trim();
    }
    
    return data;
  }
  
  getStorage() {
    const output = this.exec('shell df /data');
    
    try {
      const parts = output.split('\n')[1].split();
      return {
        total: parts[1],
        used: parts[2],
        available: parts[3],
        percent: parts[4]
      };
    } catch (e) {
      return {};
    }
  }
  
  getNetwork() {
    return {
      wifiIp: this.exec("shell ifconfig wlan0 | grep 'inet addr' | cut -d: -f2 | awk '{print $1}'") || 'N/A',
      wifiSsid: this.exec('shell dumpsys wifi | grep "SSID:" | head -1')?.split(':')[1]?.trim() || 'N/A'
    };
  }
  
  getFullStatus() {
    return {
      id: 'gibson-v20',
      name: "Gibson's V20",
      type: 'android',
      connection: 'adb-ota',
      ip: ADB_HOST,
      online: true,
      ...this.getDeviceInfo(),
      battery: this.getBattery(),
      storage: this.getStorage(),
      network: this.getNetwork(),
      timestamp: new Date().toISOString()
    };
  }
}

module.exports = new AdbService();
