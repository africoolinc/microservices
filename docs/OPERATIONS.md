# StackForge Operations Runbook

## Daily Operations Checklist

### Morning (9:00 AM)
- [ ] Check Grafana dashboard for overnight anomalies
- [ ] Review Kibana for ERROR/FATAL logs in last 24h
- [ ] Verify all services are healthy: `./check-health.sh`
- [ ] Check disk space on host: `df -h`
- [ ] Review backup completion status
- [ ] Check Portainer for any stopped containers

### Evening (6:00 PM)
- [ ] Daily metrics review
- [ ] Response time trends
- [ ] Error rate summary
- [ ] Note any issues in operations log

## Weekly Tasks (Every Monday)

### Maintenance
- [ ] Update base Docker images (test in staging first)
- [ ] Review and rotate logs if needed
- [ ] Check SSL certificate expiry (alert if <30 days)
- [ ] Review security patches for stack components
- [ ] Update documentation for any changes made

### Business
- [ ] Review customer metrics and usage
- [ ] Check billing reconciliation
- [ ] Customer check-in calls (for Growth/Enterprise tiers)
- [ ] Capacity planning review

## Monthly Tasks

### Technical
- [ ] Full disaster recovery test
- [ ] Performance benchmark
- [ ] Security audit (check for new CVEs)
- [ ] Dependency updates (major versions)
- [ ] Cost optimization review
- [ ] Backup restoration test

### Business
- [ ] Financial reconciliation
- [ ] Feature roadmap review
- [ ] Customer satisfaction survey
- [ ] Competitive analysis update
- [ ] Marketing content planning

## Emergency Procedures

### Service Down
1. Check host connectivity: `ping <host>`
2. SSH to host and check Docker: `docker ps`
3. Check logs: `docker-compose logs -f --tail=100`
4. If specific service down:
   - Try restart: `docker-compose restart <service>`
   - Check resource usage: `docker stats`
   - Review recent changes
5. If full stack down:
   - Check disk space: `df -h`
   - Check memory: `free -h`
   - Restart stack: `docker-compose down && docker-compose up -d`
6. Notify customers if >15 min downtime
7. Post-incident review within 24h

### Database Issues
1. Check PostgreSQL logs: `docker-compose logs app-db`
2. Check connections: `docker exec app-db psql -U appuser -c "SELECT count(*) FROM pg_stat_activity;"`
3. Check disk space for WAL files
4. If corruption suspected:
   - Stop writes immediately
   - Restore from backup
   - Point-in-time recovery if available
5. Contact customers with data impact

### Security Incident
1. Isolate affected services
2. Capture logs and evidence
3. Assess scope of breach
4. Rotate all credentials
5. Apply patches/updates
6. Notify affected customers
7. Post-incident report

## Monitoring & Alerting

### Key Metrics to Watch

#### Infrastructure
- CPU usage >80% for 5min
- Memory usage >90%
- Disk usage >85%
- Load average > number of CPUs

#### Application
- Error rate >1% of requests
- Response time >500ms (95th percentile)
- Service down for >2 minutes
- Kafka lag increasing
- Database connections >80% of max

#### Business
- Customer login failures spike
- Unusual traffic patterns
- Payment processing errors

### Alert Channels
- **Slack**: #stackforge-alerts
- **Email**: ops@stackforge.io
- **SMS**: For critical issues only

## Health Check Commands

```bash
# Quick status
docker-compose ps

# All services health
curl http://localhost:8001/status

# Database connectivity
docker exec app-db pg_isready -U appuser

# Redis connectivity
docker exec redis redis-cli ping

# Kafka topics
docker exec kafka kafka-topics.sh --list --bootstrap-server localhost:9092

# Consul members
curl http://localhost:8500/v1/status/peers
```

## Backup & Recovery

### Automated Backups (Daily at 2 AM)
- PostgreSQL: `pg_dump` to S3
- Configuration: Git commits
- Grafana dashboards: Export JSON

### Recovery Procedures
1. Stop affected services
2. Restore from latest backup
3. Replay WAL logs if point-in-time needed
4. Verify data integrity
5. Restart services
6. Notify customers

## Scaling Guidelines

### Vertical Scaling (Bigger server)
- Use when: Single services need more resources
- Pros: Simple, no code changes
- Cons: Downtime, limits

### Horizontal Scaling (More servers)
- Use when: Need redundancy, traffic growing
- Implementation:
  1. Set up load balancer (Kong already handles this)
  2. Deploy multiple service instances
  3. Register all with Consul
  4. Configure sticky sessions if needed

### Database Scaling
- Read replicas for query load
- Connection pooling (PgBouncer)
- Sharding for very large datasets

## Customer Onboarding

### Pre-Sale
1. Discovery call (30 min)
2. Architecture review (if migrating)
3. Quote and SOW
4. Contract signature

### Technical Onboarding (Week 1)
1. Provision dedicated stack or namespace
2. Configure custom domain and SSL
3. Set up customer admin accounts
4. Configure backup schedule
5. Run health checks and handover

### Knowledge Transfer (Week 2)
1. Admin UI walkthrough
2. API documentation review
3. Monitoring dashboard training
4. Escalation procedures
5. Go-live approval

## Cost Management

### Infrastructure Costs (Monthly Estimates)

| Component | DigitalOcean | AWS | Linode |
|-----------|--------------|-----|--------|
| 4GB/2CPU Droplet | $24 | $35 | $24 |
| 8GB/4CPU Droplet | $48 | $70 | $48 |
| 16GB/8CPU Droplet | $96 | $140 | $96 |
| Block Storage | $0.10/GB | $0.10/GB | $0.10/GB |
| Backups | 20% | 20% | 20% |

### Customer Pricing Formula
```
Base Price = Infrastructure Cost × 3 (covers: infra + labor + profit)
Example: $48 droplet → $149/month Starter tier
```

### Cost Optimization
- Right-size instances based on actual usage
- Use spot/preemptible instances for non-critical workloads
- Implement auto-shutdown for dev environments
- Reserved instances for long-term customers

## Troubleshooting Common Issues

### Kong Gateway Issues
```bash
# Check Kong migrations
docker-compose logs kong | grep migration

# Reset Kong (careful - wipes config!)
docker-compose down
rm -rf postgres-data/kong-db
docker-compose up -d kong
```

### Service Discovery Failures
```bash
# Check Consul health
curl http://localhost:8500/v1/status/leader

# Deregister dead services
curl -X PUT http://localhost:8500/v1/agent/service/deregister/<service-id>
```

### Kafka Issues
```bash
# Check topic lag
docker exec kafka kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --all-groups

# Reset consumer group (careful!)
docker exec kafka kafka-consumer-groups.sh --bootstrap-server localhost:9092 --reset-offsets --to-latest --execute --group <group>
```

### ELK Stack Issues
```bash
# Check Elasticsearch cluster health
curl http://localhost:9200/_cluster/health

# Check disk watermark
curl http://localhost:9200/_cat/allocation?v

# Clear old indices (if disk full)
curl -X DELETE http://localhost:9200/logstash-*
```

## Contact Information

| Role | Name | Contact |
|------|------|---------|
| Technical Lead | Gibson | Discord/Signal |
| Business Lead | AhieJuma | Moltbook/Discord |
| Escalation | Juma Family | Family chat |

## Revision History

| Date | Author | Changes |
|------|--------|---------|
| 2026-02-05 | AhieJuma | Initial runbook creation |

---
*Document Status: Draft - Review with team before production use*
