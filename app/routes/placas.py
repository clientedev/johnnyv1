from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Placa, Empresa, Usuario
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import cv2
import numpy as np
from PIL import Image
import io

placas_bp = Blueprint('placas', __name__)

UPLOAD_FOLDER = 'uploads/placas'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def analisar_placa_automatica(imagem_bytes):
    """
    Analisa automaticamente uma imagem de placa eletrônica e classifica como:
    - leve: Poucos componentes (< 150 contornos)
    - pesada: Muitos componentes (>= 500 contornos)
    - media: Quantidade moderada (150-499 contornos)
    
    Retorna: dict com 'classificacao' e 'componentes_detectados'
    """
    try:
        nparr = np.frombuffer(imagem_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return {'erro': 'Imagem inválida'}
        
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        lower_green = np.array([35, 40, 40])
        upper_green = np.array([85, 255, 255])
        mask_green = cv2.inRange(hsv, lower_green, upper_green)
        
        kernel = np.ones((5,5), np.uint8)
        mask_green = cv2.morphologyEx(mask_green, cv2.MORPH_CLOSE, kernel)
        mask_green = cv2.morphologyEx(mask_green, cv2.MORPH_OPEN, kernel)
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        
        edges = cv2.Canny(gray, 50, 150)
        
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        component_count = len([c for c in contours if cv2.contourArea(c) > 10])
        
        if component_count < 150:
            classificacao = "leve"
        elif component_count < 500:
            classificacao = "media"
        else:
            classificacao = "pesada"
        
        return {
            'classificacao': classificacao,
            'componentes_detectados': component_count,
            'mensagem': f'Analisada com sucesso! A placa foi classificada como: {classificacao.upper()}'
        }
        
    except Exception as e:
        return {'erro': f'Erro ao processar imagem: {str(e)}'}

@placas_bp.route('/api/placas/analisar', methods=['POST'])
@jwt_required()
def analisar_placa_endpoint():
    """
    Endpoint para analisar automaticamente uma imagem de placa eletrônica
    Espera: imagem no form-data
    Retorna: classificação (leve/pesada/media) e número de componentes detectados
    """
    if 'imagem' not in request.files:
        return jsonify({'erro': 'Nenhuma imagem enviada'}), 400
    
    file = request.files['imagem']
    
    if file.filename == '':
        return jsonify({'erro': 'Nome de arquivo vazio'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'erro': 'Formato de arquivo não permitido'}), 400
    
    try:
        imagem_bytes = file.read()
        
        resultado = analisar_placa_automatica(imagem_bytes)
        
        if 'erro' in resultado:
            return jsonify(resultado), 400
        
        return jsonify(resultado), 200
        
    except Exception as e:
        return jsonify({'erro': f'Erro ao processar imagem: {str(e)}'}), 500

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
    
    data = request.form if request.form else request.get_json()
    
    if not data:
        return jsonify({'error': 'Dados não fornecidos'}), 400
    
    empresa_id = data.get('empresa_id')
    tipo_placa = data.get('tipo_placa')
    peso_kg = data.get('peso_kg')
    valor = data.get('valor')
    relatorio_id = data.get('relatorio_id')
    observacoes = data.get('observacoes')
    localizacao_lat = data.get('localizacao_lat')
    localizacao_lng = data.get('localizacao_lng')
    endereco_completo = data.get('endereco_completo')
    
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
        localizacao_lat=float(localizacao_lat) if localizacao_lat else None,
        localizacao_lng=float(localizacao_lng) if localizacao_lng else None,
        endereco_completo=endereco_completo,
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
