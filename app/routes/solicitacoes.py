from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Solicitacao, Usuario, Empresa, Notificacao, Placa, Entrada
from app.auth import admin_required
from app import socketio
from datetime import datetime

bp = Blueprint('solicitacoes', __name__, url_prefix='/api/solicitacoes')

@bp.route('', methods=['GET'])
@jwt_required()
def listar_solicitacoes():
    usuario_id = get_jwt_identity()
    usuario = Usuario.query.get(usuario_id)
    
    status = request.args.get('status')
    empresa_id = request.args.get('empresa_id', type=int)
    busca = request.args.get('busca', '')
    
    query = Solicitacao.query
    
    if usuario.tipo == 'funcionario':
        query = query.filter_by(funcionario_id=usuario_id)
    
    if status:
        query = query.filter_by(status=status)
    
    if empresa_id:
        query = query.filter_by(empresa_id=empresa_id)
    
    if busca:
        query = query.join(Empresa).join(Usuario).filter(
            db.or_(
                Empresa.nome.ilike(f'%{busca}%'),
                Usuario.nome.ilike(f'%{busca}%')
            )
        )
    
    solicitacoes = query.order_by(Solicitacao.data_envio.desc()).all()
    
    return jsonify([solicitacao.to_dict() for solicitacao in solicitacoes]), 200

@bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def obter_solicitacao(id):
    usuario_id = get_jwt_identity()
    usuario = Usuario.query.get(usuario_id)
    
    solicitacao = Solicitacao.query.get(id)
    
    if not solicitacao:
        return jsonify({'erro': 'Solicitação não encontrada'}), 404
    
    if usuario.tipo == 'funcionario' and solicitacao.funcionario_id != usuario_id:
        return jsonify({'erro': 'Acesso negado'}), 403
    
    solicitacao_dict = solicitacao.to_dict()
    solicitacao_dict['placas'] = [placa.to_dict() for placa in solicitacao.placas]
    
    return jsonify(solicitacao_dict), 200

@bp.route('', methods=['POST'])
@jwt_required()
def criar_solicitacao():
    usuario_id = get_jwt_identity()
    usuario = Usuario.query.get(usuario_id)
    
    if usuario.tipo != 'funcionario':
        return jsonify({'erro': 'Apenas funcionários podem criar solicitações'}), 403
    
    data = request.get_json()
    
    empresa_id = data.get('empresa_id', type=int)
    observacoes = data.get('observacoes', '')
    
    if not empresa_id:
        return jsonify({'erro': 'Empresa é obrigatória'}), 400
    
    empresa = Empresa.query.get(empresa_id)
    if not empresa:
        return jsonify({'erro': 'Empresa não encontrada'}), 404
    
    solicitacao = Solicitacao(
        funcionario_id=usuario_id,
        empresa_id=empresa_id,
        observacoes=observacoes,
        status='pendente'
    )
    
    db.session.add(solicitacao)
    db.session.commit()
    
    admins = Usuario.query.filter_by(tipo='admin').all()
    for admin in admins:
        notificacao = Notificacao(
            usuario_id=admin.id,
            titulo='Nova Solicitação Criada',
            mensagem=f'{usuario.nome} criou uma nova solicitação para a empresa {empresa.nome}.'
        )
        db.session.add(notificacao)
    
    db.session.commit()
    
    socketio.emit('nova_notificacao', {'tipo': 'nova_solicitacao'}, room='admins')
    
    return jsonify(solicitacao.to_dict()), 201

@bp.route('/<int:id>/placas', methods=['POST'])
@jwt_required()
def adicionar_placa_solicitacao(id):
    usuario_id = get_jwt_identity()
    usuario = Usuario.query.get(usuario_id)
    
    solicitacao = Solicitacao.query.get(id)
    
    if not solicitacao:
        return jsonify({'erro': 'Solicitação não encontrada'}), 404
    
    if usuario.tipo == 'funcionario' and solicitacao.funcionario_id != usuario_id:
        return jsonify({'erro': 'Acesso negado'}), 403
    
    if solicitacao.status == 'confirmada':
        return jsonify({'erro': 'Não é possível adicionar placas a uma solicitação confirmada'}), 400
    
    data = request.get_json()
    
    tipo_placa = data.get('tipo_placa')
    peso_kg = data.get('peso_kg', type=float)
    valor = data.get('valor', type=float)
    
    if not all([tipo_placa, peso_kg, valor]):
        return jsonify({'erro': 'Tipo de placa, peso e valor são obrigatórios'}), 400
    
    placa = Placa(
        empresa_id=solicitacao.empresa_id,
        funcionario_id=usuario_id,
        solicitacao_id=id,
        tipo_placa=tipo_placa,
        peso_kg=peso_kg,
        valor=valor,
        status='em_analise',
        observacoes=data.get('observacoes', '')
    )
    
    db.session.add(placa)
    db.session.commit()
    
    return jsonify(placa.to_dict()), 201

@bp.route('/<int:id>/confirmar', methods=['PUT'])
@jwt_required()
def confirmar_solicitacao(id):
    usuario_id = get_jwt_identity()
    usuario = Usuario.query.get(usuario_id)
    
    solicitacao = Solicitacao.query.get(id)
    
    if not solicitacao:
        return jsonify({'erro': 'Solicitação não encontrada'}), 404
    
    if usuario.tipo == 'funcionario' and solicitacao.funcionario_id != usuario_id:
        return jsonify({'erro': 'Acesso negado'}), 403
    
    if len(solicitacao.placas) == 0:
        return jsonify({'erro': 'Não é possível confirmar solicitação sem placas'}), 400
    
    solicitacao.status = 'confirmada'
    solicitacao.data_confirmacao = datetime.utcnow()
    
    entrada = Entrada(
        solicitacao_id=id,
        admin_id=None,
        status='pendente'
    )
    db.session.add(entrada)
    
    for placa in solicitacao.placas:
        placa.status = 'entrada'
    
    db.session.commit()
    
    admins = Usuario.query.filter_by(tipo='admin').all()
    for admin in admins:
        notificacao = Notificacao(
            usuario_id=admin.id,
            titulo='Solicitação Confirmada para Entrada',
            mensagem=f'A solicitação #{solicitacao.id} foi confirmada e está aguardando aprovação na tela de Entradas.'
        )
        db.session.add(notificacao)
    
    db.session.commit()
    
    socketio.emit('nova_notificacao', {'tipo': 'solicitacao_confirmada'}, room='admins')
    
    return jsonify(solicitacao.to_dict()), 200

@bp.route('/<int:id>', methods=['DELETE'])
@admin_required
def deletar_solicitacao(id):
    solicitacao = Solicitacao.query.get(id)
    
    if not solicitacao:
        return jsonify({'erro': 'Solicitação não encontrada'}), 404
    
    db.session.delete(solicitacao)
    db.session.commit()
    
    return jsonify({'mensagem': 'Solicitação deletada com sucesso'}), 200
