from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models import Fornecedor, Preco, ConfiguracaoPrecoEstrela, Vendedor, db
from app.auth import admin_required

bp = Blueprint('fornecedores', __name__, url_prefix='/api/fornecedores')

def criar_precos_por_estrelas(fornecedor):
    tipos_placas = [
        ('leve', fornecedor.estrelas_leve),
        ('pesada', fornecedor.estrelas_pesada),
        ('media', fornecedor.estrelas_media)
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
            fornecedor_id=fornecedor.id,
            tipo_placa=tipo_placa
        ).first()
        
        if preco_existente:
            preco_existente.preco_por_kg = preco_por_kg
            preco_existente.classificacao_estrelas = estrelas
        else:
            novo_preco = Preco(
                fornecedor_id=fornecedor.id,
                tipo_placa=tipo_placa,
                preco_por_kg=preco_por_kg,
                classificacao_estrelas=estrelas
            )
            db.session.add(novo_preco)
    
    db.session.commit()

@bp.route('', methods=['GET'])
@jwt_required()
def listar_fornecedores():
    busca = request.args.get('busca', '')
    vendedor_id = request.args.get('vendedor_id', type=int)
    cidade = request.args.get('cidade', '')
    forma_pagamento = request.args.get('forma_pagamento', '')
    condicao_pagamento = request.args.get('condicao_pagamento', '')
    
    query = Fornecedor.query
    
    if busca:
        query = query.filter(
            db.or_(
                Fornecedor.nome.ilike(f'%{busca}%'),
                Fornecedor.nome_social.ilike(f'%{busca}%'),
                Fornecedor.cnpj.ilike(f'%{busca}%'),
                Fornecedor.cpf.ilike(f'%{busca}%'),
                Fornecedor.email.ilike(f'%{busca}%')
            )
        )
    
    if vendedor_id:
        query = query.filter_by(vendedor_id=vendedor_id)
    
    if cidade:
        query = query.filter(Fornecedor.cidade.ilike(f'%{cidade}%'))
    
    if forma_pagamento:
        query = query.filter_by(forma_pagamento=forma_pagamento)
    
    if condicao_pagamento:
        query = query.filter_by(condicao_pagamento=condicao_pagamento)
    
    fornecedores = query.order_by(Fornecedor.nome).all()
    return jsonify([fornecedor.to_dict() for fornecedor in fornecedores]), 200

@bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def obter_fornecedor(id):
    fornecedor = Fornecedor.query.get(id)
    
    if not fornecedor:
        return jsonify({'erro': 'Fornecedor não encontrado'}), 404
    
    fornecedor_dict = fornecedor.to_dict()
    fornecedor_dict['precos'] = [preco.to_dict() for preco in fornecedor.precos]
    fornecedor_dict['total_solicitacoes'] = len(fornecedor.solicitacoes)
    fornecedor_dict['total_placas'] = len(fornecedor.placas)
    
    return jsonify(fornecedor_dict), 200

@bp.route('', methods=['POST'])
@admin_required
def criar_fornecedor():
    data = request.get_json()
    
    if not data or not data.get('nome') or not data.get('cnpj'):
        return jsonify({'erro': 'Nome e CNPJ são obrigatórios'}), 400
    
    fornecedor_existente = Fornecedor.query.filter_by(cnpj=data['cnpj']).first()
    if fornecedor_existente:
        return jsonify({'erro': 'CNPJ já cadastrado'}), 400
    
    fornecedor = Fornecedor(
        nome=data['nome'],
        nome_social=data.get('nome_social', ''),
        cnpj=data['cnpj'],
        cpf=data.get('cpf', ''),
        endereco_coleta=data.get('endereco_coleta', ''),
        endereco_emissao=data.get('endereco_emissao', ''),
        rua=data.get('rua', ''),
        numero=data.get('numero', ''),
        cidade=data.get('cidade', ''),
        cep=data.get('cep', ''),
        estado=data.get('estado', ''),
        telefone=data.get('telefone', ''),
        email=data.get('email', ''),
        vendedor_id=data.get('vendedor_id'),
        conta_bancaria=data.get('conta_bancaria', ''),
        agencia=data.get('agencia', ''),
        chave_pix=data.get('chave_pix', ''),
        banco=data.get('banco', ''),
        condicao_pagamento=data.get('condicao_pagamento', 'avista'),
        forma_pagamento=data.get('forma_pagamento', 'pix'),
        observacoes=data.get('observacoes', ''),
        estrelas_leve=data.get('estrelas_leve', 3),
        estrelas_pesada=data.get('estrelas_pesada', 3),
        estrelas_media=data.get('estrelas_media', 3)
    )
    
    db.session.add(fornecedor)
    db.session.commit()
    
    criar_precos_por_estrelas(fornecedor)
    
    return jsonify(fornecedor.to_dict()), 201

@bp.route('/<int:id>', methods=['PUT'])
@admin_required
def atualizar_fornecedor(id):
    fornecedor = Fornecedor.query.get(id)
    
    if not fornecedor:
        return jsonify({'erro': 'Fornecedor não encontrado'}), 404
    
    data = request.get_json()
    
    atualizar_precos = False
    
    if data.get('nome'):
        fornecedor.nome = data['nome']
    if 'nome_social' in data:
        fornecedor.nome_social = data['nome_social']
    if data.get('cnpj'):
        fornecedor.cnpj = data['cnpj']
    if 'cpf' in data:
        fornecedor.cpf = data['cpf']
    if 'endereco_coleta' in data:
        fornecedor.endereco_coleta = data['endereco_coleta']
    if 'endereco_emissao' in data:
        fornecedor.endereco_emissao = data['endereco_emissao']
    if 'rua' in data:
        fornecedor.rua = data['rua']
    if 'numero' in data:
        fornecedor.numero = data['numero']
    if 'cidade' in data:
        fornecedor.cidade = data['cidade']
    if 'cep' in data:
        fornecedor.cep = data['cep']
    if 'estado' in data:
        fornecedor.estado = data['estado']
    if 'telefone' in data:
        fornecedor.telefone = data['telefone']
    if 'email' in data:
        fornecedor.email = data['email']
    if 'vendedor_id' in data:
        fornecedor.vendedor_id = data['vendedor_id']
    if 'conta_bancaria' in data:
        fornecedor.conta_bancaria = data['conta_bancaria']
    if 'agencia' in data:
        fornecedor.agencia = data['agencia']
    if 'chave_pix' in data:
        fornecedor.chave_pix = data['chave_pix']
    if 'banco' in data:
        fornecedor.banco = data['banco']
    if 'condicao_pagamento' in data:
        fornecedor.condicao_pagamento = data['condicao_pagamento']
    if 'forma_pagamento' in data:
        fornecedor.forma_pagamento = data['forma_pagamento']
    if 'observacoes' in data:
        fornecedor.observacoes = data['observacoes']
    
    if 'estrelas_leve' in data:
        fornecedor.estrelas_leve = data['estrelas_leve']
        atualizar_precos = True
    if 'estrelas_pesada' in data:
        fornecedor.estrelas_pesada = data['estrelas_pesada']
        atualizar_precos = True
    if 'estrelas_media' in data:
        fornecedor.estrelas_media = data['estrelas_media']
        atualizar_precos = True
    
    db.session.commit()
    
    if atualizar_precos:
        criar_precos_por_estrelas(fornecedor)
    
    return jsonify(fornecedor.to_dict()), 200

@bp.route('/<int:id>/preco/<string:tipo_placa>', methods=['GET'])
@jwt_required()
def obter_preco_por_kg(id, tipo_placa):
    preco = Preco.query.filter_by(fornecedor_id=id, tipo_placa=tipo_placa).first()
    
    if not preco:
        return jsonify({'erro': 'Preço não encontrado para este tipo de placa'}), 404
    
    return jsonify({
        'preco_por_kg': float(preco.preco_por_kg) if preco.preco_por_kg else 0.0,
        'tipo_placa': tipo_placa,
        'classificacao_estrelas': preco.classificacao_estrelas
    }), 200

@bp.route('/<int:id>/historico', methods=['GET'])
@jwt_required()
def obter_historico_empresa(id):
    empresa = Fornecedor.query.get(id)
    
    if not empresa:
        return jsonify({'erro': 'Fornecedor não encontrada'}), 404
    
    solicitacoes = [s.to_dict() for s in fornecedor.solicitacoes]
    placas = [p.to_dict() for p in fornecedor.placas]
    
    return jsonify({
        'solicitacoes': solicitacoes,
        'placas': placas
    }), 200

@bp.route('/<int:id>', methods=['DELETE'])
@admin_required
def deletar_empresa(id):
    empresa = Fornecedor.query.get(id)
    
    if not empresa:
        return jsonify({'erro': 'Fornecedor não encontrada'}), 404
    
    db.session.delete(fornecedor)
    db.session.commit()
    
    return jsonify({'mensagem': 'Fornecedor deletada com sucesso'}), 200
