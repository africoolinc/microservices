/**
 * Data Aggregator - Fetch all data sources
 */

const adbService = require('./adb');
const servicesMonitor = require('./docker');
const tradingService = require('./trading');

function analyzeThreats(data) {
  const threats = [];
  
  // Check devices
  for (const device of data.devices) {
    if (!device.online) {
      threats.push({
        type: 'device_offline',
        severity: 'high',
        message: `${device.name} is offline`,
        source: device.id
      });
    }
    
    if (device.battery?.level < 20) {
      threats.push({
        type: 'low_battery',
        severity: 'medium',
        message: `${device.name} battery at ${device.battery.level}%`,
        source: device.id
      });
    }
    
    if (device.storage?.percent && parseInt(device.storage.percent) > 90) {
      threats.push({
        type: 'storage_full',
        severity: 'high',
        message: `${device.name} storage at ${device.storage.percent}`,
        source: device.id
      });
    }
  }
  
  // Check services
  for (const service of data.services) {
    if (service.containers?.error) {
      threats.push({
        type: 'service_error',
        severity: 'high',
        message: `StackForge SSH failed`,
        source: 'stackforge'
      });
    }
    
    if (service.containers?.running < service.containers?.total * 0.5) {
      threats.push({
        type: 'containers_degraded',
        severity: 'medium',
        message: `Only ${service.containers.running}/${service.containers.total} containers running`,
        source: 'stackforge'
      });
    }
  }
  
  return threats;
}

function analyzeOpportunities(data) {
  const opportunities = [];
  
  // Trading opportunities
  if (data.trading?.pnl && data.trading.pnl > 0) {
    opportunities.push({
      type: 'profit',
      source: 'hyperliquid',
      message: `Trading PnL: +$${data.trading.pnl.toFixed(2)}`,
      priority: 'high'
    });
  }
  
  // New subscribers could go here
  
  return opportunities;
}

async function fetchAll() {
  console.log('📡 Fetching data from all sources...');
  
  const data = {
    devices: [],
    services: [],
    threats: [],
    opportunities: [],
    trading: {}
  };
  
  // Fetch device data
  try {
    const deviceStatus = adbService.getFullStatus();
    data.devices.push(deviceStatus);
    console.log('  ✅ Device data fetched');
  } catch (e) {
    console.error('  ❌ Device fetch failed:', e.message);
    data.devices.push({ id: 'gibson-v20', online: false, error: e.message });
  }
  
  // Fetch services data
  try {
    const servicesStatus = servicesMonitor.getFullStatus();
    data.services.push(servicesStatus);
    console.log('  ✅ Services data fetched');
  } catch (e) {
    console.error('  ❌ Services fetch failed:', e.message);
  }
  
  // Fetch trading data
  try {
    const tradingData = await tradingService.getPortfolio();
    data.trading = tradingData;
    console.log('  ✅ Trading data fetched');
  } catch (e) {
    console.error('  ❌ Trading fetch failed:', e.message);
  }
  
  // Analyze threats and opportunities
  data.threats = analyzeThreats(data);
  data.opportunities = analyzeOpportunities(data);
  
  // Update global store
  global.dashData = {
    ...data,
    lastUpdate: new Date().toISOString()
  };
  
  console.log(`  🔴 Threats: ${data.threats.length}`);
  console.log(`  🟢 Opportunities: ${data.opportunities.length}`);
  console.log('✅ Data fetch complete');
  
  return data;
}

module.exports = { fetchAll, analyzeThreats, analyzeOpportunities };
