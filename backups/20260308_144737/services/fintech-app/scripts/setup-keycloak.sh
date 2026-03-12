#!/bin/bash
# Keycloak Realm Setup for FinTech Service
# This script creates the 'fintech' realm with subscription tiers

KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
ADMIN_USER="${KEYCLOAK_ADMIN:-admin}"
ADMIN_PASS="${KEYCLOAK_ADMIN_PASSWORD:-adminpass}"

echo "=== FinTech Keycloak Realm Setup ==="
echo "Keycloak URL: $KEYCLOAK_URL"

# Wait for Keycloak to be ready
echo "Waiting for Keycloak..."
until curl -sf "$KEYCLOAK_URL/health/ready" > /dev/null 2>&1; do
    sleep 2
done
echo "Keycloak is ready!"

# Get admin token
echo "Getting admin token..."
TOKEN=$(curl -s -X POST "$KEYCLOAK_URL/realms/master/protocol/openid-connect/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$ADMIN_USER" \
    -d "password=$ADMIN_PASS" \
    -d "grant_type=password" \
    -d "client_id=admin-cli" | jq -r '.access_token')

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
    echo "Failed to get admin token"
    exit 1
fi

echo "Admin token obtained"

# Create fintech realm
echo "Creating fintech realm..."
curl -s -X POST "$KEYCLOAK_URL/admin/realms" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "realm": "fintech",
        "enabled": true,
        "displayName": "FinTech Pro",
        "registrationAllowed": true,
        "loginWithEmailAllowed": true,
        "duplicateEmailsAllowed": false,
        "resetPasswordAllowed": false,
        "editUsernameAllowed": false,
        "bruteForceProtected": true
    }'

echo ""
echo "Realm 'fintech' created"

# Create fintech-app client
echo "Creating fintech-app client..."
curl -s -X POST "$KEYCLOAK_URL/admin/realms/fintech/clients" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "clientId": "fintech-app",
        "enabled": true,
        "clientAuthenticatorType": "client-secret",
        "redirectUris": ["http://localhost:5007/*", "http://localhost:5007/dashboard"],
        "webOrigins": ["http://localhost:5007"],
        "publicClient": false,
        "serviceAccountsEnabled": true,
        "authorizationServicesEnabled": false,
        "standardFlowEnabled": true,
        "implicitFlowEnabled": false,
        "directAccessGrantsEnabled": true,
        "protocol": "openid-connect",
        "attributes": {
            "access.token.lifespan": "3600",
            "refresh.token.lifespan": "86400"
        }
    }'

echo ""
echo "Client 'fintech-app' created"

# Create client secret
CLIENT_SECRET=$(curl -s -X GET "$KEYCLOAK_URL/admin/realms/fintech/clients?clientId=fintech-app" \
    -H "Authorization: Bearer $TOKEN" | jq -r '.[0].id')

if [ "$CLIENT_SECRET" != "null" ]; then
    echo "Client ID: $CLIENT_SECRET"
fi

# Create realm roles for subscription tiers
echo "Creating subscription tier roles..."
for tier in free basic pro enterprise; do
    curl -s -X POST "$KEYCLOAK_URL/admin/realms/fintech/roles" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"$tier\", \"description\": \"$tier subscription tier\"}"
    echo "Role '$tier' created"
done

echo ""
echo "=== Setup Complete ==="
echo "Realm: fintech"
echo "Client ID: fintech-app"
echo ""
echo "To get client secret, check Keycloak admin console"
echo "or run: curl -s -X GET '$KEYCLOAK_URL/admin/realms/fintech/clients?clientId=fintech-app' -H 'Authorization: Bearer $TOKEN'"
