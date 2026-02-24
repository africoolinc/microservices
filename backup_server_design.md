# Fallback Server Infrastructure Design
## Secondary Cloud Instance for High Availability

**Prepared:** Saturday, February 21st, 2026  
**Purpose:** Design and cost estimation for a backup server on AWS/Azure

---

## 🎯 Executive Summary

This document outlines infrastructure options for deploying a secondary (fallback) server to ensure 24/7 availability if the primary StackForge server (`10.144.118.159`) goes down.

### Recommendation
**AWS t3.xlarge (4 vCPU / 16GB) with Spot Instances** — Best cost-to-performance ratio with automatic failover capability.

---

## 🏗️ Architecture Options

### Option A: Hot Standby (Active-Passive)
```
                    ┌─────────────────────┐
                    │   Cloudflare DNS    │
                    │   (Failover Rule)   │
                    └──────────┬──────────┘
                               │
         ┌─────────────────────┴─────────────────────┐
         │                                           │
         ▼                                           ▼
┌─────────────────────┐                   ┌─────────────────────┐
│   PRIMARY SERVER   │                   │   BACKUP SERVER     │
│   10.144.118.159   │────── health ─────▶│   AWS/Azure         │
│   (StackForge)    │      check         │   (Hot Standby)     │
│                   │                   │                     │
│  - 17 containers  │                   │  - Replicated       │
│  - Full traffic   │                   │    containers       │
└─────────────────────┘                   └─────────────────────┘
```

**Pros:**
- Near-instant failover (< 60 seconds)
- Zero data loss (real-time sync)
- Fully warm — instant capacity

**Cons:**
- Doubled infrastructure cost
- Requires real-time data replication

---

### Option B: Warm Standby (Scheduled Sync)
```
┌─────────────────────┐                   ┌─────────────────────┐
│   PRIMARY SERVER   │  ◄── rsync ──►   │   BACKUP SERVER     │
│   10.144.118.159   │    every 15min    │   AWS/Azure         │
│                    │                   │   (Stopped/Idle)   │
│  - Active          │                   │  - Spin up on      │
│                    │                   │    failure          │
└─────────────────────┘                   └─────────────────────┘
```

**Pros:**
- ~70% cost savings (pay only when running)
- Simpler data sync
- Good for non-critical services

**Cons:**
- 5-15 minute recovery time
- Potential data loss (up to 15 min)

---

### Option C: Cold Standby (On-Demand)
```
┌─────────────────────┐                   ┌─────────────────────┐
│   PRIMARY SERVER   │                   │   BACKUP SERVER     │
│   10.144.118.159   │                   │   AWS/Azure AMI     │
│                    │                   │   (Terminated)     │
│  - Active          │                   │  - Deploy from      │
│                    │                   │    snapshot on      │
│                    │                   │    failure          │
└─────────────────────┘                   └─────────────────────┘
```

**Pros:**
- Near-zero idle cost ($5-10/month for snapshots)
- Complete flexibility

**Cons:**
- 15-30 minute recovery
- Manual intervention required

---

## 💰 Cost Estimation

### Current Infrastructure
| Resource | Specification | Monthly Cost (Est.) |
|----------|---------------|---------------------|
| Main Server | 15GB RAM, dedicated | Existing |

### AWS EC2 Pricing (eu-west-1 - Ireland)

| Instance Type | vCPU | RAM | On-Demand/hr | Spot/hr | Monthly (Spot) |
|---------------|------|-----|--------------|---------|----------------|
| t3.large | 2 | 8GB | $0.0832 | $0.0250 | $18.25 |
| t3.xlarge | 4 | 16GB | $0.1664 | $0.0500 | $36.50 |
| t3.2xlarge | 8 | 32GB | $0.3328 | $0.1000 | $73.00 |
| r5.large | 2 | 16GB | $0.1260 | $0.0380 | $27.70 |
| r5.xlarge | 4 | 32GB | $0.2520 | $0.0760 | $55.40 |

### Azure VM Pricing (EU West)

| VM Size | vCPU | RAM | Pay-as-you-go/hr | Spot/hr | Monthly (Spot) |
|---------|------|-----|------------------|---------|----------------|
| D2s_v3 | 2 | 8GB | $0.0960 | $0.0290 | $21.10 |
| D4s_v3 | 4 | 16GB | $0.1920 | $0.0580 | $42.30 |
| D8s_v3 | 8 | 32GB | $0.3840 | $0.1150 | $83.90 |

### Additional Costs (Monthly)

| Service | AWS | Azure |
|---------|-----|-------|
| Data transfer (out) | ~$10-20 | ~$10-20 |
| EBS/Managed Disk | $15-30 | $15-25 |
| Elastic IP | $3.65 | ~$3 |
| **Total Monthly (t3.xlarge spot)** | **$65-90** | **$70-90** |

---

## 📊 Cost Comparison Summary

### Scenario: Warm Standby (runs only when primary fails)
Assuming 1 failure event per month, server runs for 24 hours during recovery:

| Configuration | Cost per Incident | Monthly (idle) | Total/Month |
|---------------|-------------------|-----------------|-------------|
| AWS t3.xlarge Spot | $2.00 | $0 | $2-5 |
| Azure D4s_v3 Spot | $2.50 | $0 | $2-5 |
| AWS t3.xlarge On-Demand | $4.00 | $0 | $4 |
| Azure D4s_v3 Pay-as-you-go | $4.60 | $0 | $5 |

### Scenario: Hot Standby (24/7 running)
| Configuration | Monthly Cost |
|---------------|-------------|
| AWS t3.xlarge Spot | $36-50 |
| Azure D4s_v3 Spot | $42-60 |
| AWS t3.xlarge On-Demand | $120+ |
| Azure D4s_v3 Pay-as-you-go | $140+ |

---

## 🔧 Recommended Implementation

### Phase 1: Warm Standby (Recommended Start)
1. **Create AMI/Image** of current server state
2. **Configure Spot Instance** with auto-termination protection
3. **Set up health monitoring** via Cloudflare or external service
4. **Script automated spin-up** on primary failure

### Phase 2: Data Sync
```bash
# Sync script (run via cron every 15 minutes)
rsync -avz --delete \
  -e "ssh -i ~/.ssh/fallback-key" \
  --exclude='.git' \
  --exclude='logs/' \
  --exclude='*.log' \
  /home/africool/ ubuntu@<backup-ip>:/home/africool/
```

### Phase 3: Failover Automation
```yaml
# cloudflare-failover.yaml (Terraform example)
resource "cloudflare_record" "fallback" {
  zone_id = var.zone_id
  name    = "api"
  value   = aws_instance.backup.public_ip
  type    = "A"
  proxied = true
}
```

---

## 📋 Implementation Checklist

- [ ] Choose cloud provider (AWS recommended)
- [ ] Select instance size (t3.xlarge recommended)
- [ ] Create server image/AMI from StackForge
- [ ] Set up AWS Spot Fleet or single Spot instance
- [ ] Configure security groups (same as primary)
- [ ] Set up DNS failover with Cloudflare
- [ ] Create data sync script
- [ ] Test failover procedure
- [ ] Document recovery procedures

---

## 🔐 Security Considerations

1. **SSH Keys:** Generate separate key pair for fallback server
2. **Firewall:** Same port rules as primary (22, 80, 443)
3. **Secrets:** Use environment variables or HashiCorp Vault
4. **Network:** Consider VPC peering for private communication

---

## 📞 Next Steps

1. **Confirm budget** — $50-100/month for hot standby
2. **Choose instance type** — t3.xlarge (16GB) matches current RAM
3. **Select region** — eu-west-1 (Ireland) for AWS, EU West for Azure
4. **Initiate account setup** if needed

---

## 📎 Appendix: Quick Commands

### AWS Spot Instance Request
```bash
aws ec2 request-spot-instances \
  --spot-price "0.05" \
  --instance-count 1 \
  --type "one-time" \
  --launch-specification "{
    \"ImageId\": \"ami-0abcdef1234567890\",
    \"InstanceType\": \"t3.xlarge\",
    \"KeyName\": \"fallback-key\",
    \"SecurityGroupIds\": [\"sg-0123456789\"],
    \"SubnetId\": \"subnet-0123456789\"
  }"
```

### Azure Spot VM
```bash
az vm create \
  --resource-group rg-failover \
  --name fallback-server \
  --size Standard_D4s_v3 \
  --image UbuntuLTS \
  --spot --max-price 0.058
```
