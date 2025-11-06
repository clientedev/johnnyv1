from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models import db, Empresa, Preco
from app.auth import admin_required

bp = Blueprint('empresas', __name__, url_prefix='/api/empresas')

@bp.route('', methods=['GET'])
@jwt_required()
def listar_empresas():
    empresas = Empresa.query.all()
    return jsonify([empresa.to_dict() for empresa in empresas]), 200

@bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def obter_empresa(id):
    empresa = Empresa.query.get(id)
    
    if not empresa:
        return jsonify({'erro': 'Empresa não encontrada'}), 404
    
    empresa_dict = empresa.to_dict()
    empresa_dict['precos'] = [preco.to_dict() for preco in empresa.precos]
    
    return jsonify(empresa_dict), 200

@bp.route('', methods=['POST'])
@admin_required
def criar_empresa():
    data = request.get_json()
    
    if not data or not data.get('nome') or not data.get('cnpj'):
        return jsonify({'erro': 'Nome e CNPJ são obrigatórios'}), 400
    
    empresa_existente = Empresa.query.filter_by(cnpj=data['cnpj']).first()
    if empresa_existente:
        return jsonify({'erro': 'CNPJ já cadastrado'}), 400
    
    empresa = Empresa(
        nome=data['nome'],
        cnpj=data['cnpj'],
        endereco=data.get('endereco', ''),
        telefone=data.get('telefone', ''),
        observacoes=data.get('observacoes', '')
    )
    
    db.session.add(empresa)
    db.session.commit()
    
    return jsonify(empresa.to_dict()), 201

@bp.route('/<int:id>', methods=['PUT'])
@admin_required
def atualizar_empresa(id):
    empresa = Empresa.query.get(id)
    
    if not empresa:
        return jsonify({'erro': 'Empresa não encontrada'}), 404
    
    data = request.get_json()
    
    if data.get('nome'):
        empresa.nome = data['nome']
    if data.get('cnpj'):
        empresa.cnpj = data['cnpj']
    if 'endereco' in data:
        empresa.endereco = data['endereco']
    if 'telefone' in data:
        empresa.telefone = data['telefone']
    if 'observacoes' in data:
        empresa.observacoes = data['observacoes']
    
    db.session.commit()
    
    return jsonify(empresa.to_dict()), 200

@bp.route('/<int:id>', methods=['DELETE'])
@admin_required
def deletar_empresa(id):
    empresa = Empresa.query.get(id)
    
    if not empresa:
        return jsonify({'erro': 'Empresa não encontrada'}), 404
    
    db.session.delete(empresa)
    db.session.commit()
    
    return jsonify({'mensagem': 'Empresa deletada com sucesso'}), 200
