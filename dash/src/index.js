/**
 * Gibson's Dash - Main Server
 * Firefly Command Center
 */

const express = require('express');
const cors = require('cors');
const cron = require('node-cron');

// Routes
const devicesRouter = require('./routes/devices');
const servicesRouter = require('./routes/services');
const tradingRouter = require('./routes/trading');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// In-memory store for dashboard data
global.dashData = {
  devices: [],
  services: [],
  threats: [],
  opportunities: [],
  trading: {},
  lastUpdate: null
};

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    service: "Gibson's Dash",
    version: '1.0.0',
    description: 'Firefly Command Center',
    endpoints: {
      health: '/health',
      status: '/api/status',
      devices: '/api/devices',
      services: '/api/services',
      trading: '/api/trading'
    }
  });
});

// Routes
app.use('/api/devices', devicesRouter);
app.use('/api/services', servicesRouter);
app.use('/api/trading', tradingRouter);

// Main status endpoint
app.get('/api/status', (req, res) => {
  res.json({
    status: 'online',
    lastUpdate: global.dashData.lastUpdate,
    uptime: process.uptime(),
    data: {
      devices: global.dashData.devices,
      services: global.dashData.services,
      threats: global.dashData.threats,
      opportunities: global.dashData.opportunities,
      trading: global.dashData.trading
    }
  });
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`🔥 Gibson's Dash running on port ${PORT}`);
  
  // Initial data fetch
  try {
    const { fetchAll } = require('./services/fetchAll');
    fetchAll();
  } catch (e) {
    console.log('Fetch service not available yet');
  }
  
  // Schedule polling every 5 minutes
  cron.schedule('*/5 * * * *', () => {
    console.log('🔄 Fetching latest data...');
    try {
      const { fetchAll } = require('./services/fetchAll');
      fetchAll();
    } catch (e) {
      console.log('Fetch service not available');
    }
  });
});

module.exports = app;
