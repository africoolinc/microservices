#!/usr/bin/env python3
"""
Crypto Stack Health Monitor
Tests all critical components every 3 hours
"""

import asyncio
import json
import os
import sys
import time
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/africool/.openclaw/workspace/projects/members/Gibson/crypto_stack/logs/health_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ServiceStatus:
    name: str
    endpoint: str
    status: str  # healthy, degraded, down
    response_time_ms: float
    last_check: str
    error: Optional[str] = None
    details: Optional[Dict] = None

class CryptoStackHealthMonitor:
    """Monitors all crypto_stack services"""
    
    def __init__(self):
        self.services = [
            # BTC Options API
            {"name": "btc-options-api", "url": "http://localhost:3000/health", "type": "http"},
            # BTC Options Frontend
            {"name": "btc-options-frontend", "url": "http://localhost:3001/", "type": "http"},
            # .crypto Resolver
            {"name": "crypto-resolver", "url": "http://localhost:8080/health", "type": "http"},
            # CF Worker Sim
            {"name": "cf-worker-sim", "url": "http://localhost:8888/health", "type": "http"},
            # Redis
            {"name": "redis", "host": "localhost", "port": 6379, "type": "redis"},
            # Docker
            {"name": "docker", "type": "docker"}
        ]
        self.results: List[ServiceStatus] = []
        self.log_file = "/home/africool/.openclaw/workspace/projects/members/Gibson/crypto_stack/logs/status.json"
        
    def check_http_service(self, service: Dict) -> ServiceStatus:
        """Check HTTP endpoint"""
        start = time.time()
        try:
            import urllib.request
            req = urllib.request.Request(service["url"])
            with urllib.request.urlopen(req, timeout=10) as response:
                elapsed = (time.time() - start) * 1000
                return ServiceStatus(
                    name=service["name"],
                    endpoint=service["url"],
                    status="healthy" if response.status < 400 else "degraded",
                    response_time_ms=round(elapsed, 2),
                    last_check=datetime.now().isoformat(),
                    details={"status_code": response.status}
                )
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            return ServiceStatus(
                name=service["name"],
                endpoint=service["url"],
                status="down",
                response_time_ms=round(elapsed, 2),
                last_check=datetime.now().isoformat(),
                error=str(e)
            )
    
    def check_redis(self, service: Dict) -> ServiceStatus:
        """Check Redis connectivity"""
        start = time.time()
        try:
            import redis
            r = redis.Redis(host=service.get("host", "localhost"), 
                          port=service.get("port", 6379), 
                          socket_timeout=5)
            r.ping()
            elapsed = (time.time() - start) * 1000
            return ServiceStatus(
                name=service["name"],
                endpoint=f"{service.get('host')}:{service.get('port')}",
                status="healthy",
                response_time_ms=round(elapsed, 2),
                last_check=datetime.now().isoformat()
            )
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            return ServiceStatus(
                name=service["name"],
                endpoint=f"{service.get('host')}:{service.get('port')}",
                status="down",
                response_time_ms=round(elapsed, 2),
                last_check=datetime.now().isoformat(),
                error=str(e)
            )
    
    def check_docker(self, service: Dict) -> ServiceStatus:
        """Check Docker daemon"""
        start = time.time()
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}"],
                capture_output=True, text=True, timeout=10
            )
            elapsed = (time.time() - start) * 1000
            containers = result.stdout.strip().split("\n")
            crypto_containers = [c for c in containers if "crypto" in c.lower() or "btc" in c.lower()]
            
            return ServiceStatus(
                name=service["name"],
                endpoint="docker.sock",
                status="healthy" if result.returncode == 0 else "degraded",
                response_time_ms=round(elapsed, 2),
                last_check=datetime.now().isoformat(),
                details={"containers": crypto_containers, "total": len(crypto_containers)}
            )
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            return ServiceStatus(
                name=service["name"],
                endpoint="docker.sock",
                status="down",
                response_time_ms=round(elapsed, 2),
                last_check=datetime.now().isoformat(),
                error=str(e)
            )
    
    def run_health_checks(self) -> Dict:
        """Run all health checks"""
        logger.info("🔍 Starting health check...")
        results = []
        
        for service in self.services:
            if service["type"] == "http":
                status = self.check_http_service(service)
            elif service["type"] == "redis":
                status = self.check_redis(service)
            elif service["type"] == "docker":
                status = self.check_docker(service)
            else:
                continue
                
            results.append(status)
            emoji = "✅" if status.status == "healthy" else "⚠️" if status.status == "degraded" else "❌"
            logger.info(f"{emoji} {status.name}: {status.status} ({status.response_time_ms}ms)")
        
        self.results = results
        return self.generate_report()
    
    def generate_report(self) -> Dict:
        """Generate health report"""
        healthy = sum(1 for r in self.results if r.status == "healthy")
        degraded = sum(1 for r in self.results if r.status == "degraded")
        down = sum(1 for r in self.results if r.status == "down")
        total = len(self.results)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": total,
                "healthy": healthy,
                "degraded": degraded,
                "down": down,
                "health_score": round((healthy / total) * 100, 1) if total > 0 else 0
            },
            "services": [asdict(r) for r in self.results]
        }
        
        # Save to file
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        with open(self.log_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 Health Score: {report['summary']['health_score']}% ({healthy}/{total})")
        return report
    
    def test_btc_options_api(self) -> Dict:
        """Specific test for BTC Options API endpoints"""
        logger.info("🧪 Testing BTC Options API endpoints...")
        
        tests = {
            "price": ("GET", "/api/price"),
            "predictions": ("GET", "/api/predictions"),
            "options_chain": ("GET", "/api/options/chain"),
            "portfolio": ("GET", "/api/portfolio"),
            "signals": ("GET", "/api/signals"),
            "trade_execute": ("POST", "/api/trade/execute")
        }
        
        results = {}
        base_url = "http://localhost:3000"
        
        for test_name, (method, path) in tests.items():
            try:
                import urllib.request
                url = f"{base_url}{path}"
                
                if method == "GET":
                    req = urllib.request.Request(url)
                else:
                    req = urllib.request.Request(url, data=b'{}'.encode(), 
                                               headers={'Content-Type': 'application/json'})
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode())
                    results[test_name] = {"status": "pass", "data": data}
                    logger.info(f"  ✅ {test_name}: PASS")
                    
            except Exception as e:
                results[test_name] = {"status": "fail", "error": str(e)}
                logger.error(f"  ❌ {test_name}: FAIL - {e}")
        
        return results


def run_dry_run():
    """Execute dry run of all tests"""
    print("=" * 60)
    print("🚀 CRYPTO STACK DRY RUN TEST")
    print("=" * 60)
    
    monitor = CryptoStackHealthMonitor()
    
    # Run health checks
    report = monitor.run_health_checks()
    
    # Test BTC Options API
    print("\n" + "=" * 60)
    print("🧪 BTC OPTIONS API ENDPOINT TESTS")
    print("=" * 60)
    btc_results = monitor.test_btc_options_api()
    
    # Print results
    print("\n" + "=" * 60)
    print("📋 FINAL REPORT")
    print("=" * 60)
    print(f"\nHealth Score: {report['summary']['health_score']}%")
    print(f"Services: {report['summary']['healthy']} healthy, {report['summary']['degraded']} degraded, {report['summary']['down']} down\n")
    
    print("Service Details:")
    for s in report['services']:
        status_icon = "✅" if s['status'] == 'healthy' else "⚠️" if s['status'] == 'degraded' else "❌"
        print(f"  {status_icon} {s['name']}: {s['status']} ({s['response_time_ms']}ms)")
    
    # Calculate rating
    score = report['summary']['health_score']
    if score >= 90:
        rating = "A - Excellent"
    elif score >= 75:
        rating = "B - Good"
    elif score >= 50:
        rating = "C - Fair"
    else:
        rating = "D - Needs Attention"
    
    print(f"\n🏆 SERVICE RATING: {rating}")
    print("=" * 60)
    
    return report, btc_results


if __name__ == "__main__":
    run_dry_run()
