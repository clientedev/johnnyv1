from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import (
    db, Solicitacao, ItemSolicitacao, Fornecedor, TipoLote, 
    FornecedorTipoLoteClassificacao, TipoLotePrecoClassificacao, Usuario, Configuracao, Lote, EntradaEstoque
)
from app.auth import admin_required
from datetime import datetime
import os
import base64
from werkzeug.utils import secure_filename
import uuid

bp = Blueprint('solicitacao_lotes', __name__, url_prefix='/api/solicitacao-lotes')

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def analisar_imagem_com_ia(imagem_path):
    """Analisa imagem usando Gemini AI para classificar lote"""
    try:
        import google.genai as genai
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("AVISO: GEMINI_API_KEY não configurada")
            return None
        
        client = genai.Client(api_key=api_key)
        
        with open(imagem_path, 'rb') as f:
            image_data = f.read()
        
        prompt = """Analise esta imagem de placas eletrônicas e classifique o lote baseado na densidade e quantidade de componentes:

- LEVE: Placas com poucos componentes, circuitos simples, baixa densidade
- MEDIO: Placas com quantidade moderada de componentes, complexidade média
- PESADO: Placas densamente povoadas com muitos componentes, circuitos complexos

Retorne APENAS uma das palavras: leve, medio ou pesado"""

        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=[prompt, {'mime_type': 'image/jpeg', 'data': base64.b64encode(image_data).decode()}]
        )
        
        classificacao = response.text.strip().lower()
        
        if classificacao not in ['leve', 'medio', 'pesado']:
            print(f"AVISO: IA retornou classificação inválida: {classificacao}")
            return 'medio'
        
        return classificacao
        
    except Exception as e:
        print(f"ERRO ao analisar imagem com IA: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def calcular_valor_item(fornecedor_id, tipo_lote_id, classificacao, peso_kg):
    """Calcula o valor do item baseado na classificação e configuração do fornecedor
    
    Raises:
        ValueError: Se não houver configuração de classificação para este fornecedor/tipo
    """
    config_class = FornecedorTipoLoteClassificacao.query.filter_by(
        fornecedor_id=fornecedor_id,
        tipo_lote_id=tipo_lote_id,
        ativo=True
    ).first()
    
    if not config_class:
        raise ValueError(
            f'Fornecedor {fornecedor_id} não possui configuração de estrelas '
            f'para o tipo de lote {tipo_lote_id}. Configure as estrelas antes de criar solicitações.'
        )
    
    estrelas = config_class.get_estrelas_por_classificacao(classificacao)
    
    preco_config = TipoLotePrecoClassificacao.query.filter_by(
        tipo_lote_id=tipo_lote_id,
        classificacao=classificacao,
        ativo=True
    ).first()
    
    if not preco_config:
        raise ValueError(
            f'Tipo de lote {tipo_lote_id} não possui preço configurado '
            f'para a classificação {classificacao}. Configure os preços antes de criar solicitações.'
        )
    
    preco_por_kg = preco_config.preco_por_kg
    valor_total = preco_por_kg * peso_kg
    
    return round(valor_total, 2), estrelas, preco_por_kg

@bp.route('/fornecedores-com-tipos', methods=['GET'])
@jwt_required()
def listar_fornecedores_com_tipos():
    """Lista fornecedores que possuem configuração de tipos de lote"""
    fornecedores = Fornecedor.query.filter_by(ativo=True).all()
    
    resultado = []
    for fornecedor in fornecedores:
        configs = FornecedorTipoLoteClassificacao.query.filter_by(
            fornecedor_id=fornecedor.id,
            ativo=True
        ).all()
        
        if configs:
            tipos_disponiveis = []
            for config in configs:
                tipo_lote = config.tipo_lote
                if tipo_lote:
                    precos = TipoLotePrecoClassificacao.query.filter_by(
                        tipo_lote_id=tipo_lote.id,
                        ativo=True
                    ).all()
                    
                    precos_dict = {}
                    for preco in precos:
                        precos_dict[preco.classificacao] = preco.preco_por_kg
                    
                    tipos_disponiveis.append({
                        'id': config.tipo_lote_id,
                        'nome': tipo_lote.nome,
                        'leve_estrelas': config.leve_estrelas,
                        'medio_estrelas': config.medio_estrelas,
                        'pesado_estrelas': config.pesado_estrelas,
                        'leve_preco': precos_dict.get('leve', 0.0),
                        'medio_preco': precos_dict.get('medio', 0.0),
                        'pesado_preco': precos_dict.get('pesado', 0.0)
                    })
            
            resultado.append({
                'id': fornecedor.id,
                'nome': fornecedor.nome,
                'tipos_lote': tipos_disponiveis
            })
    
    return jsonify(resultado), 200

@bp.route('/analisar-imagem', methods=['POST'])
@jwt_required()
def analisar_imagem():
    """Endpoint para analisar imagem e sugerir classificação"""
    if 'imagem' not in request.files:
        return jsonify({'erro': 'Nenhuma imagem enviada'}), 400
    
    arquivo = request.files['imagem']
    
    if arquivo.filename == '':
        return jsonify({'erro': 'Arquivo inválido'}), 400
    
    filename = secure_filename(f"{uuid.uuid4()}_{arquivo.filename}")
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    arquivo.save(filepath)
    
    classificacao_ia = analisar_imagem_com_ia(filepath)
    
    if classificacao_ia is None:
        return jsonify({
            'imagem_url': f'/uploads/{filename}',
            'classificacao_sugerida': None,
            'aviso': 'IA não disponível. Configure GEMINI_API_KEY para análise automática.'
        }), 200
    
    return jsonify({
        'imagem_url': f'/uploads/{filename}',
        'classificacao_sugerida': classificacao_ia
    }), 200

@bp.route('/criar', methods=['POST'])
@jwt_required()
def criar_solicitacao():
    """Cria uma nova solicitação de compra de lote"""
    usuario_id = get_jwt_identity()
    data = request.get_json()
    
    fornecedor_id = data.get('fornecedor_id')
    tipo_lote_id = data.get('tipo_lote_id')
    classificacao = data.get('classificacao')
    peso_kg = data.get('peso_kg')
    imagem_url = data.get('imagem_url')
    classificacao_ia = data.get('classificacao_sugerida_ia')
    observacoes = data.get('observacoes', '')
    
    if not all([fornecedor_id, tipo_lote_id, classificacao, peso_kg]):
        return jsonify({'erro': 'Dados incompletos'}), 400
    
    if classificacao not in ['leve', 'medio', 'pesado']:
        return jsonify({'erro': 'Classificação inválida. Use: leve, medio ou pesado'}), 400
    
    if peso_kg <= 0:
        return jsonify({'erro': 'Peso deve ser maior que zero'}), 400
    
    fornecedor = Fornecedor.query.get(fornecedor_id)
    tipo_lote = TipoLote.query.get(tipo_lote_id)
    
    if not fornecedor or not tipo_lote:
        return jsonify({'erro': 'Fornecedor ou tipo de lote não encontrado'}), 404
    
    config_existe = FornecedorTipoLoteClassificacao.query.filter_by(
        fornecedor_id=fornecedor_id,
        tipo_lote_id=tipo_lote_id,
        ativo=True
    ).first()
    
    if not config_existe:
        return jsonify({
            'erro': 'Configuração de estrelas não encontrada',
            'mensagem': f'O fornecedor "{fornecedor.nome}" não possui configuração de estrelas '
                       f'para o tipo "{tipo_lote.nome}". '
                       f'Um administrador deve configurar as estrelas antes de criar solicitações.'
        }), 400
    
    try:
        valor_total, estrelas_final, preco_por_kg = calcular_valor_item(
            fornecedor_id, tipo_lote_id, classificacao, peso_kg
        )
    except ValueError as e:
        return jsonify({'erro': str(e)}), 400
    
    if valor_total <= 0:
        return jsonify({
            'erro': 'Valor calculado inválido',
            'mensagem': 'O cálculo resultou em valor zero. Verifique a configuração de estrelas e preços.'
        }), 400
    
    solicitacao = Solicitacao(
        funcionario_id=usuario_id,
        fornecedor_id=fornecedor_id,
        status='aguardando_aprovacao',
        observacoes=observacoes
    )
    
    db.session.add(solicitacao)
    db.session.flush()
    
    item = ItemSolicitacao(
        solicitacao_id=solicitacao.id,
        tipo_lote_id=tipo_lote_id,
        peso_kg=peso_kg,
        classificacao=classificacao,
        classificacao_sugerida_ia=classificacao_ia,
        estrelas_final=estrelas_final,
        valor_calculado=valor_total,
        preco_por_kg_snapshot=preco_por_kg,
        estrelas_snapshot=estrelas_final,
        imagem_url=imagem_url,
        observacoes=observacoes
    )
    
    db.session.add(item)
    db.session.commit()
    
    return jsonify({
        'mensagem': 'Solicitação criada com sucesso',
        'solicitacao': solicitacao.to_dict(),
        'item': item.to_dict()
    }), 201

@bp.route('/aguardando-aprovacao', methods=['GET'])
@jwt_required()
def listar_aguardando_aprovacao():
    """Lista todas as solicitações aguardando aprovação"""
    solicitacoes = Solicitacao.query.filter_by(
        status='aguardando_aprovacao'
    ).order_by(Solicitacao.data_envio.desc()).all()
    
    resultado = []
    for sol in solicitacoes:
        sol_dict = sol.to_dict()
        sol_dict['itens'] = [item.to_dict() for item in sol.itens]
        resultado.append(sol_dict)
    
    return jsonify(resultado), 200

@bp.route('/<int:id>/aprovar', methods=['PUT'])
@admin_required
def aprovar_solicitacao(id):
    """Aprova uma solicitação de compra"""
    usuario_id = get_jwt_identity()
    
    solicitacao = Solicitacao.query.get(id)
    
    if not solicitacao:
        return jsonify({'erro': 'Solicitação não encontrada'}), 404
    
    if solicitacao.status != 'aguardando_aprovacao':
        return jsonify({'erro': 'Apenas solicitações aguardando aprovação podem ser aprovadas'}), 400
    
    solicitacao.status = 'aprovado'
    solicitacao.data_confirmacao = datetime.utcnow()
    solicitacao.admin_id = usuario_id
    
    db.session.commit()
    
    return jsonify({
        'mensagem': 'Solicitação aprovada com sucesso',
        'solicitacao': solicitacao.to_dict()
    }), 200

@bp.route('/<int:id>/rejeitar', methods=['PUT'])
@admin_required
def rejeitar_solicitacao(id):
    """Rejeita uma solicitação de compra"""
    data = request.get_json()
    motivo = data.get('motivo', 'Solicitação rejeitada')
    
    solicitacao = Solicitacao.query.get(id)
    
    if not solicitacao:
        return jsonify({'erro': 'Solicitação não encontrada'}), 404
    
    if solicitacao.status != 'aguardando_aprovacao':
        return jsonify({'erro': 'Apenas solicitações aguardando aprovação podem ser rejeitadas'}), 400
    
    solicitacao.status = 'rejeitado'
    solicitacao.data_confirmacao = datetime.utcnow()
    solicitacao.observacoes = f"{solicitacao.observacoes}\n\nMotivo da rejeição: {motivo}"
    
    db.session.commit()
    
    return jsonify({
        'mensagem': 'Solicitação rejeitada',
        'solicitacao': solicitacao.to_dict()
    }), 200

@bp.route('/aprovadas', methods=['GET'])
@jwt_required()
def listar_aprovadas():
    """Lista todas as solicitações aprovadas aguardando entrada"""
    solicitacoes = Solicitacao.query.filter_by(
        status='aprovado'
    ).order_by(Solicitacao.data_confirmacao.desc()).all()
    
    resultado = []
    for sol in solicitacoes:
        sol_dict = sol.to_dict()
        sol_dict['itens'] = [item.to_dict() for item in sol.itens]
        
        entrada_existente = EntradaEstoque.query.join(Lote).filter(
            Lote.solicitacao_origem_id == sol.id
        ).first()
        sol_dict['tem_entrada'] = entrada_existente is not None
        
        resultado.append(sol_dict)
    
    return jsonify(resultado), 200

@bp.route('/<int:id>/registrar-entrada', methods=['POST'])
@admin_required
def registrar_entrada(id):
    """Registra a entrada física do lote aprovado"""
    usuario_id = get_jwt_identity()
    data = request.get_json()
    
    solicitacao = Solicitacao.query.get(id)
    
    if not solicitacao:
        return jsonify({'erro': 'Solicitação não encontrada'}), 404
    
    if solicitacao.status != 'aprovado':
        return jsonify({'erro': 'Apenas solicitações aprovadas podem ter entrada registrada'}), 400
    
    entrada_existente = EntradaEstoque.query.join(Lote).filter(
        Lote.solicitacao_origem_id == solicitacao.id
    ).first()
    
    if entrada_existente:
        return jsonify({'erro': 'Entrada já registrada para esta solicitação'}), 400
    
    peso_total = sum(item.peso_kg for item in solicitacao.itens)
    valor_total = sum(item.valor_calculado for item in solicitacao.itens)
    
    primeiro_item = solicitacao.itens[0] if solicitacao.itens else None
    if not primeiro_item:
        return jsonify({'erro': 'Solicitação sem itens'}), 400
    
    lote = Lote(
        fornecedor_id=solicitacao.fornecedor_id,
        tipo_lote_id=primeiro_item.tipo_lote_id,
        solicitacao_origem_id=solicitacao.id,
        peso_total_kg=peso_total,
        valor_total=valor_total,
        quantidade_itens=len(solicitacao.itens),
        classificacao_predominante=primeiro_item.classificacao,
        status='aprovado',
        data_aprovacao=datetime.utcnow()
    )
    
    db.session.add(lote)
    db.session.flush()
    
    for item in solicitacao.itens:
        item.lote_id = lote.id
    
    entrada = EntradaEstoque(
        lote_id=lote.id,
        admin_id=usuario_id,
        status='processado',
        data_processamento=datetime.utcnow(),
        observacoes=data.get('observacoes', '')
    )
    
    db.session.add(entrada)
    
    solicitacao.status = 'recebido'
    
    db.session.commit()
    
    return jsonify({
        'mensagem': 'Entrada registrada com sucesso',
        'lote': lote.to_dict(),
        'entrada': entrada.to_dict()
    }), 201

@bp.route('/configuracao/fornecedor/<int:fornecedor_id>/tipo/<int:tipo_lote_id>', methods=['GET', 'PUT'])
@admin_required
def gerenciar_configuracao_classificacao(fornecedor_id, tipo_lote_id):
    """Gerencia configuração de estrelas por classificação para fornecedor e tipo de lote"""
    if request.method == 'GET':
        config = FornecedorTipoLoteClassificacao.query.filter_by(
            fornecedor_id=fornecedor_id,
            tipo_lote_id=tipo_lote_id
        ).first()
        
        if not config:
            return jsonify({
                'fornecedor_id': fornecedor_id,
                'tipo_lote_id': tipo_lote_id,
                'leve_estrelas': 1,
                'medio_estrelas': 3,
                'pesado_estrelas': 5
            }), 200
        
        return jsonify(config.to_dict()), 200
    
    elif request.method == 'PUT':
        data = request.get_json()
        
        config = FornecedorTipoLoteClassificacao.query.filter_by(
            fornecedor_id=fornecedor_id,
            tipo_lote_id=tipo_lote_id
        ).first()
        
        if not config:
            config = FornecedorTipoLoteClassificacao(
                fornecedor_id=fornecedor_id,
                tipo_lote_id=tipo_lote_id
            )
            db.session.add(config)
        
        if 'leve_estrelas' in data:
            config.leve_estrelas = data['leve_estrelas']
        if 'medio_estrelas' in data:
            config.medio_estrelas = data['medio_estrelas']
        if 'pesado_estrelas' in data:
            config.pesado_estrelas = data['pesado_estrelas']
        if 'ativo' in data:
            config.ativo = data['ativo']
        
        config.data_atualizacao = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify(config.to_dict()), 200
