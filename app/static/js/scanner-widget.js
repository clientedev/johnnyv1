let scannerWidgetOpen = false;
let scannerEnabled = true;

function initScannerWidget() {
    const token = getToken();
    if (!token) return;
    
    checkScannerEnabled().then(enabled => {
        if (!enabled) return;
        
        const widgetHTML = `
            <div id="scannerWidgetContainer" class="scanner-widget-container">
                <div id="scannerWidgetBubble" class="scanner-widget-bubble" onclick="toggleScannerWidget()">
                    <i class="fas fa-microchip"></i>
                </div>
                <div id="scannerWidgetPopup" class="scanner-widget-popup">
                    <div class="scanner-widget-header">
                        <div class="scanner-widget-header-info">
                            <i class="fas fa-microchip"></i>
                            <div>
                                <span class="scanner-widget-title">Scanner PCB</span>
                                <span class="scanner-widget-status">Pronto</span>
                            </div>
                        </div>
                        <div class="scanner-widget-header-actions">
                            <a href="/scanner" title="Página completa"><i class="fas fa-external-link-alt"></i></a>
                            <button onclick="toggleScannerWidget()" title="Fechar"><i class="fas fa-times"></i></button>
                        </div>
                    </div>
                    <div class="scanner-widget-body">
                        <div class="scanner-upload-area" id="scannerUploadArea">
                            <input type="file" id="scannerImageInput" accept="image/*" class="d-none">
                            <div class="scanner-upload-placeholder" id="scannerPlaceholder">
                                <i class="fas fa-camera fa-2x text-muted mb-2"></i>
                                <p class="mb-0 small">Clique ou arraste uma foto da placa</p>
                            </div>
                            <img id="scannerPreview" class="scanner-preview d-none">
                        </div>
                        <div class="scanner-weight-input mt-2">
                            <input type="number" id="scannerWeight" class="form-control form-control-sm" 
                                   placeholder="Peso (kg) - opcional" step="0.01" min="0">
                        </div>
                        <button id="scannerAnalyzeBtn" class="btn btn-primary btn-sm w-100 mt-2" disabled onclick="analyzeWithWidget()">
                            <i class="fas fa-search me-1"></i> Analisar
                        </button>
                    </div>
                    <div id="scannerWidgetResult" class="scanner-widget-result d-none">
                        <div class="scanner-result-grade" id="widgetGradeBadge">
                            <span id="widgetGradeText">-</span>
                        </div>
                        <div class="scanner-result-info">
                            <p class="mb-1"><strong id="widgetType">-</strong></p>
                            <p class="mb-0 small text-muted" id="widgetExplanation">-</p>
                        </div>
                        <div id="widgetPriceInfo" class="scanner-price-info d-none">
                            <span class="badge bg-success" id="widgetPrice">R$ 0,00</span>
                        </div>
                        <button class="btn btn-outline-secondary btn-sm w-100 mt-2" onclick="resetScannerWidget()">
                            <i class="fas fa-redo me-1"></i> Nova Análise
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', widgetHTML);
        setupScannerWidgetEvents();
    });
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
    
    uploadArea.addEventListener('click', () => imageInput.click());
    
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
    
    if (imageInput.files && imageInput.files[0]) {
        const reader = new FileReader();
        reader.onload = (e) => {
            preview.src = e.target.result;
            preview.classList.remove('d-none');
            placeholder.classList.add('d-none');
            analyzeBtn.disabled = false;
        };
        reader.readAsDataURL(imageInput.files[0]);
    }
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
        alert('Faça login para usar o scanner.');
        return;
    }
    
    const imageInput = document.getElementById('scannerImageInput');
    const weightInput = document.getElementById('scannerWeight');
    const analyzeBtn = document.getElementById('scannerAnalyzeBtn');
    
    if (!imageInput.files || !imageInput.files[0]) return;
    
    analyzeBtn.disabled = true;
    analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Analisando...';
    
    const formData = new FormData();
    formData.append('image', imageInput.files[0]);
    if (weightInput.value) {
        formData.append('weight_kg', weightInput.value);
    }
    
    try {
        const response = await fetch('/api/scanner/analyze', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayWidgetResult(data);
        } else {
            alert(data.erro || 'Erro ao analisar.');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro de conexão.');
    } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = '<i class="fas fa-search me-1"></i> Analisar';
    }
}

function displayWidgetResult(data) {
    document.querySelector('.scanner-widget-body').classList.add('d-none');
    document.getElementById('scannerWidgetResult').classList.remove('d-none');
    
    const gradeBadge = document.getElementById('widgetGradeBadge');
    gradeBadge.className = 'scanner-result-grade ' + (data.grade || 'medium').toLowerCase();
    document.getElementById('widgetGradeText').textContent = data.grade || '-';
    
    document.getElementById('widgetType').textContent = data.type_guess || 'Não identificado';
    document.getElementById('widgetExplanation').textContent = data.explanation || '';
    
    if (data.price_suggestion) {
        document.getElementById('widgetPriceInfo').classList.remove('d-none');
        document.getElementById('widgetPrice').textContent = 'R$ ' + (data.price_suggestion.total_avg || 0).toFixed(2);
    }
}

function resetScannerWidget() {
    document.querySelector('.scanner-widget-body').classList.remove('d-none');
    document.getElementById('scannerWidgetResult').classList.add('d-none');
    document.getElementById('scannerImageInput').value = '';
    document.getElementById('scannerPreview').classList.add('d-none');
    document.getElementById('scannerPlaceholder').classList.remove('d-none');
    document.getElementById('scannerAnalyzeBtn').disabled = true;
    document.getElementById('scannerWeight').value = '';
    document.getElementById('widgetPriceInfo').classList.add('d-none');
}

document.addEventListener('DOMContentLoaded', function() {
    setTimeout(initScannerWidget, 1000);
});
