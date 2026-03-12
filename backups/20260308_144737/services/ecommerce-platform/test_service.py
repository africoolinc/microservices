import requests
import json
import time

def test_ecommerce_service():
    """Test the E-Commerce Service functionality"""
    
    base_url = "http://localhost:5001"
    
    print("Testing E-Commerce Service...")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✓ Health check passed")
            print(f"  Response: {response.json()}")
        else:
            print(f"✗ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Health check error: {e}")
    
    # Test main endpoint
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✓ Main endpoint accessible")
            data = response.json()
            print(f"  Service: {data.get('service')}")
            print(f"  Status: {data.get('status')}")
        else:
            print(f"✗ Main endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Main endpoint error: {e}")
    
    # Test metrics endpoint
    try:
        response = requests.get(f"{base_url}/metrics")
        if response.status_code == 200:
            print("✓ Metrics endpoint accessible")
        else:
            print(f"✗ Metrics endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Metrics endpoint error: {e}")

if __name__ == "__main__":
    print("Waiting for service to start...")
    time.sleep(10)  # Give the service time to start
    test_ecommerce_service()