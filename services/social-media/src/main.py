# Lyrikali Social - Upgraded with BTC Lightning & Subscriptions
# Version: 3.1.0 - Added PostHog analytics + Keycloak realm

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from prometheus_flask_exporter import PrometheusMetrics
import os
import json
import uuid
import requests
from datetime import datetime, timedelta
import logging
from pythonjsonlogger import jsonlogger
from pywebpush import webpush, WebPushException
import hashlib
import time

# PostHog Analytics
try:
    from posthog import Posthog
    POSTHOG_AVAILABLE = True
except ImportError:
    POSTHOG_AVAILABLE = False

# Setup logging (must be before PostHog init)
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Initialize PostHog
posthog = None
if POSTHOG_AVAILABLE:
    try:
        posthog = Posthog(
            api_key=POSTHOG_API_KEY,
            host=POSTHOG_HOST,
            debug=False
        )
        logger.info(f"✅ PostHog initialized: {POSTHOG_HOST}")
    except Exception as e:
        logger.warning(f"⚠️ PostHog init failed: {e}")

# Initialize Flask app
app = Flask(__name__, static_folder='../frontend', static_url_path='')

# Enable CORS for Firebase hosting
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://africool-fd821.web.app", "https://africool-fd821.firebaseapp.com"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Metrics for monitoring
metrics = PrometheusMetrics(app)

# ==================== CONFIGURATION ====================

# Service Configuration
SERVICE_PORT = int(os.environ.get('SERVICE_PORT', 10500))
SERVICE_ID = os.environ.get('SERVICE_ID', 'social-media-service')

# Keycloak Configuration
KEYCLOAK_URL = os.environ.get('KEYCLOAK_URL', 'http://localhost:8080')
KEYCLOAK_REALM = os.environ.get('KEYCLOAK_REALM', 'lyrikali')
KEYCLOAK_CLIENT_ID = os.environ.get('KEYCLOAK_CLIENT_ID', 'lyrikali-app')
KEYCLOAK_ADMIN_SECRET = os.environ.get('KEYCLOAK_ADMIN_SECRET', '')

# PostHog Configuration
POSTHOG_API_KEY = os.environ.get('POSTHOG_API_KEY', 'phc_SVmgEZyseThkm6cJInz6klQxCpER3L3qfgLb6yw2pwE')
POSTHOG_HOST = os.environ.get('POSTHOG_HOST', 'https://us.i.posthog.com')

# Initialize PostHog
posthog = None
if POSTHOG_AVAILABLE:
    try:
        posthog = Posthog(
            api_key=POSTHOG_API_KEY,
            host=POSTHOG_HOST,
            debug=False
        )
        logger.info(f"✅ PostHog initialized: {POSTHOG_HOST}")
    except Exception as e:
        logger.warning(f"⚠️ PostHog init failed: {e}")

# Consul Configuration
CONSUL_URL = os.environ.get('CONSUL_URL', 'http://localhost:8500')

# ==================== POSTHOG TRACKING ====================

def track_event(event_name, distinct_id, properties=None):
    """Track event to PostHog."""
    if posthog:
        try:
            posthog.capture(
                distinct_id=distinct_id,
                event=event_name,
                properties=properties or {},
                timestamp=datetime.utcnow().isoformat()
            )
            logger.info(f"📊 PostHog: {event_name} for {distinct_id}")
        except Exception as e:
            logger.warning(f"⚠️ PostHog track error: {e}")

def track_user(distinct_id, properties):
    """Identify user in PostHog."""
    if posthog:
        try:
            posthog.identify(
                distinct_id=distinct_id,
                properties=properties
            )
        except Exception as e:
            logger.warning(f"⚠️ PostHog identify error: {e}")

# BTC Lightning Configuration (LND)
LND_GRPC_HOST = os.environ.get('LND_GRPC_HOST', '10.144.118.159:10009')
LND_MACAROON = os.environ.get('LND_MACAROON', '')  # Base64 encoded macaroon
LND_CERT = os.environ.get('LND_CERT_PATH', '/app/lnd/tls.cert')

# VAPID keys for Push Notifications
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "BC-ishmmAxcz1syjpNXdPNL_7ENM7DDmmkYkFVr9Ag57f9o3mSPoAE2C--pQBW1PhzBJmOyTJu9ML7noewPQY9Q")
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "myzvOUzZhCZKTFe9xr0j6bWaeBcX0UMXMBF8hHHUJDI")
VAPID_CLAIMS = {"sub": "mailto:ahie@juma.family"}

# Subscription Plans (in satoshis for BTC Lightning)
SUBSCRIPTION_PLANS = {
    "free": {
        "name": "Free",
        "price_sats": 0,
        "price_ksh": 0,
        "features": ["Basic meme generation", "5 memes/day", "Standard quality"],
        "limits": {"memes_per_day": 5, "ai_quality": "standard"}
    },
    "pro": {
        "name": "Pro",
        "price_sats": 5000,  # ~$2-3 USD
        "price_ksh": 350,
        "features": ["Unlimited memes", "HD quality", "Priority rendering", "No ads"],
        "limits": {"memes_per_day": -1, "ai_quality": "hd"}
    },
    "premium": {
        "name": "Premium", 
        "price_sats": 15000,  # ~$6-8 USD
        "price_ksh": 900,
        "features": ["Everything in Pro", "Early access features", "Custom branding", "API access"],
        "limits": {"memes_per_day": -1, "ai_quality": "4k", "api_calls": 1000}
    }
}

# In-memory storage
subscriptions = {}
users_db = {}  # {username: user_data}
payment_invoices = {}  # {invoice_id: payment_data}
subscription_tiers = {}  # {username: tier_info}

# ==================== CONSUL REGISTRATION ====================

def register_with_consul():
    """Register this service with Consul for service discovery."""
    try:
        service_config = {
            "ID": SERVICE_ID,
            "Name": "lyrikali-social",
            "Port": SERVICE_PORT,
            "Meta": {
                "version": "3.0.0",
                "features": "auth,meme-engine,keycloak,consul,btc-lightning,subscriptions"
            },
            "Check": {
                "HTTP": f"http://localhost:{SERVICE_PORT}/health",
                "Interval": "30s",
                "Timeout": "10s",
                "DeregisterCriticalServiceAfter": "5m"
            }
        }
        
        response = requests.put(
            f"{CONSUL_URL}/v1/agent/service/register",
            json=service_config,
            timeout=5
        )
        
        if response.status_code in [200, 201]:
            logger.info(f"✅ Service {SERVICE_ID} registered with Consul on port {SERVICE_PORT}")
            return True
        else:
            logger.warning(f"⚠️ Consul registration failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Consul registration error: {e}")
        return False

def deregister_from_consul():
    """Deregister this service from Consul."""
    try:
        response = requests.delete(
            f"{CONSUL_URL}/v1/agent/service/deregister/{SERVICE_ID}",
            timeout=5
        )
        return response.status_code in [200, 204]
    except Exception as e:
        logger.error(f"❌ Consul deregistration error: {e}")
        return False

def register_user_with_consul(user_id, email, username):
    """Register user as a service in Consul."""
    try:
        user_config = {
            "ID": f"lyrikali-user-{user_id}",
            "Name": "lyrikali-user",
            "Port": 0,
            "Meta": {
                "user_id": user_id,
                "email": email,
                "username": username,
                "registered_at": datetime.utcnow().isoformat()
            }
        }
        
        response = requests.put(
            f"{CONSUL_URL}/v1/agent/service/register",
            json=user_config,
            timeout=5
        )
        
        if response.status_code in [200, 201]:
            logger.info(f"✅ User {username} registered with Consul")
            return True
        return False
    except Exception as e:
        logger.error(f"❌ User Consul registration error: {e}")
        return False

def discover_service(service_name):
    """Discover a service from Consul."""
    try:
        response = requests.get(
            f"{CONSUL_URL}/v1/health/service/{service_name}",
            params={"passing": True},
            timeout=5
        )
        
        if response.status_code == 200:
            services = response.json()
            if services:
                # Return first healthy instance
                return services[0]['Service']
        return None
    except Exception as e:
        logger.error(f"❌ Service discovery error: {e}")
        return None

# ==================== KEYCLOAK INTEGRATION ====================

def get_keycloak_token():
    """Get admin token for Keycloak operations."""
    try:
        response = requests.post(
            f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
            data={
                "grant_type": "client_credentials",
                "client_id": "admin-cli",
                "client_secret": KEYCLOAK_ADMIN_SECRET
            },
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json().get('access_token')
    except Exception as e:
        logger.error(f"Keycloak token error: {e}")
    return None

def create_keycloak_user(username, email, password, phone):
    """Create user in Keycloak realm."""
    try:
        admin_token = get_keycloak_token()
        if not admin_token:
            logger.warning("Keycloak unavailable - using demo mode")
            return None
            
        user_data = {
            "username": username,
            "email": email,
            "enabled": True,
            "emailVerified": True,
            "firstName": username.split('.')[0] if '.' in username else username,
            "lastName": username.split('.')[-1] if '.' in username else "",
            "attributes": {
                "phone": [phone]
            },
            "credentials": [{
                "type": "password",
                "value": password,
                "temporary": False
            }]
        }
        
        response = requests.post(
            f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users",
            json=user_data,
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        
        if response.status_code in [200, 201, 204]:
            logger.info(f"✅ Keycloak user created: {username}")
            return True
        else:
            logger.warning(f"Keycloak user creation failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Keycloak user creation error: {e}")
        return None

def validate_keycloak_credentials(username, password):
    """Validate user credentials with Keycloak."""
    try:
        response = requests.post(
            f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token",
            data={
                "grant_type": "password",
                "client_id": KEYCLOAK_CLIENT_ID,
                "username": username,
                "password": password
            },
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        logger.error(f"Keycloak validation error: {e}")
        return None

def add_role_to_user(username, role):
    """Add a role to user in Keycloak."""
    try:
        admin_token = get_keycloak_token()
        if not admin_token:
            return False
        
        # Get user ID
        response = requests.get(
            f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users?username={username}",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=10
        )
        
        if response.status_code != 200 or not response.json():
            return False
        
        user_id = response.json()[0]['id']
        
        # Get role ID
        role_data = [{
            "name": role,
            "clientRole": False,
            "containerId": KEYCLOAK_REALM
        }]
        
        response = requests.post(
            f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/{user_id}/role-mappings/realm",
            json=role_data,
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        
        return response.status_code in [200, 201, 204]
    except Exception as e:
        logger.error(f"Keycloak add role error: {e}")
        return False

# ==================== BTC LIGHTNING PAYMENTS ====================

def create_lightning_invoice(amount_sats, memo, expiry_hours=1):
    """Create a Lightning Network invoice via LND gRPC."""
    try:
        import grpc
        import lnd_pb2 as ln
        import lnd_pb2_grpc as lnrpc
        
        # Create gRPC channel
        cert = open(LND_CERT, 'rb').read() if os.path.exists(LND_CERT) else None
        
        if cert:
            creds = grpc.ssl_channel_credentials(cert)
            channel = grpc.secure_channel(LND_GRPC_HOST, creds)
        else:
            # Fallback to insecure (for testing)
            channel = grpc.insecure_channel(LND_GRPC_HOST)
        
        stub = lnrpc.LightningStub(channel)
        
        # Create invoice request
        invoice_request = ln.Invoice(
            value=amount_sats,
            memo=memo,
            expiry=3600 * expiry_hours  # 1 hour default
        )
        
        response = stub.AddInvoice(invoice_request)
        
        return {
            "invoice_id": response.r_hash.hex(),
            "payment_request": response.payment_request,
            "amount_sats": amount_sats,
            "memo": memo,
            "expires_at": datetime.utcnow() + timedelta(hours=expiry_hours),
            "status": "pending"
        }
    except ImportError:
        # gRPC not available - create mock invoice for testing
        invoice_id = hashlib.sha256(f"{time.time()}{memo}".encode()).hexdigest()[:16]
        return {
            "invoice_id": invoice_id,
            "payment_request": f"lnbc{amount_sats}n1p{invoice_id}test",
            "amount_sats": amount_sats,
            "memo": memo,
            "expires_at": datetime.utcnow() + timedelta(hours=expiry_hours),
            "status": "pending",
            "demo": True
        }
    except Exception as e:
        logger.error(f"Lightning invoice creation error: {e}")
        return None

def check_invoice_status(invoice_id):
    """Check if Lightning invoice is paid."""
    try:
        import grpc
        import lnd_pb2 as ln
        import lnd_pb2_grpc as lnrpc
        
        cert = open(LND_CERT, 'rb').read() if os.path.exists(LND_CERT) else None
        
        if cert:
            creds = grpc.ssl_channel_credentials(cert)
            channel = grpc.secure_channel(LND_GRPC_HOST, creds)
        else:
            channel = grpc.insecure_channel(LND_GRPC_HOST)
        
        stub = lnrpc.LightningStub(channel)
        
        # Look up invoice
        response = stub.LookupInvoice(ln.PaymentHash(r_hash_str=invoice_id))
        
        return {
            "settled": response.settled,
            "amt_paid_sats": response.amt_paid_sat
        }
    except Exception as e:
        # Check local records for demo
        if invoice_id in payment_invoices:
            return {"settled": payment_invoices[invoice_id].get("settled", False)}
        return {"settled": False}

def simulate_payment(invoice_id):
    """Simulate payment for testing (demo mode)."""
    if invoice_id in payment_invoices:
        payment_invoices[invoice_id]["settled"] = True
        payment_invoices[invoice_id]["settled_at"] = datetime.utcnow().isoformat()
        return True
    return False

# ==================== AUTH ROUTES ====================

@app.route('/api/v1/auth/register', methods=['POST'])
def register_user():
    """Register new user with Keycloak and local DB."""
    data = request.get_json()
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone')
    
    if not all([username, email, password]):
        return jsonify({"error": "Username, email, and password required"}), 400
    
    # Check if user exists locally
    if username in users_db:
        return jsonify({"error": "User already exists"}), 409
    
    # Create user in Keycloak
    kc_result = create_keycloak_user(username, email, password, phone)
    
    # Store in local DB
    user_id = str(uuid.uuid4())
    users_db[username] = {
        "id": user_id,
        "username": username,
        "email": email,
        "phone": phone,
        "is_premium": False,
        "subscription_tier": "free",
        "balance_tokens": 0,
        "memes_created": 0,
        "daily_meme_count": 0,
        "last_meme_date": None,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Set default free tier
    subscription_tiers[username] = {
        "tier": "free",
        "started_at": datetime.utcnow().isoformat(),
        "expires_at": None,
        "paid": False
    }
    
    # Register with Consul
    register_user_with_consul(user_id, email, username)
    
    # Track registration in PostHog
    track_event("User Registered", username, {
        "email": email,
        "tier": "free",
        "keycloak_created": kc_result is not None
    })
    
    # Identify user
    track_user(username, {
        "email": email,
        "tier": "free",
        "registered_at": datetime.utcnow().isoformat()
    })
    
    logger.info(f"New user registered: {username}")
    
    return jsonify({
        "status": "success",
        "message": "User registered successfully",
        "user": {
            "id": user_id,
            "username": username,
            "email": email
        },
        "keycloak_created": kc_result is not None,
        "default_tier": "free"
    }), 201

@app.route('/api/v1/auth/login', methods=['POST'])
def login_user():
    """Authenticate user with Keycloak."""
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    
    # Try Keycloak validation
    kc_result = validate_keycloak_credentials(username, password)
    
    if kc_result:
        if username not in users_db:
            users_db[username] = {
                "id": str(uuid.uuid4()),
                "username": username,
                "email": f"{username}@lyrikali.ke",
                "is_premium": False,
                "subscription_tier": "free",
                "balance_tokens": 0,
                "memes_created": 0
            }
            subscription_tiers[username] = {
                "tier": "free",
                "started_at": datetime.utcnow().isoformat()
            }
        
        # Track login in PostHog
        track_event("User Logged In", username, {
            "tier": subscription_tiers.get(username, {}).get("tier", "free"),
            "method": "keycloak"
        })
        
        return jsonify({
            "status": "success",
            "message": "Login successful",
            "token": kc_result.get('access_token'),
            "user": users_db[username],
            "subscription": subscription_tiers.get(username, {"tier": "free"})
        })
    
    # Fallback: local demo mode
    if username in users_db:
        return jsonify({
            "status": "success",
            "message": "Login successful (demo mode)",
            "user": users_db[username],
            "subscription": subscription_tiers.get(username, {"tier": "free"})
        })
    
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/v1/auth/firebase-login', methods=['POST'])
def firebase_login():
    """Authenticate user via Firebase Google Sign-In."""
    data = request.get_json()
    
    firebase_token = data.get('firebase_token')
    email = data.get('email')
    name = data.get('name', '')
    photo_url = data.get('photo_url', '')
    
    if not firebase_token or not email:
        return jsonify({"error": "Firebase token and email required"}), 400
    
    # In production, verify the Firebase token:
    # For now, we trust the token from our own Firebase config
    # In production: use firebase-admin to verify
    
    # Extract username from email
    username = email.split('@')[0].replace('.', '_').lower()
    
    # Create or update user
    if username not in users_db:
        user_id = str(uuid.uuid4())
        users_db[username] = {
            "id": user_id,
            "username": username,
            "email": email,
            "name": name,
            "photo_url": photo_url,
            "is_premium": False,
            "subscription_tier": "free",
            "balance_tokens": 0,
            "memes_created": 0,
            "auth_provider": "google",
            "created_at": datetime.utcnow().isoformat()
        }
        subscription_tiers[username] = {
            "tier": "free",
            "started_at": datetime.utcnow().isoformat(),
            "expires_at": None,
            "paid": False
        }
        
        # Register with Consul
        register_user_with_consul(users_db[username]["id"], email, username)
        
        # Track in PostHog
        track_event("User Registered via Google", username, {
            "email": email,
            "name": name,
            "tier": "free"
        })
    else:
        # Update existing user
        users_db[username]["name"] = name
        users_db[username]["photo_url"] = photo_url
        users_db[username]["auth_provider"] = "google"
        
        # Track in PostHog
        track_event("User Logged In via Google", username, {
            "email": email,
            "tier": subscription_tiers.get(username, {}).get("tier", "free")
        })
    
    return jsonify({
        "status": "success",
        "message": "Login successful via Google",
        "user": users_db[username],
        "subscription": subscription_tiers.get(username, {"tier": "free"})
    })

@app.route('/api/v1/auth/profile', methods=['GET'])
def get_profile():
    """Get user profile with subscription info."""
    username = request.headers.get('X-User') or request.args.get('username')
    
    if not username or username not in users_db:
        return jsonify({"error": "User not found"}), 404
    
    user = users_db[username].copy()
    user["subscription"] = subscription_tiers.get(username, {"tier": "free"})
    
    return jsonify({"user": user})

@app.route('/api/v1/auth/profile', methods=['PUT'])
def update_profile():
    """Update user profile."""
    username = request.headers.get('X-User') or request.args.get('username')
    data = request.get_json()
    
    if not username or username not in users_db:
        return jsonify({"error": "User not found"}), 404
    
    if 'phone' in data:
        users_db[username]['phone'] = data['phone']
    if 'email' in data:
        users_db[username]['email'] = data['email']
    
    return jsonify({
        "status": "success",
        "user": users_db[username]
    })

# ==================== SUBSCRIPTION ROUTES ====================

@app.route('/api/v1/subscriptions/plans', methods=['GET'])
def get_subscription_plans():
    """Get available subscription plans."""
    plans = []
    for tier, info in SUBSCRIPTION_PLANS.items():
        plans.append({
            "tier": tier,
            "name": info["name"],
            "price_sats": info["price_sats"],
            "price_ksh": info["price_ksh"],
            "price_usd": round(info["price_sats"] * 0.00005, 2),  # Approximate
            "features": info["features"],
            "limits": info["limits"]
        })
    return jsonify({"plans": plans})

@app.route('/api/v1/subscriptions/create-invoice', methods=['POST'])
def create_subscription_invoice():
    """Create Lightning invoice for subscription upgrade."""
    data = request.get_json()
    
    username = data.get('username')
    tier = data.get('tier', 'pro')
    
    if not username or username not in users_db:
        return jsonify({"error": "User not found"}), 404
    
    if tier not in SUBSCRIPTION_PLANS:
        return jsonify({"error": "Invalid tier"}), 400
    
    plan = SUBSCRIPTION_PLANS[tier]
    
    if plan["price_sats"] == 0:
        return jsonify({"error": "Free tier - no payment needed"}), 400
    
    # Create Lightning invoice
    memo = f"Lyrikali {plan['name']} Subscription - {username}"
    invoice = create_lightning_invoice(plan["price_sats"], memo)
    
    if not invoice:
        return jsonify({"error": "Failed to create invoice"}), 500
    
    # Store invoice
    payment_invoices[invoice["invoice_id"]] = {
        "username": username,
        "tier": tier,
        "amount_sats": plan["price_sats"],
        "amount_ksh": plan["price_ksh"],
        "memo": memo,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Track subscription attempt in PostHog
    track_event("Subscription Invoice Created", username, {
        "tier": tier,
        "amount_sats": plan["price_sats"],
        "amount_ksh": plan["price_ksh"]
    })
    
    logger.info(f"Created subscription invoice for {username}: {tier} - {plan['price_sats']} sats")
    
    return jsonify({
        "status": "pending",
        "invoice_id": invoice["invoice_id"],
        "payment_request": invoice["payment_request"],
        "amount_sats": plan["price_sats"],
        "amount_ksh": plan["price_ksh"],
        "expires_at": invoice["expires_at"].isoformat(),
        "demo": invoice.get("demo", False),
        "instructions": "Pay with any Lightning wallet (e.g., Phoenix, Muun, BlueWallet)"
    })

@app.route('/api/v1/subscriptions/check-payment/<invoice_id>', methods=['GET'])
def check_payment(invoice_id):
    """Check if subscription payment is complete."""
    if invoice_id not in payment_invoices:
        return jsonify({"error": "Invoice not found"}), 404
    
    payment = payment_invoices[invoice_id]
    
    # Check with Lightning network
    if payment.get("demo"):
        # Demo mode - use simulated payment
        status = {"settled": payment.get("settled", False)}
    else:
        status = check_invoice_status(invoice_id)
    
    if status["settled"] and not payment.get("settled"):
        # Update payment status
        payment["settled"] = True
        payment["settled_at"] = datetime.utcnow().isoformat()
        
        # Upgrade user subscription
        username = payment["username"]
        tier = payment["tier"]
        
        users_db[username]["is_premium"] = True
        users_db[username]["subscription_tier"] = tier
        
        subscription_tiers[username] = {
            "tier": tier,
            "started_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "paid": True,
            "invoice_id": invoice_id
        }
        
        # Add Keycloak role
        add_role_to_user(username, f"{tier}_subscriber")
        
        # Track successful subscription in PostHog
        track_event("Subscription Upgraded", username, {
            "tier": tier,
            "amount_sats": payment.get("amount_sats"),
            "invoice_id": invoice_id
        })
        
        logger.info(f"User {username} upgraded to {tier}")
    
    return jsonify({
        "invoice_id": invoice_id,
        "status": "settled" if status["settled"] else "pending",
        "subscription": subscription_tiers.get(payment["username"]) if status["settled"] else None
    })

@app.route('/api/v1/subscriptions/simulate-payment/<invoice_id>', methods=['POST'])
def simulate_payment_route(invoice_id):
    """Simulate payment for testing (demo mode)."""
    if simulate_payment(invoice_id):
        payment = payment_invoices[invoice_id]
        username = payment["username"]
        tier = payment["tier"]
        
        users_db[username]["is_premium"] = True
        users_db[username]["subscription_tier"] = tier
        
        subscription_tiers[username] = {
            "tier": tier,
            "started_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "paid": True,
            "invoice_id": invoice_id,
            "demo": True
        }
        
        return jsonify({
            "status": "success",
            "message": f"Simulated payment successful - upgraded to {tier}",
            "subscription": subscription_tiers[username]
        })
    
    return jsonify({"error": "Invoice not found"}), 404

# ==================== AI MEME ENGINE ====================

MEME_CAPTIONS = {
    "funny": [
        "When the beat drops 💃🕺", "Me explaining the plot",
        "POV: You just discovered a new banger", "This hits different at 2AM"
    ],
    "trend": [
        "#Trending #Viral #Lyrikali", "When algorithm notices you",
        "POV: You're the song of the summer"
    ],
    "music": [
        "This beat is illegal 🥵", "Producer: *makes beat* Me: 👂",
        "Headphones on, world off 🎧"
    ],
    "kenyan": [
        "Nairobi nights hit different 🇰🇪", "Bongo gang rise up!",
        "Meru to the world 🌍", "Kenyan music >>>"
    ],
    "ai": [
        "Generated by AI, approved by vibes",
        "When algorithm meets creativity", "AI made this"
    ]
}

def check_meme_limit(username):
    """Check if user has reached daily meme limit."""
    user = users_db.get(username, {})
    tier_info = subscription_tiers.get(username, {"tier": "free"})
    tier = tier_info.get("tier", "free")
    
    plan = SUBSCRIPTION_PLANS[tier]
    daily_limit = plan["limits"]["memes_per_day"]
    
    if daily_limit == -1:  # Unlimited
        return True
    
    today = datetime.utcnow().date().isoformat()
    last_date = user.get("last_meme_date")
    
    if last_date != today:
        # Reset daily count
        users_db[username]["daily_meme_count"] = 0
        users_db[username]["last_meme_date"] = today
    
    return user.get("daily_meme_count", 0) < daily_limit

@app.route('/api/v1/meme/generate', methods=['POST'])
def generate_meme():
    """Generate AI meme from uploaded image/video."""
    data = request.get_json()
    
    username = data.get('username')
    style = data.get('style', 'funny')
    caption = data.get('caption', '')
    
    if not username:
        return jsonify({"error": "Username required"}), 400
    
    if username not in users_db:
        return jsonify({"error": "User not found"}), 404
    
    # Check daily limit
    if not check_meme_limit(username):
        return jsonify({
            "error": "Daily meme limit reached",
            "upgrade": "Upgrade to Pro for unlimited memes",
            "plans_url": "/api/v1/subscriptions/plans"
        }), 429
    
    # Generate AI caption if not provided
    if not caption:
        captions = MEME_CAPTIONS.get(style, MEME_CAPTIONS['funny'])
        caption = captions[datetime.utcnow().second % len(captions)]
    
    # Get quality based on tier
    tier_info = subscription_tiers.get(username, {"tier": "free"})
    tier = tier_info.get("tier", "free")
    quality = SUBSCRIPTION_PLANS[tier]["limits"].get("ai_quality", "standard")
    
    # Create meme record
    meme_id = str(uuid.uuid4())
    meme = {
        "id": meme_id,
        "username": username,
        "style": style,
        "caption": caption,
        "quality": quality,
        "likes": 0,
        "views": 0,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Store meme
    if 'memes' not in users_db[username]:
        users_db[username]['memes'] = []
    users_db[username]['memes'].append(meme)
    users_db[username]['memes_created'] += 1
    users_db[username]['daily_meme_count'] = users_db[username].get('daily_meme_count', 0) + 1
    
    logger.info(f"AI Meme generated by {username}: {meme_id} (quality: {quality})")
    
    return jsonify({
        "status": "success",
        "meme": meme,
        "caption": caption,
        "quality": quality,
        "ai_message": "🎨 Your AI-enhanced meme is ready!",
        "remaining_memes": users_db[username].get('daily_meme_count', 0)
    }), 201

@app.route('/api/v1/meme/user/<username>', methods=['GET'])
def get_user_memes(username):
    """Get all memes for a user."""
    if username not in users_db:
        return jsonify({"error": "User not found"}), 404
    
    memes = users_db[username].get('memes', [])
    return jsonify({"memes": memes, "count": len(memes)})

# ==================== PUSH NOTIFICATIONS ====================

@app.route('/api/v1/subscribe-push', methods=['POST'])
def subscribe_push():
    """Register user for web push notifications."""
    data = request.get_json()
    user_id = data.get('user_id', 'default_user')
    subscription_info = data.get('subscription')
    
    if not subscription_info:
        return jsonify({"error": "Subscription info required"}), 400
    
    subscriptions[user_id] = subscription_info
    
    try:
        webpush(
            subscription_info=subscription_info,
            data=json.dumps({
                "title": "Jambo! Welcome to Lyrikali 🎵",
                "body": "You are now part of the sound of Kenya. Start creating!",
                "icon": "/icon.png"
            }),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims=VAPID_CLAIMS
        )
    except WebPushException as ex:
        logger.error(f"Push welcome failed: {ex}")
    
    return jsonify({"message": "Successfully subscribed"}), 201

# ==================== TRENDS ====================

@app.route('/api/v1/trends', methods=['GET'])
def get_trends():
    """Google Trends based recommendations."""
    return jsonify({
        "location": "Kenya",
        "trending_artists": ["Nyaduse", "Toxic Lyrikali", "Rema"],
        "rising_queries": ["Backbencher karaoke", "Donjo Maber remix"],
        "timestamp": datetime.utcnow().isoformat()
    })

# ==================== SERVICE DISCOVERY ====================

@app.route('/api/v1/services/discover/<service_name>', methods=['GET'])
def discover_service_route(service_name):
    """Discover a service from Consul."""
    service = discover_service(service_name)
    if service:
        return jsonify({"service": service})
    return jsonify({"error": "Service not found"}), 404

# ==================== STATIC FILES ====================

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/styles.css')
def serve_css():
    return send_from_directory(app.static_folder, 'styles.css')

@app.route('/app.js')
def serve_js():
    return send_from_directory(app.static_folder, 'app.js')

@app.route('/health')
def health():
    return jsonify({
        "status": "UP",
        "service": "lyrikali-social",
        "version": "3.1.0",
        "port": SERVICE_PORT,
        "features": ["auth", "meme-engine", "keycloak", "consul", "btc-lightning", "subscriptions", "posthog"],
        "keycloak": KEYCLOAK_URL,
        "keycloak_realm": KEYCLOAK_REALM,
        "posthog": POSTHOG_HOST if POSTHOG_AVAILABLE else "not configured",
        "lnd": LND_GRPC_HOST if LND_GRPC_HOST else "not configured"
    })

# ==================== INIT ====================

if __name__ == '__main__':
    logger.info(f"🚀 Starting Lyrikali Social v3.0.0 on port {SERVICE_PORT}")
    
    # Register with Consul on startup
    register_with_consul()
    
    app.run(host='0.0.0.0', port=SERVICE_PORT)
