/**
 * Trading Router
 */

const express = require('express');
const router = express.Router();
const tradingService = require('../services/trading');

// Get portfolio
router.get('/', async (req, res) => {
  const portfolio = await tradingService.getPortfolio();
  res.json(portfolio);
});

module.exports = router;
