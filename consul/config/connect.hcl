# Consul Connect Configuration
# Enables service mesh with automatic mTLS

# Enable Connect
connect {
  enabled = true
}

# ACL Configuration (for production)
acl {
  enabled = true
  default_policy = "deny"
  down_policy = "extend-cache"
  enable_token_persistence = true
}

# Service defaults (applied to all services)
Kind = "service-defaults"
Name = "*"
Protocol = "http"

# Proxy defaults
Kind = "proxy-defaults"
Name = "global"
Config {
  protocol = "http"
  
  # Mesh gateway mode for cross-datacenter
  MeshGateway {
    Mode = "local"
  }
  
  # Local upstream defaults
  LocalUpstreamBindPort = 21000
}

# Intentions (default deny, allow specific services)
# These are applied via API after Consul starts
# Example intention configuration:
# {
#   "Kind": "service-intentions",
#   "Name": "crypto-register-api",
#   "Sources": [
#     {"Name": "kong", "Action": "allow"},
#     {"Name": "bridge-api", "Action": "allow"}
#   ]
# }

# Performance tuning
performance {
  raft_multiplier = 1
}

# Logging
log_level = "INFO"

# Telemetry (for Prometheus)
telemetry {
  prometheus_retention_time = "60s"
  disable_hostname = true
}
