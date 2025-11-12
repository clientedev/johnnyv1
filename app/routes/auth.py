from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, 
    create_refresh_token,
    jwt_required, 
    get_jwt_identity,
    get_jwt
)
from app.models import db, Usuario
from app.auth import verificar_senha, get_user_jwt_claims
from app.utils.auditoria import registrar_login
from app.rbac_config import get_menus_by_perfil, get_tela_inicial_by_perfil, get_paginas_permitidas

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('senha'):
        return jsonify({'erro': 'Email e senha são obrigatórios'}), 400
    
    usuario = Usuario.query.filter_by(email=data['email']).first()
    
    if not usuario or not verificar_senha(data['senha'], usuario.senha_hash):
        if usuario:
            registrar_login(usuario.id, sucesso=False)
        return jsonify({'erro': 'Email ou senha incorretos'}), 401
    
    if not usuario.ativo:
        return jsonify({'erro': 'Usuário inativo. Entre em contato com o administrador.'}), 403
    
    additional_claims = get_user_jwt_claims(usuario)
    access_token = create_access_token(identity=str(usuario.id), additional_claims=additional_claims)
    refresh_token = create_refresh_token(identity=str(usuario.id), additional_claims=additional_claims)
    
    registrar_login(usuario.id, sucesso=True)
    
    perfil_nome = usuario.perfil.nome if usuario.perfil else 'Administrador'
    
    permissoes = {}
    if usuario.perfil:
        permissoes = usuario.perfil.permissoes or {}
    elif usuario.tipo == 'admin':
        permissoes = {
            'gerenciar_usuarios': True,
            'gerenciar_perfis': True,
            'gerenciar_fornecedores': True,
            'gerenciar_veiculos': True,
            'gerenciar_motoristas': True,
            'criar_solicitacao': True,
            'aprovar_solicitacao': True,
            'rejeitar_solicitacao': True,
            'criar_lote': True,
            'aprovar_lote': True,
            'processar_entrada': True,
            'visualizar_auditoria': True,
            'exportar_relatorios': True,
            'definir_limites': True,
            'autorizar_descarte': True
        }
    
    tela_inicial = get_tela_inicial_by_perfil(perfil_nome)
    
    usuario_dict = usuario.to_dict()
    usuario_dict['permissoes'] = permissoes
    usuario_dict['perfil'] = perfil_nome
    usuario_dict['tela_inicial'] = tela_inicial
    
    return jsonify({
        'token': access_token,
        'refresh_token': refresh_token,
        'usuario': usuario_dict
    }), 200

@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    usuario_id = int(get_jwt_identity())
    usuario = Usuario.query.get(usuario_id)
    
    if not usuario or not usuario.ativo:
        return jsonify({'erro': 'Usuário não encontrado ou inativo'}), 404
    
    additional_claims = get_user_jwt_claims(usuario)
    access_token = create_access_token(identity=str(usuario.id), additional_claims=additional_claims)
    
    return jsonify({
        'token': access_token
    }), 200

@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user_endpoint():
    usuario_id = int(get_jwt_identity())
    usuario = Usuario.query.get(usuario_id)
    
    if not usuario:
        return jsonify({'erro': 'Usuário não encontrado'}), 404
    
    claims = get_jwt()
    perfil_nome = claims.get('perfil', 'Sem perfil')
    
    permissoes = {}
    permissoes_lista = claims.get('permissoes', [])
    
    if usuario.perfil:
        permissoes = usuario.perfil.permissoes or {}
    elif usuario.tipo == 'admin':
        permissoes = {
            'gerenciar_usuarios': True,
            'gerenciar_perfis': True,
            'gerenciar_fornecedores': True,
            'gerenciar_veiculos': True,
            'gerenciar_motoristas': True,
            'criar_solicitacao': True,
            'aprovar_solicitacao': True,
            'rejeitar_solicitacao': True,
            'criar_lote': True,
            'aprovar_lote': True,
            'processar_entrada': True,
            'visualizar_auditoria': True,
            'exportar_relatorios': True,
            'definir_limites': True,
            'autorizar_descarte': True
        }
        permissoes_lista = list(permissoes.keys())
    
    tela_inicial = get_tela_inicial_by_perfil(perfil_nome)
    
    usuario_dict = usuario.to_dict()
    usuario_dict['perfil'] = perfil_nome
    usuario_dict['permissoes'] = permissoes_lista
    usuario_dict['permissoes_detalhadas'] = permissoes
    usuario_dict['tela_inicial'] = tela_inicial
    
    return jsonify(usuario_dict), 200

@bp.route('/menus', methods=['GET'])
@jwt_required()
def get_menus():
    claims = get_jwt()
    perfil_nome = claims.get('perfil')
    
    if not perfil_nome:
        return jsonify({'erro': 'Perfil não definido'}), 403
    
    menus = get_menus_by_perfil(perfil_nome)
    paginas_permitidas = get_paginas_permitidas(perfil_nome)
    
    return jsonify({
        'perfil': perfil_nome,
        'menus': menus,
        'paginas_permitidas': paginas_permitidas
    }), 200
