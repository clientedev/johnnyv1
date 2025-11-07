from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models import db, Empresa, Preco, ConfiguracaoPrecoEstrela, Vendedor
from app.auth import admin_required

bp = Blueprint('empresas', __name__, url_prefix='/api/empresas')

def criar_precos_por_estrelas(empresa):
    tipos_placas = [
        ('leve', empresa.estrelas_leve),
        ('pesada', empresa.estrelas_pesada),
        ('media', empresa.estrelas_media)
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
    busca = request.args.get('busca', '')
    vendedor_id = request.args.get('vendedor_id', type=int)
    cidade = request.args.get('cidade', '')
    forma_pagamento = request.args.get('forma_pagamento', '')
    condicao_pagamento = request.args.get('condicao_pagamento', '')
    
    query = Empresa.query
    
    if busca:
        query = query.filter(
            db.or_(
                Empresa.nome.ilike(f'%{busca}%'),
                Empresa.nome_social.ilike(f'%{busca}%'),
                Empresa.cnpj.ilike(f'%{busca}%'),
                Empresa.cpf.ilike(f'%{busca}%'),
                Empresa.email.ilike(f'%{busca}%')
            )
        )
    
    if vendedor_id:
        query = query.filter_by(vendedor_id=vendedor_id)
    
    if cidade:
        query = query.filter(Empresa.cidade.ilike(f'%{cidade}%'))
    
    if forma_pagamento:
        query = query.filter_by(forma_pagamento=forma_pagamento)
    
    if condicao_pagamento:
        query = query.filter_by(condicao_pagamento=condicao_pagamento)
    
    empresas = query.order_by(Empresa.nome).all()
    return jsonify([empresa.to_dict() for empresa in empresas]), 200

@bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def obter_empresa(id):
    empresa = Empresa.query.get(id)
    
    if not empresa:
        return jsonify({'erro': 'Empresa não encontrada'}), 404
    
    empresa_dict = empresa.to_dict()
    empresa_dict['precos'] = [preco.to_dict() for preco in empresa.precos]
    empresa_dict['total_solicitacoes'] = len(empresa.solicitacoes)
    empresa_dict['total_placas'] = len(empresa.placas)
    
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
    if 'nome_social' in data:
        empresa.nome_social = data['nome_social']
    if data.get('cnpj'):
        empresa.cnpj = data['cnpj']
    if 'cpf' in data:
        empresa.cpf = data['cpf']
    if 'endereco_coleta' in data:
        empresa.endereco_coleta = data['endereco_coleta']
    if 'endereco_emissao' in data:
        empresa.endereco_emissao = data['endereco_emissao']
    if 'rua' in data:
        empresa.rua = data['rua']
    if 'numero' in data:
        empresa.numero = data['numero']
    if 'cidade' in data:
        empresa.cidade = data['cidade']
    if 'cep' in data:
        empresa.cep = data['cep']
    if 'estado' in data:
        empresa.estado = data['estado']
    if 'telefone' in data:
        empresa.telefone = data['telefone']
    if 'email' in data:
        empresa.email = data['email']
    if 'vendedor_id' in data:
        empresa.vendedor_id = data['vendedor_id']
    if 'conta_bancaria' in data:
        empresa.conta_bancaria = data['conta_bancaria']
    if 'agencia' in data:
        empresa.agencia = data['agencia']
    if 'chave_pix' in data:
        empresa.chave_pix = data['chave_pix']
    if 'banco' in data:
        empresa.banco = data['banco']
    if 'condicao_pagamento' in data:
        empresa.condicao_pagamento = data['condicao_pagamento']
    if 'forma_pagamento' in data:
        empresa.forma_pagamento = data['forma_pagamento']
    if 'observacoes' in data:
        empresa.observacoes = data['observacoes']
    
    if 'estrelas_leve' in data:
        empresa.estrelas_leve = data['estrelas_leve']
        atualizar_precos = True
    if 'estrelas_pesada' in data:
        empresa.estrelas_pesada = data['estrelas_pesada']
        atualizar_precos = True
    if 'estrelas_media' in data:
        empresa.estrelas_media = data['estrelas_media']
        atualizar_precos = True
    
    db.session.commit()
    
    if atualizar_precos:
        criar_precos_por_estrelas(empresa)
    
    return jsonify(empresa.to_dict()), 200

@bp.route('/<int:id>/preco/<string:tipo_placa>', methods=['GET'])
@jwt_required()
def obter_preco_por_kg(id, tipo_placa):
    preco = Preco.query.filter_by(empresa_id=id, tipo_placa=tipo_placa).first()
    
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
    empresa = Empresa.query.get(id)
    
    if not empresa:
        return jsonify({'erro': 'Empresa não encontrada'}), 404
    
    solicitacoes = [s.to_dict() for s in empresa.solicitacoes]
    placas = [p.to_dict() for p in empresa.placas]
    
    return jsonify({
        'solicitacoes': solicitacoes,
        'placas': placas
    }), 200

@bp.route('/<int:id>', methods=['DELETE'])
@admin_required
def deletar_empresa(id):
    empresa = Empresa.query.get(id)
    
    if not empresa:
        return jsonify({'erro': 'Empresa não encontrada'}), 404
    
    db.session.delete(empresa)
    db.session.commit()
    
    return jsonify({'mensagem': 'Empresa deletada com sucesso'}), 200
