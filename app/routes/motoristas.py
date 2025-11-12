from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Motorista, Veiculo
from app.auth import permission_required, admin_required, perfil_required
from app.utils.auditoria import registrar_criacao, registrar_atualizacao, registrar_exclusao

bp = Blueprint('motoristas', __name__, url_prefix='/api/motoristas')

@bp.route('', methods=['GET'])
@jwt_required()
def listar_motoristas():
    motoristas = Motorista.query.filter_by(ativo=True).all()
    return jsonify([m.to_dict() for m in motoristas]), 200

@bp.route('/<int:motorista_id>', methods=['GET'])
@jwt_required()
def obter_motorista(motorista_id):
    motorista = Motorista.query.get(motorista_id)
    if not motorista:
        return jsonify({'erro': 'Motorista não encontrado'}), 404
    return jsonify(motorista.to_dict()), 200

@bp.route('/cpf/<cpf>', methods=['GET'])
@jwt_required()
def buscar_por_cpf(cpf):
    cpf_limpo = cpf.replace('.', '').replace('-', '')
    motorista = Motorista.query.filter_by(cpf=cpf_limpo).first()
    if not motorista:
        return jsonify({'erro': 'Motorista não encontrado'}), 404
    return jsonify(motorista.to_dict()), 200

@bp.route('', methods=['POST'])
@permission_required('gerenciar_motoristas')
def criar_motorista():
    data = request.get_json()
    
    if not data or not data.get('nome') or not data.get('cpf'):
        return jsonify({'erro': 'Nome e CPF são obrigatórios'}), 400
    
    cpf_limpo = data['cpf'].replace('.', '').replace('-', '')
    
    if Motorista.query.filter_by(cpf=cpf_limpo).first():
        return jsonify({'erro': 'Já existe um motorista com este CPF'}), 400
    
    if data.get('cnh') and Motorista.query.filter_by(cnh=data['cnh']).first():
        return jsonify({'erro': 'Já existe um motorista com esta CNH'}), 400
    
    if data.get('veiculo_id'):
        veiculo = Veiculo.query.get(data['veiculo_id'])
        if not veiculo:
            return jsonify({'erro': 'Veículo não encontrado'}), 404
    
    try:
        usuario_id = int(get_jwt_identity())
        
        motorista = Motorista(
            nome=data['nome'],
            cpf=cpf_limpo,
            telefone=data.get('telefone'),
            email=data.get('email'),
            cnh=data.get('cnh'),
            categoria_cnh=data.get('categoria_cnh'),
            veiculo_id=data.get('veiculo_id'),
            ativo=data.get('ativo', True),
            criado_por=usuario_id
        )
        
        db.session.add(motorista)
        db.session.commit()
        
        registrar_criacao(usuario_id, 'motorista', motorista.id, {'nome': motorista.nome, 'cpf': motorista.cpf})
        
        return jsonify(motorista.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 400

@bp.route('/<int:motorista_id>', methods=['PUT'])
@permission_required('gerenciar_motoristas')
def atualizar_motorista(motorista_id):
    motorista = Motorista.query.get(motorista_id)
    if not motorista:
        return jsonify({'erro': 'Motorista não encontrado'}), 404
    
    data = request.get_json()
    
    if data.get('cpf'):
        cpf_limpo = data['cpf'].replace('.', '').replace('-', '')
        if cpf_limpo != motorista.cpf:
            if Motorista.query.filter_by(cpf=cpf_limpo).first():
                return jsonify({'erro': 'Já existe um motorista com este CPF'}), 400
    
    if data.get('cnh') and data['cnh'] != motorista.cnh:
        if Motorista.query.filter_by(cnh=data['cnh']).first():
            return jsonify({'erro': 'Já existe um motorista com esta CNH'}), 400
    
    if data.get('veiculo_id'):
        veiculo = Veiculo.query.get(data['veiculo_id'])
        if not veiculo:
            return jsonify({'erro': 'Veículo não encontrado'}), 404
    
    try:
        alteracoes = {}
        
        if 'nome' in data:
            motorista.nome = data['nome']
        if 'cpf' in data:
            cpf_limpo = data['cpf'].replace('.', '').replace('-', '')
            if cpf_limpo != motorista.cpf:
                alteracoes['cpf_antigo'] = motorista.cpf
                motorista.cpf = cpf_limpo
        if 'telefone' in data:
            motorista.telefone = data['telefone']
        if 'email' in data:
            motorista.email = data['email']
        if 'cnh' in data:
            motorista.cnh = data['cnh']
        if 'categoria_cnh' in data:
            motorista.categoria_cnh = data['categoria_cnh']
        if 'veiculo_id' in data:
            alteracoes['veiculo_alterado'] = True
            motorista.veiculo_id = data['veiculo_id']
        if 'ativo' in data:
            motorista.ativo = data['ativo']
        
        db.session.commit()
        
        usuario_id = int(get_jwt_identity())
        registrar_atualizacao(usuario_id, 'motorista', motorista.id, alteracoes)
        
        return jsonify(motorista.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 400

@bp.route('/<int:motorista_id>', methods=['DELETE'])
@admin_required
def deletar_motorista(motorista_id):
    motorista = Motorista.query.get(motorista_id)
    if not motorista:
        return jsonify({'erro': 'Motorista não encontrado'}), 404
    
    try:
        usuario_id = int(get_jwt_identity())
        registrar_exclusao(usuario_id, 'motorista', motorista.id, {'nome': motorista.nome, 'cpf': motorista.cpf})
        
        db.session.delete(motorista)
        db.session.commit()
        
        return jsonify({'mensagem': 'Motorista deletado com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 400
