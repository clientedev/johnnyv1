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
            '/api/tipos-lote',
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
        'tela_inicial': '/app-motorista.html',
        'rotas_api_permitidas': [
            '/api/solicitacoes',
            '/api/motoristas'
        ],
        'paginas_permitidas': [
            '/app-motorista.html',
            '/notificacoes.html'
        ],
        'menus': [
            {'id': 'app-motorista', 'nome': 'Meu App', 'url': '/app-motorista.html', 'icone': 'local_shipping'},
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

TIPOS_USUARIO = {
    'admin': {
        'nome': 'Administrador',
        'descricao': 'Acesso total ao sistema',
        'homepage': '/dashboard.html'
    },
    'funcionario': {
        'nome': 'Funcionário',
        'descricao': 'Acesso limitado baseado no perfil',
        'homepage': '/funcionario.html'
    },
    'motorista': {
        'nome': 'Motorista',
        'descricao': 'Acesso ao app de entregas',
        'homepage': '/app-motorista.html'
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
    """Retorna os menus que devem ser exibidos para cada perfil"""
    if not perfil_nome or perfil_nome == 'Administrador':
        return [
            {'nome': 'Dashboard', 'icone': 'fa-home', 'url': '/dashboard.html'},
            {'nome': 'Cadastros', 'icone': 'fa-database', 'url': '/administracao.html'},
            {'nome': 'Solicitações', 'icone': 'fa-plus-circle', 'url': '/solicitacoes.html'},
            {'nome': 'Aprovação', 'icone': 'fa-check-circle', 'url': '/aprovar_solicitacoes.html'},
            {'nome': 'Compras', 'icone': 'fa-shopping-cart', 'url': '/compras.html'},
            {'nome': 'Logística', 'icone': 'fa-truck', 'url': '/logistica.html'},
            {'nome': 'Conferência', 'icone': 'fa-clipboard-check', 'url': '/conferencia.html'},
            {'nome': 'Kanban', 'icone': 'fa-tasks', 'url': '/kanban.html'},
            {'nome': 'Lotes', 'icone': 'fa-boxes', 'url': '/lotes.html'},
            {'nome': 'Entradas', 'icone': 'fa-arrow-down', 'url': '/entradas.html'},
            {'nome': 'Consulta', 'icone': 'fa-search', 'url': '/consulta.html'}
        ]

    menus_por_perfil = {
        'Comprador': [
            {'nome': 'Dashboard', 'icone': 'fa-home', 'url': '/dashboard.html'},
            {'nome': 'Solicitações', 'icone': 'fa-plus-circle', 'url': '/solicitacoes.html'},
            {'nome': 'Compras', 'icone': 'fa-shopping-cart', 'url': '/compras.html'}
        ],
        'Aprovador': [
            {'nome': 'Dashboard', 'icone': 'fa-home', 'url': '/dashboard.html'},
            {'nome': 'Aprovação', 'icone': 'fa-check-circle', 'url': '/aprovar_solicitacoes.html'}
        ],
        'Conferente': [
            {'nome': 'Dashboard', 'icone': 'fa-home', 'url': '/dashboard.html'},
            {'nome': 'Conferência', 'icone': 'fa-clipboard-check', 'url': '/conferencia.html'},
            {'nome': 'Entradas', 'icone': 'fa-arrow-down', 'url': '/entradas.html'}
        ],
        'Logística': [
            {'nome': 'Dashboard', 'icone': 'fa-home', 'url': '/dashboard.html'},
            {'nome': 'Logística', 'icone': 'fa-truck', 'url': '/logistica.html'},
            {'nome': 'Kanban', 'icone': 'fa-tasks', 'url': '/kanban.html'}
        ],
        'Motorista': [
            {'nome': 'Minhas Rotas', 'icone': 'fa-route', 'url': '/app-motorista.html'}
        ]
    }

    return menus_por_perfil.get(perfil_nome, [])

def get_tela_inicial_by_perfil(perfil_nome):
    """Retorna a tela inicial baseada no perfil"""
    if not perfil_nome or perfil_nome == 'Administrador':
        return '/dashboard.html'

    mapeamento = {
        'Comprador': '/solicitacoes.html',
        'Aprovador': '/aprovar_solicitacoes.html',
        'Conferente': '/conferencia.html',
        'Logística': '/logistica.html',
        'Motorista': '/app-motorista.html'
    }

    return mapeamento.get(perfil_nome, '/acesso-negado.html')

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
    """Retorna lista de páginas que o perfil pode acessar"""
    if not perfil_nome or perfil_nome == 'Administrador':
        return [
            '/dashboard.html', '/administracao.html', '/solicitacoes.html', 
            '/aprovar_solicitacoes.html', '/compras.html', '/logistica.html',
            '/conferencia.html', '/kanban.html', '/lotes.html', '/entradas.html',
            '/consulta.html', '/fornecedores.html', '/tipos-lote.html',
            '/veiculos.html', '/motoristas.html', '/usuarios.html',
            '/perfis.html', '/configuracoes.html', '/notificacoes.html'
        ]

    paginas_por_perfil = {
        'Comprador': [
            '/dashboard.html', '/solicitacoes.html', '/fornecedores.html',
            '/tipos-lote.html', '/consulta.html', '/notificacoes.html'
        ],
        'Aprovador': [
            '/dashboard.html', '/aprovar_solicitacoes.html', '/consulta.html',
            '/notificacoes.html'
        ],
        'Conferente': [
            '/dashboard.html', '/conferencia.html', '/consulta.html',
            '/notificacoes.html'
        ],
        'Logística': [
            '/dashboard.html', '/logistica.html', '/kanban.html',
            '/veiculos.html', '/motoristas.html', '/consulta.html',
            '/notificacoes.html'
        ],
        'Motorista': [
            '/app-motorista.html', '/notificacoes.html'
        ]
    }

    return paginas_por_perfil.get(perfil_nome, [])