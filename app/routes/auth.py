from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, 
    create_refresh_token,
    jwt_required, 
    get_jwt_identity
)
from app.models import db, Usuario
from app.auth import verificar_senha
from app.utils.auditoria import registrar_login

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
    
    access_token = create_access_token(identity=str(usuario.id))
    refresh_token = create_refresh_token(identity=str(usuario.id))
    
    registrar_login(usuario.id, sucesso=True)
    
    return jsonify({
        'token': access_token,
        'refresh_token': refresh_token,
        'usuario': usuario.to_dict()
    }), 200

@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    usuario_id = int(get_jwt_identity())
    usuario = Usuario.query.get(usuario_id)
    
    if not usuario or not usuario.ativo:
        return jsonify({'erro': 'Usuário não encontrado ou inativo'}), 404
    
    access_token = create_access_token(identity=str(usuario.id))
    
    return jsonify({
        'token': access_token
    }), 200

@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    usuario_id = int(get_jwt_identity())
    usuario = Usuario.query.get(usuario_id)
    
    if not usuario:
        return jsonify({'erro': 'Usuário não encontrado'}), 404
    
    return jsonify(usuario.to_dict()), 200
