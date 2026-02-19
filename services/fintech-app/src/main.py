from flask import Flask, request, jsonify, send_from_directory, redirect, session, url_for
from prometheus_flask_exporter import PrometheusMetrics
import os
import json
import uuid
from datetime import datetime
import logging
from functools import wraps
import requests
from pythonjsonlogger import jsonlogger

# Initialize Flask app
app = Flask(__name__, static_folder='../frontend', static_url_path='')

# Security configuration
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Keycloak configuration
KEYCLOAK_URL = os.environ.get('KEYCLOAK_URL', 'http://keycloak:8080')
KEYCLOAK_REALM = os.environ.get('KEYCLOAK_REALM', 'fintech')
KEYCLOAK_CLIENT_ID = os.environ.get('KEYCLOAK_CLIENT_ID', 'fintech-app')
KEYCLOAK_CLIENT_SECRET = os.environ.get('KEYCLOAK_CLIENT_SECRET', 'fintech-secret-key')

# Metrics
metrics = PrometheusMetrics(app)

# Setup logging
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Subscription Tiers Configuration
SUBSCRIPTION_TIERS = {
    'free': {
        'name': 'Free',
        'price': 0,
        'features': ['Basic wallet', '5 transactions/month', 'Email support'],
        'limits': {'transactions': 5, 'wallets': 1, 'api_calls': 100}
    },
    'basic': {
        'name': 'Basic',
        'price': 9.99,
        'features': ['Premium wallet', '50 transactions/month', 'Priority support', 'Basic analytics'],
        'limits': {'transactions': 50, 'wallets': 3, 'api_calls': 1000}
    },
    'pro': {
        'name': 'Pro',
        'price': 29.99,
        'features': ['Multiple wallets', 'Unlimited transactions', '24/7 support', 'Advanced analytics', 'API access'],
        'limits': {'transactions': -1, 'wallets': 10, 'api_calls': 10000}
    },
    'enterprise': {
        'name': 'Enterprise',
        'price': 99.99,
        'features': ['Unlimited everything', 'Dedicated support', 'Custom integrations', 'White-label', 'SLA'],
        'limits': {'transactions': -1, 'wallets': -1, 'api_calls': -1}
    }
}

# Mock Data Storage (In-memory for demo)
users = {
    "demo@fintech.io": {
        "id": "user_001",
        "email": "demo@fintech.io",
        "name": "Demo User",
        "tier": "free",
        "subscription_status": "active",
        "created_at": "2026-01-01"
    }
}

wallets = {
    "usdc_primary": {"id": "usdc_primary", "name": "Primary USDC", "balance": 11.97, "currency": "USD", "owner": "user_001"},
    "btc_cold": {"id": "btc_cold", "name": "Bitcoin Cold Storage", "balance": 1.84, "currency": "BTC", "owner": "user_001"},
    "mpesa_pool": {"id": "mpesa_pool", "name": "M-Pesa Pool", "balance": 450000, "currency": "KES", "owner": "user_001"}
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

# Keycloak helper functions
def get_keycloak_token(username, password):
    """Authenticate with Keycloak and get token"""
    try:
        token_url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token"
        data = {
            'grant_type': 'password',
            'client_id': KEYCLOAK_CLIENT_ID,
            'client_secret': KEYCLOAK_CLIENT_SECRET,
            'username': username,
            'password': password
        }
        response = requests.post(token_url, data=data, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.warning(f"Keycloak auth failed: {e}")
    return None

def get_user_info(token):
    """Get user info from Keycloak"""
    try:
        userinfo_url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/userinfo"
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(userinfo_url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.warning(f"Keycloak userinfo failed: {e}")
    return None

def check_tier_permission(tier, permission):
    """Check if tier has permission"""
    tier_config = SUBSCRIPTION_TIERS.get(tier, SUBSCRIPTION_TIERS['free'])
    # For simplicity, all tiers have basic access
    return True

def get_tier_limits(tier):
    """Get limits for a tier"""
    return SUBSCRIPTION_TIERS.get(tier, SUBSCRIPTION_TIERS['free'])['limits']

# Authentication decorator
def require_auth(f):
    """Require authentication for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = session.get('access_token')
        if not token:
            return jsonify({'error': 'Authentication required', 'code': 'AUTH_REQUIRED'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Static Routes
# Templates are served from ../templates relative to this file
import os
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), '..', 'templates')
STATIC_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend')

@app.route('/')
def serve_index():
    # Check if user is logged in, redirect to dashboard
    token = session.get('access_token')
    if token:
        return redirect('/dashboard')
    return send_from_directory(TEMPLATES_DIR, 'index.html')

@app.route('/auth')
def serve_auth():
    return send_from_directory(TEMPLATES_DIR, 'auth.html')

@app.route('/dashboard')
def serve_dashboard():
    return send_from_directory(TEMPLATES_DIR, 'dashboard.html')

@app.route('/styles.css')
def serve_css():
    return send_from_directory(app.static_folder, 'styles.css')

@app.route('/app.js')
def serve_js():
    return send_from_directory(app.static_folder, 'app.js')

# Authentication Routes
@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    """Login endpoint - integrates with Keycloak"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    # Try Keycloak authentication first
    token_data = get_keycloak_token(email, password)
    
    if token_data:
        # Store token in session
        session['access_token'] = token_data.get('access_token')
        session['refresh_token'] = token_data.get('refresh_token')
        session['email'] = email
        
        # Get or create user
        if email not in users:
            users[email] = {
                "id": f"user_{uuid.uuid4().hex[:8]}",
                "email": email,
                "name": email.split('@')[0],
                "tier": "free",
                "subscription_status": "active",
                "created_at": datetime.now().strftime("%Y-%m-%d")
            }
        
        user = users[email]
        
        logger.info(f"User logged in via Keycloak: {email}")
        
        return jsonify({
            'status': 'success',
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'email': user['email'],
                'name': user['name'],
                'tier': user['tier']
            },
            'token': token_data.get('access_token')
        })
    
    # Fallback to mock authentication for demo
    if email in users:
        session['email'] = email
        session['access_token'] = f"mock_token_{uuid.uuid4().hex}"
        user = users[email]
        
        return jsonify({
            'status': 'success',
            'message': 'Login successful (demo mode)',
            'user': {
                'id': user['id'],
                'email': user['email'],
                'name': user['name'],
                'tier': user['tier']
            },
            'token': session['access_token']
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/v1/auth/register', methods=['POST'])
def register():
    """Register new user - creates Keycloak user"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name', email.split('@')[0])
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    if email in users:
        return jsonify({'error': 'User already exists'}), 409
    
    # In production, create user in Keycloak here
    # For demo, create local user
    
    user_id = f"user_{uuid.uuid4().hex[:8]}"
    users[email] = {
        "id": user_id,
        "email": email,
        "name": name,
        "tier": "free",
        "subscription_status": "active",
        "created_at": datetime.now().strftime("%Y-%m-%d")
    }
    
    # Give initial tokens
    session['email'] = email
    session['access_token'] = f"mock_token_{uuid.uuid4().hex}"
    
    logger.info(f"New user registered: {email}")
    
    return jsonify({
        'status': 'success',
        'message': 'Registration successful',
        'user': {
            'id': user_id,
            'email': email,
            'name': name,
            'tier': 'free'
        }
    }), 201

@app.route('/api/v1/auth/logout', methods=['POST'])
def logout():
    """Logout endpoint"""
    session.clear()
    return jsonify({'status': 'success', 'message': 'Logged out'})

@app.route('/api/v1/auth/me', methods=['GET'])
@require_auth
def get_current_user():
    """Get current user info"""
    email = session.get('email')
    if email and email in users:
        return jsonify({'user': users[email]})
    return jsonify({'error': 'User not found'}), 404

# Subscription Routes
@app.route('/api/v1/subscription/tiers', methods=['GET'])
def get_tiers():
    """Get available subscription tiers"""
    tiers = []
    for tier_id, tier_data in SUBSCRIPTION_TIERS.items():
        tiers.append({
            'id': tier_id,
            'name': tier_data['name'],
            'price': tier_data['price'],
            'features': tier_data['features'],
            'limits': tier_data['limits']
        })
    return jsonify({'tiers': tiers})

@app.route('/api/v1/subscription/upgrade', methods=['POST'])
@require_auth
def upgrade_subscription():
    """Upgrade user subscription tier"""
    data = request.get_json()
    new_tier = data.get('tier')
    
    email = session.get('email')
    if not email or email not in users:
        return jsonify({'error': 'User not found'}), 404
    
    if new_tier not in SUBSCRIPTION_TIERS:
        return jsonify({'error': 'Invalid tier'}), 400
    
    users[email]['tier'] = new_tier
    users[email]['subscription_status'] = 'active'
    
    logger.info(f"User {email} upgraded to {new_tier}")
    
    return jsonify({
        'status': 'success',
        'message': f'Upgraded to {SUBSCRIPTION_TIERS[new_tier]["name"]}',
        'tier': new_tier
    })

@app.route('/api/v1/subscription/check', methods=['GET'])
@require_auth
def check_subscription():
    """Check current subscription status"""
    email = session.get('email')
    if email and email in users:
        user = users[email]
        tier_info = SUBSCRIPTION_TIERS.get(user['tier'], SUBSCRIPTION_TIERS['free'])
        return jsonify({
            'tier': user['tier'],
            'status': user['subscription_status'],
            'tier_info': tier_info
        })
    return jsonify({'error': 'User not found'}), 404

# Fintech API Routes
@app.route('/api/v1/wallets', methods=['GET'])
@require_auth
def get_wallets():
    """Get user wallets"""
    email = session.get('email')
    user = users.get(email)
    if not user:
        return jsonify({'wallets': []})
    
    user_wallets = [w for w in wallets.values() if w.get('owner') == user['id']]
    return jsonify({'wallets': user_wallets})

@app.route('/api/v1/wallets', methods=['POST'])
@require_auth
def create_wallet():
    """Create new wallet"""
    email = session.get('email')
    user = users.get(email)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check tier limits
    limits = get_tier_limits(user['tier'])
    if limits['wallets'] > 0:
        current_wallets = len([w for w in wallets.values() if w.get('owner') == user['id']])
        if current_wallets >= limits['wallets']:
            return jsonify({
                'error': 'Wallet limit reached',
                'message': f'Upgrade to {user["tier"]} tier to create more wallets',
                'upgrade_required': True
            }), 403
    
    data = request.get_json()
    wallet_id = f"wallet_{uuid.uuid4().hex[:8]}"
    wallets[wallet_id] = {
        "id": wallet_id,
        "name": data.get('name', 'New Wallet'),
        "balance": 0,
        "currency": data.get('currency', 'USD'),
        "owner": user['id']
    }
    
    return jsonify({'wallet': wallets[wallet_id]}), 201

@app.route('/api/v1/transactions', methods=['GET'])
@require_auth
def get_transactions():
    """Get user transactions"""
    return jsonify({'transactions': transactions})

@app.route('/api/v1/transfer', methods=['POST'])
@require_auth
def transfer_funds():
    """Transfer funds between wallets"""
    email = session.get('email')
    user = users.get(email)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    wallet_id = data.get('wallet_id')
    amount = float(data.get('amount', 0))
    recipient = data.get('recipient')

    if wallet_id in wallets and wallets[wallet_id]['balance'] >= amount:
        wallets[wallet_id]['balance'] -= amount
        new_tx = {
            "id": str(uuid.uuid4()),
            "title": f"Transfer to {recipient[:8]}...",
            "type": "send",
            "amount": amount,
            "currency": wallets[wallet_id]['currency'],
            "date": datetime.now().strftime("%Y-%m-%d"),
            "status": "completed"
        }
        transactions.insert(0, new_tx)
        
        logger.info(f"Transfer: {email} sent {amount} {wallets[wallet_id]['currency']}")
        return jsonify({"status": "success", "transaction": new_tx})
    
    return jsonify({"status": "error", "message": "Insufficient funds or invalid wallet"}), 400

@app.route('/api/v1/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "UP",
        "service": "fintech-app",
        "version": "2.0.0",
        "keycloak": "CONFIGURED",
        "subscription_tiers": len(SUBSCRIPTION_TIERS)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
