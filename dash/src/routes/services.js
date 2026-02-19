/**
 * Services Router
 */

const express = require('express');
const router = express.Router();

// Get all services
router.get('/', (req, res) => {
  res.json(global.dashData.services || []);
});

// Get container status
router.get('/containers', (req, res) => {
  const services = global.dashData.services?.[0];
  res.json(services?.containers || []);
});

module.exports = router;
