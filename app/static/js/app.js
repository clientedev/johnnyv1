const API_URL = '/api';
let currentUser = null;
let socket = null;

function getToken() {
    return localStorage.getItem('token');
}

function setToken(token) {
    localStorage.setItem('token', token);
}

function removeToken() {
    localStorage.removeItem('token');
}

function initMobileMenu() {
    const menuToggle = document.querySelector('.menu-toggle');
    const nav = document.querySelector('nav');
    const navOverlay = document.querySelector('.nav-overlay');
    
    if (!menuToggle) return;
    
    menuToggle.addEventListener('click', () => {
        menuToggle.classList.toggle('active');
        nav.classList.toggle('active');
        if (navOverlay) {
            navOverlay.classList.toggle('active');
        }
    });
    
    if (navOverlay) {
        navOverlay.addEventListener('click', () => {
            menuToggle.classList.remove('active');
            nav.classList.remove('active');
            navOverlay.classList.remove('active');
        });
    }
    
    const navLinks = nav.querySelectorAll('a');
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            menuToggle.classList.remove('active');
            nav.classList.remove('active');
            if (navOverlay) {
                navOverlay.classList.remove('active');
            }
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    initMobileMenu();
});

async function fetchAPI(endpoint, options = {}) {
    const token = getToken();
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
        ...options,
        headers
    });

    if (response.status === 401) {
        removeToken();
        window.location.href = '/';
        return;
    }

    return response;
}

async function login(email, senha) {
    const response = await fetchAPI('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, senha })
    });

    const data = await response.json();

    if (response.ok) {
        setToken(data.token);
        currentUser = data.usuario;
        return data.usuario;
    } else {
        throw new Error(data.erro || 'Erro ao fazer login');
    }
}

async function getCurrentUser() {
    try {
        const response = await fetchAPI('/auth/me');
        
        if (!response) {
            return null;
        }
        
        if (response.ok) {
            const data = await response.json();
            currentUser = data;
            return data;
        }
        
        return null;
    } catch (error) {
        console.error('Erro ao obter usuário atual:', error);
        return null;
    }
}

function logout() {
    removeToken();
    if (socket) {
        socket.disconnect();
    }
    window.location.href = '/';
}

function showAlert(message, type = 'error') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    
    const container = document.querySelector('.container') || document.body;
    container.insertBefore(alertDiv, container.firstChild);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('pt-BR');
}

function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

function initWebSocket() {
    if (!getToken()) return;

    socket = io({
        auth: {
            token: getToken()
        }
    });

    socket.on('connect', () => {
        console.log('WebSocket conectado');
    });

    socket.on('nova_notificacao', async () => {
        await atualizarNotificacoes();
    });
}

async function atualizarNotificacoes() {
    const response = await fetchAPI('/notificacoes/nao-lidas');
    
    if (response.ok) {
        const data = await response.json();
        const badge = document.querySelector('.notification-count');
        
        if (badge) {
            if (data.count > 0) {
                badge.textContent = data.count;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        }
    }
}

async function verificarAuth() {
    const token = getToken();
    
    if (!token) {
        if (window.location.pathname !== '/' && !window.location.pathname.includes('index.html')) {
            window.location.href = '/';
        }
        return null;
    }

    const user = await getCurrentUser();
    
    if (!user) {
        removeToken();
        window.location.href = '/';
        return null;
    }

    initWebSocket();
    return user;
}

if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/js/sw.js')
            .then(registration => {
                console.log('Service Worker registrado:', registration);
            })
            .catch(error => {
                console.log('Erro ao registrar Service Worker:', error);
            });
    });
}

let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    
    const banner = document.querySelector('.pwa-install-banner');
    if (banner) {
        banner.classList.add('show');
    }
});

function instalarPWA() {
    if (deferredPrompt) {
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then((choiceResult) => {
            if (choiceResult.outcome === 'accepted') {
                console.log('PWA instalado');
            }
            deferredPrompt = null;
            const banner = document.querySelector('.pwa-install-banner');
            if (banner) {
                banner.classList.remove('show');
            }
        });
    }
}

function fecharBannerPWA() {
    const banner = document.querySelector('.pwa-install-banner');
    if (banner) {
        banner.classList.remove('show');
    }
}
