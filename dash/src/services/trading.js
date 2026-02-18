/**
 * Hyperliquid Trading Service
 */

const axios = require('axios');

const HL_API = 'https://api.hyperliquid.xyz';
const MASTER_ADDRESS = '0x970d1e1756804cc1420e1202cd3833d83f2b93d5';

class TradingService {
  async getPortfolio() {
    try {
      // Get wallet info
      const info = await axios.post(`${HL_API}/info`, {
        type: 'clearinghouseState',
        user: MASTER_ADDRESS
      }, { timeout: 10000 });
      
      const data = info.data;
      
      return {
        address: MASTER_ADDRESS,
        balance: parseFloat(data?.withdrawable || 0) / 1e6,
        pnl: parseFloat(data?.totalPnl || 0) / 1e6,
        marginUsed: parseFloat(data?.marginUsed || 0) / 1e6,
        timestamp: new Date().toISOString()
      };
    } catch (e) {
      console.error('Hyperliquid API error:', e.message);
      return {
        address: MASTER_ADDRESS,
        balance: 0,
        pnl: 0,
        error: e.message
      };
    }
  }
}

module.exports = new TradingService();
