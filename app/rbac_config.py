PERFIL_CONFIG = {
    'Administrador': {
        'tela_inicial': '/dashboard.html',
        'rotas_api_permitidas': [
            '/api/usuarios',
            '/api/perfis',
            '/api/fornecedores',
            '/api/veiculos',
            '/api/motoristas',
            '/api/solicitacoes',
            '/api/lotes',
            '/api/entradas',
            '/api/auditoria',
            '/api/relatorios',
            '/api/tipos-lote',
            '/api/precos'
        ],
        'paginas_permitidas': [
            '/dashboard.html',
            '/usuarios.html',
            '/perfis.html',
            '/fornecedores.html',
            '/fornecedores-lista.html',
            '/produtos.html',
            '/tipos-lote.html',
            '/solicitacoes.html',
            '/aprovar_solicitacoes.html',
            '/lotes.html',
            '/lotes_aprovados.html',
            '/estoque.html',
            '/entradas.html',
            '/veiculos.html',
            '/motoristas.html',
            '/financeiro.html',
            '/auditoria.html',
            '/administracao.html',
            '/configuracoes.html',
            '/notificacoes.html',
            '/funcionarios.html'
        ],
        'menus': [
            {'id': 'usuarios', 'nome': 'Administração', 'url': '/administracao.html', 'icone': 'settings'},
            {'id': 'dashboard', 'nome': 'Dashboard', 'url': '/dashboard.html', 'icone': 'dashboard'},
            {'id': 'solicitacoes', 'nome': 'Solicitações', 'url': '/solicitacoes.html', 'icone': 'request_quote'},
            {'id': 'fornecedores', 'nome': 'Fornecedores', 'url': '/fornecedores.html', 'icone': 'business'}
        ]
    },
    'Comprador (PJ)': {
        'tela_inicial': '/solicitacoes.html',
        'rotas_api_permitidas': [
            '/api/solicitacoes',
            '/api/fornecedores',
            '/api/notificacoes'
        ],
        'paginas_permitidas': [
            '/solicitacoes.html',
            '/fornecedores.html',
            '/fornecedores-lista.html',
            '/notificacoes.html',
            '/compras.html'
        ],
        'menus': [
            {'id': 'solicitacoes', 'nome': 'Solicitações', 'url': '/solicitacoes.html', 'icone': 'request_quote'},
            {'id': 'fornecedores', 'nome': 'Fornecedores', 'url': '/fornecedores.html', 'icone': 'business'}
        ]
    },
    'Conferente / Estoque': {
        'tela_inicial': '/entradas.html',
        'rotas_api_permitidas': [
            '/api/lotes',
            '/api/entradas',
            '/api/solicitacoes'
        ],
        'paginas_permitidas': [
            '/dashboard.html',
            '/lotes.html',
            '/lotes_aprovados.html',
            '/entradas.html',
            '/validacao.html',
            '/notificacoes.html'
        ],
        'menus': [
            {'id': 'entradas', 'nome': 'Entrada Estoque', 'url': '/entradas.html', 'icone': 'input'},
            {'id': 'validacao', 'nome': 'Validação', 'url': '/validacao.html', 'icone': 'fact_check'},
            {'id': 'lotes', 'nome': 'Lotes', 'url': '/lotes.html', 'icone': 'inventory_2'},
            {'id': 'dashboard', 'nome': 'Dashboard', 'url': '/dashboard.html', 'icone': 'dashboard'}
        ]
    },
    'Separação': {
        'tela_inicial': '/lotes.html',
        'rotas_api_permitidas': [
            '/api/lotes',
            '/api/entradas'
        ],
        'paginas_permitidas': [
            '/dashboard.html',
            '/lotes.html',
            '/lotes_aprovados.html',
            '/notificacoes.html'
        ],
        'menus': [
            {'id': 'lotes', 'nome': 'Lotes', 'url': '/lotes.html', 'icone': 'inventory_2'},
            {'id': 'lotes_aprovados', 'nome': 'Aprovados', 'url': '/lotes_aprovados.html', 'icone': 'check_circle'},
            {'id': 'dashboard', 'nome': 'Dashboard', 'url': '/dashboard.html', 'icone': 'dashboard'}
        ]
    },
    'Motorista': {
        'tela_inicial': '/funcionario.html',
        'rotas_api_permitidas': [
            '/api/solicitacoes'
        ],
        'paginas_permitidas': [
            '/funcionario.html',
            '/notificacoes.html'
        ],
        'menus': [
            {'id': 'funcionario', 'nome': 'Minhas Coletas', 'url': '/funcionario.html', 'icone': 'local_shipping'},
            {'id': 'notificacoes', 'nome': 'Notificações', 'url': '/notificacoes.html', 'icone': 'notifications'}
        ]
    },
    'Financeiro': {
        'tela_inicial': '/dashboard.html',
        'rotas_api_permitidas': [
            '/api/solicitacoes',
            '/api/fornecedores',
            '/api/lotes'
        ],
        'paginas_permitidas': [
            '/dashboard.html',
            '/fornecedores.html',
            '/fornecedores-lista.html',
            '/solicitacoes.html',
            '/lotes.html',
            '/notificacoes.html'
        ],
        'menus': [
            {'id': 'dashboard', 'nome': 'Dashboard', 'url': '/dashboard.html', 'icone': 'dashboard'},
            {'id': 'solicitacoes', 'nome': 'Solicitações', 'url': '/solicitacoes.html', 'icone': 'receipt_long'},
            {'id': 'fornecedores', 'nome': 'Fornecedores', 'url': '/fornecedores.html', 'icone': 'business'},
            {'id': 'lotes', 'nome': 'Lotes', 'url': '/lotes.html', 'icone': 'inventory_2'}
        ]
    },
    'Auditoria / BI': {
        'tela_inicial': '/dashboard.html',
        'rotas_api_permitidas': [
            '/api/auditoria',
            '/api/relatorios',
            '/api/usuarios',
            '/api/fornecedores',
            '/api/solicitacoes',
            '/api/lotes',
            '/api/entradas'
        ],
        'paginas_permitidas': [
            '/dashboard.html',
            '/auditoria.html',
            '/usuarios.html',
            '/fornecedores.html',
            '/fornecedores-lista.html',
            '/solicitacoes.html',
            '/lotes.html',
            '/lotes_aprovados.html',
            '/entradas.html',
            '/notificacoes.html'
        ],
        'menus': [
            {'id': 'dashboard', 'nome': 'Dashboard', 'url': '/dashboard.html', 'icone': 'dashboard'},
            {'id': 'auditoria', 'nome': 'Auditoria', 'url': '/auditoria.html', 'icone': 'verified'},
            {'id': 'solicitacoes', 'nome': 'Solicitações', 'url': '/solicitacoes.html', 'icone': 'request_quote'},
            {'id': 'lotes', 'nome': 'Lotes', 'url': '/lotes.html', 'icone': 'inventory_2'}
        ]
    }
}

def get_perfil_config(perfil_nome):
    """
    Retorna a configuração de um perfil específico
    """
    return PERFIL_CONFIG.get(perfil_nome, {
        'tela_inicial': '/acesso-negado.html',
        'rotas_api_permitidas': [],
        'paginas_permitidas': [],
        'menus': []
    })

def get_menus_by_perfil(perfil_nome):
    """
    Retorna os menus permitidos para um perfil
    """
    config = get_perfil_config(perfil_nome)
    return config.get('menus', [])

def get_tela_inicial_by_perfil(perfil_nome):
    """
    Retorna a tela inicial de um perfil
    """
    config = get_perfil_config(perfil_nome)
    return config.get('tela_inicial', '/acesso-negado.html')

def check_rota_api_permitida(perfil_nome, rota):
    """
    Verifica se uma rota de API é permitida para um perfil
    """
    config = get_perfil_config(perfil_nome)
    rotas_api_permitidas = config.get('rotas_api_permitidas', [])
    
    for rota_permitida in rotas_api_permitidas:
        if rota.startswith(rota_permitida):
            return True
    
    return False

def check_pagina_permitida(perfil_nome, pagina):
    """
    Verifica se uma página HTML é permitida para um perfil
    """
    config = get_perfil_config(perfil_nome)
    paginas_permitidas = config.get('paginas_permitidas', [])
    
    for pagina_permitida in paginas_permitidas:
        if pagina == pagina_permitida or pagina.endswith(pagina_permitida):
            return True
    
    return False

def get_paginas_permitidas(perfil_nome):
    """
    Retorna a lista de páginas permitidas para um perfil
    """
    config = get_perfil_config(perfil_nome)
    return config.get('paginas_permitidas', [])
