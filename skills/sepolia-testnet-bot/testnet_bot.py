#!/usr/bin/env python3
"""
Sepolia Testnet Bot - Test deployment and rate service
"""

import argparse
import json
import sys
import time
from datetime import datetime

# Try to import web3, install if missing
try:
    from web3 import Web3
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "web3", "requests"])
    from web3 import Web3

# Configuration
SEPOLIA_RPC = "https://sepolia.infura.io/v3/YOUR_INFURA_KEY"
SEPOLIA_CHAIN_ID = 11155111
TEST_ADDRESS = "0xcA2a481E128d8A1FCE636E0D4fe10fF5987f028F"
ETHERSCAN_API = "https://api-sepolia.etherscan.io/api"

# Service endpoints to test
CRYPTO_REGISTER_FRONTEND = "http://localhost:3001"
CRYPTO_REGISTER_API = "http://localhost:3002"


def get_eth_balance(rpc_url=None):
    """Get ETH balance on Sepolia testnet"""
    if rpc_url is None:
        # Use public RPC
        rpc_url = "https://rpc.sepolia.org"
    
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            return {"error": "Failed to connect to Sepolia", "balance_eth": 0}
        
        balance_wei = w3.eth.get_balance(TEST_ADDRESS)
        balance_eth = w3.from_wei(balance_wei, 'ether')
        
        return {
            "address": TEST_ADDRESS,
            "balance_wei": str(balance_wei),
            "balance_eth": float(balance_eth),
            "network": "sepolia",
            "connected": w3.is_connected()
        }
    except Exception as e:
        return {"error": str(e), "balance_eth": 0}


def test_deployment():
    """Test the crypto-register deployment"""
    import requests
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {}
    }
    
    # Test 1: Frontend availability
    try:
        r = requests.get(CRYPTO_REGISTER_FRONTEND, timeout=10)
        results["tests"]["frontend"] = {
            "status": "pass" if r.status_code == 200 else "fail",
            "status_code": r.status_code,
            "content_type": r.headers.get("content-type", ""),
            "has_crypto_domain": "crypto" in r.text.lower()
        }
    except Exception as e:
        results["tests"]["frontend"] = {"status": "error", "error": str(e)}
    
    # Test 2: API Health
    try:
        r = requests.get(f"{CRYPTO_REGISTER_API}/health", timeout=10)
        results["tests"]["api_health"] = {
            "status": "pass" if r.status_code == 200 else "fail",
            "status_code": r.status_code,
            "response": r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
        }
    except Exception as e:
        results["tests"]["api_health"] = {"status": "error", "error": str(e)}
    
    # Test 3: Domain check endpoint
    try:
        r = requests.get(f"{CRYPTO_REGISTER_API}/api/check-domain?domain=test.crypto", timeout=10)
        results["tests"]["domain_check"] = {
            "status": "pass" if r.status_code == 200 else "fail",
            "response": r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
        }
    except Exception as e:
        results["tests"]["domain_check"] = {"status": "error", "error": str(e)}
    
    # Test 4: Registration API
    try:
        test_data = {
            "phone": "+254700000000",
            "domain": "testuser.crypto",
            "email": "test@example.com",
            "services": ["signals"]
        }
        r = requests.post(f"{CRYPTO_REGISTER_API}/api/register", json=test_data, timeout=10)
        results["tests"]["registration"] = {
            "status": "pass" if r.status_code in [200, 201] else "fail",
            "status_code": r.status_code,
            "response": r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
        }
    except Exception as e:
        results["tests"]["registration"] = {"status": "error", "error": str(e)}
    
    # Calculate score
    passed = sum(1 for t in results["tests"].values() if t.get("status") == "pass")
    total = len(results["tests"])
    results["score"] = f"{passed}/{total}"
    results["pass_rate"] = round(passed / total * 100, 1)
    
    return results


def rate_service(eth_balance=None, deployment_results=None):
    """Rate the overall service"""
    rating = {
        "timestamp": datetime.now().isoformat(),
        "score": 0,
        "max_score": 10,
        "breakdown": {}
    }
    
    # Get deployment results if not provided
    if deployment_results is None:
        deployment_results = test_deployment()
    
    # Criteria weighting
    # 1. ETH on testnet (2 points)
    if eth_balance and eth_balance.get("balance_eth", 0) > 0:
        rating["breakdown"]["testnet_funds"] = 2
    else:
        rating["breakdown"]["testnet_funds"] = 0
    
    # 2. Frontend available (2 points)
    if deployment_results["tests"].get("frontend", {}).get("status") == "pass":
        rating["breakdown"]["frontend"] = 2
    
    # 3. API health (2 points)
    if deployment_results["tests"].get("api_health", {}).get("status") == "pass":
        rating["breakdown"]["api_health"] = 2
    
    # 4. Domain check working (2 points)
    if deployment_results["tests"].get("domain_check", {}).get("status") == "pass":
        rating["breakdown"]["domain_check"] = 2
    
    # 5. Registration working (2 points)
    if deployment_results["tests"].get("registration", {}).get("status") == "pass":
        rating["breakdown"]["registration"] = 2
    
    rating["score"] = sum(rating["breakdown"].values())
    
    # Rating description
    if rating["score"] >= 9:
        rating["grade"] = "A - Excellent"
    elif rating["score"] >= 7:
        rating["grade"] = "B - Good"
    elif rating["score"] >= 5:
        rating["grade"] = "C - Average"
    elif rating["score"] >= 3:
        rating["grade"] = "D - Below Average"
    else:
        rating["grade"] = "F - Failing"
    
    return rating


def main():
    parser = argparse.ArgumentParser(description="Sepolia Testnet Bot")
    parser.add_argument("--balance", action="store_true", help="Check ETH balance")
    parser.add_argument("--test-deployment", action="store_true", help="Test deployment")
    parser.add_argument("--rate", action="store_true", help="Rate service")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--rpc", type=str, help="Custom RPC URL")
    args = parser.parse_args()
    
    # Default: run all
    if not any([args.balance, args.test_deployment, args.rate, args.all]):
        args.all = True
    
    print("=" * 60)
    print("Sepolia Testnet Bot")
    print("=" * 60)
    
    results = {}
    
    if args.balance or args.all:
        print("\n[1] Checking ETH balance on Sepolia...")
        balance = get_eth_balance(args.rpc)
        results["balance"] = balance
        
        if balance.get("error"):
            print(f"  ❌ Error: {balance['error']}")
        else:
            print(f"  ✅ Address: {balance['address']}")
            print(f"  ✅ Balance: {balance['balance_eth']} ETH")
            print(f"  ✅ Network: {balance['network']}")
    
    if args.test_deployment or args.all:
        print("\n[2] Testing deployment...")
        deployment = test_deployment()
        results["deployment"] = deployment
        
        print(f"  Score: {deployment['score']} ({deployment['pass_rate']}% passed)")
        for test_name, test_result in deployment["tests"].items():
            status_symbol = "✅" if test_result.get("status") == "pass" else "❌"
            print(f"  {status_symbol} {test_name}")
    
    if args.rate or args.all:
        print("\n[3] Rating service...")
        
        # Get balance if not already done
        if "balance" not in results:
            results["balance"] = get_eth_balance(args.rpc)
        
        # Get deployment if not already done
        if "deployment" not in results:
            results["deployment"] = test_deployment()
        
        rating = rate_service(results["balance"], results["deployment"])
        results["rating"] = rating
        
        print(f"  Score: {rating['score']}/10")
        print(f"  Grade: {rating['grade']}")
        print("\n  Breakdown:")
        for criteria, score in rating["breakdown"].items():
            print(f"    - {criteria}: {score}/2")
    
    # Save results
    output_file = "logs/sepolia_test_results.json"
    import os
    os.makedirs("logs", exist_ok=True)
    
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Results saved to: {output_file}")
    print("=" * 60)
    
    return 0 if results.get("rating", {}).get("score", 0) >= 5 else 1


if __name__ == "__main__":
    sys.exit(main())