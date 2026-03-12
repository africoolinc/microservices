/**
 * BTC Options Surge Predictor API
 * Main server for managing call options based on ML predictions
 */

const express = require('express');
const cors = require('cors');
const winston = require('winston');
const axios = require('axios');
const Redis = require('ioredis');

const app = express();
const PORT = process.env.PORT || 3000;

// Logger
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console()
  ]
});

// Redis cache
const redis = new Redis(process.env.REDIS_URL || 'redis://localhost:6379');

// Configuration
const CONFIG = {
  SURGE_THRESHOLD: 0.05, // 5%
  CONFIDENCE_THRESHOLD: 0.70, // 70%
  POSITION_SIZE_PCT: 0.02, // 2%
  STOP_LOSS_PCT: 0.50, // 50%
  EXCHANGE: process.env.EXCHANGE || 'deribit',
  DERIBIT_API: process.env.DERIBIT_API_URL || 'https://www.deribit.com/api/v2',
  DERIBIT_KEY: process.env.DERIBIT_KEY || '',
  DERIBIT_SECRET: process.env.DERIBIT_SECRET || ''
};

// Middleware
app.use(cors());
app.use(express.json());

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    service: 'btc-options-api',
    version: '1.0.0',
    config: {
      surgeThreshold: CONFIG.SURGE_THRESHOLD,
      confidenceThreshold: CONFIG.CONFIDENCE_THRESHOLD,
      positionSizePct: CONFIG.POSITION_SIZE_PCT
    }
  });
});

// Get current BTC price
app.get('/api/price', async (req, res) => {
  try {
    const cached = await redis.get('btc:price');
    if (cached) {
      return res.json(JSON.parse(cached));
    }

    // Fetch from Deribit
    const response = await axios.post(`${CONFIG.DERIBIT_API}/public/get_index_price`, {
      index_name: 'btc_usd'
    });
    
    const price = response.data.result.index_price;
    
    await redis.setex('btc:price', 30, JSON.stringify({ price, timestamp: Date.now() }));
    
    res.json({ price, timestamp: Date.now() });
  } catch (error) {
    logger.error('Price fetch error:', error.message);
    res.status(500).json({ error: error.message });
  }
});

// Get current predictions
app.get('/api/predictions', async (req, res) => {
  try {
    const cached = await redis.get('predictions:latest');
    if (cached) {
      return res.json(JSON.parse(cached));
    }
    
    // Return mock data for now (ML model integration pending)
    const predictions = {
      btc: {
        currentPrice: 85000,
        predictedChange24h: 0.062, // 6.2%
        predictedChange72h: 0.098, // 9.8%
        confidence: 0.78,
        surgeProbability: 0.82,
        recommendation: 'BUY_CALL',
        strikePremium: 0.08, // 8% OTM
        expiry: '7d'
      },
      generatedAt: new Date().toISOString(),
      model: 'CNN-LSTM-v1'
    };
    
    await redis.setex('predictions:latest', 300, JSON.stringify(predictions));
    
    res.json(predictions);
  } catch (error) {
    logger.error('Prediction error:', error.message);
    res.status(500).json({ error: error.message });
  }
});

// Get options chain
app.get('/api/options/chain', async (req, res) => {
  try {
    const { expiry = '7d' } = req.query;
    
    // Get current BTC price
    let price;
    const cached = await redis.get('btc:price');
    if (cached) {
      price = JSON.parse(cached).price;
    } else {
      const response = await axios.post(`${CONFIG.DERIBIT_API}/public/get_index_price`, {
        index_name: 'btc_usd'
      });
      price = response.data.result.index_price;
    }
    
    // Generate options chain (simplified)
    const strikes = [];
    const premiumPct = 0.03; // 3% for ATM
    
    for (let i = -15; i <= 20; i += 5) {
      const strike = Math.round(price * (1 + i / 100) / 100) * 100;
      const premium = Math.round(price * premiumPct * (1 + Math.abs(i) / 100) * 100) / 100;
      
      strikes.push({
        strike,
        premium,
        premiumPct: (premium / price * 100).toFixed(2),
        otmPct: i,
        type: i > 0 ? 'CALL' : 'PUT',
        breakEven: i > 0 ? strike + premium : strike - premium,
        maxLoss: premium,
        maxProfit: i > 0 ? (price - strike - premium) * 100 : (strike - price - premium) * 100
      });
    }
    
    res.json({
      underlying: 'BTC',
      spotPrice: price,
      expiry,
      strikes,
      generatedAt: new Date().toISOString()
    });
  } catch (error) {
    logger.error('Options chain error:', error.message);
    res.status(500).json({ error: error.message });
  }
});

// Get portfolio positions
app.get('/api/portfolio', async (req, res) => {
  try {
    const cached = await redis.get('portfolio:positions');
    if (cached) {
      return res.json(JSON.parse(cached));
    }
    
    // Mock portfolio
    const positions = {
      totalValue: 0,
      positions: [],
      pnl: { realized: 0, unrealized: 0 },
      availableCapital: 10000,
      riskUtilization: 0
    };
    
    await redis.setex('portfolio:positions', 60, JSON.stringify(positions));
    
    res.json(positions);
  } catch (error) {
    logger.error('Portfolio error:', error.message);
    res.status(500).json({ error: error.message });
  }
});

// Execute options trade (dry run by default)
app.post('/api/trade/execute', async (req, res) => {
  try {
    const { 
      action = 'BUY_CALL',
      strike,
      expiry = '7d',
      size = 0.01,
      dryRun = true 
    } = req.body;
    
    const result = {
      success: true,
      action,
      strike,
      expiry,
      size,
      dryRun,
      timestamp: new Date().toISOString(),
      message: dryRun 
        ? 'DRY RUN - No actual trade executed' 
        : 'Trade execution not yet implemented - requires API keys'
    };
    
    logger.info('Trade executed:', result);
    
    res.json(result);
  } catch (error) {
    logger.error('Trade execution error:', error.message);
    res.status(500).json({ error: error.message });
  }
});

// Get signals history
app.get('/api/signals', async (req, res) => {
  try {
    const { limit = 20 } = req.query;
    
    // Mock signals
    const signals = [
      {
        id: 'sig_001',
        timestamp: new Date(Date.now() - 3600000).toISOString(),
        type: 'SURGE_WARNING',
        confidence: 0.82,
        predictedMove: 0.078,
        action: 'BUY_CALL_8%OTM',
        status: 'EXPIRED'
      },
      {
        id: 'sig_002',
        timestamp: new Date(Date.now() - 7200000).toISOString(),
        type: 'TREND_REVERSAL',
        confidence: 0.65,
        predictedMove: 0.032,
        action: 'HOLD',
        status: 'HIT'
      }
    ];
    
    res.json({ signals: signals.slice(0, limit), count: signals.length });
  } catch (error) {
    logger.error('Signals error:', error.message);
    res.status(500).json({ error: error.message });
  }
});

// Start server
app.listen(PORT, () => {
  logger.info(`BTC Options API running on port ${PORT}`);
  logger.info(`Surge Threshold: ${CONFIG.SURGE_THRESHOLD * 100}%`);
  logger.info(`Confidence Threshold: ${CONFIG.CONFIDENCE_THRESHOLD * 100}%`);
});

module.exports = { app, CONFIG };
