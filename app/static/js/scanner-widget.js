let scannerWidgetOpen = false;
let scannerEnabled = true;
let scannerWidgetInitialized = false;
let scannerInitAttempts = 0;

function isUserAdmin() {
    if (typeof currentUser !== 'undefined' && currentUser) {
        return currentUser.tipo === 'admin' || currentUser.perfil_nome === 'Administrador';
    }
    return false;
}

function initScannerWidget() {
    if (scannerWidgetInitialized) return;
    
    const token = getToken();
    if (!token) return;
    
    if (typeof currentUser === 'undefined' || !currentUser) {
        scannerInitAttempts++;
        const delay = Math.min(500 * Math.pow(1.5, scannerInitAttempts - 1), 5000);
        console.log('Scanner widget: aguardando currentUser... tentativa ' + scannerInitAttempts + ' (proximo em ' + delay + 'ms)');
        setTimeout(initScannerWidget, delay);
        return;
    }
    
    if (!isUserAdmin()) {
        console.log('Scanner widget: usuario nao e admin, ocultando widget');
        return;
    }
    
    scannerWidgetInitialized = true;
    console.log('Scanner widget: inicializando para admin');
    
    checkScannerEnabled().then(enabled => {
        if (!enabled) return;
        
        const widgetHTML = `
            <div id="scannerWidgetContainer" class="scanner-widget-container">
                <div id="scannerWidgetBubble" class="scanner-widget-bubble" onclick="toggleScannerWidget()">
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
                <div id="scannerWidgetPopup" class="scanner-widget-popup">
                    <div class="scanner-widget-header">
                        <div class="scanner-widget-header-info">
                            <div class="scanner-header-icon">
                                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M3 7V5a2 2 0 0 1 2-2h2"/>
                                    <path d="M17 3h2a2 2 0 0 1 2 2v2"/>
                                    <path d="M21 17v2a2 2 0 0 1-2 2h-2"/>
                                    <path d="M7 21H5a2 2 0 0 1-2-2v-2"/>
                                    <line x1="7" y1="12" x2="17" y2="12"/>
                                </svg>
                            </div>
                            <div class="scanner-header-text">
                                <span class="scanner-widget-title">Scanner de PCB</span>
                                <span class="scanner-widget-status" id="scannerStatusText">Pronto para analisar</span>
                            </div>
                        </div>
                        <button class="scanner-close-btn" onclick="toggleScannerWidget()" title="Fechar">
                            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="18" y1="6" x2="6" y2="18"/>
                                <line x1="6" y1="6" x2="18" y2="18"/>
                            </svg>
                        </button>
                    </div>
                    <div class="scanner-widget-body" id="scannerWidgetBody">
                        <div class="scanner-upload-area" id="scannerUploadArea">
                            <input type="file" id="scannerImageInput" accept="image/*" class="scanner-file-input">
                            <div class="scanner-upload-placeholder" id="scannerPlaceholder">
                                <div class="scanner-upload-icon">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                        <rect x="3" y="3" width="18" height="18" rx="2"/>
                                        <circle cx="8.5" cy="8.5" r="1.5"/>
                                        <path d="M21 15l-5-5L5 21"/>
                                    </svg>
                                </div>
                                <p class="scanner-upload-text">Clique ou arraste uma foto</p>
                                <span class="scanner-upload-hint">JPG, PNG ou WEBP</span>
                            </div>
                            <img id="scannerPreview" class="scanner-preview">
                            <button id="scannerRemoveImage" class="scanner-remove-image" onclick="removeScannerImage(event)">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <line x1="18" y1="6" x2="6" y2="18"/>
                                    <line x1="6" y1="6" x2="18" y2="18"/>
                                </svg>
                            </button>
                        </div>
                        <button id="scannerAnalyzeBtn" class="scanner-analyze-btn" disabled onclick="analyzeWithWidget()">
                            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="11" cy="11" r="8"/>
                                <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                            </svg>
                            <span>Analisar Placa</span>
                        </button>
                    </div>
                    <div id="scannerWidgetResult" class="scanner-widget-result">
                        <div class="scanner-result-header" id="resultHeader">
                            <div class="scanner-result-grade-badge" id="widgetGradeBadge">
                                <span id="widgetGradeText">-</span>
                            </div>
                            <div class="scanner-result-title" id="widgetType">-</div>
                        </div>
                        <div class="scanner-result-stats" id="resultStats">
                            <div class="scanner-stat-item">
                                <span class="scanner-stat-label">Componentes</span>
                                <span class="scanner-stat-value" id="widgetComponents">0</span>
                            </div>
                            <div class="scanner-stat-item">
                                <span class="scanner-stat-label">Confianca</span>
                                <span class="scanner-stat-value" id="widgetConfidence">0%</span>
                            </div>
                        </div>
                        <div class="scanner-result-explanation" id="widgetExplanation">-</div>
                        <button class="scanner-new-analysis-btn" onclick="resetScannerWidget()">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
                                <path d="M3 3v5h5"/>
                            </svg>
                            <span>Nova Analise</span>
                        </button>
                    </div>
                    <div id="scannerWidgetNotDetected" class="scanner-widget-not-detected">
                        <div class="scanner-not-detected-icon">
                            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                <circle cx="12" cy="12" r="10"/>
                                <line x1="12" y1="8" x2="12" y2="12"/>
                                <line x1="12" y1="16" x2="12.01" y2="16"/>
                            </svg>
                        </div>
                        <h4 class="scanner-not-detected-title">Placa nao detectada</h4>
                        <p class="scanner-not-detected-text">Nao foi possivel identificar uma placa eletronica na imagem. Tente enviar uma foto mais clara de uma PCB.</p>
                        <button class="scanner-new-analysis-btn" onclick="resetScannerWidget()">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
                                <path d="M3 3v5h5"/>
                            </svg>
                            <span>Tentar Novamente</span>
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', widgetHTML);
        setupScannerWidgetEvents();
        injectScannerStyles();
    });
}

function injectScannerStyles() {
    if (document.getElementById('scannerWidgetStyles')) return;
    
    const styles = `
        .scanner-widget-container {
            position: fixed;
            bottom: 90px;
            right: 20px;
            z-index: 9998;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
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
        
        .scanner-widget-bubble.active {
            transform: scale(0.95);
        }
        
        .scanner-widget-popup {
            position: absolute;
            bottom: 70px;
            right: 0;
            width: 340px;
            background: #ffffff;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
            opacity: 0;
            visibility: hidden;
            transform: translateY(20px) scale(0.95);
            transition: all 0.3s ease;
            overflow: hidden;
        }
        
        .scanner-widget-popup.active {
            opacity: 1;
            visibility: visible;
            transform: translateY(0) scale(1);
        }
        
        .scanner-widget-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px;
            background: linear-gradient(135deg, #0d9488 0%, #14b8a6 100%);
            color: white;
        }
        
        .scanner-widget-header-info {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .scanner-header-icon {
            width: 40px;
            height: 40px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .scanner-header-text {
            display: flex;
            flex-direction: column;
        }
        
        .scanner-widget-title {
            font-weight: 600;
            font-size: 15px;
        }
        
        .scanner-widget-status {
            font-size: 12px;
            opacity: 0.9;
        }
        
        .scanner-close-btn {
            width: 32px;
            height: 32px;
            border: none;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.2s;
        }
        
        .scanner-close-btn:hover {
            background: rgba(255, 255, 255, 0.3);
        }
        
        .scanner-widget-body {
            padding: 16px;
        }
        
        .scanner-upload-area {
            position: relative;
            border: 2px dashed #e5e7eb;
            border-radius: 12px;
            padding: 24px;
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
            background: #fafafa;
            min-height: 140px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .scanner-upload-area:hover, .scanner-upload-area.dragover {
            border-color: #0d9488;
            background: #f0fdfa;
        }
        
        .scanner-file-input {
            position: absolute;
            width: 100%;
            height: 100%;
            opacity: 0;
            cursor: pointer;
            top: 0;
            left: 0;
        }
        
        .scanner-upload-placeholder {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
        }
        
        .scanner-upload-icon {
            color: #9ca3af;
        }
        
        .scanner-upload-text {
            font-size: 14px;
            color: #4b5563;
            margin: 0;
            font-weight: 500;
        }
        
        .scanner-upload-hint {
            font-size: 12px;
            color: #9ca3af;
        }
        
        .scanner-preview {
            max-width: 100%;
            max-height: 160px;
            border-radius: 8px;
            display: none;
            object-fit: contain;
        }
        
        .scanner-preview.visible {
            display: block;
        }
        
        .scanner-remove-image {
            position: absolute;
            top: 8px;
            right: 8px;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            background: rgba(0, 0, 0, 0.6);
            border: none;
            color: white;
            cursor: pointer;
            display: none;
            align-items: center;
            justify-content: center;
            transition: background 0.2s;
        }
        
        .scanner-remove-image.visible {
            display: flex;
        }
        
        .scanner-remove-image:hover {
            background: rgba(0, 0, 0, 0.8);
        }
        
        .scanner-analyze-btn {
            width: 100%;
            padding: 12px;
            margin-top: 12px;
            border: none;
            border-radius: 10px;
            background: linear-gradient(135deg, #0d9488 0%, #14b8a6 100%);
            color: white;
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            transition: all 0.3s ease;
        }
        
        .scanner-analyze-btn:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(13, 148, 136, 0.4);
        }
        
        .scanner-analyze-btn:disabled {
            background: #d1d5db;
            cursor: not-allowed;
        }
        
        .scanner-analyze-btn.loading {
            pointer-events: none;
        }
        
        .scanner-widget-result, .scanner-widget-not-detected {
            display: none;
            padding: 16px;
        }
        
        .scanner-widget-result.visible, .scanner-widget-not-detected.visible {
            display: block;
        }
        
        .scanner-result-header {
            text-align: center;
            margin-bottom: 16px;
        }
        
        .scanner-result-grade-badge {
            display: inline-block;
            padding: 8px 24px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 18px;
            margin-bottom: 8px;
            text-transform: uppercase;
        }
        
        .scanner-result-grade-badge.low {
            background: linear-gradient(135deg, #fecaca 0%, #fca5a5 100%);
            color: #991b1b;
        }
        
        .scanner-result-grade-badge.medium {
            background: linear-gradient(135deg, #fef08a 0%, #fde047 100%);
            color: #854d0e;
        }
        
        .scanner-result-grade-badge.high {
            background: linear-gradient(135deg, #86efac 0%, #4ade80 100%);
            color: #166534;
        }
        
        .scanner-result-title {
            font-size: 13px;
            color: #6b7280;
        }
        
        .scanner-result-stats {
            display: flex;
            gap: 12px;
            margin-bottom: 16px;
        }
        
        .scanner-stat-item {
            flex: 1;
            background: #f3f4f6;
            padding: 12px;
            border-radius: 10px;
            text-align: center;
        }
        
        .scanner-stat-label {
            display: block;
            font-size: 11px;
            color: #9ca3af;
            text-transform: uppercase;
            margin-bottom: 4px;
        }
        
        .scanner-stat-value {
            font-size: 18px;
            font-weight: 700;
            color: #111827;
        }
        
        .scanner-result-explanation {
            font-size: 13px;
            color: #4b5563;
            line-height: 1.5;
            background: #f9fafb;
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 16px;
        }
        
        .scanner-new-analysis-btn {
            width: 100%;
            padding: 10px;
            border: 2px solid #e5e7eb;
            border-radius: 10px;
            background: white;
            color: #4b5563;
            font-weight: 500;
            font-size: 14px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            transition: all 0.2s ease;
        }
        
        .scanner-new-analysis-btn:hover {
            border-color: #0d9488;
            color: #0d9488;
            background: #f0fdfa;
        }
        
        .scanner-not-detected-icon {
            color: #f59e0b;
            margin-bottom: 12px;
            text-align: center;
        }
        
        .scanner-not-detected-title {
            font-size: 16px;
            font-weight: 600;
            color: #111827;
            margin: 0 0 8px;
            text-align: center;
        }
        
        .scanner-not-detected-text {
            font-size: 13px;
            color: #6b7280;
            line-height: 1.5;
            text-align: center;
            margin: 0 0 16px;
        }
        
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        
        .scanner-analyze-btn.loading svg {
            animation: spin 1s linear infinite;
        }
    `;
    
    const styleElement = document.createElement('style');
    styleElement.id = 'scannerWidgetStyles';
    styleElement.textContent = styles;
    document.head.appendChild(styleElement);
}

async function checkScannerEnabled() {
    try {
        const response = await fetch('/api/scanner/status');
        const data = await response.json();
        scannerEnabled = data.ready;
        return data.ready;
    } catch {
        return false;
    }
}

function setupScannerWidgetEvents() {
    const uploadArea = document.getElementById('scannerUploadArea');
    const imageInput = document.getElementById('scannerImageInput');
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            imageInput.files = e.dataTransfer.files;
            handleScannerImageSelect();
        }
    });
    
    imageInput.addEventListener('change', handleScannerImageSelect);
}

function handleScannerImageSelect() {
    const imageInput = document.getElementById('scannerImageInput');
    const preview = document.getElementById('scannerPreview');
    const placeholder = document.getElementById('scannerPlaceholder');
    const analyzeBtn = document.getElementById('scannerAnalyzeBtn');
    const removeBtn = document.getElementById('scannerRemoveImage');
    
    if (imageInput.files && imageInput.files[0]) {
        const reader = new FileReader();
        reader.onload = (e) => {
            preview.src = e.target.result;
            preview.classList.add('visible');
            placeholder.style.display = 'none';
            analyzeBtn.disabled = false;
            removeBtn.classList.add('visible');
        };
        reader.readAsDataURL(imageInput.files[0]);
    }
}

function removeScannerImage(event) {
    event.stopPropagation();
    const imageInput = document.getElementById('scannerImageInput');
    const preview = document.getElementById('scannerPreview');
    const placeholder = document.getElementById('scannerPlaceholder');
    const analyzeBtn = document.getElementById('scannerAnalyzeBtn');
    const removeBtn = document.getElementById('scannerRemoveImage');
    
    imageInput.value = '';
    preview.src = '';
    preview.classList.remove('visible');
    placeholder.style.display = 'flex';
    analyzeBtn.disabled = true;
    removeBtn.classList.remove('visible');
}

function toggleScannerWidget() {
    const popup = document.getElementById('scannerWidgetPopup');
    const bubble = document.getElementById('scannerWidgetBubble');
    
    if (!popup || !bubble) return;
    
    scannerWidgetOpen = !scannerWidgetOpen;
    
    if (scannerWidgetOpen) {
        popup.classList.add('active');
        bubble.classList.add('active');
    } else {
        popup.classList.remove('active');
        bubble.classList.remove('active');
    }
}

async function analyzeWithWidget() {
    const token = getToken();
    if (!token) {
        alert('Faca login para usar o scanner.');
        return;
    }
    
    const imageInput = document.getElementById('scannerImageInput');
    const analyzeBtn = document.getElementById('scannerAnalyzeBtn');
    const statusText = document.getElementById('scannerStatusText');
    
    if (!imageInput.files || !imageInput.files[0]) return;
    
    analyzeBtn.disabled = true;
    analyzeBtn.classList.add('loading');
    analyzeBtn.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 12a9 9 0 11-6.219-8.56"/>
        </svg>
        <span>Analisando...</span>
    `;
    statusText.textContent = 'Processando imagem...';
    
    const formData = new FormData();
    formData.append('image', imageInput.files[0]);
    
    try {
        const response = await fetch('/api/scanner/analyze', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            if (data.board_detected === false) {
                displayNotDetected();
            } else {
                displayWidgetResult(data);
            }
        } else {
            alert(data.erro || 'Erro ao analisar.');
            resetAnalyzeButton();
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro de conexao.');
        resetAnalyzeButton();
    }
}

function resetAnalyzeButton() {
    const analyzeBtn = document.getElementById('scannerAnalyzeBtn');
    const statusText = document.getElementById('scannerStatusText');
    
    analyzeBtn.disabled = false;
    analyzeBtn.classList.remove('loading');
    analyzeBtn.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <span>Analisar Placa</span>
    `;
    statusText.textContent = 'Pronto para analisar';
}

function displayWidgetResult(data) {
    document.getElementById('scannerWidgetBody').style.display = 'none';
    document.getElementById('scannerWidgetNotDetected').classList.remove('visible');
    document.getElementById('scannerWidgetResult').classList.add('visible');
    document.getElementById('scannerStatusText').textContent = 'Analise concluida';
    
    const gradeBadge = document.getElementById('widgetGradeBadge');
    const gradeText = (data.grade || 'medium').toLowerCase();
    gradeBadge.className = 'scanner-result-grade-badge ' + gradeText;
    document.getElementById('widgetGradeText').textContent = data.grade || '-';
    
    document.getElementById('widgetType').textContent = data.type_guess || 'Tipo nao identificado';
    document.getElementById('widgetComponents').textContent = data.components_count || 0;
    document.getElementById('widgetConfidence').textContent = Math.round((data.confidence || 0) * 100) + '%';
    document.getElementById('widgetExplanation').textContent = data.explanation || 'Sem explicacao disponivel.';
}

function displayNotDetected() {
    document.getElementById('scannerWidgetBody').style.display = 'none';
    document.getElementById('scannerWidgetResult').classList.remove('visible');
    document.getElementById('scannerWidgetNotDetected').classList.add('visible');
    document.getElementById('scannerStatusText').textContent = 'Placa nao detectada';
}

function resetScannerWidget() {
    document.getElementById('scannerWidgetBody').style.display = 'block';
    document.getElementById('scannerWidgetResult').classList.remove('visible');
    document.getElementById('scannerWidgetNotDetected').classList.remove('visible');
    document.getElementById('scannerImageInput').value = '';
    document.getElementById('scannerPreview').classList.remove('visible');
    document.getElementById('scannerPreview').src = '';
    document.getElementById('scannerPlaceholder').style.display = 'flex';
    document.getElementById('scannerRemoveImage').classList.remove('visible');
    resetAnalyzeButton();
}

document.addEventListener('DOMContentLoaded', function() {
    setTimeout(initScannerWidget, 1000);
});
