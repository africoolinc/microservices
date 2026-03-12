"""
Keycloak Authentication & Subscription Service
================================================
Integrates with Keycloak for auth + provides subscription tier management.
"""

import os
import requests
from functools import wraps
from flask import request, jsonify, g
import logging

logger = logging.getLogger(__name__)

# Keycloak Configuration
KEYCLOAK_URL = os.environ.get('KEYCLOAK_URL', 'http://localhost:8080')
KEYCLOAK_REALM = os.environ.get('KEYCLOAK_REALM', 'stack-duka')
KEYCLOAK_CLIENT_ID = os.environ.get('KEYCLOAK_CLIENT_ID', 'stack-duka-app')
KEYCLOAK_CLIENT_SECRET = os.environ.get('KEYCLOAK_CLIENT_SECRET', '')

# Subscription Tiers
SUBSCRIPTION_TIERS = {
    'free': {
        'name': 'Free Tier',
        'price': 0,
        'features': ['Basic API access', '100 requests/day', 'Community support'],
        'rate_limit': 100
    },
    'starter': {
        'name': 'Starter',
        'price': 29,
        'features': ['Full API access', '10,000 requests/day', 'Email support', 'Basic analytics'],
        'rate_limit': 10000
    },
    'pro': {
        'name': 'Professional',
        'price': 99,
        'features': ['Priority API access', '100,000 requests/day', '24/7 support', 'Advanced analytics', 'Custom webhooks'],
        'rate_limit': 100000
    },
    'enterprise': {
        'name': 'Enterprise',
        'price': 299,
        'features': ['Unlimited requests', 'Dedicated support', 'Custom SLAs', 'White-label options', 'On-premise deployment'],
        'rate_limit': -1  # Unlimited
    }
}


def get_keycloak_public_key():
    """Fetch public key from Keycloak realm"""
    try:
        url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Convert Keycloak's RSA public key to PEM format
            public_key = data.get('public_key', '')
            if public_key:
                pem_key = f"-----BEGIN PUBLIC KEY-----\n"
                # Add newlines every 64 chars
                for i in range(0, len(public_key), 64):
                    pem_key += public_key[i:i+64] + "\n"
                pem_key += "-----END PUBLIC KEY-----"
                return pem_key
    except Exception as e:
        logger.error(f"Failed to fetch Keycloak public key: {e}")
    return None


def get_user_subscription(user_id: str) -> dict:
    """
    Get user's subscription tier from Keycloak user attributes.
    In production, this would query Keycloak or a database.
    """
    # For demo: check user attributes from token or database
    # In production: query Keycloak Admin API or local cache
    try:
        # Try to get from environment or default to free
        tier = os.environ.get(f'USER_TIER_{user_id[:8]}', 'free')
        return SUBSCRIPTION_TIERS.get(tier, SUBSCRIPTION_TIERS['free'])
    except Exception:
        return SUBSCRIPTION_TIERS['free']


def check_rate_limit(user_tier: str) -> tuple:
    """Check if user has exceeded rate limit"""
    tier_data = SUBSCRIPTION_TIERS.get(user_tier, SUBSCRIPTION_TIERS['free'])
    limit = tier_data.get('rate_limit', 100)
    
    # In production: track actual usage in Redis/database
    # For now: allow all requests (implement Redis-based tracking)
    return True, limit


def keycloak_required(f):
    """
    Decorator to require valid Keycloak JWT token.
    Validates Bearer token and extracts user info.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Valid Bearer token required. Obtain from Keycloak login.'
            }), 401
        
        token = auth_header[7:]  # Remove 'Bearer '
        
        # Validate token with Keycloak
        try:
            # Option 1: Introspect token with Keycloak
            introspect_url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token/introspect"
            data = {
                'token': token,
                'client_id': KEYCLOAK_CLIENT_ID,
                'client_secret': KEYCLOAK_CLIENT_SECRET
            }
            response = requests.post(introspect_url, data=data, timeout=10)
            
            if response.status_code != 200:
                return jsonify({'error': 'Invalid token'}), 401
            
            token_data = response.json()
            if not token_data.get('active'):
                return jsonify({'error': 'Token expired or invalid'}), 401
            
            # Store user info in request context
            g.user_id = token_data.get('sub')
            g.username = token_data.get('preferred_username')
            g.email = token_data.get('email')
            g.tier = token_data.get('tier', 'free')
            
            # Check rate limit
            allowed, limit = check_rate_limit(g.tier)
            if not allowed:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'tier': g.tier,
                    'limit': limit,
                    'message': f'Upgrade to {g.tier} tier for higher limits'
                }), 429
            
            return f(*args, **kwargs)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Keycloak validation error: {e}")
            # Fail open for development, fail closed for production
            if os.environ.get('FLASK_ENV') == 'production':
                return jsonify({'error': 'Auth service unavailable'}), 503
        
        return f(*args, **kwargs)
    return decorated


def subscription_required(tier: str):
    """
    Decorator to require specific subscription tier.
    Usage: @subscription_required('pro')
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user_tier = getattr(g, 'tier', 'free')
            tier_hierarchy = ['free', 'starter', 'pro', 'enterprise']
            
            if tier_hierarchy.index(user_tier) < tier_hierarchy.index(tier):
                return jsonify({
                    'error': 'Upgrade required',
                    'current_tier': user_tier,
                    'required_tier': tier,
                    'message': f'This feature requires {tier} tier or higher',
                    'upgrade_url': '/api/v1/subscription/upgrade'
                }), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator


# API Routes for Auth & Subscription
def register_routes(app):
    """Register auth and subscription routes with Flask app"""
    from flask import Blueprint
    
    auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')
    
    @auth_bp.route('/login', methods=['POST'])
    def login():
        """Redirect to Keycloak login - returns Keycloak auth URL"""
        keycloak_auth_url = (
            f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/auth"
            f"?client_id={KEYCLOAK_CLIENT_ID}"
            f"&redirect_uri={request.json.get('redirect_uri', 'http://localhost:3000/callback')}"
            f"&response_type=code"
            f"&scope=openid profile email"
        )
        return jsonify({
            'auth_url': keycloak_auth_url,
            'message': 'Redirect user to Keycloak login'
        })
    
    @auth_bp.route('/callback', methods=['POST'])
    def callback():
        """Exchange authorization code for tokens"""
        code = request.json.get('code')
        if not code:
            return jsonify({'error': 'Authorization code required'}), 400
        
        try:
            token_url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token"
            data = {
                'grant_type': 'authorization_code',
                'client_id': KEYCLOAK_CLIENT_ID,
                'client_secret': KEYCLOAK_CLIENT_SECRET,
                'code': code,
                'redirect_uri': request.json.get('redirect_uri', 'http://localhost:3000/callback')
            }
            response = requests.post(token_url, data=data, timeout=10)
            
            if response.status_code == 200:
                token_data = response.json()
                return jsonify({
                    'access_token': token_data.get('access_token'),
                    'refresh_token': token_data.get('refresh_token'),
                    'expires_in': token_data.get('expires_in'),
                    'token_type': token_data.get('token_type')
                })
            else:
                return jsonify({'error': 'Token exchange failed'}), 400
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @auth_bp.route('/logout', methods=['POST'])
    @keycloak_required
    def logout():
        """Logout user and invalidate session"""
        return jsonify({'message': 'Logged out successfully'})
    
    # Subscription routes
    sub_bp = Blueprint('subscription', __name__, url_prefix='/api/v1/subscription')
    
    @sub_bp.route('/tiers', methods=['GET'])
    def get_tiers():
        """Get all subscription tiers"""
        return jsonify(SUBSCRIPTION_TIERS)
    
    @sub_bp.route('/current', methods=['GET'])
    @keycloak_required
    def get_current_subscription():
        """Get current user's subscription"""
        user_id = getattr(g, 'user_id', None)
        tier = get_user_subscription(user_id or '')
        return jsonify({
            'tier': tier,
            'tier_name': tier['name'],
            'price': tier['price']
        })
    
    @sub_bp.route('/upgrade', methods=['POST'])
    @keycloak_required
    def upgrade_subscription():
        """Initiate subscription upgrade (integrate with payment)"""
        new_tier = request.json.get('tier')
        if new_tier not in SUBSCRIPTION_TIERS:
            return jsonify({'error': 'Invalid tier'}), 400
        
        # In production: integrate with payment provider (Stripe, M-Pesa, etc.)
        return jsonify({
            'message': 'Redirect to payment',
            'tier': new_tier,
            'amount': SUBSCRIPTION_TIERS[new_tier]['price'],
            'payment_url': f'/api/v1/payment/checkout?tier={new_tier}'
        })
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(sub_bp)
