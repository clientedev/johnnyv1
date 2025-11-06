from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models import db, Usuario
from app.auth import admin_required, hash_senha

bp = Blueprint('usuarios', __name__, url_prefix='/api/usuarios')

@bp.route('', methods=['GET'])
@admin_required
def listar_usuarios():
    usuarios = Usuario.query.all()
    return jsonify([usuario.to_dict() for usuario in usuarios]), 200

@bp.route('/<int:id>', methods=['GET'])
@admin_required
def obter_usuario(id):
    usuario = Usuario.query.get(id)
    
    if not usuario:
        return jsonify({'erro': 'Usuário não encontrado'}), 404
    
    return jsonify(usuario.to_dict()), 200

@bp.route('', methods=['POST'])
@admin_required
def criar_usuario():
    data = request.get_json()
    
    if not data or not data.get('nome') or not data.get('email') or not data.get('senha'):
        return jsonify({'erro': 'Nome, email e senha são obrigatórios'}), 400
    
    usuario_existente = Usuario.query.filter_by(email=data['email']).first()
    if usuario_existente:
        return jsonify({'erro': 'Email já cadastrado'}), 400
    
    usuario = Usuario(
        nome=data['nome'],
        email=data['email'],
        senha_hash=hash_senha(data['senha']),
        tipo=data.get('tipo', 'funcionario')
    )
    
    db.session.add(usuario)
    db.session.commit()
    
    return jsonify(usuario.to_dict()), 201

@bp.route('/<int:id>', methods=['PUT'])
@admin_required
def atualizar_usuario(id):
    usuario = Usuario.query.get(id)
    
    if not usuario:
        return jsonify({'erro': 'Usuário não encontrado'}), 404
    
    data = request.get_json()
    
    if data.get('nome'):
        usuario.nome = data['nome']
    if data.get('email'):
        usuario.email = data['email']
    if data.get('senha'):
        usuario.senha_hash = hash_senha(data['senha'])
    if data.get('tipo'):
        usuario.tipo = data['tipo']
    
    db.session.commit()
    
    return jsonify(usuario.to_dict()), 200

@bp.route('/<int:id>', methods=['DELETE'])
@admin_required
def deletar_usuario(id):
    usuario = Usuario.query.get(id)
    
    if not usuario:
        return jsonify({'erro': 'Usuário não encontrado'}), 404
    
    if usuario.tipo == 'admin':
        admins = Usuario.query.filter_by(tipo='admin').count()
        if admins <= 1:
            return jsonify({'erro': 'Não é possível deletar o único administrador do sistema'}), 400
    
    db.session.delete(usuario)
    db.session.commit()
    
    return jsonify({'mensagem': 'Usuário deletado com sucesso'}), 200
