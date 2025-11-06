from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from app.models import db, Relatorio, Usuario, Empresa, Notificacao
from app.auth import admin_required
from app import socketio
import os
from datetime import datetime

bp = Blueprint('relatorios', __name__, url_prefix='/api/relatorios')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('', methods=['GET'])
@jwt_required()
def listar_relatorios():
    usuario_id = get_jwt_identity()
    usuario = Usuario.query.get(usuario_id)
    
    status = request.args.get('status')
    empresa_id = request.args.get('empresa_id', type=int)
    
    query = Relatorio.query
    
    if usuario.tipo == 'funcionario':
        query = query.filter_by(funcionario_id=usuario_id)
    
    if status:
        query = query.filter_by(status=status)
    
    if empresa_id:
        query = query.filter_by(empresa_id=empresa_id)
    
    relatorios = query.order_by(Relatorio.data_envio.desc()).all()
    
    return jsonify([relatorio.to_dict() for relatorio in relatorios]), 200

@bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def obter_relatorio(id):
    usuario_id = get_jwt_identity()
    usuario = Usuario.query.get(usuario_id)
    
    relatorio = Relatorio.query.get(id)
    
    if not relatorio:
        return jsonify({'erro': 'Relatório não encontrado'}), 404
    
    if usuario.tipo == 'funcionario' and relatorio.funcionario_id != usuario_id:
        return jsonify({'erro': 'Acesso negado'}), 403
    
    return jsonify(relatorio.to_dict()), 200

@bp.route('', methods=['POST'])
@jwt_required()
def criar_relatorio():
    usuario_id = get_jwt_identity()
    usuario = Usuario.query.get(usuario_id)
    
    if usuario.tipo != 'funcionario':
        return jsonify({'erro': 'Apenas funcionários podem criar relatórios'}), 403
    
    if 'foto' not in request.files:
        return jsonify({'erro': 'Foto é obrigatória'}), 400
    
    file = request.files['foto']
    
    if file.filename == '':
        return jsonify({'erro': 'Nenhuma foto selecionada'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'erro': 'Formato de arquivo não permitido'}), 400
    
    empresa_id = request.form.get('empresa_id', type=int)
    tipo_placa = request.form.get('tipo_placa')
    peso_kg = request.form.get('peso_kg', type=float)
    localizacao_lat = request.form.get('localizacao_lat', type=float)
    localizacao_lng = request.form.get('localizacao_lng', type=float)
    observacoes = request.form.get('observacoes', '')
    
    if not empresa_id or not tipo_placa or not peso_kg:
        return jsonify({'erro': 'Empresa, tipo de placa e peso são obrigatórios'}), 400
    
    empresa = Empresa.query.get(empresa_id)
    if not empresa:
        return jsonify({'erro': 'Empresa não encontrada'}), 404
    
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{filename}"
    filepath = os.path.join('uploads', filename)
    file.save(filepath)
    
    relatorio = Relatorio(
        funcionario_id=usuario_id,
        empresa_id=empresa_id,
        tipo_placa=tipo_placa,
        peso_kg=peso_kg,
        foto_url=f'/uploads/{filename}',
        localizacao_lat=localizacao_lat,
        localizacao_lng=localizacao_lng,
        observacoes=observacoes,
        status='pendente'
    )
    
    db.session.add(relatorio)
    db.session.commit()
    
    admins = Usuario.query.filter_by(tipo='admin').all()
    for admin in admins:
        notificacao = Notificacao(
            usuario_id=admin.id,
            titulo='Novo Relatório Enviado',
            mensagem=f'{usuario.nome} enviou um novo relatório de {tipo_placa} ({peso_kg} kg) da empresa {empresa.nome}.'
        )
        db.session.add(notificacao)
    
    db.session.commit()
    
    socketio.emit('nova_notificacao', {'tipo': 'novo_relatorio'}, room='admins')
    
    return jsonify(relatorio.to_dict()), 201

@bp.route('/<int:id>/aprovar', methods=['PUT'])
@admin_required
def aprovar_relatorio(id):
    relatorio = Relatorio.query.get(id)
    
    if not relatorio:
        return jsonify({'erro': 'Relatório não encontrado'}), 404
    
    relatorio.status = 'aprovado'
    
    notificacao = Notificacao(
        usuario_id=relatorio.funcionario_id,
        titulo='Relatório Aprovado',
        mensagem=f'Seu relatório #{relatorio.id} foi aprovado pelo administrador.'
    )
    db.session.add(notificacao)
    db.session.commit()
    
    socketio.emit('nova_notificacao', {'tipo': 'relatorio_aprovado'}, room=f'user_{relatorio.funcionario_id}')
    
    return jsonify(relatorio.to_dict()), 200

@bp.route('/<int:id>/reprovar', methods=['PUT'])
@admin_required
def reprovar_relatorio(id):
    relatorio = Relatorio.query.get(id)
    
    if not relatorio:
        return jsonify({'erro': 'Relatório não encontrado'}), 404
    
    relatorio.status = 'reprovado'
    
    notificacao = Notificacao(
        usuario_id=relatorio.funcionario_id,
        titulo='Relatório Reprovado',
        mensagem=f'Seu relatório #{relatorio.id} foi reprovado pelo administrador.'
    )
    db.session.add(notificacao)
    db.session.commit()
    
    socketio.emit('nova_notificacao', {'tipo': 'relatorio_reprovado'}, room=f'user_{relatorio.funcionario_id}')
    
    return jsonify(relatorio.to_dict()), 200

@bp.route('/<int:id>', methods=['DELETE'])
@admin_required
def deletar_relatorio(id):
    relatorio = Relatorio.query.get(id)
    
    if not relatorio:
        return jsonify({'erro': 'Relatório não encontrado'}), 404
    
    if relatorio.foto_url:
        filepath = relatorio.foto_url.lstrip('/')
        if os.path.exists(filepath):
            os.remove(filepath)
    
    db.session.delete(relatorio)
    db.session.commit()
    
    return jsonify({'mensagem': 'Relatório deletado com sucesso'}), 200
