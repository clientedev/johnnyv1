from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models import Fornecedor, FornecedorTipoLotePreco, Vendedor, TipoLote, db
from app.auth import admin_required
import requests

bp = Blueprint('fornecedores', __name__, url_prefix='/api/fornecedores')

@bp.route('', methods=['GET'])
@jwt_required()
def listar_fornecedores():
    try:
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
    
    except Exception as e:
        return jsonify({'erro': f'Erro ao listar fornecedores: {str(e)}'}), 500

@bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def obter_fornecedor(id):
    try:
        fornecedor = Fornecedor.query.get(id)
        
        if not fornecedor:
            return jsonify({'erro': 'Fornecedor não encontrado'}), 404
        
        fornecedor_dict = fornecedor.to_dict()
        fornecedor_dict['precos'] = [preco.to_dict() for preco in fornecedor.precos]
        fornecedor_dict['total_solicitacoes'] = len(fornecedor.solicitacoes)
        fornecedor_dict['total_lotes'] = len(fornecedor.lotes)
        
        return jsonify(fornecedor_dict), 200
    
    except Exception as e:
        return jsonify({'erro': f'Erro ao obter fornecedor: {str(e)}'}), 500

@bp.route('', methods=['POST'])
@admin_required
def criar_fornecedor():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'erro': 'Dados não fornecidos'}), 400
        
        if not data.get('nome'):
            return jsonify({'erro': 'Nome é obrigatório'}), 400
        
        if not data.get('cnpj') and not data.get('cpf'):
            return jsonify({'erro': 'CNPJ ou CPF é obrigatório'}), 400
        
        if data.get('cnpj'):
            fornecedor_existente = Fornecedor.query.filter_by(cnpj=data['cnpj']).first()
            if fornecedor_existente:
                return jsonify({'erro': 'CNPJ já cadastrado'}), 400
        
        if data.get('cpf'):
            fornecedor_existente = Fornecedor.query.filter_by(cpf=data['cpf']).first()
            if fornecedor_existente:
                return jsonify({'erro': 'CPF já cadastrado'}), 400
        
        fornecedor = Fornecedor(
            nome=data['nome'],
            nome_social=data.get('nome_social', ''),
            cnpj=data.get('cnpj', ''),
            cpf=data.get('cpf', ''),
            rua=data.get('rua', ''),
            numero=data.get('numero', ''),
            cidade=data.get('cidade', ''),
            cep=data.get('cep', ''),
            estado=data.get('estado', ''),
            bairro=data.get('bairro', ''),
            complemento=data.get('complemento', ''),
            tem_outro_endereco=data.get('tem_outro_endereco', False),
            outro_rua=data.get('outro_rua', ''),
            outro_numero=data.get('outro_numero', ''),
            outro_cidade=data.get('outro_cidade', ''),
            outro_cep=data.get('outro_cep', ''),
            outro_estado=data.get('outro_estado', ''),
            outro_bairro=data.get('outro_bairro', ''),
            outro_complemento=data.get('outro_complemento', ''),
            telefone=data.get('telefone', ''),
            email=data.get('email', ''),
            vendedor_id=data.get('vendedor_id'),
            conta_bancaria=data.get('conta_bancaria', ''),
            agencia=data.get('agencia', ''),
            chave_pix=data.get('chave_pix', ''),
            banco=data.get('banco', ''),
            condicao_pagamento=data.get('condicao_pagamento', 'avista'),
            forma_pagamento=data.get('forma_pagamento', 'pix'),
            observacoes=data.get('observacoes', '')
        )
        
        db.session.add(fornecedor)
        db.session.commit()
        
        if 'precos' in data and isinstance(data['precos'], list):
            for preco_data in data['precos']:
                tipo_lote_id = preco_data.get('tipo_lote_id')
                estrelas = preco_data.get('estrelas', 3)
                preco_kg = preco_data.get('preco_por_kg', 0.0)
                
                if tipo_lote_id and 1 <= estrelas <= 5:
                    tipo_lote = TipoLote.query.get(tipo_lote_id)
                    if tipo_lote:
                        preco_obj = FornecedorTipoLotePreco(
                            fornecedor_id=fornecedor.id,
                            tipo_lote_id=tipo_lote_id,
                            estrelas=estrelas,
                            preco_por_kg=preco_kg
                        )
                        db.session.add(preco_obj)
            
            db.session.commit()
        
        return jsonify(fornecedor.to_dict()), 201
    
    except ValueError as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao criar fornecedor: {str(e)}'}), 500

@bp.route('/<int:id>', methods=['PUT'])
@admin_required
def atualizar_fornecedor(id):
    try:
        fornecedor = Fornecedor.query.get(id)
        
        if not fornecedor:
            return jsonify({'erro': 'Fornecedor não encontrado'}), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({'erro': 'Dados não fornecidos'}), 400
        
        if data.get('nome'):
            fornecedor.nome = data['nome']
        if 'nome_social' in data:
            fornecedor.nome_social = data['nome_social']
        if 'cnpj' in data and data['cnpj']:
            fornecedor.cnpj = data['cnpj']
        if 'cpf' in data and data['cpf']:
            fornecedor.cpf = data['cpf']
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
        if 'bairro' in data:
            fornecedor.bairro = data['bairro']
        if 'complemento' in data:
            fornecedor.complemento = data['complemento']
        if 'tem_outro_endereco' in data:
            fornecedor.tem_outro_endereco = data['tem_outro_endereco']
        if 'outro_rua' in data:
            fornecedor.outro_rua = data['outro_rua']
        if 'outro_numero' in data:
            fornecedor.outro_numero = data['outro_numero']
        if 'outro_cidade' in data:
            fornecedor.outro_cidade = data['outro_cidade']
        if 'outro_cep' in data:
            fornecedor.outro_cep = data['outro_cep']
        if 'outro_estado' in data:
            fornecedor.outro_estado = data['outro_estado']
        if 'outro_bairro' in data:
            fornecedor.outro_bairro = data['outro_bairro']
        if 'outro_complemento' in data:
            fornecedor.outro_complemento = data['outro_complemento']
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
        
        db.session.commit()
        
        return jsonify(fornecedor.to_dict()), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao atualizar fornecedor: {str(e)}'}), 500

@bp.route('/<int:id>', methods=['DELETE'])
@admin_required
def deletar_fornecedor(id):
    try:
        fornecedor = Fornecedor.query.get(id)
        
        if not fornecedor:
            return jsonify({'erro': 'Fornecedor não encontrado'}), 404
        
        db.session.delete(fornecedor)
        db.session.commit()
        
        return jsonify({'mensagem': 'Fornecedor deletado com sucesso'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao deletar fornecedor: {str(e)}'}), 500

@bp.route('/<int:id>/precos', methods=['GET'])
@jwt_required()
def listar_precos_fornecedor(id):
    try:
        fornecedor = Fornecedor.query.get(id)
        
        if not fornecedor:
            return jsonify({'erro': 'Fornecedor não encontrado'}), 404
        
        precos = FornecedorTipoLotePreco.query.filter_by(fornecedor_id=id).all()
        
        precos_agrupados = {}
        for preco in precos:
            tipo_id = preco.tipo_lote_id
            if tipo_id not in precos_agrupados:
                precos_agrupados[tipo_id] = {
                    'tipo_lote_id': tipo_id,
                    'tipo_lote_nome': preco.tipo_lote.nome if preco.tipo_lote else '',
                    'estrelas': {}
                }
            precos_agrupados[tipo_id]['estrelas'][preco.estrelas] = preco.preco_por_kg
        
        return jsonify(list(precos_agrupados.values())), 200
    
    except Exception as e:
        return jsonify({'erro': f'Erro ao listar preços: {str(e)}'}), 500

@bp.route('/<int:id>/precos', methods=['POST'])
@admin_required
def configurar_precos_fornecedor(id):
    try:
        fornecedor = Fornecedor.query.get(id)
        
        if not fornecedor:
            return jsonify({'erro': 'Fornecedor não encontrado'}), 404
        
        data = request.get_json()
        
        if not data or 'precos' not in data:
            return jsonify({'erro': 'Lista de preços não fornecida'}), 400
        
        precos_inseridos = 0
        precos_atualizados = 0
        
        for preco_data in data['precos']:
            tipo_lote_id = preco_data.get('tipo_lote_id')
            estrelas = preco_data.get('estrelas')
            preco_kg = preco_data.get('preco_por_kg', 0.0)
            
            if not tipo_lote_id or not estrelas:
                continue
            
            if not (1 <= estrelas <= 5):
                continue
            
            tipo_lote = TipoLote.query.get(tipo_lote_id)
            if not tipo_lote:
                continue
            
            preco_existente = FornecedorTipoLotePreco.query.filter_by(
                fornecedor_id=id,
                tipo_lote_id=tipo_lote_id,
                estrelas=estrelas
            ).first()
            
            if preco_existente:
                preco_existente.preco_por_kg = preco_kg
                preco_existente.ativo = preco_data.get('ativo', True)
                precos_atualizados += 1
            else:
                novo_preco = FornecedorTipoLotePreco(
                    fornecedor_id=id,
                    tipo_lote_id=tipo_lote_id,
                    estrelas=estrelas,
                    preco_por_kg=preco_kg,
                    ativo=preco_data.get('ativo', True)
                )
                db.session.add(novo_preco)
                precos_inseridos += 1
        
        db.session.commit()
        
        return jsonify({
            'mensagem': 'Preços configurados com sucesso',
            'inseridos': precos_inseridos,
            'atualizados': precos_atualizados
        }), 200
    
    except ValueError as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao configurar preços: {str(e)}'}), 500

@bp.route('/<int:fornecedor_id>/preco/<int:tipo_lote_id>/<int:estrelas>', methods=['GET'])
@jwt_required()
def obter_preco_especifico(fornecedor_id, tipo_lote_id, estrelas):
    try:
        if not (1 <= estrelas <= 5):
            return jsonify({'erro': 'Estrelas deve estar entre 1 e 5'}), 400
        
        preco = FornecedorTipoLotePreco.query.filter_by(
            fornecedor_id=fornecedor_id,
            tipo_lote_id=tipo_lote_id,
            estrelas=estrelas
        ).first()
        
        if not preco:
            return jsonify({'erro': 'Preço não encontrado para esta combinação'}), 404
        
        return jsonify(preco.to_dict()), 200
    
    except Exception as e:
        return jsonify({'erro': f'Erro ao obter preço: {str(e)}'}), 500

@bp.route('/consultar-cnpj/<string:cnpj>', methods=['GET'])
@jwt_required()
def consultar_cnpj(cnpj):
    try:
        cnpj_limpo = cnpj.replace('.', '').replace('/', '').replace('-', '')
        
        if len(cnpj_limpo) != 14:
            return jsonify({'erro': 'CNPJ inválido'}), 400
        
        url = f'https://api.cnpja.com/open/{cnpj_limpo}'
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return jsonify({'erro': 'CNPJ não encontrado na base de dados'}), 404
        
        data = response.json()
        
        empresa_data = {
            'cnpj': data.get('taxId', ''),
            'nome': data.get('alias', data.get('company', {}).get('name', '')),
            'nome_social': data.get('company', {}).get('name', ''),
            'telefone': '',
            'email': data.get('emails', [{}])[0].get('address', '') if data.get('emails') else '',
            'situacao': data.get('status', {}).get('text', ''),
            'data_abertura': data.get('founded', ''),
        }
        
        address = data.get('address', {})
        if address:
            empresa_data['rua'] = f"{address.get('street', '')} {address.get('number', '')}".strip()
            empresa_data['cidade'] = address.get('city', '')
            empresa_data['estado'] = address.get('state', '')
            empresa_data['cep'] = address.get('zip', '')
            empresa_data['bairro'] = address.get('district', '')
            empresa_data['complemento'] = address.get('details', '')
        
        phones = data.get('phones', [])
        if phones:
            phone = phones[0]
            area = phone.get('area', '')
            number = phone.get('number', '')
            empresa_data['telefone'] = f"({area}) {number}" if area and number else ''
        
        empresa_data['atividade_principal'] = ''
        if data.get('mainActivity'):
            main = data.get('mainActivity', {})
            empresa_data['atividade_principal'] = f"{main.get('id', '')} - {main.get('text', '')}"
        
        return jsonify(empresa_data), 200
        
    except requests.Timeout:
        return jsonify({'erro': 'Timeout ao consultar CNPJ. Tente novamente.'}), 504
    except requests.RequestException as e:
        return jsonify({'erro': f'Erro ao consultar API de CNPJ: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'erro': f'Erro ao processar dados do CNPJ: {str(e)}'}), 500
