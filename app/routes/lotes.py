from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Lote, Compra, Placa, Usuario, Notificacao
from app.auth import admin_required
from app import socketio
from datetime import datetime

bp = Blueprint('lotes', __name__, url_prefix='/api/lotes')

@bp.route('', methods=['GET'])
@jwt_required()
def listar_lotes():
    status = request.args.get('status')
    fornecedor_id = request.args.get('fornecedor_id', type=int)
    tipo_material = request.args.get('tipo_material')
    
    query = Lote.query
    
    if status:
        query = query.filter_by(status=status)
    
    if fornecedor_id:
        query = query.filter_by(fornecedor_id=fornecedor_id)
    
    if tipo_material:
        query = query.filter_by(tipo_material=tipo_material)
    
    lotes = query.order_by(Lote.data_criacao.desc()).all()
    
    return jsonify([lote.to_dict() for lote in lotes]), 200

@bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def obter_lote(id):
    lote = Lote.query.get(id)
    
    if not lote:
        return jsonify({'erro': 'Lote não encontrado'}), 404
    
    lote_dict = lote.to_dict()
    placas_list = list(lote.placas) if lote.placas else []
    lote_dict['placas'] = [placa.to_dict() for placa in placas_list]
    
    return jsonify(lote_dict), 200

@bp.route('/<int:id>/aprovar', methods=['PUT'])
@admin_required
def aprovar_lote(id):
    usuario_id = get_jwt_identity()
    
    lote = Lote.query.get(id)
    
    if not lote:
        return jsonify({'erro': 'Lote não encontrado'}), 404
    
    if lote.status != 'aberto':
        return jsonify({'erro': 'Apenas lotes com status "aberto" podem ser aprovados'}), 400
    
    lote.status = 'aprovado'
    lote.data_fechamento = datetime.utcnow()
    
    compra = Compra(
        lote_id=lote.id,
        fornecedor_id=lote.fornecedor_id,
        material=f"{lote.tipo_material.capitalize()} - {lote.numero_lote}",
        peso_total_kg=lote.peso_total_kg,
        valor_total=lote.valor_total,
        status='pendente'
    )
    
    db.session.add(compra)
    db.session.commit()
    
    return jsonify({
        'lote': lote.to_dict(),
        'compra': compra.to_dict()
    }), 200

@bp.route('/<int:id>/rejeitar', methods=['PUT'])
@admin_required
def rejeitar_lote(id):
    data = request.get_json()
    
    lote = Lote.query.get(id)
    
    if not lote:
        return jsonify({'erro': 'Lote não encontrado'}), 404
    
    if lote.status != 'aberto':
        return jsonify({'erro': 'Apenas lotes com status "aberto" podem ser rejeitados'}), 400
    
    lote.status = 'rejeitado'
    lote.data_fechamento = datetime.utcnow()
    lote.observacoes = data.get('observacoes', 'Lote rejeitado')
    
    for placa in lote.placas:
        placa.status = 'reprovada'
        placa.lote_id = None
    
    db.session.commit()
    
    return jsonify(lote.to_dict()), 200

@bp.route('/estatisticas', methods=['GET'])
@jwt_required()
def obter_estatisticas():
    total_abertos = Lote.query.filter_by(status='aberto').count()
    total_aprovados = Lote.query.filter_by(status='aprovado').count()
    total_rejeitados = Lote.query.filter_by(status='rejeitado').count()
    
    peso_total = db.session.query(db.func.sum(Lote.peso_total_kg)).filter_by(status='aprovado').scalar() or 0
    valor_total = db.session.query(db.func.sum(Lote.valor_total)).filter_by(status='aprovado').scalar() or 0
    
    return jsonify({
        'lotes_abertos': total_abertos,
        'lotes_aprovados': total_aprovados,
        'lotes_rejeitados': total_rejeitados,
        'peso_total_kg': float(peso_total),
        'valor_total': float(valor_total)
    }), 200
