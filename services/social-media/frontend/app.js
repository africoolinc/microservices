// Lyrikali Mix - App JavaScript
// AI Meme Engine & Auth Controller

const API_BASE = ''; // Same origin

// Auth State
let isLoginMode = true;
let currentUser = null;
let memes = [];

// Keycloak & Consul Config
const KEYCLOAK_URL = 'http://10.144.118.159:8080';
const CONSUL_URL = 'http://10.144.118.159:8500';
const REALM = 'lyrikali';

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkExistingSession();
    setupDragDrop();
});

function checkExistingSession() {
    const savedUser = localStorage.getItem('lyrikali_user');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        showDashboard();
    }
}

function showAuth() {
    document.getElementById('heroSection')?.classList.add('hidden');
    document.getElementById('features')?.classList.add('hidden');
    document.querySelector('.footer')?.classList.add('hidden');
    document.getElementById('mainNav')?.classList.add('hidden');
    document.getElementById('authSection')?.classList.remove('hidden');
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
            currentUser = data.user || { username, email, phone };
            localStorage.setItem('lyrikali_user', JSON.stringify(currentUser));
            showDashboard();
        } else {
            alert(data.error || 'Authentication failed');
        }
    } catch (error) {
        console.error('Auth error:', error);
        // Demo mode fallback
        currentUser = { username: username || 'demo', email: email || 'demo@lyrikali.ke', phone };
        localStorage.setItem('lyrikali_user', JSON.stringify(currentUser));
        showDashboard();
    }
    
    if (authBtn) {
        authBtn.textContent = isLoginMode ? 'Sign In' : 'Sign Up';
        authBtn.disabled = false;
    }
}

function logout() {
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
        if (file && file.type.startsWith('image/') || file.type.startsWith('video/')) {
            selectedFile = file;
            uploadZone.innerHTML = `
                <div class="upload-icon">✅</div>
                <div class="upload-text">${file.name}</div>
                <div class="upload-hint">${(file.size / 1024 / 1024).toFixed(2)} MB</div>
            `;
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
    
    try {
        // Upload file if exists
        let imageUrl = null;
        if (selectedFile) {
            // In production, upload to cloud storage and get URL
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
        } else {
            alert(data.error || 'Failed to generate meme');
        }
    } catch (error) {
        console.error('Meme generation error:', error);
        // Demo: add local meme
        memes.unshift({
            id: Date.now(),
            caption: caption || generateAICaption(style),
            image: selectedFile ? URL.createObjectURL(selectedFile) : null,
            likes: 0,
            views: 0
        });
        renderMemes();
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

// Make functions globally available
window.showAuth = showAuth;
window.toggleAuthMode = toggleAuthMode;
window.handleAuth = handleAuth;
window.logout = logout;
window.handleFileSelect = handleFileSelect;
window.generateMeme = generateMeme;
