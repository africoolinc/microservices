# Deployment Policy - Gibson Project

## Critical Deployment Rules

### NEVER DEPLOY REMOTE STACKS LOCALLY
- `docker-compose.yml` is for REMOTE deployment only (10.144.118.159)
- `docker-compose-local.yml` is for LOCAL development only
- Violating this rule causes system conflicts and environment pollution

### Environment Separation
- **Local Environment**: For config storage and management scripts
- **Remote Environment**: For development, testing, debugging, production, deployment, live services
- Services must be deployed to appropriate environments only

### File Naming Convention
- `docker-compose.yml` → Remote production stack
- Never run remote compose files on local machine

### Deployment Process
1. Verify target environment before deployment
2. Use appropriate compose file for environment
3. Confirm network connectivity to target before deployment
4. Document deployment decisions in memory files

### Violation Consequences
- System instability
- Environment conflicts
- Service disruptions
- Resource misallocation

---

*Policy established: February 6, 2026*
*Effective immediately*
