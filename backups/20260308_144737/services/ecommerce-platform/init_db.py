import os
import uuid
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Configuration (match main.py)
DB_USER = os.environ.get('DB_USER', 'appuser')
DB_PASS = os.environ.get('DB_PASS', 'apppass')
DB_HOST = os.environ.get('DB_HOST', 'app-db')
DB_NAME = os.environ.get('DB_NAME', 'appdb')
DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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

def init_products():
    sample_products = [
        {
            "name": "Sovereign Agent Node",
            "description": "Enterprise-grade hardware for running your own sovereign AI agents.",
            "price": 2499.00,
            "stock_quantity": 50,
            "category": "Hardware"
        },
        {
            "name": "Moltchain Bridge v1",
            "description": "Lightning-to-Mpesa settlement bridge for agentic commerce.",
            "price": 499.00,
            "stock_quantity": 100,
            "category": "Software"
        },
        {
            "name": "Kafka Broker Managed",
            "description": "Fully managed Kafka broker for event-driven architectures.",
            "price": 199.00,
            "stock_quantity": 1000,
            "category": "Infrastructure"
        }
    ]
    
    for p_data in sample_products:
        p = Product.query.filter_by(name=p_data['name']).first()
        if not p:
            p = Product(**p_data)
            db.session.add(p)
    
    db.session.commit()
    print("Sample products initialized!")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_products()
