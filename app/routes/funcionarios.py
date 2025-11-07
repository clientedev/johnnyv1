from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models import db, Funcionario, Empresa, Vendedor
from app.auth import admin_required

bp = Blueprint('funcionarios', __name__, url_prefix='/api/funcionarios')

@bp.route('', methods=['GET'])
@jwt_required()
def listar_funcionarios():
    busca = request.args.get('busca', '')
    cargo = request.args.get('cargo', '')
    empresa_id = request.args.get('empresa_id', type=int)
    ativo = request.args.get('ativo', type=bool)
    
    query = Funcionario.query
    
    if busca:
        query = query.filter(
            db.or_(
                Funcionario.nome.ilike(f'%{busca}%'),
                Funcionario.cpf.ilike(f'%{busca}%'),
                Funcionario.telefone.ilike(f'%{busca}%')
            )
        )
    
    if cargo:
        query = query.filter(Funcionario.cargo.ilike(f'%{cargo}%'))
    
    if empresa_id:
        query = query.filter_by(empresa_id=empresa_id)
    
    if ativo is not None:
        query = query.filter_by(ativo=ativo)
    
    funcionarios = query.order_by(Funcionario.nome).all()
    return jsonify([funcionario.to_dict() for funcionario in funcionarios]), 200

@bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def obter_funcionario(id):
    funcionario = Funcionario.query.get(id)
    
    if not funcionario:
        return jsonify({'erro': 'Funcionário não encontrado'}), 404
    
    return jsonify(funcionario.to_dict()), 200

@bp.route('', methods=['POST'])
@admin_required
def criar_funcionario():
    data = request.get_json()
    
    if not data or not data.get('nome') or not data.get('cpf'):
        return jsonify({'erro': 'Nome e CPF são obrigatórios'}), 400
    
    funcionario_existente = Funcionario.query.filter_by(cpf=data['cpf']).first()
    if funcionario_existente:
        return jsonify({'erro': 'CPF já cadastrado'}), 400
    
    funcionario = Funcionario(
        nome=data['nome'],
        cpf=data['cpf'],
        telefone=data.get('telefone'),
        cargo=data.get('cargo'),
        empresa_id=data.get('empresa_id'),
        vendedor_id=data.get('vendedor_id'),
        ativo=data.get('ativo', True)
    )
    
    db.session.add(funcionario)
    db.session.commit()
    
    return jsonify(funcionario.to_dict()), 201

@bp.route('/<int:id>', methods=['PUT'])
@admin_required
def atualizar_funcionario(id):
    funcionario = Funcionario.query.get(id)
    
    if not funcionario:
        return jsonify({'erro': 'Funcionário não encontrado'}), 404
    
    data = request.get_json()
    
    if data.get('cpf') and data['cpf'] != funcionario.cpf:
        funcionario_existente = Funcionario.query.filter_by(cpf=data['cpf']).first()
        if funcionario_existente:
            return jsonify({'erro': 'CPF já cadastrado'}), 400
    
    if data.get('nome'):
        funcionario.nome = data['nome']
    if data.get('cpf'):
        funcionario.cpf = data['cpf']
    if data.get('telefone') is not None:
        funcionario.telefone = data['telefone']
    if data.get('cargo') is not None:
        funcionario.cargo = data['cargo']
    if data.get('empresa_id') is not None:
        funcionario.empresa_id = data['empresa_id']
    if data.get('vendedor_id') is not None:
        funcionario.vendedor_id = data['vendedor_id']
    if 'ativo' in data:
        funcionario.ativo = data['ativo']
    
    db.session.commit()
    
    return jsonify(funcionario.to_dict()), 200

@bp.route('/<int:id>', methods=['DELETE'])
@admin_required
def deletar_funcionario(id):
    funcionario = Funcionario.query.get(id)
    
    if not funcionario:
        return jsonify({'erro': 'Funcionário não encontrado'}), 404
    
    db.session.delete(funcionario)
    db.session.commit()
    
    return jsonify({'mensagem': 'Funcionário deletado com sucesso'}), 200
