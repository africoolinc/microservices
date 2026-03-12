// Lyrikali Mix - App JavaScript
// AI Meme Engine & Auth Controller
// Version: Firebase + Mixpanel Enabled

// ==================== CONFIGURATION ====================
const API_BASE = 'http://192.168.100.182:10500'; // Gibson Production API
const FALLBACK_BASE = 'https://africool-fd821.web.app'; // Firebase fallback

// Mixpanel Configuration - REPLACE WITH YOUR TOKEN
const MIXPANEL_TOKEN = '6f1822434e5fe7491b6acf4efe9a0b5d';

// Expose current user globally for other scripts
window.currentUser = null;
window.API_BASE = 'http://192.168.100.182:10500'; // Same origin

// Auth State
let isLoginMode = true;
let memes = [];

// Keycloak & Gibson Server Config
const KEYCLOAK_URL = 'http://192.168.100.182:8080';
const CONSUL_URL = 'http://192.168.100.182:8500';
const REALM = 'lyrikali';

// ==================== MIXPANEL TRACKING ====================
const Mixpanel = {
    token: MIXPANEL_TOKEN,
    
    init() {
        if (typeof mixpanel !== 'undefined') {
            mixpanel.init(this.token, {
                debug: false,
                track_pageview: true,
                persistence: 'localStorage'
            });
            this.track('App Loaded', { version: '3.1.0', timestamp: new Date().toISOString() });
        }
    },
    
    track(event, props = {}) {
        if (typeof mixpanel !== 'undefined') {
            mixpanel.track(event, {
                ...props,
                timestamp: new Date().toISOString(),
                url: window.location.href
            });
        }
        console.log('[Mixpanel]', event, props);
    },
    
    identify(userId, props = {}) {
        if (typeof mixpanel !== 'undefined') {
            mixpanel.identify(userId);
            mixpanel.people.set(props);
        }
    }
};

// ==================== FIREBASE AUTH ====================
const FirebaseAuth = {
    provider: null,
    
    init() {
        if (typeof firebase !== 'undefined' && firebase.auth) {
            this.provider = new firebase.auth.GoogleAuthProvider();
            this.provider.setCustomParameters({
                prompt: 'select_account'
            });
            console.log('[Firebase] Google Auth initialized');
            return true;
        }
        console.warn('[Firebase] Not available');
        return false;
    },
    
    async signInWithGoogle() {
        if (!this.provider) {
            this.init();
        }
        
        try {
            const result = await firebase.auth().signInWithPopup(this.provider);
            const user = result.user;
            
            console.log('[Firebase] Signed in:', user.email);
            
            // Send ID token to backend for verification
            const idToken = await user.getIdToken();
            
            // Try to register/login on backend
            const response = await fetch(`${API_BASE}/api/v1/auth/firebase-login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    firebase_token: idToken,
                    email: user.email,
                    name: user.displayName,
                    photo_url: user.photoURL
                })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                window.currentUser = data.user;
                localStorage.setItem('lyrikali_user', JSON.stringify(data.user));
                Mixpanel.identify(user.uid, {
                    email: user.email,
                    name: user.displayName,
                    provider: 'google'
                });
                Mixpanel.track('Signed In with Google', {
                    email: user.email,
                    user_id: user.uid
                });
            }
            
            return { success: true, user: user, backend: data };
        } catch (error) {
            console.error('[Firebase] Auth error:', error);
            Mixpanel.track('Google Sign In Error', { error: error.message });
            return { success: false, error: error.message };
        }
    },
    
    async signOut() {
        try {
            await firebase.auth().signOut();
            Mixpanel.track('Signed Out');
            return true;
        } catch (error) {
            console.error('[Firebase] Sign out error:', error);
            return false;
        }
    },
    
    onAuthChange(callback) {
        if (typeof firebase !== 'undefined' && firebase.auth) {
            firebase.auth().onAuthStateChanged(callback);
        }
    }
};
    }
};

// ==================== FIREBASE FALLBACK ====================
// Firebase fallback - activates when primary Gibson API is unavailable
const FirebaseFallback = {
    enabled: false,
    firebaseUrl: 'https://africool-fd821.web.app',
    
    async checkHealth() {
        try {
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), 3000);
            
            // Check primary API health
            const response = await fetch('/api/health', { 
                method: 'HEAD',
                signal: controller.signal 
            });
            clearTimeout(timeout);
            
            if (!response.ok) throw new Error('API not healthy');
            
            // Primary is up - no fallback needed
            this.enabled = false;
            return true;
        } catch (e) {
            console.warn('Primary API unavailable, activating Firebase fallback');
            this.enabled = true;
            Mixpanel.track('Fallback Activated', { reason: 'api_unavailable', error: e.message });
            return false;
        }
    },
    
    getBaseUrl() {
        return this.enabled ? FALLBACK_BASE : API_BASE;
    }
};

// ==================== API CLIENT ====================
async function apiCall(endpoint, options = {}) {
    const base = FirebaseFallback.getBaseUrl();
    const url = `${base}${endpoint}`;
    
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }
        
        return response;
    } catch (error) {
        // Try fallback if primary fails
        if (!FirebaseFallback.enabled) {
            await FirebaseFallback.checkHealth();
            return apiCall(endpoint, options);
        }
        throw error;
    }
}

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', () => {
    checkExistingSession();
    setupDragDrop();
    Mixpanel.init();
    
    // Check API health every 12 hours for fallback decision
    const HEALTH_CHECK_INTERVAL = 12 * 60 * 60 * 1000; // 12 hours
    setInterval(() => FirebaseFallback.checkHealth(), HEALTH_CHECK_INTERVAL);
    
    // Initial health check
    FirebaseFallback.checkHealth();
});

// ==================== AUTH ====================
function checkExistingSession() {
    const savedUser = localStorage.getItem('lyrikali_user');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        Mixpanel.identify(currentUser.id || currentUser.email, {
            username: currentUser.username,
            email: currentUser.email
        });
        showDashboard();
    }
}

function showAuth() {
    document.getElementById('heroSection')?.classList.add('hidden');
    document.getElementById('features')?.classList.add('hidden');
    document.querySelector('.footer')?.classList.add('hidden');
    document.getElementById('mainNav')?.classList.add('hidden');
    document.getElementById('authSection')?.classList.remove('hidden');
    Mixpanel.track('Auth Screen Viewed', { mode: isLoginMode ? 'login' : 'signup' });
}

function showDashboard() {
    const hero = document.getElementById('heroSection');
    const features = document.getElementById('features');
    const auth = document.getElementById('authSection');
    const nav = document.getElementById('mainNav');
    const footer = document.querySelector('.footer');
    const dashboard = document.getElementById('dashboardSection');
    
    if (hero) hero.classList.add('hidden');
    if (features) features.classList.add('hidden');
    if (auth) auth.classList.add('hidden');
    if (nav) nav.classList.add('hidden');
    if (footer) footer.classList.add('hidden');
    if (dashboard) dashboard.classList.remove('hidden');
    
    // Update user info
    if (currentUser) {
        const userName = document.getElementById('userName');
        const userEmail = document.getElementById('userEmail');
        const userAvatar = document.getElementById('userAvatar');
        
        if (userName) userName.textContent = currentUser.username || 'User';
        if (userEmail) userEmail.textContent = currentUser.email || 'user@lyrikali.ke';
        if (userAvatar) userAvatar.textContent = (currentUser.username || 'U').charAt(0).toUpperCase();
    }
    
    loadUserMemes();
    Mixpanel.track('Dashboard Viewed', { user_id: currentUser?.id });
}

function toggleAuthMode(e) {
    if (e) e.preventDefault();
    isLoginMode = !isLoginMode;
    
    const title = document.getElementById('authTitle');
    const subtitle = document.getElementById('authSubtitle');
    const usernameGroup = document.getElementById('usernameGroup');
    const confirmGroup = document.getElementById('confirmGroup');
    const authBtn = document.getElementById('authBtn');
    const toggle = document.getElementById('authToggle');
    
    if (isLoginMode) {
        if (title) title.textContent = 'Welcome Back';
        if (subtitle) subtitle.textContent = 'Sign in to continue to Lyrikali';
        if (usernameGroup) usernameGroup.style.display = 'none';
        if (confirmGroup) confirmGroup.style.display = 'none';
        if (authBtn) authBtn.textContent = 'Sign In';
        if (toggle) toggle.innerHTML = "Don't have an account? <a href='#' onclick='toggleAuthMode(event)'>Sign Up</a>";
    } else {
        if (title) title.textContent = 'Join Lyrikali';
        if (subtitle) subtitle.textContent = 'Create your account';
        if (usernameGroup) usernameGroup.style.display = 'block';
        if (confirmGroup) confirmGroup.style.display = 'block';
        if (authBtn) authBtn.textContent = 'Sign Up';
        if (toggle) toggle.innerHTML = "Already have an account? <a href='#' onclick='toggleAuthMode(event)'>Sign In</a>";
    }
    
    Mixpanel.track('Auth Mode Toggled', { mode: isLoginMode ? 'login' : 'signup' });
}

async function handleAuth(e) {
    e.preventDefault();
    
    const email = document.getElementById('email')?.value;
    const password = document.getElementById('password')?.value;
    const username = document.getElementById('username')?.value || email?.split('@')[0];
    const phone = document.getElementById('phone')?.value;
    
    const authBtn = document.getElementById('authBtn');
    if (authBtn) {
        authBtn.textContent = 'Please wait...';
        authBtn.disabled = true;
    }
    
    try {
        const endpoint = isLoginMode ? '/api/v1/auth/login' : '/api/v1/auth/register';
        
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password, phone })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentUser = data.user || { username, email, phone, id: Date.now() };
            localStorage.setItem('lyrikali_user', JSON.stringify(currentUser));
            
            // Mixpanel tracking
            Mixpanel.track(isLoginMode ? 'User Logged In' : 'User Signed Up', {
                user_id: currentUser.id,
                username: currentUser.username,
                email: currentUser.email,
                method: 'email'
            });
            Mixpanel.identify(currentUser.id, {
                username: currentUser.username,
                email: currentUser.email,
                created_at: new Date().toISOString()
            });
            
            showDashboard();
        } else {
            Mixpanel.track('Auth Error', { error: data.error, mode: isLoginMode ? 'login' : 'signup' });
            alert(data.error || 'Authentication failed');
        }
    } catch (error) {
        console.error('Auth error:', error);
        Mixpanel.track('Auth Error', { error: error.message, mode: isLoginMode ? 'login' : 'signup' });
        
        // Demo mode fallback
        currentUser = { id: 'demo_' + Date.now(), username: username || 'demo', email: email || 'demo@lyrikali.ke', phone };
        localStorage.setItem('lyrikali_user', JSON.stringify(currentUser));
        showDashboard();
    }
    
    if (authBtn) {
        authBtn.textContent = isLoginMode ? 'Sign In' : 'Sign Up';
        authBtn.disabled = false;
    }
}

function logout() {
    Mixpanel.track('User Logged Out', { user_id: currentUser?.id });
    
    localStorage.removeItem('lyrikali_user');
    localStorage.removeItem('keycloak_token');
    currentUser = null;
    
    const dashboard = document.getElementById('dashboardSection');
    const hero = document.getElementById('heroSection');
    const features = document.getElementById('features');
    const footer = document.querySelector('.footer');
    const nav = document.getElementById('mainNav');
    
    if (dashboard) dashboard.classList.add('hidden');
    if (hero) hero.classList.remove('hidden');
    if (features) features.classList.remove('hidden');
    if (footer) footer.classList.remove('hidden');
    if (nav) nav.classList.remove('hidden');
}

// ==================== MEME ENGINE ====================

let selectedFile = null;

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        selectedFile = file;
        const uploadZone = document.getElementById('uploadZone');
        if (uploadZone) {
            uploadZone.innerHTML = `
                <div class="upload-icon">✅</div>
                <div class="upload-text">${file.name}</div>
                <div class="upload-hint">${(file.size / 1024 / 1024).toFixed(2)} MB</div>
            `;
        }
        Mixpanel.track('File Selected', { 
            filename: file.name, 
            size_bytes: file.size,
            type: file.type 
        });
    }
}

function setupDragDrop() {
    const uploadZone = document.getElementById('uploadZone');
    if (!uploadZone) return;
    
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });
    
    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });
    
    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file && (file.type.startsWith('image/') || file.type.startsWith('video/'))) {
            selectedFile = file;
            uploadZone.innerHTML = `
                <div class="upload-icon">✅</div>
                <div class="upload-text">${file.name}</div>
                <div class="upload-hint">${(file.size / 1024 / 1024).toFixed(2)} MB</div>
            `;
            Mixpanel.track('File Dropped', { 
                filename: file.name, 
                size_bytes: file.size,
                type: file.type 
            });
        }
    });
}

async function generateMeme() {
    const style = document.getElementById('memeStyle')?.value || 'funny';
    const caption = document.getElementById('memeCaption')?.value || '';
    const btn = document.querySelector('.btn-upload');
    
    if (!currentUser) {
        alert('Please sign in first');
        showAuth();
        return;
    }
    
    if (btn) {
        btn.textContent = '🎨 AI is creating your meme...';
        btn.disabled = true;
    }
    
    Mixpanel.track('Meme Generation Started', {
        style: style,
        has_caption: !!caption,
        has_image: !!selectedFile,
        user_id: currentUser.id
    });
    
    try {
        // Upload file if exists
        let imageUrl = null;
        if (selectedFile) {
            imageUrl = URL.createObjectURL(selectedFile);
        }
        
        // Call meme generation API
        const response = await fetch('/api/v1/meme/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: currentUser.username,
                style,
                caption,
                image_url: imageUrl
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            memes.unshift({
                id: data.meme.id,
                caption: data.meme.caption,
                image: imageUrl,
                likes: 0,
                views: 0
            });
            renderMemes();
            Mixpanel.track('Meme Generated', {
                meme_id: data.meme.id,
                style: style,
                source: 'api'
            });
        } else {
            Mixpanel.track('Meme Generation Failed', { error: data.error });
            alert(data.error || 'Failed to generate meme');
        }
    } catch (error) {
        console.error('Meme generation error:', error);
        Mixpanel.track('Meme Generation Error', { error: error.message });
        
        // Demo: add local meme
        memes.unshift({
            id: Date.now(),
            caption: caption || generateAICaption(style),
            image: selectedFile ? URL.createObjectURL(selectedFile) : null,
            likes: 0,
            views: 0
        });
        renderMemes();
        Mixpanel.track('Meme Generated (Demo)', { style: style });
    }
    
    if (btn) {
        btn.textContent = '✨ Generate AI Meme';
        btn.disabled = false;
    }
    
    // Reset upload
    selectedFile = null;
    const fileInput = document.getElementById('fileInput');
    if (fileInput) fileInput.value = '';
    const uploadZone = document.getElementById('uploadZone');
    if (uploadZone) {
        uploadZone.innerHTML = `
            <div class="upload-icon">🚀</div>
            <div class="upload-text">Drop your images/videos here or click to browse</div>
            <div class="upload-hint">Supports: JPG, PNG, GIF, MP4, WebM (Max 50MB)</div>
        `;
    }
}

async function loadUserMemes() {
    if (!currentUser?.username) return;
    
    try {
        const response = await fetch(`/api/v1/meme/user/${currentUser.username}`);
        const data = await response.json();
        
        if (response.ok) {
            memes = data.memes || [];
            renderMemes();
        }
    } catch (error) {
        console.log('Using local memes');
    }
}

function renderMemes() {
    const grid = document.getElementById('memeGrid');
    if (!grid) return;
    
    if (memes.length === 0) {
        grid.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 3rem; color: var(--text-secondary);">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🎨</div>
                <p>No memes yet. Upload an image and generate your first AI meme!</p>
            </div>
        `;
        return;
    }
    
    grid.innerHTML = memes.map(meme => `
        <div class="meme-card">
            <div class="meme-media">
                ${meme.image || meme.caption ? 
                    (meme.image ? `<img src="${meme.image}" alt="Meme">` : `<div style="font-size: 4rem; padding: 2rem;">🎨</div>`) 
                    : `<div style="font-size: 4rem;">${getStyleEmoji(meme.style)}</div>`
                }
            </div>
            <div class="meme-info">
                <div class="meme-title">${meme.caption || 'AI Generated Meme'}</div>
                <div class="meme-stats">
                    <span>❤️ ${meme.likes || 0}</span>
                    <span>👁️ ${meme.views || 0}</span>
                </div>
            </div>
        </div>
    `).join('');
    
    // Track meme views
    Mixpanel.track('Memes Rendered', { count: memes.length });
}

function getStyleEmoji(style) {
    const emojis = { funny: '😂', trend: '🔥', music: '🎵', kenyan: '🇰🇪', ai: '🤖' };
    return emojis[style] || '🎨';
}

function generateAICaption(style) {
    const captions = {
        funny: ["When the beat drops 💃🕺", "POV: You discovered a new banger", "This hits different at 2AM"],
        trend: ["#Trending #Viral", "When algorithm notices you"],
        music: ["This beat is illegal 🥵", "Producer: *makes beat* Me: 👂"],
        kenyan: ["Nairobi nights 🇰🇪", "Bongo gang rise up!", "Meru to the world"],
        ai: ["Generated by AI ✨", "Algorithm meets creativity"]
    };
    
    const styleCaps = captions[style] || captions.funny;
    return styleCaps[Math.floor(Math.random() * styleCaps.length)];
}

// ==================== ERROR TRACKING ====================
window.addEventListener('error', (e) => {
    Mixpanel.track('JavaScript Error', {
        message: e.message,
        filename: e.filename,
        lineno: e.lineno,
        url: window.location.href
    });
});

window.addEventListener('unhandledrejection', (e) => {
    Mixpanel.track('Unhandled Promise Rejection', {
        reason: e.reason?.message || String(e.reason)
    });
});

// Make functions globally available
window.showAuth = showAuth;
window.toggleAuthMode = toggleAuthMode;
window.handleAuth = handleAuth;
window.logout = logout;
window.handleFileSelect = handleFileSelect;
window.generateMeme = generateMeme;
