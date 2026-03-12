const express = require('express');
const cors = require('cors');
const { v4: uuidv4 } = require('uuid');

const app = express();
const PORT = process.env.PORT || 5100;

app.use(cors());
app.use(express.json());

// In-memory data stores
const workflows = [
  { id: uuidv4(), name: 'Payment Flow A', status: 'draft', created: new Date().toISOString() },
  { id: uuidv4(), name: 'Data Sync B', status: 'draft', created: new Date().toISOString() },
  { id: uuidv4(), name: 'Token Bridge C', status: 'draft', created: new Date().toISOString() }
];

const payments = [];
const pings = [];
const requests = [];

let startTime = Date.now();

// Initialize with sample data
for (let i = 0; i < 10; i++) {
  payments.push({
    id: uuidv4(),
    amount: Math.floor(Math.random() * 1000) + 100,
    currency: 'USDT',
    status: i < 5 ? 'pending' : 'completed',
    timestamp: new Date(Date.now() - Math.random() * 86400000).toISOString()
  });
}

for (let i = 0; i < 20; i++) {
  pings.push({
    id: uuidv4(),
    service: ['bridge-api', 'bridge-heartbeat', 'bridge-tracker'][Math.floor(Math.random() * 3)],
    latency: Math.floor(Math.random() * 200) + 10,
    timestamp: new Date(Date.now() - Math.random() * 3600000).toISOString()
  });
}

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    service: 'bridge-api-dev',
    version: '1.0.0',
    uptime: (Date.now() - startTime) / 1000,
    timestamp: new Date().toISOString()
  });
});

// Heartbeat
app.get('/heartbeat', (req, res) => {
  res.json({
    status: 'alive',
    timestamp: new Date().toISOString(),
    uptime: (Date.now() - startTime) / 1000
  });
});

// Workflows
app.get('/api/workflows', (req, res) => {
  res.json({ workflows, total: workflows.length });
});

app.post('/api/workflows', (req, res) => {
  const workflow = {
    id: uuidv4(),
    name: req.body.name || 'New Workflow',
    status: 'draft',
    created: new Date().toISOString()
  };
  workflows.push(workflow);
  res.status(201).json(workflow);
});

app.post('/api/workflows/:id/simulate', (req, res) => {
  const workflow = workflows.find(w => w.id === req.params.id);
  if (!workflow) {
    return res.status(404).json({ error: 'Workflow not found' });
  }
  workflow.status = 'running';
  setTimeout(() => {
    workflow.status = 'completed';
  }, 2000);
  res.json({ message: 'Simulation started', workflow });
});

// Pings
app.get('/api/pings', (req, res) => {
  res.json({ pings, total: pings.length, recent: pings.slice(-10) });
});

app.post('/api/pings', (req, res) => {
  const ping = {
    id: uuidv4(),
    service: req.body.service || 'unknown',
    latency: req.body.latency || 0,
    timestamp: new Date().toISOString()
  };
  pings.push(ping);
  res.status(201).json(ping);
});

// Payments
app.get('/api/payments', (req, res) => {
  res.json({ 
    payments, 
    total: payments.length,
    pending: payments.filter(p => p.status === 'pending').length,
    completed: payments.filter(p => p.status === 'completed').length
  });
});

app.post('/api/payments', (req, res) => {
  const payment = {
    id: uuidv4(),
    amount: req.body.amount || 0,
    currency: req.body.currency || 'USDT',
    status: 'pending',
    timestamp: new Date().toISOString()
  };
  payments.push(payment);
  res.status(201).json(payment);
});

// Stats
app.get('/api/stats', (req, res) => {
  res.json({
    workflows: { total: workflows.length, active: workflows.filter(w => w.status === 'running').length, draft: workflows.filter(w => w.status === 'draft').length },
    simulations: { total: 0, completed: 0, failed: 0 },
    pings: { total: pings.length, recent: pings.slice(-10).length },
    payments: { 
      total: payments.length, 
      pending: payments.filter(p => p.status === 'pending').length,
      completed: payments.filter(p => p.status === 'completed').length,
      failed: payments.filter(p => p.status === 'failed').length
    },
    requests: { total: requests.length },
    heartbeat: { last: null, history: 0 }
  });
});

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    service: 'Bridge API SaaS',
    version: '1.0.0',
    description: 'Data aggregation service for crypto services',
    endpoints: [
      'GET /health',
      'GET /heartbeat',
      'GET /api/workflows',
      'POST /api/workflows',
      'GET /api/pings',
      'POST /api/pings',
      'GET /api/payments',
      'POST /api/payments',
      'GET /api/stats'
    ]
  });
});

app.listen(PORT, () => {
  console.log(`Bridge API DEV running on port ${PORT}`);
});
