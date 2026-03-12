# Social Media & Streaming Microservice
User feeds, content recommendations, event streaming, and user behavior analytics.

## 🎬 Features
- User Feeds (timeline algorithm)
- Content Recommendations (ML-based)
- Event Streaming (Kafka)
- User Behavior Analytics
- Real-time Notifications
- Content Management
- Social Graph (follow/friends)

## 🚀 Quick Start

```bash
# Build and run
docker build -t social-media-service .
docker run -p 5003:5000 social-media-service
```

## 📡 API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/logout` - Logout
- `GET /auth/me` - Current user profile

### Users
- `GET /users/:id` - User profile
- `PUT /users/:id` - Update profile
- `GET /users/search?q=query` - Search users
- `POST /users/:id/follow` - Follow user
- `DELETE /users/:id/follow` - Unfollow user
- `GET /users/:id/followers` - List followers
- `GET /users/:id/following` - List following

### Feed
- `GET /feed` - Personal feed (algorithm-based)
- `GET /feed/trending` - Trending content
- `POST /feed/preference` - Update feed preferences

### Content
- `POST /content` - Create post/video
- `GET /content/:id` - Get content
- `PUT /content/:id` - Update content
- `DELETE /content/:id` - Delete content
- `POST /content/:id/like` - Like content
- `POST /content/:id/comment` - Comment on content
- `GET /content/:id/comments` - Get comments

### Recommendations
- `GET /recommendations/for-you` - Personalized recommendations
- `GET /recommendations/similar?content=id` - Similar content
- `GET /recommendations/popular` - Popular content
- `GET /recommendations/new` - Fresh content

### Events
- `POST /events/track` - Track user event
- `GET /events/history` - User event history

### Analytics
- `GET /analytics/user/:id` - User behavior analytics
- `GET /analytics/content/:id` - Content performance
- `GET /analytics/trending` - Trending topics

### Notifications
- `GET /notifications` - User notifications
- `PUT /notifications/:id/read` - Mark as read

### Health
- `GET /health` - Service health check
- `GET /metrics` - Prometheus metrics

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│   Social Media Service (Port 5003)       │
├─────────────────────────────────────────┤
│  ┌─────────┐ ┌─────────┐ ┌──────────┐  │
│  │  Feed   │ │ Content │ │Social    │  │
│  │Algorithm│ │ Module  │ │ Graph    │  │
│  └────┬────┘ └────┬────┘ └────┬─────┘  │
│       │           │           │         │
│  ┌────┴───────────┴───────────┴─────┐  │
│  │    Recommendation Engine         │  │
│  │       (ML-based scoring)         │  │
│  └──────────────┬───────────────────┘  │
│                 │                       │
│  ┌──────────────┴───────────────────┐  │
│  │         Data Layer               │  │
│  │  ┌────────┐ ┌────────┐          │  │
│  │  │PostgreSQL│ │ Redis │          │  │
│  │  │(Content)│ │(Feed)  │          │  │
│  │  └────────┘ └────────┘          │  │
│  └──────────────────────────────────┘  │
│                 │                       │
│         ┌───────┴───────┐              │
│         ▼               ▼              │
│    ┌─────────┐     ┌─────────┐         │
│    │  Kafka  │     │   ELK   │         │
│    │(Events) │     │ (Analytics)      │
│    └─────────┘     └─────────┘         │
└─────────────────────────────────────────┘
```

## 🔧 Configuration

Environment variables:
- `DB_HOST` - PostgreSQL host
- `REDIS_HOST` - Redis host (for feed caching)
- `KAFKA_BOOTSTRAP` - Kafka bootstrap servers
- `RECOMMENDATION_ALGO` - Algorithm type (trending, personalized, hybrid)
- `FEED_CACHE_TTL` - Feed cache time (default: 300s)

## 📊 Monitoring

Metrics exposed on `/metrics`:
- `social_posts_created_total` - Posts created
- `social_feed_requests_total` - Feed API calls
- `social_engagement_rate` - Likes/comments per view
- `social_active_users` - Daily active users
- `social_recommendation_clicks` - Recommendation CTR

## 💼 Business Logic

### Feed Algorithm
1. Recency: Newer posts score higher (exponential decay)
2. Engagement: Posts with more likes/comments rank higher
3. Social Graph: Content from followed users prioritized
4. Diversity: Mix of content types (70% following, 30% discovery)
5. Personalization: Based on past interactions

### Recommendation Engine
- Collaborative filtering: "Users like you enjoyed..."
- Content-based: Similar tags/categories
- Trending: What's popular now
- Fresh: New content boost

### Event Tracking
All user actions published to Kafka:
- `content.viewed` - User viewed content
- `content.liked` - User liked content
- `content.commented` - User commented
- `user.followed` - User followed someone
- `feed.scrolled` - Feed scroll events

### Analytics Pipeline
1. Events published to Kafka
2. Logstash consumes and processes
3. Elasticsearch indexes for search
4. Kibana dashboards for visualization

## 🧪 Testing

```bash
# Run tests
pytest tests/

# Load testing
locust -f tests/locustfile.py
```

---

*Part of Gibson's Microservices Stack*
*Use Case: Social Media/Streaming Services*
