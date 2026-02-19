# E-Commerce Platform Microservice
Production-ready e-commerce backend with user auth, product catalog, orders, and inventory.

## 🛍️ Features
- **User Authentication** (JWT-based with role management)
- **Product Catalog Management** (CRUD, search, categorization)
- **Shopping Cart & Checkout** (persistent cart, guest checkout)
- **Order Processing** (async via Kafka, status tracking)
- **Inventory Management** (real-time stock, low-stock alerts)
- **Payment Processing hooks** (Stripe integration ready)
- **Real-time Traffic Monitoring** (Prometheus/Grafana metrics)
- **Caching Layer** (Redis for hot products and user sessions)
- **Event Streaming** (Kafka for order/product events)
- **Frontend Interface** (Modern Vue.js UI with responsive design)

## 🚀 Quick Start

```bash
# Build and run the entire stack
docker-compose up -d

# Access the services:
# - E-Commerce API: http://localhost:5001
# - E-Commerce Frontend: http://localhost:80 (nginx proxy)
# - Keycloak Admin: http://localhost:8080
# - Grafana Dashboard: http://localhost:3010
# - Prometheus Metrics: http://localhost:9090
```

## 📡 API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `GET /auth/profile` - User profile
- `GET /auth/logout` - User logout

### Products
- `GET /products` - List all products (with pagination/filtering)
- `GET /products/:id` - Get product details
- `POST /products` - Create product (admin only)
- `PUT /products/:id` - Update product (admin only)
- `DELETE /products/:id` - Delete product (admin only)
- `GET /products/search?q=query` - Search products
- `GET /products/category/:category` - Filter by category

### Cart
- `GET /cart` - View cart
- `POST /cart/items` - Add item to cart
- `PUT /cart/items/:id` - Update cart item
- `DELETE /cart/items/:id` - Remove from cart
- `DELETE /cart` - Clear entire cart

### Orders
- `POST /orders` - Create order (publishes to Kafka)
- `GET /orders` - List user orders
- `GET /orders/:id` - Order details
- `PUT /orders/:id/cancel` - Cancel order

### Inventory
- `GET /inventory/:productId` - Check stock
- `POST /inventory/update` - Update stock (admin only)
- `GET /inventory/low-stock` - Low stock alerts

### Analytics
- `GET /analytics/top-selling` - Top selling products
- `GET /analytics/revenue` - Revenue metrics
- `GET /analytics/users` - User activity metrics

### Health & Metrics
- `GET /health` - Service health check
- `GET /metrics` - Prometheus metrics
- `GET /` - Service info and status

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Load Balancer/Nginx                     │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│              E-Commerce Service (Port 5001)                │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌──────────────┐    │
│  │  Auth   │ │ Products│ │   Cart   │ │   Orders     │    │
│  │ Module  │ │ Module  │ │  Module  │ │  Module      │    │
│  └────┬────┘ └────┬────┘ └────┬─────┘ └──────┬───────┘    │
│       │           │           │              │             │
│  ┌────┴───────────┴───────────┴──────────────┴─────────┐  │
│  │           Flask Service Layer                       │  │
│  └──────────────┬──────────────────────────────────────┘  │
│                 │                                          │
│  ┌──────────────┴──────────────────────────────────────┐  │
│  │                 Data Layer                         │  │
│  │  ┌────────────┐ ┌────────┐ ┌─────────────────────┐ │  │
│  │  │ PostgreSQL │ │  Redis │ │   Message Queue     │ │  │
│  │  │(Persistent │ │(Cache, │ │     (Kafka)         │ │  │
│  │  │  Storage)  │ │Session)│ │(Async Events)       │ │  │
│  │  └────────────┘ └────────┘ └─────────────────────┘ │  │
│  └─────────────────────────────────────────────────────┘  │
│                           │                                │
│         ┌─────────────────┼─────────────────┐              │
│         ▼                 ▼                 ▼              │
│    ┌─────────┐     ┌────────────┐    ┌─────────────┐     │
│    │  Kafka  │     │  Keycloak  │    │ Monitoring  │     │
│    │(Events) │     │(Identity)  │    │ (Prometheus │     │
│    └─────────┘     └────────────┘    │   + Grafana)│     │
│                                     └─────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Configuration

Environment variables:
- `DB_HOST` - PostgreSQL host (default: app-db)
- `DB_NAME` - Database name (default: appdb)
- `DB_USER` - Database user (default: appuser)
- `DB_PASS` - Database password (default: apppass)
- `REDIS_HOST` - Redis host (default: redis)
- `REDIS_PORT` - Redis port (default: 6379)
- `KAFKA_BOOTSTRAP` - Kafka bootstrap servers (default: kafka:9092)
- `SECRET_KEY` - JWT secret key (default: your-secret-key-change-in-production)

## 📊 Monitoring

Metrics exposed on `/metrics`:
- `ecommerce_products_total` - Total products in catalog
- `ecommerce_users_total` - Total registered users
- `ecommerce_orders_total` - Total orders created
- `ecommerce_inventory_stock` - Current stock levels
- `http_requests_total` - HTTP request count
- `http_request_duration_seconds` - Request latency

## 💼 Business Logic

### Order Flow
1. User authenticates and browses products (cached in Redis)
2. User adds items to cart (stored in DB for persistence)
3. User submits order → Order created in DB with status 'PENDING'
4. Order event published to Kafka topic `order_events`
5. Inventory system processes event and reserves stock
6. Payment processing (external webhook to Stripe/PayPal)
7. Order status updated to 'CONFIRMED' or 'FAILED'
8. Shipping notification sent to user

### Caching Strategy
- Hot products cached in Redis (5min TTL)
- User sessions stored in Redis
- Recently viewed items cached per user
- Category listings cached separately

### Event-Driven Architecture
- Product events (created/updated/deleted) sent to Kafka
- Order events (created/paid/shipped/cancelled) sent to Kafka
- Inventory updates triggered by order events
- Analytics events for business intelligence

## 🧪 Testing

```bash
# Run tests
pytest tests/

# With coverage
pytest --cov=src tests/
```

## 📦 Deployment

Included in main `docker-compose.yml`:
```yaml
ecommerce-service:
  build: ./services/ecommerce-platform
  ports:
    - "5001:5000"
  environment:
    - SERVICE_ID=ecommerce-service
    - DB_HOST=app-db
    - REDIS_HOST=redis
    - KAFKA_BOOTSTRAP=kafka:9092
    - SECRET_KEY=your-production-secret-key
  depends_on:
    - app-db
    - redis
    - kafka
```

## 🌐 Frontend Integration

The service includes a modern, responsive frontend built with:
- Vue.js for dynamic UI components
- Responsive design for mobile/desktop
- Real-time cart updates
- Product search and filtering
- User authentication flows
- Order history and tracking

Accessible at: http://localhost (proxied through nginx)

## 🚀 Scaling Considerations

- Horizontal scaling via container orchestration
- Database read replicas for high-read scenarios
- CDN for static assets and product images
- Auto-scaling based on traffic metrics
- Load balancing across multiple instances

---

*Part of Gibson's Microservices Stack*
*Use Case: E-commerce Platforms - Production Ready*
