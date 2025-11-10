from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models import Fornecedor, FornecedorTipoLotePreco, FornecedorTipoLoteClassificacao, Vendedor, TipoLote, db
from app.auth import admin_required
import requests
import re

bp = Blueprint('fornecedores', __name__, url_prefix='/api/fornecedores')

def normalizar_cnpj(cnpj):
    if not cnpj:
        return None
    return re.sub(r'[^\d]', '', cnpj)

def normalizar_cpf(cpf):
    if not cpf:
        return None
    return re.sub(r'[^\d]', '', cpf)

def validar_cnpj(cnpj):
    cnpj = normalizar_cnpj(cnpj)
    if not cnpj or len(cnpj) != 14:
        return False
    if cnpj == cnpj[0] * 14:
        return False
    return True

def validar_cpf(cpf):
    cpf = normalizar_cpf(cpf)
    if not cpf or len(cpf) != 11:
        return False
    if cpf == cpf[0] * 11:
        return False
    return True

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
        fornecedor_dict['classificacoes'] = [classif.to_dict() for classif in fornecedor.classificacoes_tipo_lote]
        fornecedor_dict['precos'] = [preco.to_dict() for preco in fornecedor.precos]
        fornecedor_dict['total_solicitacoes'] = len(fornecedor.solicitacoes)
        fornecedor_dict['total_lotes'] = len(fornecedor.lotes)
        
        return jsonify(fornecedor_dict), 200
    
    except Exception as e:
        return jsonify({'erro': f'Erro ao obter fornecedor: {str(e)}'}), 500

@bp.route('', methods=['POST'])
@jwt_required()
def criar_fornecedor():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'erro': 'Dados não fornecidos'}), 400
        
        if not data.get('nome'):
            return jsonify({'erro': 'Nome é obrigatório'}), 400
        
        if not data.get('cnpj') and not data.get('cpf'):
            return jsonify({'erro': 'CNPJ ou CPF é obrigatório'}), 400
        
        cnpj_normalizado = None
        cpf_normalizado = None
        
        if data.get('cnpj'):
            cnpj_normalizado = normalizar_cnpj(data['cnpj'])
            if not validar_cnpj(cnpj_normalizado):
                return jsonify({'erro': 'CNPJ inválido'}), 400
            
            fornecedor_existente = Fornecedor.query.filter_by(cnpj=cnpj_normalizado).first()
            if fornecedor_existente:
                return jsonify({'erro': 'CNPJ já cadastrado'}), 400
        
        if data.get('cpf'):
            cpf_normalizado = normalizar_cpf(data['cpf'])
            if not validar_cpf(cpf_normalizado):
                return jsonify({'erro': 'CPF inválido'}), 400
            
            fornecedor_existente = Fornecedor.query.filter_by(cpf=cpf_normalizado).first()
            if fornecedor_existente:
                return jsonify({'erro': 'CPF já cadastrado'}), 400
        
        if data.get('email'):
            email_existente = Fornecedor.query.filter_by(email=data['email']).first()
            if email_existente:
                return jsonify({'erro': 'E-mail já cadastrado para outro fornecedor'}), 400
        
        fornecedor = Fornecedor(
            nome=data['nome'],
            nome_social=data.get('nome_social', ''),
            cnpj=cnpj_normalizado,
            cpf=cpf_normalizado,
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
        
        # Processar tipos de lote selecionados com classificações (leve/médio/pesado)
        if 'tipos_lote' in data and isinstance(data['tipos_lote'], list):
            for tipo_data in data['tipos_lote']:
                tipo_lote_id = tipo_data.get('tipo_lote_id')
                leve = tipo_data.get('leve_estrelas', 1)
                medio = tipo_data.get('medio_estrelas', 3)
                pesado = tipo_data.get('pesado_estrelas', 5)
                
                if tipo_lote_id:
                    tipo_lote = TipoLote.query.get(tipo_lote_id)
                    if tipo_lote:
                        classif_obj = FornecedorTipoLoteClassificacao(
                            fornecedor_id=fornecedor.id,
                            tipo_lote_id=tipo_lote_id,
                            leve_estrelas=leve,
                            medio_estrelas=medio,
                            pesado_estrelas=pesado
                        )
                        db.session.add(classif_obj)
            
            db.session.commit()
        
        # Processar preços (campo antigo, mantido para compatibilidade)
        elif 'precos' in data and isinstance(data['precos'], list):
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
@jwt_required()
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
            cnpj_normalizado = normalizar_cnpj(data['cnpj'])
            if not validar_cnpj(cnpj_normalizado):
                return jsonify({'erro': 'CNPJ inválido'}), 400
            if cnpj_normalizado != fornecedor.cnpj:
                existente = Fornecedor.query.filter_by(cnpj=cnpj_normalizado).first()
                if existente:
                    return jsonify({'erro': 'CNPJ já cadastrado para outro fornecedor'}), 400
                fornecedor.cnpj = cnpj_normalizado
        
        if 'cpf' in data and data['cpf']:
            cpf_normalizado = normalizar_cpf(data['cpf'])
            if not validar_cpf(cpf_normalizado):
                return jsonify({'erro': 'CPF inválido'}), 400
            if cpf_normalizado != fornecedor.cpf:
                existente = Fornecedor.query.filter_by(cpf=cpf_normalizado).first()
                if existente:
                    return jsonify({'erro': 'CPF já cadastrado para outro fornecedor'}), 400
                fornecedor.cpf = cpf_normalizado
        
        if 'email' in data and data['email']:
            if data['email'] != fornecedor.email:
                email_existente = Fornecedor.query.filter_by(email=data['email']).first()
                if email_existente:
                    return jsonify({'erro': 'E-mail já cadastrado para outro fornecedor'}), 400
                fornecedor.email = data['email']
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
        
        # Atualizar tipos de lote selecionados com classificações (leve/médio/pesado)
        if 'tipos_lote' in data and isinstance(data['tipos_lote'], list):
            # Remover classificações antigas
            FornecedorTipoLoteClassificacao.query.filter_by(fornecedor_id=fornecedor.id).delete()
            FornecedorTipoLotePreco.query.filter_by(fornecedor_id=fornecedor.id).delete()
            
            # Adicionar novas classificações
            for tipo_data in data['tipos_lote']:
                tipo_lote_id = tipo_data.get('tipo_lote_id')
                leve = tipo_data.get('leve_estrelas', 1)
                medio = tipo_data.get('medio_estrelas', 3)
                pesado = tipo_data.get('pesado_estrelas', 5)
                
                if tipo_lote_id:
                    tipo_lote = TipoLote.query.get(tipo_lote_id)
                    if tipo_lote:
                        classif_obj = FornecedorTipoLoteClassificacao(
                            fornecedor_id=fornecedor.id,
                            tipo_lote_id=tipo_lote_id,
                            leve_estrelas=leve,
                            medio_estrelas=medio,
                            pesado_estrelas=pesado
                        )
                        db.session.add(classif_obj)
        
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
        cnpj_limpo = normalizar_cnpj(cnpj)
        
        if not validar_cnpj(cnpj_limpo):
            return jsonify({'erro': 'CNPJ inválido. Verifique o número digitado.'}), 400
        
        fornecedor_existente = Fornecedor.query.filter_by(cnpj=cnpj_limpo).first()
        if fornecedor_existente:
            return jsonify({
                'erro': 'CNPJ já cadastrado',
                'fornecedor': fornecedor_existente.to_dict()
            }), 409
        
        empresa_data = None
        apis = [
            {
                'name': 'BrasilAPI',
                'url': f'https://brasilapi.com.br/api/cnpj/v1/{cnpj_limpo}',
                'parser': lambda data: {
                    'cnpj': cnpj_limpo,
                    'nome': data.get('nome_fantasia', '') or data.get('razao_social', ''),
                    'nome_social': data.get('razao_social', ''),
                    'telefone': data.get('ddd_telefone_1', ''),
                    'email': data.get('email', ''),
                    'rua': data.get('descricao_tipo_logradouro', '') + ' ' + data.get('logradouro', ''),
                    'numero': data.get('numero', ''),
                    'cidade': data.get('municipio', ''),
                    'estado': data.get('uf', ''),
                    'cep': data.get('cep', '').replace('.', '').replace('-', ''),
                    'bairro': data.get('bairro', ''),
                    'complemento': data.get('complemento', ''),
                }
            },
            {
                'name': 'OpenCNPJ',
                'url': f'https://opencnpj.org/{cnpj_limpo}',
                'parser': lambda data: {
                    'cnpj': cnpj_limpo,
                    'nome': data.get('nome_fantasia', '') or data.get('razao_social', ''),
                    'nome_social': data.get('razao_social', ''),
                    'telefone': data.get('ddd_telefone_1', ''),
                    'email': data.get('email', ''),
                    'rua': data.get('descricao_tipo_logradouro', '') + ' ' + data.get('logradouro', ''),
                    'numero': data.get('numero', ''),
                    'cidade': data.get('municipio', ''),
                    'estado': data.get('uf', ''),
                    'cep': data.get('cep', '').replace('.', '').replace('-', ''),
                    'bairro': data.get('bairro', ''),
                    'complemento': data.get('complemento', ''),
                }
            },
            {
                'name': 'ReceitaWS',
                'url': f'https://receitaws.com.br/v1/cnpj/{cnpj_limpo}',
                'parser': lambda data: {
                    'cnpj': cnpj_limpo,
                    'nome': data.get('fantasia', '') or data.get('nome', ''),
                    'nome_social': data.get('nome', ''),
                    'telefone': data.get('telefone', ''),
                    'email': data.get('email', ''),
                    'rua': data.get('logradouro', ''),
                    'numero': data.get('numero', ''),
                    'cidade': data.get('municipio', ''),
                    'estado': data.get('uf', ''),
                    'cep': data.get('cep', '').replace('.', '').replace('-', ''),
                    'bairro': data.get('bairro', ''),
                    'complemento': data.get('complemento', ''),
                }
            }
        ]
        
        for api in apis:
            try:
                response = requests.get(api['url'], timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'error' in data or data.get('status') == 'ERROR':
                        continue
                    
                    empresa_data = api['parser'](data)
                    break
                    
            except (requests.Timeout, requests.ConnectionError, requests.RequestException):
                continue
        
        if not empresa_data:
            return jsonify({'erro': 'CNPJ não encontrado. Preencha os dados manualmente.'}), 404
        
        return jsonify(empresa_data), 200
        
    except Exception as e:
        return jsonify({'erro': f'Erro ao processar dados do CNPJ: {str(e)}'}), 500
