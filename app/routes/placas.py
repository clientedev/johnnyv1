from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Placa, Empresa, Usuario
from werkzeug.utils import secure_filename
import os
from datetime import datetime

placas_bp = Blueprint('placas', __name__)

UPLOAD_FOLDER = 'uploads/placas'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@placas_bp.route('/placas', methods=['GET'])
@jwt_required()
def get_placas():
    user_id = get_jwt_identity()
    user = Usuario.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    empresa_id = request.args.get('empresa_id', type=int)
    relatorio_id = request.args.get('relatorio_id', type=int)
    
    query = Placa.query
    
    if empresa_id:
        query = query.filter_by(empresa_id=empresa_id)
    
    if relatorio_id:
        query = query.filter_by(relatorio_id=relatorio_id)
    
    placas = query.order_by(Placa.data_registro.desc()).all()
    return jsonify([placa.to_dict() for placa in placas])

@placas_bp.route('/placas/<int:id>', methods=['GET'])
@jwt_required()
def get_placa(id):
    placa = Placa.query.get(id)
    if not placa:
        return jsonify({'error': 'Placa não encontrada'}), 404
    
    return jsonify(placa.to_dict())

@placas_bp.route('/placas', methods=['POST'])
@jwt_required()
def create_placa():
    user_id = get_jwt_identity()
    user = Usuario.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    imagem_url = None
    
    if 'imagem' in request.files:
        file = request.files['imagem']
        if file and allowed_file(file.filename):
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            imagem_url = f'/uploads/placas/{filename}'
    
    data = request.form if request.files else request.get_json()
    
    empresa_id = data.get('empresa_id')
    tipo_placa = data.get('tipo_placa')
    peso_kg = data.get('peso_kg')
    valor = data.get('valor')
    relatorio_id = data.get('relatorio_id')
    observacoes = data.get('observacoes')
    
    if not all([empresa_id, tipo_placa, peso_kg, valor]):
        return jsonify({'error': 'Dados incompletos'}), 400
    
    empresa = Empresa.query.get(empresa_id)
    if not empresa:
        return jsonify({'error': 'Empresa não encontrada'}), 404
    
    nova_placa = Placa(
        empresa_id=empresa_id,
        funcionario_id=user_id,
        relatorio_id=relatorio_id if relatorio_id else None,
        tipo_placa=tipo_placa,
        peso_kg=float(peso_kg),
        valor=float(valor),
        imagem_url=imagem_url,
        observacoes=observacoes
    )
    
    db.session.add(nova_placa)
    db.session.commit()
    
    return jsonify(nova_placa.to_dict()), 201

@placas_bp.route('/placas/<int:id>', methods=['PUT'])
@jwt_required()
def update_placa(id):
    user_id = get_jwt_identity()
    user = Usuario.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    placa = Placa.query.get(id)
    if not placa:
        return jsonify({'error': 'Placa não encontrada'}), 404
    
    data = request.get_json()
    
    if 'tipo_placa' in data:
        placa.tipo_placa = data['tipo_placa']
    if 'peso_kg' in data:
        placa.peso_kg = float(data['peso_kg'])
    if 'valor' in data:
        placa.valor = float(data['valor'])
    if 'relatorio_id' in data:
        placa.relatorio_id = data['relatorio_id']
    if 'observacoes' in data:
        placa.observacoes = data['observacoes']
    
    db.session.commit()
    
    return jsonify(placa.to_dict())

@placas_bp.route('/placas/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_placa(id):
    user_id = get_jwt_identity()
    user = Usuario.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    placa = Placa.query.get(id)
    if not placa:
        return jsonify({'error': 'Placa não encontrada'}), 404
    
    db.session.delete(placa)
    db.session.commit()
    
    return jsonify({'message': 'Placa removida com sucesso'})

@placas_bp.route('/placas/stats', methods=['GET'])
@jwt_required()
def get_placas_stats():
    empresa_id = request.args.get('empresa_id', type=int)
    
    query = Placa.query
    
    if empresa_id:
        query = query.filter_by(empresa_id=empresa_id)
    
    total_placas = query.count()
    total_peso = db.session.query(db.func.sum(Placa.peso_kg)).filter(
        Placa.empresa_id == empresa_id if empresa_id else True
    ).scalar() or 0
    total_valor = db.session.query(db.func.sum(Placa.valor)).filter(
        Placa.empresa_id == empresa_id if empresa_id else True
    ).scalar() or 0
    
    placas_por_tipo = {}
    tipos = db.session.query(
        Placa.tipo_placa,
        db.func.count(Placa.id),
        db.func.sum(Placa.peso_kg)
    ).group_by(Placa.tipo_placa)
    
    if empresa_id:
        tipos = tipos.filter_by(empresa_id=empresa_id)
    
    for tipo, count, peso in tipos:
        placas_por_tipo[tipo] = {
            'quantidade': count,
            'peso_total': float(peso) if peso else 0
        }
    
    return jsonify({
        'total_placas': total_placas,
        'total_peso_kg': float(total_peso),
        'total_valor': float(total_valor),
        'placas_por_tipo': placas_por_tipo
    })
