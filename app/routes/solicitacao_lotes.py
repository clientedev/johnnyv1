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
    """Analisa imagem usando Gemini AI para classificar lote e fornecer justificativa"""
    try:
        import google.genai as genai
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("AVISO: GEMINI_API_KEY não configurada")
            return None
        
        client = genai.Client(api_key=api_key)
        
        with open(imagem_path, 'rb') as f:
            image_data = f.read()
        
        prompt = """Analise esta imagem de placas eletrônicas e classifique o lote baseado na densidade e quantidade de componentes.

CRITÉRIOS DE CLASSIFICAÇÃO:
- LEVE: Placas com poucos componentes, circuitos simples, baixa densidade, muito cobre/área verde visível
- MEDIO: Placas com quantidade moderada de componentes, complexidade média, densidade balanceada
- PESADO: Placas densamente povoadas com muitos componentes, circuitos complexos, alta densidade

FORMATO DE RESPOSTA (obrigatório):
Classificação: [LEVE ou MEDIO ou PESADO]
Justificativa: [Descreva em 1-2 frases o que você observou na imagem que levou a esta classificação]

Exemplo:
Classificação: LEVE
Justificativa: A placa apresenta poucos componentes SMD e muita área de cobre exposta, indicando baixa densidade de componentes e circuito simples."""

        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=[prompt, {'mime_type': 'image/jpeg', 'data': base64.b64encode(image_data).decode()}]
        )
        
        resposta_texto = response.text.strip()
        
        classificacao = None
        justificativa = ""
        
        linhas = resposta_texto.split('\n')
        for linha in linhas:
            if 'Classificação:' in linha or 'Classificacao:' in linha:
                class_parte = linha.split(':', 1)[1].strip().lower()
                if 'leve' in class_parte:
                    classificacao = 'leve'
                elif 'medio' in class_parte or 'média' in class_parte:
                    classificacao = 'medio'
                elif 'pesado' in class_parte or 'pesada' in class_parte:
                    classificacao = 'pesado'
            elif 'Justificativa:' in linha:
                justificativa = linha.split(':', 1)[1].strip()
        
        if not classificacao or classificacao not in ['leve', 'medio', 'pesado']:
            print(f"AVISO: IA retornou classificação inválida. Resposta: {resposta_texto}")
            return {
                'classificacao': 'medio',
                'justificativa': 'Classificação padrão aplicada (IA retornou resposta inválida)',
                'resposta_bruta': resposta_texto
            }
        
        if not justificativa:
            justificativa = "A IA classificou esta placa mas não forneceu justificativa detalhada."
        
        return {
            'classificacao': classificacao,
            'justificativa': justificativa,
            'resposta_bruta': resposta_texto
        }
        
    except Exception as e:
        print(f"ERRO ao analisar imagem com IA: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def calcular_valor_item(fornecedor_id, tipo_lote_id, classificacao, peso_kg):
    """Calcula o valor do item baseado na classificação e configuração do fornecedor
    
    Fluxo:
    1. Busca configuração de classificação (leve/médio/pesado → estrelas)
    2. Busca preço por kg baseado nas estrelas do fornecedor
    3. Calcula valor total = preço_por_kg * peso_kg
    
    Raises:
        ValueError: Se não houver configuração de classificação ou preço para este fornecedor/tipo
    """
    from app.models import FornecedorTipoLotePreco
    
    config_class = FornecedorTipoLoteClassificacao.query.filter_by(
        fornecedor_id=fornecedor_id,
        tipo_lote_id=tipo_lote_id,
        ativo=True
    ).first()
    
    if not config_class:
        raise ValueError(
            f'Fornecedor {fornecedor_id} não possui configuração de estrelas '
            f'para o tipo de lote {tipo_lote_id}. Configure as estrelas por classificação antes de criar solicitações.'
        )
    
    estrelas = config_class.get_estrelas_por_classificacao(classificacao)
    
    preco_fornecedor = FornecedorTipoLotePreco.query.filter_by(
        fornecedor_id=fornecedor_id,
        tipo_lote_id=tipo_lote_id,
        estrelas=estrelas,
        ativo=True
    ).first()
    
    if not preco_fornecedor:
        raise ValueError(
            f'Fornecedor {fornecedor_id} não possui preço configurado para {estrelas} estrelas '
            f'no tipo de lote {tipo_lote_id}. Configure os preços por estrela antes de criar solicitações.'
        )
    
    preco_por_kg = preco_fornecedor.preco_por_kg
    valor_total = preco_por_kg * peso_kg
    
    return round(valor_total, 2), estrelas, preco_por_kg

@bp.route('/fornecedores-com-tipos', methods=['GET'])
@jwt_required()
def listar_fornecedores_com_tipos():
    """Lista fornecedores que possuem configuração de tipos de lote com preços"""
    from app.models import FornecedorTipoLotePreco
    fornecedores = Fornecedor.query.filter_by(ativo=True).all()
    
    resultado = []
    for fornecedor in fornecedores:
        precos_fornecedor = FornecedorTipoLotePreco.query.filter_by(
            fornecedor_id=fornecedor.id,
            ativo=True
        ).all()
        
        if precos_fornecedor:
            tipos_dict = {}
            for preco in precos_fornecedor:
                tipo_id = preco.tipo_lote_id
                if tipo_id not in tipos_dict:
                    tipos_dict[tipo_id] = {
                        'id': tipo_id,
                        'nome': preco.tipo_lote.nome if preco.tipo_lote else '',
                        'precos_estrelas': {}
                    }
                tipos_dict[tipo_id]['precos_estrelas'][preco.estrelas] = preco.preco_por_kg
            
            tipos_list = list(tipos_dict.values())
            
            resultado.append({
                'id': fornecedor.id,
                'nome': fornecedor.nome,
                'tipos_lote': tipos_list
            })
    
    return jsonify(resultado), 200

@bp.route('/precos/<int:fornecedor_id>/<int:tipo_lote_id>', methods=['GET'])
@jwt_required()
def buscar_precos(fornecedor_id, tipo_lote_id):
    """Busca todos os preços (1-5 estrelas) para um fornecedor e tipo de lote"""
    from app.models import FornecedorTipoLotePreco
    
    precos = FornecedorTipoLotePreco.query.filter_by(
        fornecedor_id=fornecedor_id,
        tipo_lote_id=tipo_lote_id,
        ativo=True
    ).order_by(FornecedorTipoLotePreco.estrelas).all()
    
    if not precos:
        return jsonify({
            'erro': 'Nenhum preço configurado',
            'mensagem': 'Este fornecedor não possui preços configurados para este tipo de lote.'
        }), 404
    
    precos_dict = {}
    for preco in precos:
        precos_dict[preco.estrelas] = {
            'estrelas': preco.estrelas,
            'preco_por_kg': preco.preco_por_kg
        }
    
    return jsonify({
        'fornecedor_id': fornecedor_id,
        'tipo_lote_id': tipo_lote_id,
        'precos': precos_dict
    }), 200

@bp.route('/analisar-imagem', methods=['POST'])
@jwt_required()
def analisar_imagem():
    """Endpoint para analisar imagem e sugerir classificação com justificativa"""
    if 'imagem' not in request.files:
        return jsonify({'erro': 'Nenhuma imagem enviada'}), 400
    
    arquivo = request.files['imagem']
    
    if arquivo.filename == '':
        return jsonify({'erro': 'Arquivo inválido'}), 400
    
    filename = secure_filename(f"{uuid.uuid4()}_{arquivo.filename}")
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    arquivo.save(filepath)
    
    resultado_ia = analisar_imagem_com_ia(filepath)
    
    if resultado_ia is None:
        return jsonify({
            'imagem_url': f'/uploads/{filename}',
            'classificacao_sugerida': None,
            'justificativa_ia': None,
            'aviso': 'IA não disponível. Configure GEMINI_API_KEY para análise automática.'
        }), 200
    
    return jsonify({
        'imagem_url': f'/uploads/{filename}',
        'classificacao_sugerida': resultado_ia['classificacao'],
        'justificativa_ia': resultado_ia['justificativa'],
        'resposta_completa': resultado_ia.get('resposta_bruta', '')
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
    estrelas = data.get('estrelas', 3)
    peso_kg = data.get('peso_kg')
    imagem_url = data.get('imagem_url')
    classificacao_ia = data.get('classificacao_sugerida_ia')
    justificativa_ia = data.get('justificativa_ia')
    estrelas_sugeridas_ia = data.get('estrelas_sugeridas_ia')
    observacoes = data.get('observacoes', '')
    
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    endereco = data.get('endereco', '')
    rua = data.get('rua', '')
    numero = data.get('numero', '')
    cep = data.get('cep', '')
    
    if not all([fornecedor_id, tipo_lote_id, classificacao, peso_kg]):
        return jsonify({'erro': 'Dados incompletos'}), 400
    
    if classificacao not in ['leve', 'medio', 'pesado']:
        return jsonify({'erro': 'Classificação inválida. Use: leve, medio ou pesado'}), 400
    
    if peso_kg <= 0:
        return jsonify({'erro': 'Peso deve ser maior que zero'}), 400
    
    if estrelas < 1 or estrelas > 5:
        return jsonify({'erro': 'Estrelas deve estar entre 1 e 5'}), 400
    
    fornecedor = Fornecedor.query.get(fornecedor_id)
    tipo_lote = TipoLote.query.get(tipo_lote_id)
    
    if not fornecedor or not tipo_lote:
        return jsonify({'erro': 'Fornecedor ou tipo de lote não encontrado'}), 404
    
    from app.models import FornecedorTipoLotePreco
    preco_config = FornecedorTipoLotePreco.query.filter_by(
        fornecedor_id=fornecedor_id,
        tipo_lote_id=tipo_lote_id,
        estrelas=estrelas,
        ativo=True
    ).first()
    
    if not preco_config:
        return jsonify({
            'erro': 'Preço não configurado',
            'mensagem': f'O fornecedor "{fornecedor.nome}" não possui preço configurado '
                       f'para o tipo "{tipo_lote.nome}" com {estrelas} estrelas. '
                       f'Um administrador deve configurar os preços antes de criar solicitações.'
        }), 400
    
    preco_por_kg = preco_config.preco_por_kg
    valor_total = round(preco_por_kg * peso_kg, 2)
    
    if valor_total <= 0:
        return jsonify({
            'erro': 'Valor calculado inválido',
            'mensagem': 'O cálculo resultou em valor zero. Verifique a configuração de preços.'
        }), 400
    
    solicitacao = Solicitacao(
        funcionario_id=usuario_id,
        fornecedor_id=fornecedor_id,
        status='aguardando_aprovacao',
        observacoes=observacoes,
        localizacao_lat=latitude,
        localizacao_lng=longitude,
        endereco_completo=endereco,
        rua=rua,
        numero=numero,
        cep=cep
    )
    
    db.session.add(solicitacao)
    db.session.flush()
    
    item = ItemSolicitacao(
        solicitacao_id=solicitacao.id,
        tipo_lote_id=tipo_lote_id,
        peso_kg=peso_kg,
        classificacao=classificacao,
        classificacao_sugerida_ia=classificacao_ia,
        justificativa_ia=justificativa_ia,
        estrelas_sugeridas_ia=estrelas_sugeridas_ia,
        estrelas_final=estrelas,
        valor_calculado=valor_total,
        preco_por_kg_snapshot=preco_por_kg,
        estrelas_snapshot=estrelas,
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
