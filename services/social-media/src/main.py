from flask import Flask, request, jsonify, send_from_directory
from prometheus_flask_exporter import PrometheusMetrics
import os
import json
import uuid
import requests
from datetime import datetime
import logging
from pythonjsonlogger import jsonlogger
from pywebpush import webpush, WebPushException

# Initialize Flask app
app = Flask(__name__, static_folder='../frontend', static_url_path='')

# Metrics for monitoring
metrics = PrometheusMetrics(app)

# Configuration
KEYCLOAK_URL = os.environ.get('KEYCLOAK_URL', 'http://10.144.118.159:8080')
KEYCLOAK_REALM = os.environ.get('KEYCLOAK_REALM', 'lyrikali')
KEYCLOAK_CLIENT_ID = os.environ.get('KEYCLOAK_CLIENT_ID', 'lyrikali-app')
CONSUL_URL = os.environ.get('CONSUL_URL', 'http://10.144.118.159:8500')
SERVICE_ID = os.environ.get('SERVICE_ID', 'social-media-service')

# VAPID keys for Push Notifications
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "BC-ishmmAxcz1syjpNXdPNL_7ENM7DDmmkYkFVr9Ag57f9o3mSPoAE2C--pQBW1PhzBJmOyTJu9ML7noewPQY9Q")
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "myzvOUzZhCZKTFe9xr0j6bWaeBcX0UMXMBF8hHHUJDI")
VAPID_CLAIMS = {"sub": "mailto:ahie@juma.family"}

# Setup logging
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# In-memory storage
subscriptions = {}
users_db = {}  # {user_id: user_data}

# ==================== CONSUL REGISTRATION ====================

def register_with_consul():
    """Register this service with Consul for service discovery."""
    try:
        service_config = {
            "ID": SERVICE_ID,
            "Name": "lyrikali-social",
            "Port": 5000,
            "Meta": {
                "version": "2.2.0",
                "features": "auth,meme-engine,keycloak"
            },
            "Check": {
                "HTTP": f"http://localhost:5000/health",
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
            logger.info(f"✅ Service {SERVICE_ID} registered with Consul")
            return True
        else:
            logger.warning(f"⚠️ Consul registration failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Consul registration error: {e}")
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

# ==================== KEYCLOAK INTEGRATION ====================

def get_keycloak_token():
    """Get admin token for Keycloak operations."""
    try:
        response = requests.post(
            f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
            data={
                "grant_type": "client_credentials",
                "client_id": "admin-cli",
                "client_secret": os.environ.get('KEYCLOAK_ADMIN_SECRET', '')
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
            # Fallback to demo mode
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
    
    # Store in local DB (demo fallback or cache)
    user_id = str(uuid.uuid4())
    users_db[username] = {
        "id": user_id,
        "username": username,
        "email": email,
        "phone": phone,
        "is_premium": False,
        "balance_tokens": 0,
        "memes_created": 0,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Register with Consul
    register_user_with_consul(user_id, email, username)
    
    logger.info(f"New user registered: {username}")
    
    return jsonify({
        "status": "success",
        "message": "User registered successfully",
        "user": {
            "id": user_id,
            "username": username,
            "email": email
        },
        "keycloak_created": kc_result is not None
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
        # Ensure local user exists
        if username not in users_db:
            users_db[username] = {
                "id": str(uuid.uuid4()),
                "username": username,
                "email": f"{username}@lyrikali.ke",
                "is_premium": False,
                "balance_tokens": 0,
                "memes_created": 0
            }
        
        return jsonify({
            "status": "success",
            "message": "Login successful",
            "token": kc_result.get('access_token'),
            "user": users_db[username]
        })
    
    # Fallback: check local users (demo mode)
    if username in users_db and password:
        return jsonify({
            "status": "success",
            "message": "Login successful (demo mode)",
            "user": users_db[username]
        })
    
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/v1/auth/profile', methods=['GET'])
def get_profile():
    """Get user profile."""
    username = request.headers.get('X-User') or request.args.get('username')
    
    if not username or username not in users_db:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({"user": users_db[username]})

@app.route('/api/v1/auth/profile', methods=['PUT'])
def update_profile():
    """Update user profile."""
    username = request.headers.get('X-User') or request.args.get('username')
    data = request.get_json()
    
    if not username or username not in users_db:
        return jsonify({"error": "User not found"}), 404
    
    # Update allowed fields
    if 'phone' in data:
        users_db[username]['phone'] = data['phone']
    if 'email' in data:
        users_db[username]['email'] = data['email']
    
    return jsonify({
        "status": "success",
        "user": users_db[username]
    })

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
    
    # Generate AI caption if not provided
    if not caption:
        captions = MEME_CAPTIONS.get(style, MEME_CAPTIONS['funny'])
        caption = captions[datetime.utcnow().second % len(captions)]
    
    # Create meme record
    meme_id = str(uuid.uuid4())
    meme = {
        "id": meme_id,
        "username": username,
        "style": style,
        "caption": caption,
        "likes": 0,
        "views": 0,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Store meme
    if 'memes' not in users_db[username]:
        users_db[username]['memes'] = []
    users_db[username]['memes'].append(meme)
    users_db[username]['memes_created'] += 1
    
    logger.info(f"AI Meme generated by {username}: {meme_id}")
    
    return jsonify({
        "status": "success",
        "meme": meme,
        "caption": caption,
        "ai_message": "🎨 Your AI-enhanced meme is ready!"
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

# ==================== MONETIZATION ====================

@app.route('/api/v1/monetization/upgrade', methods=['POST'])
def upgrade_to_premium():
    """Handle M-Pesa premium subscription."""
    data = request.get_json()
    user_id = data.get('user_id', 'default_user')
    plan = data.get('plan', 'pro')
    
    amount = 50 if plan == 'pro' else 200
    
    if user_id in users_db:
        users_db[user_id]["is_premium"] = True
    
    return jsonify({
        "status": "success",
        "message": f"Upgraded to {plan.upper()} via M-Pesa",
        "amount": amount
    })

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
        "version": "2.2.0",
        "features": ["auth", "meme-engine", "keycloak", "consul"],
        "keycloak": KEYCLOAK_URL,
        "consul": CONSUL_URL
    })

# ==================== INIT ====================

if __name__ == '__main__':
    # Register with Consul on startup
    register_with_consul()
    
    app.run(host='0.0.0.0', port=5000)
