from flask import Flask, request, jsonify, send_from_directory
from prometheus_flask_exporter import PrometheusMetrics
import os
import json
import uuid
from datetime import datetime
import logging
from pythonjsonlogger import jsonlogger

# Initialize Flask app
app = Flask(__name__, static_folder='../frontend', static_url_path='')

# Metrics
metrics = PrometheusMetrics(app)

# Setup logging
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Mock Data Storage (In-memory for demo)
wallets = {
    "usdc_primary": {"id": "usdc_primary", "name": "Primary USDC", "balance": 11.97, "currency": "USD"},
    "btc_cold": {"id": "btc_cold", "name": "Bitcoin Cold Storage", "balance": 1.84, "currency": "BTC"},
    "mpesa_pool": {"id": "mpesa_pool", "name": "M-Pesa Pool", "balance": 450000, "currency": "KES"}
}

transactions = [
    {
        "id": str(uuid.uuid4()),
        "title": "Payment from Moltchain",
        "type": "receive",
        "amount": 500.00,
        "currency": "USD",
        "date": "2026-02-08",
        "status": "completed"
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Liquidation Pusher",
        "type": "send",
        "amount": 50.00,
        "currency": "USD",
        "date": "2026-02-07",
        "status": "processing"
    }
]

# Static Routes
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/styles.css')
def serve_css():
    return send_from_directory(app.static_folder, 'styles.css')

@app.route('/app.js')
def serve_js():
    return send_from_directory(app.static_folder, 'app.js')

# Fintech API
@app.route('/api/v1/wallets', methods=['GET'])
def get_wallets():
    return jsonify(list(wallets.values()))

@app.route('/api/v1/transactions', methods=['GET'])
def get_transactions():
    return jsonify(transactions)

@app.route('/api/v1/transfer', methods=['POST'])
def transfer_funds():
    data = request.get_json()
    wallet_id = data.get('wallet_id')
    amount = float(data.get('amount', 0))
    recipient = data.get('recipient')

    if wallet_id in wallets and wallets[wallet_id]['balance'] >= amount:
        # Mock logic
        wallets[wallet_id]['balance'] -= amount
        new_tx = {
            "id": str(uuid.uuid4()),
            "title": f"Transfer to {recipient[:8]}...",
            "type": "send",
            "amount": amount,
            "currency": wallets[wallet_id]['currency'],
            "date": datetime.now().strftime("%b %d, %Y"),
            "status": "completed"
        }
        transactions.insert(0, new_tx)
        
        logger.info(f"Transfer successful", extra={'amount': amount, 'recipient': recipient})
        return jsonify({"status": "success", "transaction": new_tx})
    
    return jsonify({"status": "error", "message": "Insufficient funds or invalid wallet"}), 400

@app.route('/api/v1/health')
def health():
    return jsonify({
        "status": "UP",
        "service": "fintech-app",
        "db": "CONNECTED",
        "keycloak": "ACTIVE"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
