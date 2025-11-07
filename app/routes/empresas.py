from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models import db, Empresa, Preco, ConfiguracaoPrecoEstrela
from app.auth import admin_required

bp = Blueprint('empresas', __name__, url_prefix='/api/empresas')

def criar_precos_por_estrelas(empresa):
    """Cria ou atualiza os preços da empresa baseado nas estrelas configuradas"""
    tipos_placas = [
        ('leve', empresa.estrelas_leve),
        ('pesada', empresa.estrelas_pesada),
        ('misturada', empresa.estrelas_misturada)
    ]
    
    for tipo_placa, estrelas in tipos_placas:
        if estrelas is None:
            continue
            
        config = ConfiguracaoPrecoEstrela.query.filter_by(tipo_placa=tipo_placa).first()
        
        if not config:
            continue
        
        valor_por_estrela = {
            1: config.valor_1_estrela,
            2: config.valor_2_estrelas,
            3: config.valor_3_estrelas,
            4: config.valor_4_estrelas,
            5: config.valor_5_estrelas
        }
        
        preco_por_kg = valor_por_estrela.get(estrelas, config.valor_3_estrelas)
        
        preco_existente = Preco.query.filter_by(
            empresa_id=empresa.id,
            tipo_placa=tipo_placa
        ).first()
        
        if preco_existente:
            preco_existente.preco_por_kg = preco_por_kg
            preco_existente.classificacao_estrelas = estrelas
        else:
            novo_preco = Preco(
                empresa_id=empresa.id,
                tipo_placa=tipo_placa,
                preco_por_kg=preco_por_kg,
                classificacao_estrelas=estrelas
            )
            db.session.add(novo_preco)
    
    db.session.commit()

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
        observacoes=data.get('observacoes', ''),
        estrelas_leve=data.get('estrelas_leve', 3),
        estrelas_pesada=data.get('estrelas_pesada', 3),
        estrelas_misturada=data.get('estrelas_misturada', 3)
    )
    
    db.session.add(empresa)
    db.session.commit()
    
    criar_precos_por_estrelas(empresa)
    
    return jsonify(empresa.to_dict()), 201

@bp.route('/<int:id>', methods=['PUT'])
@admin_required
def atualizar_empresa(id):
    empresa = Empresa.query.get(id)
    
    if not empresa:
        return jsonify({'erro': 'Empresa não encontrada'}), 404
    
    data = request.get_json()
    
    atualizar_precos = False
    
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
    
    if 'estrelas_leve' in data:
        empresa.estrelas_leve = data['estrelas_leve']
        atualizar_precos = True
    if 'estrelas_pesada' in data:
        empresa.estrelas_pesada = data['estrelas_pesada']
        atualizar_precos = True
    if 'estrelas_misturada' in data:
        empresa.estrelas_misturada = data['estrelas_misturada']
        atualizar_precos = True
    
    db.session.commit()
    
    if atualizar_precos:
        criar_precos_por_estrelas(empresa)
    
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
