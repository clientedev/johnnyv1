
// CONFERENCIAS.JS - Versão 2.0 - Independente
console.log('🔄 conferencias.js carregado - v2.0 -', new Date().toISOString());

const CONFERENCIA_API_URL = '/api/conferencia';
let conferencias = [];

async function carregarEstatisticas() {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${CONFERENCIA_API_URL}/estatisticas`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const stats = await response.json();
            document.getElementById('stat-pendentes').textContent = stats.pendentes || 0;
            document.getElementById('stat-divergentes').textContent = stats.divergentes || 0;
            document.getElementById('stat-aguardando').textContent = stats.aguardando_adm || 0;
            document.getElementById('stat-aprovadas').textContent = stats.aprovadas || 0;
        }
    } catch (error) {
        console.error('Erro ao carregar estatísticas:', error);
    }
}

async function carregarConferencias(status = '') {
    try {
        const token = localStorage.getItem('token');
        const url = status ? `${CONFERENCIA_API_URL}?status=${status}` : CONFERENCIA_API_URL;
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            conferencias = await response.json();
            renderizarTabela();
        }
    } catch (error) {
        console.error('Erro ao carregar conferências:', error);
        alert('Erro ao carregar conferências');
    }
}

function renderizarTabela() {
    const tbody = document.querySelector('#tabela-conferencias tbody');
    tbody.innerHTML = '';
    
    console.log('📊 Renderizando conferências:', conferencias.length);
    console.log('📋 Dados completos das conferências:', JSON.stringify(conferencias, null, 2));
    
    conferencias.forEach(conf => {
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        console.log('Conferência ID:', conf.id);
        console.log('Status:', conf.conferencia_status);
        console.log('Tipo do status:', typeof conf.conferencia_status);
        console.log('Status === "DIVERGENTE"?', conf.conferencia_status === 'DIVERGENTE');
        console.log('Status === "PENDENTE"?', conf.conferencia_status === 'PENDENTE');
        console.log('Status === "AGUARDANDO_ADM"?', conf.conferencia_status === 'AGUARDANDO_ADM');
        
        const tr = document.createElement('tr');
        
        const statusBadge = getStatusBadge(conf.conferencia_status);
        const divergenciaBadge = conf.divergencia ? 
            `<span class="badge bg-danger">
                <i class="bi bi-exclamation-triangle-fill"></i> ${conf.percentual_diferenca?.toFixed(1)}%
            </span>` : 
            '<span class="badge bg-success"><i class="bi bi-check-circle-fill"></i> OK</span>';
        
        const fornecedor = conf.ordem_servico?.fornecedor_snapshot?.nome || '-';
        
        // Gerar botão de ação baseado no status
        let botaoAcao = '';
        if (conf.conferencia_status === 'PENDENTE') {
            console.log('→ Criando botão PROCESSAR');
            botaoAcao = `<a href="/conferencia-form/${conf.id}" class="btn btn-sm btn-primary">Processar</a>`;
        } else if (conf.conferencia_status === 'DIVERGENTE') {
            console.log('→ ✅ Criando botão ENVIAR P/ ADM');
            botaoAcao = `<button class="btn btn-sm btn-warning" onclick="enviarParaAdmDireto(${conf.id})">
                            <i class="bi bi-exclamation-triangle"></i> Enviar p/ ADM
                        </button>`;
        } else if (conf.conferencia_status === 'AGUARDANDO_ADM') {
            console.log('→ Criando botão DECIDIR');
            botaoAcao = `<a href="/conferencia-decisao-adm/${conf.id}" class="btn btn-sm btn-warning">Decidir</a>`;
        } else {
            console.log('→ Criando botão VER DETALHES (status:', conf.conferencia_status, ')');
            botaoAcao = `<button class="btn btn-sm btn-secondary" onclick="verDetalhes(${conf.id})">Ver Detalhes</button>`;
        }
        
        console.log('→ Botão HTML gerado:', botaoAcao);
        
        tr.innerHTML = `
            <td>${conf.id}</td>
            <td>${conf.os_id}</td>
            <td>${conf.oc_id}</td>
            <td>${fornecedor}</td>
            <td>${conf.peso_fornecedor ? conf.peso_fornecedor.toFixed(2) + ' kg' : '-'}</td>
            <td>${conf.peso_real ? conf.peso_real.toFixed(2) + ' kg' : '-'}</td>
            <td>${divergenciaBadge}</td>
            <td>${statusBadge}</td>
            <td>
                ${botaoAcao}
            </td>
        `;
        
        tbody.appendChild(tr);
    });
}

function getStatusBadge(status) {
    const badges = {
        'PENDENTE': '<span class="badge bg-primary">Pendente</span>',
        'DIVERGENTE': '<span class="badge bg-warning text-dark">Divergente</span>',
        'AGUARDANDO_ADM': '<span class="badge bg-info">Aguardando ADM</span>',
        'APROVADA': '<span class="badge bg-success">Aprovada</span>',
        'REJEITADA': '<span class="badge bg-danger">Rejeitada</span>'
    };
    return badges[status] || status;
}

function verDetalhes(id) {
    window.location.href = `/conferencia-form/${id}`;
}

async function enviarParaAdmDireto(conferenciaId) {
    console.log('🚀 enviarParaAdmDireto chamada para conferência:', conferenciaId);
    
    if (!confirm('Confirma o envio desta divergência para análise administrativa?')) {
        return;
    }
    
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${CONFERENCIA_API_URL}/${conferenciaId}/enviar-para-adm`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const result = await response.json();
            alert('✅ Divergência enviada para análise administrativa com sucesso!');
            // Recarregar a lista
            const filtro = document.getElementById('filtro-status').value;
            await carregarConferencias(filtro);
            await carregarEstatisticas();
        } else {
            const error = await response.json();
            alert('❌ Erro: ' + (error.erro || 'Erro ao enviar para ADM'));
        }
    } catch (error) {
        console.error('Erro ao enviar para ADM:', error);
        alert('❌ Erro ao enviar para análise administrativa');
    }
}

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ Iniciando carregamento de dados');
    
    const filtroStatus = document.getElementById('filtro-status');
    if (filtroStatus) {
        filtroStatus.addEventListener('change', (e) => {
            carregarConferencias(e.target.value);
        });
    }
    
    carregarEstatisticas();
    carregarConferencias();
    
    setInterval(() => {
        carregarEstatisticas();
        const filtro = document.getElementById('filtro-status').value;
        carregarConferencias(filtro);
    }, 30000);
});
