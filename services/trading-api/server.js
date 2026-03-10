/**
 * Gibson Trading API - Unified API-as-a-Service Platform
 * 
 * Features:
 * - API Key Authentication
 * - Rate Limiting per tier
 * - Subscription management
 * - Unified access to BTC Options Bot + Bridge API
 * 
 * Tiers:
 * - FREE: 100 req/min, basic endpoints
 * - STARTER ($29/mo): 500 req/min, all endpoints
 * - PRO ($59/mo): 2000 req/min, priority support
 * - ENTERPRISE ($99/mo): unlimited, dedicated infrastructure
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const { v4: uuidv4 } = require('uuid');
const axios = require('axios');

const app = express();
const PORT = process.env.PORT || 5200;

// Configuration
const CONFIG = {
  BTC_OPTIONS_URL: process.env.BTC_OPTIONS_URL || 'http://localhost:5000',
  BRIDGE_API_URL: process.env.BRIDGE_API_URL || 'http://localhost:3100'
};

// Tier configuration
const TIERS = {
  FREE: { name: 'Free', price: 0, requestsPerMinute: 100, features: ['price', 'health'] },
  STARTER: { name: 'Starter', price: 29, requestsPerMinute: 500, features: ['price', 'predictions', 'options_chain', 'signals', 'portfolio'] },
  PRO: { name: 'Pro', price: 59, requestsPerMinute: 2000, features: ['price', 'predictions', 'options_chain', 'signals', 'portfolio', 'trade_execute'] },
  ENTERPRISE: { name: 'Enterprise', price: 99, requestsPerMinute: 10000, features: ['price', 'predictions', 'options_chain', 'signals', 'portfolio', 'trade_execute', 'webhooks'] }
};

// In-memory stores
const users = new Map();
const apiKeys = new Map();
const subscriptions = new Map();

// Initialize demo
function initDemoData() {
  const demoUserId = 'demo-user-001';
  const demoKey = 'gib_live_' + uuidv4().replace(/-/g, '').substring(0, 32);
  
  users.set(demoUserId, { id: demoUserId, email: 'demo@gibson.trade', name: 'Demo User', tier: 'FREE', createdAt: new Date().toISOString() });
  apiKeys.set(demoKey, { key: demoKey, userId: demoUserId, tier: 'FREE', createdAt: new Date().toISOString() });
  subscriptions.set(demoUserId, { userId: demoUserId, tier: 'FREE', status: 'active', currentPeriodEnd: new Date(Date.now() + 30*24*60*60*1000).toISOString() });
  
  console.log('Demo API Key:', demoKey);
  console.log('Demo User: demo@gibson.trade');
}

initDemoData();

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json());

// Get tier from key
function getTierFromKey(apiKey) {
  const keyData = apiKeys.get(apiKey);
  return keyData ? keyData.tier : 'FREE';
}

// Rate limiter middleware
function tierRateLimit(req, res, next) {
  const apiKey = req.headers['x-api-key'] || req.query.api_key;
  const tier = getTierFromKey(apiKey) || 'FREE';
  const requestsPerMinute = TIERS[tier]?.requestsPerMinute || 100;
  
  rateLimit({ windowMs: 60000, max: requestsPerMinute, message: { error: 'Rate limit exceeded', retryAfter: 60 } })(req, res, next);
}

// Auth middleware
function authenticate(req, res, next) {
  const apiKey = req.headers['x-api-key'] || req.query.api_key;
  if (!apiKey) return res.status(401).json({ error: 'API key required', hint: 'Add X-API-Key header' });
  const keyData = apiKeys.get(apiKey);
  if (!keyData) return res.status(401).json({ error: 'Invalid API key' });
  req.user = users.get(keyData.userId);
  req.keyData = keyData;
  next();
}

// Health
app.get('/health', (req, res) => res.json({ status: 'ok', service: 'gibson-trading-api', version: '1.0.0', timestamp: new Date().toISOString() }));

// Tiers
app.get('/api/v1/tiers', (req, res) => res.json({ tiers: Object.entries(TIERS).map(([k,v]) => ({ id:k, ...v })) }));

// Register
app.post('/api/v1/auth/register', async (req, res) => {
  const { email, password, name } = req.body;
  if (!email || !password) return res.status(400).json({ error: 'Email and password required' });
  
  const userId = uuidv4();
  const newKey = 'gib_live_' + uuidv4().replace(/-/g, '').substring(0, 32);
  
  users.set(userId, { id: userId, email, name: name||email.split('@')[0], tier: 'FREE', createdAt: new Date().toISOString() });
  apiKeys.set(newKey, { key: newKey, userId, tier: 'FREE', createdAt: new Date().toISOString() });
  subscriptions.set(userId, { userId, tier: 'FREE', status: 'active', currentPeriodEnd: new Date(Date.now() + 30*24*60*60*1000).toISOString() });
  
  res.status(201).json({ message: 'Registration successful', user: { id: userId, email, name: name||email.split('@')[0] }, apiKey: newKey, tier: 'FREE' });
});

// Login
app.post('/api/v1/auth/login', (req, res) => {
  const { email } = req.body;
  for (const [id, user] of users) {
    if (user.email === email) {
      for (const [key, keyData] of apiKeys) {
        if (keyData.userId === id) return res.json({ user: { id: user.id, email: user.email, name: user.name }, apiKey: key, tier: user.tier });
      }
    }
  }
  res.status(401).json({ error: 'Invalid credentials' });
});

// Key info
app.get('/api/v1/auth/key', authenticate, (req, res) => {
  const sub = subscriptions.get(req.user.id);
  res.json({ key: req.keyData.key, tier: req.user.tier, features: TIERS[req.user.tier].features, subscription: sub });
});

// Upgrade
app.post('/api/v1/subscription/upgrade', authenticate, (req, res) => {
  const { tier } = req.body;
  if (!TIERS[tier]) return res.status(400).json({ error: 'Invalid tier' });
  req.user.tier = tier;
  users.set(req.user.id, req.user);
  req.keyData.tier = tier;
  apiKeys.set(req.keyData.key, req.keyData);
  subscriptions.set(req.user.id, { userId: req.user.id, tier, status: 'active', currentPeriodEnd: new Date(Date.now() + 30*24*60*60*1000).toISOString() });
  res.json({ message: 'Subscription upgraded', tier, price: TIERS[tier].price, features: TIERS[tier].features });
});

// Protected endpoints
app.get('/api/v1/price', authenticate, tierRateLimit, async (req, res) => {
  try {
    const response = await axios.get(`${CONFIG.BTC_OPTIONS_URL}/api/price`, { timeout: 5000 });
    res.json(response.data);
  } catch { res.json({ price: 85000, timestamp: new Date().toISOString(), source: 'mock' }); }
});

app.get('/api/v1/predictions', authenticate, tierRateLimit, (req, res) => {
  if (!TIERS[req.user.tier].features.includes('predictions')) return res.status(403).json({ error: 'Upgrade to Starter tier for predictions' });
  res.json({ btc: { currentPrice: 85000, predictedChange24h: 0.062, confidence: 0.78, recommendation: 'BUY_CALL' }, generatedAt: new Date().toISOString() });
});

app.get('/api/v1/options/chain', authenticate, tierRateLimit, (req, res) => {
  if (!TIERS[req.user.tier].features.includes('options_chain')) return res.status(403).json({ error: 'Upgrade to Starter tier for options chain' });
  res.json({ underlying: 'BTC', spotPrice: 85000, strikes: [], generatedAt: new Date().toISOString() });
});

app.get('/api/v1/signals', authenticate, tierRateLimit, (req, res) => {
  if (!TIERS[req.user.tier].features.includes('signals')) return res.status(403).json({ error: 'Upgrade to Starter tier for signals' });
  res.json({ signals: [], count: 0 });
});

app.get('/api/v1/portfolio', authenticate, tierRateLimit, (req, res) => {
  if (!TIERS[req.user.tier].features.includes('portfolio')) return res.status(403).json({ error: 'Upgrade to Starter tier for portfolio' });
  res.json({ totalValue: 0, positions: [], availableCapital: 10000 });
});

app.post('/api/v1/trade/execute', authenticate, tierRateLimit, (req, res) => {
  if (!TIERS[req.user.tier].features.includes('trade_execute')) return res.status(403).json({ error: 'Upgrade to Pro tier for trade execution' });
  res.json({ success: true, message: 'Dry run - trade not executed', ...req.body });
});

// Bridge API
app.get('/api/v1/bridge/workflows', authenticate, tierRateLimit, async (req, res) => {
  try { const r = await axios.get(`${CONFIG.BRIDGE_API_URL}/api/workflows`, { timeout: 5000 }); res.json(r.data); }
  catch { res.json({ workflows: [], total: 0 }); }
});

app.get('/api/v1/bridge/stats', authenticate, tierRateLimit, async (req, res) => {
  try { const r = await axios.get(`${CONFIG.BRIDGE_API_URL}/api/stats`, { timeout: 5000 }); res.json(r.data); }
  catch { res.json({ error: 'Bridge API unavailable' }); }
});

// Root
app.get('/', (req, res) => res.json({
  service: 'Gibson Trading API', version: '1.0.0', description: 'Unified API-as-a-Service Platform',
  tiers: '/api/v1/tiers', auth: { register: 'POST /api/v1/auth/register', login: 'POST /api/v1/auth/login' }
}));

app.listen(PORT, () => console.log(`🚀 Gibson Trading API running on port ${PORT}`));
