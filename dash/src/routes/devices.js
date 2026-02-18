/**
 * Devices Router
 */

const express = require('express');
const router = express.Router();
const adbService = require('../services/adb');

// Get all devices
router.get('/', (req, res) => {
  res.json(global.dashData.devices || []);
});

// Get single device
router.get('/:id', (req, res) => {
  const device = global.dashData.devices?.find(d => d.id === req.params.id);
  
  if (!device) {
    return res.status(404).json({ error: 'Device not found' });
  }
  
  res.json(device);
});

// Trigger device sync
router.post('/:id/sync', async (req, res) => {
  const status = adbService.getFullStatus();
  res.json({ message: 'Sync triggered', status });
});

module.exports = router;
