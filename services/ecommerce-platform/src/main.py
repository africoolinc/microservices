from flask import Flask, request, jsonify, send_from_directory
from prometheus_flask_exporter import PrometheusMetrics
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import redis
import json
import os
import uuid
from datetime import datetime
from kafka import KafkaProducer
import logging
from pythonjsonlogger import jsonlogger
from functools import wraps
from marshmallow import Schema, fields

# Initialize Flask app
app = Flask(__name__, static_folder='../frontend', static_url_path='')

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sf_ecommerce_secure_key_2026')
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{os.environ.get('DB_USER', 'appuser')}:{os.environ.get('DB_PASS', 'apppass')}@{os.environ.get('DB_HOST', 'app-db')}/{os.environ.get('DB_NAME', 'appdb')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
metrics = PrometheusMetrics(app)

# Initialize Redis (for Hot Items Caching)
redis_client = redis.Redis(
    host=os.environ.get('REDIS_HOST', 'redis'),
    port=int(os.environ.get('REDIS_PORT', 6379)),
    decode_responses=True
)

# Initialize Kafka producer (for Order Events)
try:
    kafka_producer = KafkaProducer(
        bootstrap_servers=[os.environ.get('KAFKA_BOOTSTRAP', 'kafka:9092')],
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        acks='all',
        retries=3
    )
except Exception as e:
    print(f"Warning: Could not connect to Kafka: {e}")
    kafka_producer = None

# Setup logging
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Models
class Product(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock_quantity = db.Column(db.Integer, default=0)
    category = db.Column(db.String(100))
    image_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class Order(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='PENDING')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Schemas
class ProductSchema(Schema):
    id = fields.Str()
    name = fields.Str()
    description = fields.Str()
    price = fields.Float()
    stock_quantity = fields.Int()
    category = fields.Str()
    image_url = fields.Str()

# Keycloak Token Validation Placeholder
def keycloak_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # In production, use python-keycloak to validate the bearer token
        # For now, we allow access if a token exists
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Authorization required (Keycloak)'}), 401
        return f(*args, **kwargs)
    return decorated

# Static Routes (Frontend)
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/styles.css')
def serve_css():
    return send_from_directory(app.static_folder, 'styles.css')

@app.route('/app.js')
def serve_js():
    return send_from_directory(app.static_folder, 'app.js')

# API Routes
@app.route('/api/v1/health')
def health():
    return jsonify({
        "status": "UP",
        "service": "catalog-service",
        "kafka": "CONNECTED" if kafka_producer else "DISCONNECTED",
        "redis": "CONNECTED" if redis_client.ping() else "DISCONNECTED"
    })

@app.route('/api/v1/products', methods=['GET'])
def get_products():
    # Check hot cache
    cached = redis_client.get('hot_products')
    if cached:
        return jsonify(json.loads(cached))
    
    products = Product.query.filter_by(is_active=True).all()
    schema = ProductSchema(many=True)
    result = schema.dump(products)
    
    # Cache hot items for 60 seconds
    redis_client.setex('hot_products', 60, json.dumps(result))
    return jsonify(result)

@app.route('/api/v1/orders', methods=['POST'])
@keycloak_required
def place_order():
    data = request.get_json()
    order_id = str(uuid.uuid4())
    
    # Async Event to Kafka (Amazon-style checkout)
    if kafka_producer:
        kafka_producer.send('order_events', {
            'event_type': 'ORDER_PLACED',
            'order_id': order_id,
            'user_id': data.get('user_id'),
            'items': data.get('items'),
            'timestamp': datetime.utcnow().isoformat()
        })
        logger.info(f"Order event sent to Kafka: {order_id}")
    
    return jsonify({
        "message": "Order accepted and processing",
        "order_id": order_id,
        "status": "QUEUED"
    }), 202

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)
