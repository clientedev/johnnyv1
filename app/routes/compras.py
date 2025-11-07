from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime
from app.models import db, Compra, Fornecedor, Solicitacao
from app.auth import admin_required
import os
from werkzeug.utils import secure_filename

bp = Blueprint('compras', __name__, url_prefix='/api/compras')

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('', methods=['GET'])
@jwt_required()
def listar_compras():
    fornecedor_id = request.args.get('fornecedor_id', type=int)
    tipo = request.args.get('tipo')
    status = request.args.get('status')
    
    query = Compra.query
    
    if fornecedor_id:
        query = query.filter_by(fornecedor_id=fornecedor_id)
    
    if tipo:
        query = query.filter_by(tipo=tipo)
    
    if status:
        query = query.filter_by(status=status)
    
    compras = query.order_by(Compra.data_compra.desc()).all()
    return jsonify([compra.to_dict() for compra in compras]), 200

@bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def obter_compra(id):
    compra = Compra.query.get(id)
    
    if not compra:
        return jsonify({'erro': 'Compra não encontrada'}), 404
    
    return jsonify(compra.to_dict()), 200

@bp.route('', methods=['POST'])
@admin_required
def criar_compra():
    data = request.get_json() if request.is_json else request.form.to_dict()
    
    if not data.get('fornecedor_id') or not data.get('material') or not data.get('valor'):
        return jsonify({'erro': 'Fornecedor, material e valor são obrigatórios'}), 400
    
    fornecedor = Fornecedor.query.get(int(data['fornecedor_id']))
    if not fornecedor:
        return jsonify({'erro': 'Fornecedor não encontrado'}), 404
    
    comprovante_url = None
    if 'comprovante' in request.files:
        file = request.files['comprovante']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join('uploads/comprovantes', filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            file.save(filepath)
            comprovante_url = filepath
    
    solicitacao_id = None
    if data.get('solicitacao_id'):
        solicitacao_id = int(data['solicitacao_id'])
    
    compra = Compra(
        fornecedor_id=int(data['fornecedor_id']),
        solicitacao_id=solicitacao_id,
        material=data['material'],
        tipo=data.get('tipo', 'compra'),
        valor=float(data['valor']),
        status=data.get('status', 'pendente'),
        comprovante_url=comprovante_url,
        observacoes=data.get('observacoes')
    )
    
    db.session.add(compra)
    db.session.commit()
    
    return jsonify(compra.to_dict()), 201

@bp.route('/<int:id>', methods=['PUT'])
@admin_required
def atualizar_compra(id):
    compra = Compra.query.get(id)
    
    if not compra:
        return jsonify({'erro': 'Compra não encontrada'}), 404
    
    data = request.get_json()
    
    if data.get('material'):
        compra.material = data['material']
    if data.get('valor'):
        compra.valor = float(data['valor'])
    if data.get('tipo'):
        compra.tipo = data['tipo']
    if data.get('status'):
        compra.status = data['status']
        if data['status'] == 'pago' and not compra.data_pagamento:
            compra.data_pagamento = datetime.utcnow()
    if data.get('observacoes') is not None:
        compra.observacoes = data['observacoes']
    
    db.session.commit()
    
    return jsonify(compra.to_dict()), 200

@bp.route('/<int:id>', methods=['DELETE'])
@admin_required
def deletar_compra(id):
    compra = Compra.query.get(id)
    
    if not compra:
        return jsonify({'erro': 'Compra não encontrada'}), 404
    
    if compra.comprovante_url and os.path.exists(compra.comprovante_url):
        os.remove(compra.comprovante_url)
    
    db.session.delete(compra)
    db.session.commit()
    
    return jsonify({'mensagem': 'Compra deletada com sucesso'}), 200

@bp.route('/estatisticas', methods=['GET'])
@jwt_required()
def obter_estatisticas_compras():
    total_compras = Compra.query.filter_by(tipo='compra').count()
    total_despesas = Compra.query.filter_by(tipo='despesa').count()
    
    valor_total_compras = db.session.query(db.func.sum(Compra.valor)).filter_by(tipo='compra').scalar() or 0
    valor_total_despesas = db.session.query(db.func.sum(Compra.valor)).filter_by(tipo='despesa').scalar() or 0
    
    pendentes = Compra.query.filter_by(status='pendente').count()
    pagas = Compra.query.filter_by(status='pago').count()
    
    return jsonify({
        'total_compras': total_compras,
        'total_despesas': total_despesas,
        'valor_total_compras': float(valor_total_compras),
        'valor_total_despesas': float(valor_total_despesas),
        'pendentes': pendentes,
        'pagas': pagas
    }), 200
