#!/usr/bin/env python3
"""
Configure Keycloak for Crypto Register Service
Creates realms, clients, and subscription tiers
"""

import json
import requests
import time
import sys

# Configuration
KEYCLOAK_URL = "http://localhost:8080"
ADMIN_USER = "admin"
ADMIN_PASSWORD = "adminpass"
REALM = "crypto-register"

# Subscription tiers configuration
TIERS = {
    "free": {
        "name": "Free",
        "description": "Basic trading signals",
        "price": 0,
        "attributes": {
            "max_api_calls": 100,
            "signals": True,
            "api_access": False,
            "priority_support": False
        }
    },
    "bronze": {
        "name": "Bronze", 
        "description": "Basic API access",
        "price": 9.99,
        "attributes": {
            "max_api_calls": 1000,
            "signals": True,
            "api_access": True,
            "priority_support": False
        }
    },
    "silver": {
        "name": "Silver",
        "description": "Full API + Signals",
        "price": 24.99,
        "attributes": {
            "max_api_calls": 5000,
            "signals": True,
            "api_access": True,
            "priority_support": False
        }
    },
    "gold": {
        "name": "Gold",
        "description": "Priority support + more calls",
        "price": 49.99,
        "attributes": {
            "max_api_calls": 20000,
            "signals": True,
            "api_access": True,
            "priority_support": True
        }
    },
    "platinum": {
        "name": "Platinum",
        "description": "Unlimited everything",
        "price": 99.99,
        "attributes": {
            "max_api_calls": -1,  # Unlimited
            "signals": True,
            "api_access": True,
            "priority_support": True,
            "managed_account": True
        }
    }
}

def get_token():
    """Get admin access token"""
    data = {
        "grant_type": "password",
        "client_id": "admin-cli",
        "username": ADMIN_USER,
        "password": ADMIN_PASSWORD
    }
    r = requests.post(f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token", data=data)
    if r.status_code != 200:
        print(f"Failed to get token: {r.text}")
        return None
    return r.json()["access_token"]

def create_realm(token):
    """Create crypto-register realm"""
    realm_data = {
        "realm": REALM,
        "enabled": True,
        "displayName": "Crypto Register",
        "registrationAllowed": True,
        "loginWithEmailAllowed": True,
        "duplicateEmailsAllowed": False,
        "resetPasswordAllowed": False,
        "editUsernameAllowed": False,
        "branding": {
            "displayName": "Gibson Crypto",
            "footerLegal": "© 2026 Gibson Crypto. All rights reserved.",
            "link": "https://gibson.trade"
        }
    }
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Check if realm exists
    r = requests.get(f"{KEYCLOAK_URL}/admin/realms/{REALM}", headers=headers)
    if r.status_code == 200:
        print(f"Realm {REALM} already exists")
        return True
    
    r = requests.post(f"{KEYCLOAK_URL}/admin/realms", headers=headers, json=realm_data)
    if r.status_code in [200, 201]:
        print(f"✅ Created realm: {REALM}")
        return True
    else:
        print(f"❌ Failed to create realm: {r.text}")
        return False

def create_client(token):
    """Create client for crypto-register app"""
    client_data = {
        "clientId": "crypto-register-app",
        "enabled": True,
        "publicClient": False,
        "bearerOnly": False,
        "standardFlowEnabled": True,
        "implicitFlowEnabled": False,
        "directAccessGrantsEnabled": True,
        "serviceAccountsEnabled": True,
        "redirectUris": [
            "http://localhost:10110/*",
            "http://localhost:3001/*",
            "http://localhost:3002/*"
        ],
        "webOrigins": ["*"],
        "attributes": {
            "access.token.lifespan": 3600,
            "refresh.token.lifespan": 86400
        }
    }
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Check if client exists
    r = requests.get(f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients?clientId=crypto-register-app", headers=headers)
    if r.status_code == 200 and r.json():
        print(f"Client crypto-register-app already exists")
        return True
    
    r = requests.post(f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients", headers=headers, json=client_data)
    if r.status_code in [200, 201]:
        client_id = r.json().get("id")
        # Get client secret
        r = requests.get(f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients/{client_id}/client-secret", headers=headers)
        secret = r.json().get("value") if r.status_code == 200 else "temp-secret"
        print(f"✅ Created client: crypto-register-app")
        print(f"   Client Secret: {secret}")
        return True
    else:
        print(f"❌ Failed to create client: {r.text}")
        return False

def create_user(token, username, password, tier="free"):
    """Create a user with tier"""
    user_data = {
        "username": username,
        "enabled": True,
        "emailVerified": True,
        "email": f"{username}@gibson.trade",
        "credentials": [
            {
                "type": "password",
                "value": password,
                "temporary": False
            }
        ],
        "attributes": {
            "tier": [tier],
            "subscription_tier": [tier],
            "max_api_calls": [TIERS[tier]["attributes"]["max_api_calls"]],
            "signals": [str(TIERS[tier]["attributes"]["signals"]).lower()],
            "api_access": [str(TIERS[tier]["attributes"]["api_access"]).lower()]
        }
    }
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    r = requests.post(f"{KEYCLOAK_URL}/admin/realms/{REALM}/users", headers=headers, json=user_data)
    if r.status_code in [200, 201]:
        print(f"✅ Created user: {username} (tier: {tier})")
        return True
    else:
        print(f"❌ Failed to create user: {r.text}")
        return False

def get_client_secrets(token):
    """Get client secret"""
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients", headers=headers)
    clients = r.json()
    for client in clients:
        if client.get("clientId") == "crypto-register-app":
            r = requests.get(f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients/{client['id']}/client-secret", headers=headers)
            if r.status_code == 200:
                return r.json().get("value")
    return None

def main():
    print("=" * 60)
    print("Keycloak Configuration for Crypto Register")
    print("=" * 60)
    
    # Get admin token
    print("\n[1] Getting admin token...")
    token = get_token()
    if not token:
        print("❌ Failed to authenticate")
        return 1
    print("✅ Authenticated")
    
    # Create realm
    print("\n[2] Creating realm...")
    if not create_realm(token):
        return 1
    
    # Create client
    print("\n[3] Creating client...")
    if not create_client(token):
        return 1
    
    # Create test users for each tier
    print("\n[4] Creating test users...")
    for tier in TIERS:
        create_user(token, f"user-{tier}", "password123", tier)
    
    # Get client secret
    print("\n[5] Getting client configuration...")
    client_secret = get_client_secrets(token)
    print(f"   Client ID: crypto-register-app")
    print(f"   Client Secret: {client_secret}")
    print(f"   Realm: {REALM}")
    print(f"   Auth URL: {KEYCLOAK_URL}/realms/{REALM}")
    
    # Save configuration
    config = {
        "keycloak_url": KEYCLOAK_URL,
        "realm": REALM,
        "client_id": "crypto-register-app",
        "client_secret": client_secret,
        "tiers": TIERS
    }
    
    with open("services/crypto-register/keycloak-config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✅ Configuration saved to: services/crypto-register/keycloak-config.json")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())