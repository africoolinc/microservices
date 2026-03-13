const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const url = require('url');
const https = require('https');

// Try to import keycloak-client, install if needed
let keycloak;
try {
    keycloak = require('./keycloak');
} catch(e) {
    console.log('Keycloak library not found, using mock');
    keycloak = null;
}

const PORT = process.env.PORT || 10112;
const DATA_FILE = process.env.DB_PATH || '/data/registrations.json';
const KEYCLOAK_URL = process.env.KEYCLOAK_URL || 'http://localhost:8080';
const REALM = process.env.KEYCLOAK_REALM || 'crypto-register';

// Ensure data directory exists
const dataDir = path.dirname(DATA_FILE);
if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
}

// Load or initialize data
function loadData() {
    try {
        if (fs.existsSync(DATA_FILE)) {
            return JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
        }
    } catch (e) {
        console.error('Error loading data:', e);
    }
    return { registrations: [], users: {} };
}

function saveData(data) {
    try {
        fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2));
        return true;
    } catch (e) {
        console.error('Error saving data:', e);
        return false;
    }
}

// Generate UUID
function uuidv4() {
    return crypto.randomUUID ? crypto.randomUUID() : crypto.randomBytes(16).toString('hex');
}

// Hash phone for privacy
function hashPhone(phone) {
    return crypto.createHash('sha256').update(phone).digest('hex').slice(0, 12);
}

// Subscription tiers
const TIERS = {
    free: { maxApiCalls: 100, price: 0 },
    bronze: { maxApiCalls: 1000, price: 9.99 },
    silver: { maxApiCalls: 5000, price: 24.99 },
    gold: { maxApiCalls: 20000, price: 49.99 },
    platinum: { maxApiCalls: -1, price: 99.99 }
};

// Keycloak admin token
let adminToken = null;
let adminTokenExpiry = 0;

async function getAdminToken() {
    if (adminToken && Date.now() < adminTokenExpiry - 60000) {
        return adminToken;
    }
    
    const data = new URLSearchParams({
        grant_type: 'password',
        client_id: 'admin-cli',
        username: 'admin',
        password: 'adminpass'
    });
    
    try {
        const response = await fetch(`${KEYCLOAK_URL}/realms/master/protocol/openid-connect/token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: data
        });
        
        const tokenData = await response.json();
        adminToken = tokenData.access_token;
        adminTokenExpiry = Date.now() + (tokenData.expires_in * 1000);
        return adminToken;
    } catch (e) {
        console.error('Failed to get admin token:', e.message);
        return null;
    }
}

// Keycloak user creation
async function createKeycloakUser(username, email, password, tier) {
    const token = await getAdminToken();
    if (!token) return null;
    
    const userData = {
        username,
        enabled: true,
        emailVerified: true,
        email,
        credentials: [{
            type: 'password',
            value: password,
            temporary: false
        }],
        attributes: {
            tier: [tier],
            phone_verified: [false]
        }
    };
    
    try {
        const response = await fetch(`${KEYCLOAK_URL}/admin/realms/${REALM}/users`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(userData)
        });
        
        if (response.status === 201) {
            return { success: true };
        } else {
            const error = await response.text();
            console.error('Keycloak create user error:', error);
            return null;
        }
    } catch (e) {
        console.error('Keycloak API error:', e.message);
        return null;
    }
}

// User authentication
async function authenticateUser(username, password) {
    const clientSecret = 'XqAM1ch2uaE6D4ZENTzOTo8ddJGvFK2t'; // Set from Keycloak
    
    const data = new URLSearchParams({
        grant_type: 'password',
        client_id: 'crypto-register-app',
        client_secret: clientSecret,
        username,
        password
    });
    
    try {
        const response = await fetch(`${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: data
        });
        
        if (response.ok) {
            return await response.json();
        }
        return null;
    } catch (e) {
        console.error('Auth error:', e.message);
        return null;
    }
}

// Get user info from Keycloak
async function getUserInfo(token) {
    try {
        const response = await fetch(`${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/userinfo`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            return await response.json();
        }
        return null;
    } catch (e) {
        return null;
    }
}

// HTTP Server
const server = http.createServer(async (req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    
    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
    }
    
    const urlParts = req.url.split('?');
    const urlPath = urlParts[0];
    const queryParams = new URLSearchParams(urlParts[1] || '');
    
    const authHeader = req.headers.authorization;
    let userToken = null;
    let userInfo = null;
    
    if (authHeader && authHeader.startsWith('Bearer ')) {
        userToken = authHeader.slice(7);
        userInfo = await getUserInfo(userToken);
    }
    
    // Health check
    if (urlPath === '/health') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ 
            status: 'healthy', 
            timestamp: new Date().toISOString(),
            keycloak: KEYCLOAK_URL
        }));
        return;
    }
    
    // === AUTH API ===
    
    // Register
    if (urlPath === '/api/auth/register' && req.method === 'POST') {
        let body = '';
        req.on('data', chunk => body += chunk);
        req.on('end', async () => {
            try {
                const data = JSON.parse(body);
                const { phone, domain, email, password, tier = 'free' } = data;
                
                if (!phone || !domain || !password) {
                    res.writeHead(400, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ error: 'Phone, domain, and password required' }));
                    return;
                }
                
                if (!domain.endsWith('.crypto')) {
                    res.writeHead(400, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ error: 'Domain must end with .crypto' }));
                    return;
                }
                
                const db = loadData();
                
                // Check domain availability
                if (db.registrations.some(r => r.domain === domain)) {
                    res.writeHead(409, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ error: 'Domain already taken' }));
                    return;
                }
                
                // Check phone
                const phoneHash = hashPhone(phone);
                if (db.registrations.some(r => r.phoneHash === phoneHash)) {
                    res.writeHead(409, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ error: 'Phone already registered' }));
                    return;
                }
                
                // Create Keycloak user
                const username = domain.replace('.crypto', '');
                const kcUser = await createKeycloakUser(username, email || `${username}@gibson.trade`, password, tier);
                
                let keycloakId = null;
                if (kcUser && kcUser.success) {
                    // Get user ID from Keycloak
                    const token = await getAdminToken();
                    if (token) {
                        const usersResp = await fetch(`${KEYCLOAK_URL}/admin/realms/${REALM}/users?username=${username}`, {
                            headers: { 'Authorization': `Bearer ${token}` }
                        });
                        const users = await usersResp.json();
                        if (users.length > 0) {
                            keycloakId = users[0].id;
                        }
                    }
                }
                
                // Create local registration
                const registration = {
                    id: uuidv4(),
                    keycloakId,
                    phoneHash,
                    domain,
                    email: email || `${username}@gibson.trade`,
                    tier,
                    services: ['signals'],
                    apiCalls: 0,
                    maxApiCalls: TIERS[tier]?.maxApiCalls || 100,
                    createdAt: new Date().toISOString(),
                    status: 'active'
                };
                
                db.registrations.push(registration);
                
                if (saveData(db)) {
                    // Get token
                    const auth = await authenticateUser(username, password);
                    
                    res.writeHead(201, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({
                        success: true,
                        registration: {
                            id: registration.id,
                            domain: registration.domain,
                            tier: registration.tier
                        },
                        token: auth?.access_token,
                        expires_in: auth?.expires_in
                    }));
                } else {
                    res.writeHead(500, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ error: 'Failed to save registration' }));
                }
            } catch (e) {
                console.error('Registration error:', e);
                res.writeHead(400, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: 'Invalid request' }));
            }
        });
        return;
    }
    
    // Login
    if (urlPath === '/api/auth/login' && req.method === 'POST') {
        let body = '';
        req.on('data', chunk => body += chunk);
        req.on('end', async () => {
            try {
                const data = JSON.parse(body);
                const { username, password } = data;
                
                if (!username || !password) {
                    res.writeHead(400, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ error: 'Username and password required' }));
                    return;
                }
                
                const auth = await authenticateUser(username, password);
                
                if (auth) {
                    // Get user tier from local DB
                    const db = loadData();
                    const reg = db.registrations.find(r => r.domain === `${username}.crypto`);
                    
                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({
                        success: true,
                        token: auth.access_token,
                        expires_in: auth.expires_in,
                        refresh_token: auth.refresh_token,
                        user: {
                            username,
                            domain: reg?.domain,
                            tier: reg?.tier || 'free',
                            apiCalls: reg?.apiCalls || 0,
                            maxApiCalls: reg?.maxApiCalls || 100
                        }
                    }));
                } else {
                    res.writeHead(401, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ error: 'Invalid credentials' }));
                }
            } catch (e) {
                res.writeHead(400, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: 'Invalid request' }));
            }
        });
        return;
    }
    
    // Auth status
    if (urlPath === '/api/auth/status' && req.method === 'GET') {
        if (userInfo) {
            res.writeHead(200, { 'Content-Type': 'application/json' });
            
            const db = loadData();
            const reg = db.registrations.find(r => r.domain === `${userInfo.preferred_username}.crypto`);
            
            res.end(JSON.stringify({
                authenticated: true,
                username: userInfo.preferred_username,
                email: userInfo.email,
                tier: reg?.tier || 'free',
                domain: reg?.domain
            }));
        } else {
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ authenticated: false }));
        }
        return;
    }
    
    // Get user profile (protected)
    if (urlPath === '/api/user/profile' && req.method === 'GET' && userInfo) {
        const db = loadData();
        const reg = db.registrations.find(r => r.keycloakId === userInfo.sub || r.domain === `${userInfo.preferred_username}.crypto`);
        
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            domain: reg?.domain,
            email: userInfo.email,
            tier: reg?.tier || 'free',
            apiCalls: reg?.apiCalls || 0,
            maxApiCalls: reg?.maxApiCalls || 100,
            services: reg?.services || ['signals'],
            createdAt: reg?.createdAt
        }));
        return;
    }
    
    // Subscription tiers
    if (urlPath === '/api/tiers' && req.method === 'GET') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(TIERS));
        return;
    }
    
    // === PUBLIC API ===
    
    // Check domain
    if (urlPath === '/api/check-domain' && req.method === 'GET') {
        const domain = queryParams.get('domain');
        
        if (!domain) {
            res.writeHead(400, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: 'Domain required' }));
            return;
        }
        
        const db = loadData();
        const exists = db.registrations.some(r => r.domain === domain);
        
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ available: !exists, domain }));
        return;
    }
    
    // System status
    if (urlPath === '/api/status' && req.method === 'GET') {
        const db = loadData();
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            status: 'operational',
            totalUsers: db.registrations.length,
            keycloak: KEYCLOAK_URL,
            realm: REALM,
            timestamp: new Date().toISOString()
        }));
        return;
    }
    
    // 404
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Not found' }));
});

server.listen(PORT, () => {
    console.log(`Crypto Register API running on port ${PORT}`);
    console.log(`Keycloak: ${KEYCLOAK_URL}/realms/${REALM}`);
    console.log(`Data file: ${DATA_FILE}`);
});