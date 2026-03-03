# Gibson's Microservices Stack - Long-Term Memory

## Project Overview
An AI-driven microservices ecosystem designed for e-commerce, fintech, and social networking. Hosted on `ahie` (host) with some remote components.

## Recent Decisions & Updates
- **2026-02-27**: 
    - Identified Kafka listener configuration error (port conflict) and updated `docker-compose.yml`.
    - Initiated rebuild of `ecommerce-service`, `fintech-service`, and `social-media-service`.
    - Discovered Keycloak unhealthy status due to `realm_attribute` missing in DB.
    - Proposed "StackDuka Connect" business model.

## Infrastructure
- **Host**: ahie
- **Project Name**: microservices-stack
- **Key Services**: Kong, Keycloak, Consul, Kafka, Redis, PostgreSQL.

## Todos
- [ ] Fix Keycloak DB schema.
- [ ] Verify Fintech service functionality.
- [ ] Implement automated backup script for volumes.
- [ ] Rotate admin passwords (currently `adminpass`).
