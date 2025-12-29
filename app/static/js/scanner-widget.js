function toggleScannerWidget() {
    window.location.href = 'https://scanv1-production.up.railway.app/';
}

function initScannerWidget() {
    if (scannerWidgetInitialized) return;
    
    const token = getToken();
    if (!token) return;
    
    if (typeof currentUser === 'undefined' || !currentUser) {
        scannerInitAttempts++;
        const delay = Math.min(500 * Math.pow(1.5, scannerInitAttempts - 1), 5000);
        setTimeout(initScannerWidget, delay);
        return;
    }
    
    if (!isUserAdmin()) {
        return;
    }
    
    scannerWidgetInitialized = true;
    
    const widgetHTML = `
        <div id="scannerWidgetContainer" class="scanner-widget-container">
            <div id="scannerWidgetBubble" class="scanner-widget-bubble" onclick="toggleScannerWidget()" title="Abrir Scanner">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 7V5a2 2 0 0 1 2-2h2"/>
                    <path d="M17 3h2a2 2 0 0 1 2 2v2"/>
                    <path d="M21 17v2a2 2 0 0 1-2 2h-2"/>
                    <path d="M7 21H5a2 2 0 0 1-2-2v-2"/>
                    <line x1="7" y1="12" x2="17" y2="12"/>
                    <line x1="12" y1="7" x2="12" y2="7.01"/>
                    <line x1="12" y1="17" x2="12" y2="17.01"/>
                </svg>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', widgetHTML);
    injectScannerStyles();
}

function injectScannerStyles() {
    if (document.getElementById('scannerWidgetStyles')) return;
    
    const styles = `
        .scanner-widget-container {
            position: fixed;
            bottom: 90px;
            right: 20px;
            z-index: 9999;
        }
        
        .scanner-widget-bubble {
            width: 56px;
            height: 56px;
            border-radius: 50%;
            background: linear-gradient(135deg, #0d9488 0%, #14b8a6 100%);
            box-shadow: 0 4px 20px rgba(13, 148, 136, 0.4);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.3s ease;
            color: white;
        }
        
        .scanner-widget-bubble:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 25px rgba(13, 148, 136, 0.5);
        }
    `;
    
    const styleElement = document.createElement('style');
    styleElement.id = 'scannerWidgetStyles';
    styleElement.textContent = styles;
    document.head.appendChild(styleElement);
}

let scannerWidgetInitialized = false;
let scannerInitAttempts = 0;

function isUserAdmin() {
    if (typeof currentUser !== 'undefined' && currentUser) {
        return currentUser.tipo === 'admin' || currentUser.perfil_nome === 'Administrador';
    }
    return false;
}

document.addEventListener('DOMContentLoaded', () => {
    initScannerWidget();
});
