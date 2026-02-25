"""
Insilico/Blofin Trading API Integration Module
==============================================
Provides connectivity to Insilico Terminal's Blofin API for:
- Market data (prices, order books, trades)
- Account positions and balances
- Order placement (future phase)

Author: Gibson Microservices
Date: 2026-02-25
"""

import os
import time
import hmac
import hashlib
import base64
import json
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BLOFIN_API_KEY = os.environ.get('BLOFIN_API_KEY', '')
BLOFIN_API_SECRET = os.environ.get('BLOFIN_API_SECRET', '')
BLOFIN_API_PASSPHRASE = os.environ.get('BLOFIN_API_PASSPHRASE', '')
BLOFIN_BASE_URL = os.environ.get('BLOFIN_BASE_URL', 'https://api.blofin.com')

# Local IP for whitelist (current public IP)
CURRENT_IP = os.environ.get('CURRENT_IP', '104.28.211.149')


class BlofinAPI:
    """Blofin API Client for Futures Trading"""
    
    def __init__(self, api_key: str = None, api_secret: str = None, passphrase: str = None):
        self.api_key = api_key or BLOFIN_API_KEY
        self.api_secret = api_secret or BLOFIN_API_SECRET
        self.passphrase = passphrase or BLOFIN_API_PASSPHRASE
        self.base_url = BLOFIN_BASE_URL
        
    def _generate_signature(self, timestamp: str, method: str, path: str, body: str = '') -> str:
        """Generate HMAC SHA256 signature for API authentication"""
        message = timestamp + method + path + body
        mac = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        )
        return base64.b64encode(mac.digest()).decode('utf-8')
    
    def _generate_headers(self, method: str, path: str, body: str = '') -> Dict[str, str]:
        """Generate authentication headers"""
        timestamp = str(int(time.time() * 1000))
        signature = self._generate_signature(timestamp, method, path, body)
        
        return {
            'Content-Type': 'application/json',
            'BLOFIN-ACCESSKEY': self.api_key,
            'BLOFIN-TIMESTAMP': timestamp,
            'BLOFIN-SIGNATURE': signature,
            'BLOFIN-PASSPHRASE': self.passphrase
        }
    
    def get_account_balance(self) -> Dict[str, Any]:
        """Get account balance"""
        path = '/api/v1/account/balance'
        headers = self._generate_headers('GET', path)
        
        try:
            response = requests.get(self.base_url + path, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get balance: {e}")
            return {'error': str(e)}
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions"""
        path = '/api/v1/positions'
        headers = self._generate_headers('GET', path)
        
        try:
            response = requests.get(self.base_url + path, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json().get('data', [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get positions: {e}")
            return []
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker for specific symbol (e.g., BTC-USDT-PERPETUAL)"""
        path = f'/api/v1/market/ticker?symbol={symbol}'
        headers = self._generate_headers('GET', path)
        
        try:
            response = requests.get(self.base_url + path, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get ticker: {e}")
            return {'error': str(e)}
    
    def get_orderbook(self, symbol: str, size: int = 20) -> Dict[str, Any]:
        """Get order book for symbol"""
        path = f'/api/v1/market/orderbook?symbol={symbol}&size={size}'
        headers = self._generate_headers('GET', path)
        
        try:
            response = requests.get(self.base_url + path, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get orderbook: {e}")
            return {'error': str(e)}
    
    def get_instruments(self, inst_type: str = 'FUTURE') -> List[Dict[str, Any]]:
        """Get available trading instruments"""
        path = f'/api/v1/instruments?instType={inst_type}'
        headers = self._generate_headers('GET', path)
        
        try:
            response = requests.get(self.base_url + path, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json().get('data', [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get instruments: {e}")
            return []
    
    def place_order(self, symbol: str, side: str, size: float, 
                   order_type: str = 'market', price: float = None) -> Dict[str, Any]:
        """Place a trading order"""
        path = '/api/v1/orders'
        body = json.dumps({
            'symbol': symbol,
            'side': side,  # 'buy' or 'sell'
            'size': size,
            'type': order_type,  # 'market' or 'limit'
            'price': price
        })
        headers = self._generate_headers('POST', path, body)
        
        try:
            response = requests.post(self.base_url + path, headers=headers, 
                                    data=body, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to place order: {e}")
            return {'error': str(e)}


# Trading Signal Generator (Mock AI)
class TradingSignals:
    """AI-powered trading signal generator"""
    
    def __init__(self, api_client: BlofinAPI):
        self.api = api_client
        
    def generate_signal(self, symbol: str = 'BTC-USDT-PERPETUAL') -> Dict[str, Any]:
        """
        Generate trading signal based on market data
        In production: Use ML models for signal generation
        """
        # Get current market data
        ticker = self.api.get_ticker(symbol)
        orderbook = self.api.get_orderbook(symbol)
        
        if 'error' in ticker:
            return {'status': 'error', 'message': ticker['error']}
        
        # Simple signal logic (placeholder for ML model)
        # In production: Use trained model weights
        current_price = float(ticker.get('last', 0))
        bid_1 = float(orderbook.get('bids', [[0, 0]])[0][0]) if orderbook.get('bids') else 0
        ask_1 = float(orderbook.get('asks', [[0, 0]])[0][0]) if orderbook.get('asks') else 0
        spread = ask_1 - bid_1
        
        # Signal based on spread and price movement
        signal = 'hold'
        confidence = 0.5
        
        if spread < current_price * 0.001:  # Tight spread = high liquidity
            confidence = 0.7
            if current_price > bid_1 * 1.001:
                signal = 'buy'
            elif current_price < ask_1 * 0.999:
                signal = 'sell'
        
        return {
            'symbol': symbol,
            'signal': signal,
            'confidence': confidence,
            'price': current_price,
            'bid': bid_1,
            'ask': ask_1,
            'spread': spread,
            'timestamp': datetime.utcnow().isoformat(),
            'generated_by': 'insilico-signal-v1'
        }
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary with signals"""
        positions = self.api.get_positions()
        balance = self.api.get_account_balance()
        
        total_pnl = 0
        for pos in positions:
            total_pnl += float(pos.get('unrealized_pnl', 0))
        
        return {
            'balance': balance,
            'positions': positions,
            'total_unrealized_pnl': total_pnl,
            'position_count': len(positions),
            'timestamp': datetime.utcnow().isoformat()
        }


# Flask Routes for Trading Desk API
def register_trading_routes(app):
    """Register trading API routes with Flask app"""
    from flask import Blueprint, jsonify, request
    
    trading_bp = Blueprint('trading', __name__, url_prefix='/api/v1/trading')
    api_client = BlofinAPI()
    signals = TradingSignals(api_client)
    
    @trading_bp.route('/status', methods=['GET'])
    def status():
        """Check API connection status"""
        balance = api_client.get_account_balance()
        return jsonify({
            'connected': 'error' not in balance,
            'api': 'blofin',
            'current_ip': CURRENT_IP,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    @trading_bp.route('/balance', methods=['GET'])
    def get_balance():
        """Get account balance"""
        return jsonify(api_client.get_account_balance())
    
    @trading_bp.route('/positions', methods=['GET'])
    def get_positions():
        """Get open positions"""
        return jsonify(api_client.get_positions())
    
    @trading_bp.route('/ticker/<symbol>', methods=['GET'])
    def get_ticker(symbol):
        """Get ticker for symbol"""
        return jsonify(api_client.get_ticker(symbol))
    
    @trading_bp.route('/orderbook/<symbol>', methods=['GET'])
    def get_orderbook(symbol):
        """Get orderbook for symbol"""
        size = request.args.get('size', 20, type=int)
        return jsonify(api_client.get_orderbook(symbol, size))
    
    @trading_bp.route('/signal', methods=['GET'])
    def get_signal():
        """Get trading signal"""
        symbol = request.args.get('symbol', 'BTC-USDT-PERPETUAL')
        return jsonify(signals.generate_signal(symbol))
    
    @trading_bp.route('/portfolio', methods=['GET'])
    def get_portfolio():
        """Get portfolio summary"""
        return jsonify(signals.get_portfolio_summary())
    
    @trading_bp.route('/instruments', methods=['GET'])
    def get_instruments():
        """Get available instruments"""
        inst_type = request.args.get('type', 'FUTURE')
        return jsonify(api_client.get_instruments(inst_type))
    
    @trading_bp.route('/order', methods=['POST'])
    def place_order():
        """Place order"""
        data = request.get_json()
        required = ['symbol', 'side', 'size']
        if not all(k in data for k in required):
            return jsonify({'error': 'Missing required fields'}), 400
        
        return jsonify(api_client.place_order(
            symbol=data['symbol'],
            side=data['side'],
            size=data['size'],
            order_type=data.get('type', 'market'),
            price=data.get('price')
        ))
    
    app.register_blueprint(trading_bp)


# CLI for testing
if __name__ == '__main__':
    import sys
    
    print("=== Insilico/Blofin Trading API Test ===")
    print(f"Current IP: {CURRENT_IP}")
    print(f"API Configured: {bool(BLOFIN_API_KEY)}")
    
    if not BLOFIN_API_KEY:
        print("\n⚠️  API keys not configured!")
        print("Set environment variables:")
        print("  BLOFIN_API_KEY")
        print("  BLOFIN_API_SECRET") 
        print("  BLOFIN_API_PASSPHRASE")
        print("\nThen whitelist IP:", CURRENT_IP)
        sys.exit(1)
    
    api = BlofinAPI()
    
    # Test connection
    print("\n=== Testing Connection ===")
    balance = api.get_account_balance()
    if 'error' in balance:
        print(f"❌ Connection failed: {balance['error']}")
        print(f"\n⚠️  Add IP {CURRENT_IP} to Blofin API whitelist!")
    else:
        print(f"✅ Connected! Balance: {balance}")
    
    # Get positions
    print("\n=== Open Positions ===")
    positions = api.get_positions()
    print(f"Positions: {len(positions)}")
    for pos in positions[:3]:
        print(f"  {pos}")
