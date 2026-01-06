from flask import Blueprint, jsonify, request, render_template, send_file, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import (
    db, Usuario, Fornecedor, Lote, ClassificacaoGrade,
    OrdemProducao, ItemSeparadoProducao, BagProducao
)
from app.auth import admin_required
from datetime import datetime
from decimal import Decimal
from io import BytesIO
import pandas as pd
import logging

logger = logging.getLogger(__name__)

MAX_EXPORT_LIMIT = 5000

bp = Blueprint('producao', __name__, url_prefix='/api/producao')


# ============================
# CLASSIFICAÇÕES GRADE
# ============================

@bp.route('/classificacoes', methods=['GET'])
@jwt_required()
def listar_classificacoes():
    """Lista todas as classificações de grade"""
    try:
        categoria = request.args.get('categoria')
        ativo = request.args.get('ativo', 'true').lower() == 'true'

        query = ClassificacaoGrade.query
        if categoria:
            query = query.filter(ClassificacaoGrade.categoria == categoria)
        if ativo is not None:
            query = query.filter(ClassificacaoGrade.ativo == ativo)

        classificacoes = query.order_by(ClassificacaoGrade.categoria, ClassificacaoGrade.nome).all()
        return jsonify([c.to_dict() for c in classificacoes])
    except Exception as e:
        logger.error(f'Erro ao listar classificações: {str(e)}')
        return jsonify({'erro': str(e)}), 500


@bp.route('/classificacoes/<int:id>', methods=['GET'])
@jwt_required()
def obter_classificacao(id):
    """Obtém uma classificação específica"""
    try:
        classificacao = ClassificacaoGrade.query.get_or_404(id)
        return jsonify(classificacao.to_dict())
    except Exception as e:
        logger.error(f'Erro ao obter classificação {id}: {str(e)}')
        return jsonify({'erro': str(e)}), 500


@bp.route('/classificacoes', methods=['POST'])
@jwt_required()
def criar_classificacao():
    """Cria uma nova classificação de grade"""
    try:
        current_user_id = get_jwt_identity()
        usuario = Usuario.query.get(current_user_id)
        if not usuario or usuario.tipo != 'admin':
            return jsonify({'erro': 'Acesso não autorizado'}), 403

        dados = request.get_json()

        existente = ClassificacaoGrade.query.filter_by(nome=dados.get('nome')).first()
        if existente:
            return jsonify({'erro': 'Classificação com este nome já existe'}), 400

        classificacao = ClassificacaoGrade(
            nome=dados.get('nome'),
            categoria=dados.get('categoria', 'HIGH_GRADE'),
            descricao=dados.get('descricao'),
            codigo=dados.get('codigo'),
            preco_estimado_kg=dados.get('preco_estimado_kg', 0),
            is_teste=dados.get('is_teste', False),
            criado_por=current_user_id
        )

        db.session.add(classificacao)
        db.session.commit()

        return jsonify(classificacao.to_dict()), 201
    except ValueError as e:
        logger.error(f'Erro de valor ao criar classificação: {str(e)}')
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erro ao criar classificação: {str(e)}')
        return jsonify({'erro': str(e)}), 500


@bp.route('/classificacoes/<int:id>', methods=['PUT'])
@jwt_required()
def atualizar_classificacao(id):
    """Atualiza uma classificação de grade"""
    try:
        current_user_id = get_jwt_identity()
        usuario = Usuario.query.get(current_user_id)
        if not usuario or usuario.tipo != 'admin':
            return jsonify({'erro': 'Acesso não autorizado'}), 403

        classificacao = ClassificacaoGrade.query.get_or_404(id)
        dados = request.get_json()

        if 'nome' in dados:
            existente = ClassificacaoGrade.query.filter(
                ClassificacaoGrade.nome == dados['nome'],
                ClassificacaoGrade.id != id
            ).first()
            if existente:
                return jsonify({'erro': 'Classificação com este nome já existe'}), 400
            classificacao.nome = dados['nome']

        if 'categoria' in dados:
            classificacao.categoria = dados['categoria']
        if 'descricao' in dados:
            classificacao.descricao = dados['descricao']
        if 'codigo' in dados:
            classificacao.codigo = dados['codigo']
        if 'preco_estimado_kg' in dados:
            classificacao.preco_estimado_kg = dados['preco_estimado_kg']
        if 'ativo' in dados:
            classificacao.ativo = dados['ativo']
        if 'is_teste' in dados:
            classificacao.is_teste = dados['is_teste']

        db.session.commit()
        return jsonify(classificacao.to_dict())
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erro ao atualizar classificação {id}: {str(e)}')
        return jsonify({'erro': str(e)}), 500


@bp.route('/classificacoes/<int:id>', methods=['DELETE'])
@jwt_required()
def deletar_classificacao(id):
    """Deleta uma classificação de grade"""
    try:
        current_user_id = get_jwt_identity()
        usuario = Usuario.query.get(current_user_id)
        if not usuario or usuario.tipo != 'admin':
            return jsonify({'erro': 'Acesso não autorizado'}), 403

        classificacao = ClassificacaoGrade.query.get_or_404(id)

        itens_usando = ItemSeparadoProducao.query.filter_by(classificacao_grade_id=id).count()
        bags_usando = BagProducao.query.filter_by(classificacao_grade_id=id).count()

        if itens_usando > 0 or bags_usando > 0:
            return jsonify({
                'erro': f'Não é possível deletar. Esta classificação está sendo usada em {itens_usando} item(ns) e {bags_usando} bag(s).'
            }), 400

        db.session.delete(classificacao)
        db.session.commit()

        return jsonify({'mensagem': 'Classificação deletada com sucesso'})
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erro ao deletar classificação {id}: {str(e)}')
        return jsonify({'erro': str(e)}), 500


@bp.route('/categorias', methods=['GET'])
@jwt_required()
def listar_categorias():
    """Lista todas as categorias disponíveis (incluindo personalizadas)"""
    try:
        categorias_padrao = ['HIGH_GRADE', 'MID_GRADE', 'LOW_GRADE', 'RESIDUO', 'OUTRO']

        categorias_customizadas = db.session.query(
            ClassificacaoGrade.categoria
        ).distinct().all()

        todas_categorias = set(categorias_padrao)
        for (cat,) in categorias_customizadas:
            if cat:
                todas_categorias.add(cat)

        return jsonify(sorted(list(todas_categorias)))
    except Exception as e:
        logger.error(f'Erro ao listar categorias: {str(e)}')
        return jsonify({'erro': str(e)}), 500


@bp.route('/categorias', methods=['POST'])
@jwt_required()
def criar_categoria():
    """Cria uma nova categoria personalizada"""
    try:
        current_user_id = get_jwt_identity()
        usuario = Usuario.query.get(current_user_id)
        if not usuario or usuario.tipo != 'admin':
            return jsonify({'erro': 'Acesso não autorizado'}), 403

        dados = request.get_json()
        nome_categoria = dados.get('nome', '').strip().upper().replace(' ', '_')

        if not nome_categoria:
            return jsonify({'erro': 'Nome da categoria é obrigatório'}), 400

        return jsonify({'categoria': nome_categoria, 'mensagem': 'Categoria criada com sucesso'})
    except Exception as e:
        logger.error(f'Erro ao criar categoria: {str(e)}')
        return jsonify({'erro': str(e)}), 500


# ============================
# ORDENS DE PRODUÇÃO
# ============================

@bp.route('/ordens', methods=['GET'])
@jwt_required()
def listar_ordens():
    """Lista ordens de produção com filtros"""
    try:
        status = request.args.get('status')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        tipo_material = request.args.get('tipo_material')
        responsavel_id = request.args.get('responsavel_id')

        query = OrdemProducao.query

        if status:
            query = query.filter(OrdemProducao.status == status)
        if data_inicio:
            query = query.filter(OrdemProducao.data_abertura >= datetime.fromisoformat(data_inicio))
        if data_fim:
            query = query.filter(OrdemProducao.data_abertura <= datetime.fromisoformat(data_fim))
        if tipo_material:
            query = query.filter(OrdemProducao.tipo_material.ilike(f'%{tipo_material}%'))
        if responsavel_id:
            query = query.filter(OrdemProducao.responsavel_id == int(responsavel_id))

        ordens = query.order_by(OrdemProducao.data_abertura.desc()).all()
        return jsonify([op.to_dict() for op in ordens])
    except Exception as e:
        logger.error(f'Erro ao listar ordens de produção: {str(e)}')
        return jsonify({'erro': str(e)}), 500


@bp.route('/ordens/<int:id>', methods=['GET'])
@jwt_required()
def obter_ordem(id):
    """Obtém detalhes de uma ordem de produção"""
    try:
        ordem = OrdemProducao.query.get_or_404(id)
        resultado = ordem.to_dict()
        resultado['itens_separados'] = [item.to_dict() for item in ordem.itens_separados]
        return jsonify(resultado)
    except Exception as e:
        logger.error(f'Erro ao obter ordem de produção {id}: {str(e)}')
        return jsonify({'erro': str(e)}), 500


@bp.route('/ordens', methods=['POST'])
@jwt_required()
def criar_ordem():
    """Cria uma nova ordem de produção"""
    try:
        current_user_id = get_jwt_identity()
        dados = request.get_json()

        numero_op = OrdemProducao.gerar_numero_op()

        lotes_ids = dados.get('lotes_ids', [])
        fornecedores_ids = dados.get('fornecedores_ids', [])
        outros_origens = dados.get('outros_origens', [])

        peso_entrada = Decimal(str(dados.get('peso_entrada', 0)))
        if lotes_ids and len(lotes_ids) > 0:
            peso_total_lotes = Decimal('0')
            for lote_id in lotes_ids:
                lote = Lote.query.get(lote_id)
                if lote and lote.peso_liquido:
                    peso_total_lotes += Decimal(str(lote.peso_liquido))
            if peso_total_lotes > 0:
                peso_entrada = peso_total_lotes

        ordem = OrdemProducao(
            numero_op=numero_op,
            origem_tipo=dados.get('origem_tipo'),
            fornecedor_id=dados.get('fornecedor_id'),
            lote_origem_id=dados.get('lote_origem_id'),
            lotes_ids=lotes_ids if lotes_ids else None,
            fornecedores_ids=fornecedores_ids if fornecedores_ids else None,
            outros_origens=outros_origens if outros_origens else None,
            tipo_material=dados.get('tipo_material'),
            descricao_material=dados.get('descricao_material'),
            peso_entrada=peso_entrada,
            custo_total=Decimal(str(dados.get('custo_total', 0))),
            custo_unitario=Decimal(str(dados.get('custo_unitario', 0))),
            responsavel_id=current_user_id,
            observacoes=dados.get('observacoes'),
            status='aberta'
        )

        db.session.add(ordem)
        
        if lotes_ids and len(lotes_ids) > 0:
            for lote_id in lotes_ids:
                lote = Lote.query.get(lote_id)
                if lote:
                    lote.status = 'em_producao'
                    logger.info(f'Lote {lote.numero_lote} marcado como em_producao para OP {numero_op}')
        
        db.session.commit()

        return jsonify(ordem.to_dict()), 201
    except ValueError as e:
        logger.error(f'Erro de valor ao criar ordem de produção: {str(e)}')
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erro ao criar ordem de produção: {str(e)}')
        return jsonify({'erro': str(e)}), 500


@bp.route('/ordens/<int:id>', methods=['PUT'])
@jwt_required()
def atualizar_ordem(id):
    """Atualiza uma ordem de produção"""
    try:
        current_user_id = get_jwt_identity()
        ordem = OrdemProducao.query.get_or_404(id)
        dados = request.get_json()

        if ordem.status == 'finalizada':
            return jsonify({'erro': 'Ordem de produção já finalizada não pode ser alterada'}), 400

        campos_atualizaveis = [
            'tipo_material', 'descricao_material', 'peso_entrada',
            'custo_total', 'custo_unitario', 'observacoes'
        ]

        for campo in campos_atualizaveis:
            if campo in dados:
                if campo in ['peso_entrada', 'custo_total', 'custo_unitario']:
                    setattr(ordem, campo, Decimal(str(dados[campo])))
                else:
                    setattr(ordem, campo, dados[campo])

        db.session.commit()
        return jsonify(ordem.to_dict())
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erro ao atualizar ordem de produção {id}: {str(e)}')
        return jsonify({'erro': str(e)}), 500


@bp.route('/ordens/<int:id>/iniciar-separacao', methods=['POST'])
@jwt_required()
def iniciar_separacao(id):
    """Inicia o processo de separação de uma OP"""
    try:
        ordem = OrdemProducao.query.get_or_404(id)

        if ordem.status != 'aberta':
            return jsonify({'erro': 'Apenas ordens abertas podem iniciar separação'}), 400

        ordem.status = 'em_separacao'
        ordem.data_inicio_separacao = datetime.utcnow()

        db.session.commit()
        return jsonify(ordem.to_dict())
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erro ao iniciar separação da ordem {id}: {str(e)}')
        return jsonify({'erro': str(e)}), 500


@bp.route('/ordens/<int:id>/finalizar', methods=['POST'])
@jwt_required()
def finalizar_ordem(id):
    """Finaliza uma ordem de produção"""
    try:
        current_user_id = get_jwt_identity()
        ordem = OrdemProducao.query.get_or_404(id)
        
        # Tentar obter JSON, mas aceitar requisições sem corpo
        try:
            dados = request.get_json(silent=True) or {}
        except:
            dados = {}

        if ordem.status not in ['aberta', 'em_separacao']:
            return jsonify({'erro': 'Ordem não pode ser finalizada'}), 400

        categorias = set()
        for item in ordem.itens_separados:
            if item.classificacao_grade:
                categorias.add(item.classificacao_grade.categoria)

        categorias_mistas = len(categorias) > 1
        categoria_manual = dados.get('categoria_manual')

        if categorias_mistas and not categoria_manual:
            return jsonify({
                'erro': 'Este bag possui categorias mistas. Por favor, defina uma categoria manual.',
                'categorias_mistas': True,
                'categorias': list(categorias)
            }), 400

        peso_total_separado = sum(float(item.peso_kg) for item in ordem.itens_separados)
        peso_entrada = float(ordem.peso_entrada) if ordem.peso_entrada else 0
        peso_perdas = peso_entrada - peso_total_separado
        percentual_perda = (peso_perdas / peso_entrada * 100) if peso_entrada > 0 else 0

        valor_estimado_total = sum(float(item.valor_estimado or 0) for item in ordem.itens_separados)
        custo_total = float(ordem.custo_total) if ordem.custo_total else 0
        lucro_prejuizo = valor_estimado_total - custo_total

        ordem.peso_total_separado = Decimal(str(peso_total_separado))
        ordem.peso_perdas = Decimal(str(max(0, peso_perdas)))
        ordem.percentual_perda = Decimal(str(max(0, percentual_perda)))
        ordem.valor_estimado_total = Decimal(str(valor_estimado_total))
        ordem.lucro_prejuizo = Decimal(str(lucro_prejuizo))
        ordem.status = 'finalizada'
        ordem.finalizado_por_id = current_user_id
        ordem.data_finalizacao = datetime.utcnow()

        # Atualizar bags conforme o tipo de categoria e marcar como cheio
        bag_ids = set(item.bag_id for item in ordem.itens_separados if item.bag_id)
        for bag_id in bag_ids:
            bag = BagProducao.query.get(bag_id)
            if bag:
                # Marcar bag como cheio quando a OP é finalizada
                if bag.status == 'aberto':
                    bag.status = 'cheio'
                    bag.data_atualizacao = datetime.utcnow()
                
                if categorias_mistas:
                    # Bag com categorias mistas - requer categoria manual
                    if categoria_manual:
                        bag.categoria_manual = categoria_manual
                        bag.categorias_mistas = True
                else:
                    # Bag com categoria única - garantir que está marcado corretamente
                    bag.categorias_mistas = False
                    bag.categoria_manual = None

        db.session.commit()
        return jsonify(ordem.to_dict())
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erro ao finalizar ordem {id}: {str(e)}')
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'erro': f'Erro ao finalizar OP: {str(e)}'}), 500


@bp.route('/ordens/<int:id>/cancelar', methods=['POST'])
@jwt_required()
def cancelar_ordem(id):
    """Cancela uma ordem de produção"""
    try:
        current_user_id = get_jwt_identity()
        usuario = Usuario.query.get(current_user_id)
        if not usuario or usuario.tipo != 'admin':
            return jsonify({'erro': 'Apenas administradores podem cancelar OPs'}), 403

        ordem = OrdemProducao.query.get_or_404(id)

        if ordem.status == 'finalizada':
            return jsonify({'erro': 'Ordem finalizada não pode ser cancelada'}), 400

        ordem.status = 'cancelada'
        db.session.commit()

        return jsonify(ordem.to_dict())
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erro ao cancelar ordem {id}: {str(e)}')
        return jsonify({'erro': str(e)}), 500


# ============================
# ITENS SEPARADOS
# ============================

@bp.route('/ordens/<int:op_id>/itens', methods=['GET'])
@jwt_required()
def listar_itens_ordem(op_id):
    """Lista itens separados de uma OP"""
    try:
        ordem = OrdemProducao.query.get_or_404(op_id)
        return jsonify([item.to_dict() for item in ordem.itens_separados])
    except Exception as e:
        logger.error(f'Erro ao listar itens da ordem {op_id}: {str(e)}')
        return jsonify({'erro': str(e)}), 500


@bp.route('/ordens/<int:op_id>/itens', methods=['POST'])
@jwt_required()
def adicionar_item(op_id):
    """Adiciona um item separado a uma OP"""
    try:
        current_user_id = get_jwt_identity()
        ordem = OrdemProducao.query.get_or_404(op_id)

        if ordem.status not in ['aberta', 'em_separacao']:
            return jsonify({'erro': 'Não é possível adicionar itens a esta OP'}), 400

        dados = request.get_json()
        classificacao = ClassificacaoGrade.query.get(dados.get('classificacao_grade_id'))

        if not classificacao:
            return jsonify({'erro': 'Classificação não encontrada'}), 404

        peso_kg = Decimal(str(dados.get('peso_kg', 0)))
        custo_total = float(ordem.custo_total) if ordem.custo_total else 0
        peso_entrada = float(ordem.peso_entrada) if ordem.peso_entrada else 1
        custo_proporcional = (float(peso_kg) / peso_entrada) * custo_total

        preco_kg = float(classificacao.preco_estimado_kg) if classificacao.preco_estimado_kg else 0
        valor_estimado = float(peso_kg) * preco_kg

        item = ItemSeparadoProducao(
            ordem_producao_id=op_id,
            classificacao_grade_id=dados.get('classificacao_grade_id'),
            nome_item=dados.get('nome_item'),
            peso_kg=peso_kg,
            quantidade=dados.get('quantidade', 1),
            custo_proporcional=Decimal(str(custo_proporcional)),
            valor_estimado=Decimal(str(valor_estimado)),
            separado_por_id=current_user_id,
            observacoes=dados.get('observacoes')
        )

        bag = encontrar_ou_criar_bag(classificacao, current_user_id)
        if bag:
            item.bag_id = bag.id
            bag.peso_acumulado = Decimal(str(float(bag.peso_acumulado or 0) + float(peso_kg)))
            bag.quantidade_itens = (bag.quantidade_itens or 0) + 1

            if ordem.id not in (bag.lotes_origem or []):
                lotes = bag.lotes_origem or []
                lotes.append(ordem.id)
                bag.lotes_origem = lotes

            if float(bag.peso_acumulado) >= float(bag.peso_capacidade_max or 50):
                bag.status = 'cheio'

        if ordem.status == 'aberta':
            ordem.status = 'em_separacao'
            ordem.data_inicio_separacao = datetime.utcnow()

        db.session.add(item)
        db.session.commit()

        return jsonify(item.to_dict()), 201
    except ValueError as e:
        logger.error(f'Erro de valor ao adicionar item na ordem {op_id}: {str(e)}')
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erro ao adicionar item na ordem {op_id}: {str(e)}')
        return jsonify({'erro': str(e)}), 500


@bp.route('/itens/<int:id>', methods=['DELETE'])
@jwt_required()
def remover_item(id):
    """Remove um item separado"""
    try:
        current_user_id = get_jwt_identity()
        usuario = Usuario.query.get(current_user_id)

        item = ItemSeparadoProducao.query.get_or_404(id)
        ordem = item.ordem_producao

        if ordem.status == 'finalizada':
            return jsonify({'erro': 'Não é possível remover itens de OP finalizada'}), 400

        if item.bag:
            bag = item.bag
            bag.peso_acumulado = Decimal(str(max(0, float(bag.peso_acumulado or 0) - float(item.peso_kg))))
            bag.quantidade_itens = max(0, (bag.quantidade_itens or 1) - 1)
            if bag.status == 'cheio':
                bag.status = 'aberto'

        db.session.delete(item)
        db.session.commit()

        return jsonify({'mensagem': 'Item removido com sucesso'})
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erro ao remover item {id}: {str(e)}')
        return jsonify({'erro': str(e)}), 500


# ============================
# BAGS
# ============================

def encontrar_ou_criar_bag(classificacao, usuario_id):
    """Encontra um bag aberto ou cria um novo para a classificação"""
    bag = BagProducao.query.filter(
        BagProducao.classificacao_grade_id == classificacao.id,
        BagProducao.status == 'aberto'
    ).first()

    if not bag:
        codigo = BagProducao.gerar_codigo_bag(classificacao.nome)
        bag = BagProducao(
            codigo=codigo,
            classificacao_grade_id=classificacao.id,
            criado_por_id=usuario_id,
            status='aberto'
        )
        db.session.add(bag)
        db.session.flush()

    return bag


@bp.route('/bags', methods=['GET'])
@jwt_required()
def listar_bags():
    """Lista todos os bags"""
    try:
        status = request.args.get('status')
        classificacao_id = request.args.get('classificacao_id')
        categoria = request.args.get('categoria')

        query = BagProducao.query

        if status:
            query = query.filter(BagProducao.status == status)
        if classificacao_id:
            query = query.filter(BagProducao.classificacao_grade_id == int(classificacao_id))
        if categoria:
            query = query.join(ClassificacaoGrade).filter(ClassificacaoGrade.categoria == categoria)

        bags = query.order_by(BagProducao.data_criacao.desc()).all()
        return jsonify([bag.to_dict() for bag in bags])
    except Exception as e:
        logger.error(f'Erro ao listar bags: {str(e)}')
        return jsonify({'erro': str(e)}), 500


@bp.route('/bags/<int:id>', methods=['GET'])
@jwt_required()
def obter_bag(id):
    """Obtém detalhes de um bag"""
    try:
        bag = BagProducao.query.get_or_404(id)
        resultado = bag.to_dict()
        resultado['itens'] = [item.to_dict() for item in bag.itens]
        return jsonify(resultado)
    except Exception as e:
        logger.error(f'Erro ao obter bag {id}: {str(e)}')
        return jsonify({'erro': str(e)}), 500


@bp.route('/bags/<int:id>/enviar-refinaria', methods=['POST'])
@jwt_required()
def enviar_bag_refinaria(id):
    """Marca um bag como enviado para refinaria"""
    try:
        current_user_id = get_jwt_identity()
        usuario = Usuario.query.get(current_user_id)
        if not usuario or usuario.tipo != 'admin':
            return jsonify({'erro': 'Apenas administradores podem enviar bags para refinaria'}), 403

        bag = BagProducao.query.get_or_404(id)
        dados = request.get_json() or {}

        if bag.status == 'enviado_refinaria':
            return jsonify({'erro': 'Bag já foi enviado para refinaria'}), 400

        bag.status = 'enviado_refinaria'
        bag.data_envio_refinaria = datetime.utcnow()
        bag.enviado_por_id = current_user_id
        bag.numero_remessa = dados.get('numero_remessa')

        db.session.commit()
        return jsonify(bag.to_dict())
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erro ao enviar bag {id} para refinaria: {str(e)}')
        return jsonify({'erro': str(e)}), 500


@bp.route('/bags/<int:id>/devolver-estoque', methods=['POST'])
@jwt_required()
def devolver_bag_estoque(id):
    """Devolve um bag ao estoque ativo"""
    try:
        current_user_id = get_jwt_identity()
        usuario = Usuario.query.get(current_user_id)
        if not usuario or usuario.tipo != 'admin':
            return jsonify({'erro': 'Apenas administradores podem devolver bags ao estoque'}), 403

        bag = BagProducao.query.get_or_404(id)

        if bag.status == 'devolvido_estoque':
            return jsonify({'erro': 'Bag já está no estoque'}), 400

        if bag.status == 'enviado_refinaria':
            return jsonify({'erro': 'Bag já foi enviado para refinaria e não pode ser devolvido'}), 400

        bag.status = 'devolvido_estoque'
        bag.data_atualizacao = datetime.utcnow()

        db.session.commit()
        logger.info(f'Bag {bag.codigo} devolvido ao estoque por {usuario.nome}')
        return jsonify(bag.to_dict())
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erro ao devolver bag {id} ao estoque: {str(e)}')
        return jsonify({'erro': str(e)}), 500


# ============================
# DASHBOARD E RELATÓRIOS
# ============================

@bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard_producao():
    """Retorna dados para o dashboard de produção"""
    try:
        ops_abertas = OrdemProducao.query.filter(OrdemProducao.status.in_(['aberta', 'em_separacao'])).count()
        ops_finalizadas = OrdemProducao.query.filter(OrdemProducao.status == 'finalizada').count()

        total_high_grade = db.session.query(
            db.func.sum(BagProducao.peso_acumulado)
        ).join(ClassificacaoGrade).filter(
            ClassificacaoGrade.categoria == 'HIGH_GRADE',
            BagProducao.status.in_(['aberto', 'cheio'])
        ).scalar() or 0

        total_pronto_refinaria = db.session.query(
            db.func.sum(BagProducao.peso_acumulado)
        ).join(ClassificacaoGrade).filter(
            ClassificacaoGrade.categoria == 'HIGH_GRADE',
            BagProducao.status == 'cheio'
        ).scalar() or 0

        lucro_medio = db.session.query(
            db.func.avg(OrdemProducao.lucro_prejuizo)
        ).filter(
            OrdemProducao.status == 'finalizada',
            OrdemProducao.lucro_prejuizo.isnot(None)
        ).scalar() or 0

        bags_por_categoria = db.session.query(
            ClassificacaoGrade.categoria,
            db.func.count(BagProducao.id).label('quantidade'),
            db.func.sum(BagProducao.peso_acumulado).label('peso_total')
        ).join(ClassificacaoGrade).filter(
            BagProducao.status.in_(['aberto', 'cheio'])
        ).group_by(ClassificacaoGrade.categoria).all()

        return jsonify({
            'ops_abertas': ops_abertas,
            'ops_finalizadas': ops_finalizadas,
            'total_high_grade_kg': float(total_high_grade),
            'total_pronto_refinaria_kg': float(total_pronto_refinaria),
            'lucro_medio_por_op': float(lucro_medio),
            'bags_por_categoria': [
                {'categoria': cat, 'quantidade': qtd, 'peso_total': float(peso or 0)}
                for cat, qtd, peso in bags_por_categoria
            ]
        })
    except Exception as e:
        logger.error(f'Erro ao obter dashboard: {str(e)}')
        return jsonify({'erro': str(e)}), 500


@bp.route('/relatorio-refinaria', methods=['GET'])
@jwt_required()
def relatorio_refinaria():
    """Gera relatório de materiais prontos para refinaria"""
    try:
        bags = BagProducao.query.join(ClassificacaoGrade).filter(
            ClassificacaoGrade.categoria == 'HIGH_GRADE',
            BagProducao.status.in_(['aberto', 'cheio'])
        ).order_by(ClassificacaoGrade.nome).all()

        total_peso = sum(float(bag.peso_acumulado or 0) for bag in bags)

        return jsonify({
            'bags': [bag.to_dict() for bag in bags],
            'total_bags': len(bags),
            'total_peso_kg': total_peso,
            'data_geracao': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f'Erro ao gerar relatório de refinaria: {str(e)}')
        return jsonify({'erro': str(e)}), 500


@bp.route('/fornecedores', methods=['GET'])
@jwt_required()
def listar_fornecedores_producao():
    """Lista fornecedores ativos para seleção na criação de OP"""
    try:
        fornecedores = Fornecedor.query.filter_by(ativo=True).order_by(Fornecedor.nome).all()

        resultado = []
        for f in fornecedores:
            resultado.append({
                'id': f.id,
                'nome': f.nome,
                'cnpj': f.cnpj if f.cnpj else '',
                'cpf': f.cpf if f.cpf else '',
                'documento': f.cnpj if f.cnpj else (f.cpf if f.cpf else 'N/A')
            })

        logger.info(f'Retornando {len(resultado)} fornecedores')
        return jsonify(resultado), 200

    except Exception as e:
        logger.error(f'Erro ao listar fornecedores: {str(e)}')
        return jsonify({'erro': str(e), 'fornecedores': []}), 500


@bp.route('/lotes-estoque', methods=['GET'])
@jwt_required()
def listar_lotes_estoque():
    """Lista lotes disponíveis em estoque para seleção na criação de OP.
    Inclui lotes principais e sublotes (materiais separados) com status ativo.
    """
    try:
        # Status válidos para lotes disponíveis para produção
        # Inclui sublotes criados na separação com status 'CRIADO_SEPARACAO', 'criado_separacao', 'em_estoque'
        status_disponiveis = [
            'em_estoque', 'disponivel', 'aprovado',
            'CRIADO_SEPARACAO', 'criado_separacao', 'Em Estoque'
        ]
        
        # Buscar lotes que estão em estoque e disponíveis (inclui sublotes)
        lotes = Lote.query.filter(
            Lote.status.in_(status_disponiveis),
            Lote.bloqueado == False,
            Lote.reservado == False
        ).order_by(Lote.id.desc()).limit(200).all()

        resultado = []
        for l in lotes:
            tipo_lote_nome = 'N/A'
            if l.tipo_lote:
                tipo_lote_nome = l.tipo_lote.nome

            fornecedor_nome = 'N/A'
            if l.fornecedor:
                fornecedor_nome = l.fornecedor.nome
            
            # Indicar se é sublote
            is_sublote = l.lote_pai_id is not None
            peso = float(l.peso_liquido or l.peso_total_kg or 0)
            
            # Tentar pegar o valor mais preciso possível
            valor_total = 0
            
            if is_sublote:
                # Prioridade 1: Valor total registrado no sublote
                valor_total = float(l.valor_total or 0)
                logger.info(f"DEBUG LOTE {l.numero_lote}: is_sublote=True, valor_total_db={valor_total}")
                
                # Prioridade 2: Itens de separação vinculados diretamente a este sublote
                if valor_total <= 0 and l.itens:
                    valor_total = sum(float(item.valor_calculado or 0) for item in l.itens)
                    logger.info(f"DEBUG LOTE {l.numero_lote}: valor_dos_itens={valor_total}")
                
                # Prioridade 3: Proporcional ao lote pai se o valor acima for 0
                if valor_total <= 0 and l.lote_pai:
                    pai_valor = float(l.lote_pai.valor_total or 0)
                    pai_peso = float(l.lote_pai.peso_total_kg or 1)
                    if pai_peso > 0:
                        valor_total = (peso / pai_peso) * pai_valor
                        logger.info(f"DEBUG LOTE {l.numero_lote}: valor_proporcional_pai={valor_total} (pai_val={pai_valor}, pai_peso={pai_peso})")
                
                # Fallback final: se ainda for 0, tenta buscar nos itens da solicitação do pai
                if valor_total <= 0 and l.lote_pai and l.lote_pai.solicitacao_origem_id:
                    from app.models import ItemSolicitacao
                    itens_solic = ItemSolicitacao.query.filter_by(
                        solicitacao_id=l.lote_pai.solicitacao_origem_id,
                        tipo_lote_id=l.tipo_lote_id
                    ).all()
                    if itens_solic:
                        valor_total = sum(float(item.valor_calculado or 0) for item in itens_solic)
                        # Como é um sublote, aplicamos a proporção do peso se necessário, 
                        # mas aqui vamos considerar o valor total dos itens se for compatível
                        logger.info(f"DEBUG LOTE {l.numero_lote}: valor_itens_solic_pai={valor_total}")
            else:
                # Para lotes principais
                # Prioridade 1: Itens da solicitação original específicos para este tipo de lote
                from app.models import ItemSolicitacao
                itens_solic = ItemSolicitacao.query.filter_by(
                    solicitacao_id=l.solicitacao_origem_id,
                    tipo_lote_id=l.tipo_lote_id
                ).all()
                
                if itens_solic:
                    valor_total = sum(float(item.valor_calculado or 0) for item in itens_solic)
                
                # Prioridade 2: Valor total do lote no banco se não achou itens específicos
                if valor_total == 0:
                    valor_total = float(l.valor_total or 0)

            resultado.append({
                'id': l.id,
                'numero_lote': l.numero_lote,
                'tipo_lote_nome': tipo_lote_nome,
                'peso_liquido': peso,
                'valor_total': round(valor_total, 2),
                'fornecedor_nome': fornecedor_nome,
                'is_sublote': is_sublote,
                'lote_pai_id': l.lote_pai_id,
                'qualidade': l.qualidade_recebida or 'N/A'
            })

        logger.info(f'Retornando {len(resultado)} lotes (incluindo sublotes)')
        return jsonify(resultado), 200

    except Exception as e:
        logger.error(f'Erro ao listar lotes: {str(e)}')
        return jsonify({'erro': str(e), 'lotes': []}), 500


# ============================
# PÁGINAS HTML
# ============================

@bp.route('/', methods=['GET'])
def pagina_producao():
    """Página principal do módulo de produção"""
    return render_template('producao.html')


@bp.route('/ordem/<int:id>', methods=['GET'])
def pagina_ordem(id):
    """Página de detalhes/separação de uma OP"""
    return render_template('producao-ordem.html')


# ============================
# EXPORTAÇÕES
# ============================

@bp.route('/ordens/<int:id>/exportar-html', methods=['GET'])
@admin_required
def exportar_op_html(id):
    """
    Exporta uma Ordem de Produção como HTML para impressão.
    O usuário pode usar Ctrl+P no navegador para salvar como PDF.
    Restrito a administradores.
    """
    try:
        ordem = OrdemProducao.query.get_or_404(id)
        itens = ordem.itens_separados

        responsavel = Usuario.query.get(ordem.responsavel_id) if ordem.responsavel_id else None
        fornecedor = Fornecedor.query.get(ordem.fornecedor_id) if ordem.fornecedor_id else None
        lote_origem = Lote.query.get(ordem.lote_origem_id) if ordem.lote_origem_id else None

        itens_por_categoria = {}
        for item in itens:
            cat = item.classificacao_grade.categoria if item.classificacao_grade else 'SEM CATEGORIA'
            if cat not in itens_por_categoria:
                itens_por_categoria[cat] = []

            bag_codigo = item.bag.codigo if item.bag else 'N/A'
            itens_por_categoria[cat].append({
                'nome': item.nome_item or (item.classificacao_grade.nome if item.classificacao_grade else 'N/A'),
                'peso_kg': float(item.peso_kg or 0),
                'quantidade': item.quantidade or 1,
                'valor_estimado': float(item.valor_estimado or 0),
                'custo_proporcional': float(item.custo_proporcional or 0),
                'bag_codigo': bag_codigo,
                'data_separacao': item.data_separacao.strftime('%d/%m/%Y %H:%M') if item.data_separacao else 'N/A'
            })

        lote_info = f"Lote: {lote_origem.numero_lote}" if lote_origem else "Lote: N/A"

        html_content = f'''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>OP {ordem.numero_op}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; font-size: 12px; }}
        .header {{ text-align: center; margin-bottom: 20px; border-bottom: 2px solid #333; padding-bottom: 10px; }}
        .header h1 {{ margin: 0; color: #333; }}
        .header p {{ margin: 5px 0; color: #666; }}
        .print-btn {{ background: #4CAF50; color: white; padding: 10px 20px; border: none; cursor: pointer; margin: 10px; font-size: 14px; }}
        .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }}
        .info-box {{ border: 1px solid #ddd; padding: 10px; border-radius: 5px; }}
        .info-box h3 {{ margin: 0 0 10px 0; color: #333; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
        .info-row {{ display: flex; justify-content: space-between; margin: 5px 0; }}
        .info-label {{ font-weight: bold; color: #666; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #f5f5f5; font-weight: bold; }}
        .categoria-header {{ background: #333; color: white; font-weight: bold; padding: 10px; margin-top: 15px; }}
        .totals {{ margin-top: 20px; background: #f9f9f9; padding: 15px; border-radius: 5px; }}
        .totals-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; }}
        .total-item {{ text-align: center; }}
        .total-value {{ font-size: 18px; font-weight: bold; color: #333; }}
        .total-label {{ font-size: 11px; color: #666; }}
        .status {{ display: inline-block; padding: 3px 10px; border-radius: 3px; font-weight: bold; }}
        .status-aberta {{ background: #ffeeba; color: #856404; }}
        .status-em_separacao {{ background: #b8daff; color: #004085; }}
        .status-finalizada {{ background: #c3e6cb; color: #155724; }}
        .status-cancelada {{ background: #f5c6cb; color: #721c24; }}
        .footer {{ margin-top: 30px; text-align: center; font-size: 10px; color: #999; border-top: 1px solid #ddd; padding-top: 10px; }}
        @media print {{
            body {{ margin: 0; }}
            .no-print {{ display: none !important; }}
        }}
    </style>
</head>
<body>
    <div class="no-print" style="text-align: center; margin-bottom: 20px;">
        <button class="print-btn" onclick="window.print()">Imprimir / Salvar como PDF</button>
    </div>

    <div class="header">
        <h1>ORDEM DE PRODUÇÃO</h1>
        <p><strong>{ordem.numero_op}</strong></p>
        <p>Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
    </div>

    <div class="info-grid">
        <div class="info-box">
            <h3>Informações Gerais</h3>
            <div class="info-row"><span class="info-label">Status:</span><span class="status status-{ordem.status}">{ordem.status.upper().replace('_', ' ')}</span></div>
            <div class="info-row"><span class="info-label">Data Abertura:</span><span>{ordem.data_abertura.strftime('%d/%m/%Y %H:%M') if ordem.data_abertura else 'N/A'}</span></div>
            <div class="info-row"><span class="info-label">Responsável:</span><span>{responsavel.nome if responsavel else 'N/A'}</span></div>
            <div class="info-row"><span class="info-label">Origem:</span><span>{ordem.origem_tipo or 'N/A'}</span></div>
            <div class="info-row"><span class="info-label">Fornecedor:</span><span>{fornecedor.nome if fornecedor else 'N/A'}</span></div>
            <div class="info-row"><span class="info-label">{lote_info}</span></div>
        </div>
        <div class="info-box">
            <h3>Material</h3>
            <div class="info-row"><span class="info-label">Tipo:</span><span>{ordem.tipo_material or 'N/A'}</span></div>
            <div class="info-row"><span class="info-label">Descrição:</span><span>{ordem.descricao_material or 'N/A'}</span></div>
            <div class="info-row"><span class="info-label">Peso Entrada:</span><span>{float(ordem.peso_entrada or 0):.2f} kg</span></div>
            <div class="info-row"><span class="info-label">Quantidade:</span><span>{ordem.quantidade_entrada or 0}</span></div>
            <div class="info-row"><span class="info-label">Custo Total:</span><span>R$ {float(ordem.custo_total or 0):,.2f}</span></div>
            <div class="info-row"><span class="info-label">Data Finalização:</span><span>{ordem.data_finalizacao.strftime('%d/%m/%Y %H:%M') if ordem.data_finalizacao else 'N/A'}</span></div>
        </div>
    </div>

    <h3>Itens Separados</h3>
'''

        if itens_por_categoria:
            for categoria, lista_itens in itens_por_categoria.items():
                html_content += f'<div class="categoria-header">{categoria}</div>'
                html_content += '''
    <table>
        <thead>
            <tr>
                <th>Item</th>
                <th>Peso (kg)</th>
                <th>Qtd</th>
                <th>Custo Prop.</th>
                <th>Valor Est.</th>
                <th>Bag</th>
                <th>Data Separação</th>
            </tr>
        </thead>
        <tbody>
'''
                for item in lista_itens:
                    html_content += f'''
            <tr>
                <td>{item['nome']}</td>
                <td>{item['peso_kg']:.3f}</td>
                <td>{item['quantidade']}</td>
                <td>R$ {item['custo_proporcional']:,.2f}</td>
                <td>R$ {item['valor_estimado']:,.2f}</td>
                <td>{item['bag_codigo']}</td>
                <td>{item['data_separacao']}</td>
            </tr>
'''
                html_content += '</tbody></table>'
        else:
            html_content += '<p style="color: #666; font-style: italic;">Nenhum item separado ainda.</p>'

        peso_separado = float(ordem.peso_total_separado or 0)
        peso_perdas = float(ordem.peso_perdas or 0)
        percentual_perda = float(ordem.percentual_perda or 0)
        valor_estimado = float(ordem.valor_estimado_total or 0)
        custo_total = float(ordem.custo_total or 0)
        lucro = float(ordem.lucro_prejuizo or 0)

        html_content += f'''
    <div class="totals">
        <h3>Resumo Financeiro</h3>
        <div class="totals-grid">
            <div class="total-item">
                <div class="total-value">{peso_separado:.2f} kg</div>
                <div class="total-label">Peso Total Separado</div>
            </div>
            <div class="total-item">
                <div class="total-value">{peso_perdas:.2f} kg ({percentual_perda:.1f}%)</div>
                <div class="total-label">Perdas</div>
            </div>
            <div class="total-item">
                <div class="total-value">R$ {valor_estimado:,.2f}</div>
                <div class="total-label">Valor Estimado Total</div>
            </div>
            <div class="total-item">
                <div class="total-value">R$ {custo_total:,.2f}</div>
                <div class="total-label">Custo Total</div>
            </div>
            <div class="total-item">
                <div class="total-value" style="color: {'green' if lucro >= 0 else 'red'}">R$ {lucro:,.2f}</div>
                <div class="total-label">{'Lucro' if lucro >= 0 else 'Prejuízo'}</div>
            </div>
        </div>
    </div>

    <div class="footer">
        <p>MRX System - Gestão de Compras de Sucata Eletrônica</p>
        <p>Este documento foi gerado automaticamente pelo sistema.</p>
        <p>Para salvar como PDF: Use Ctrl+P e selecione "Salvar como PDF" como destino.</p>
    </div>
</body>
</html>
'''

        return Response(
            html_content,
            mimetype='text/html',
            headers={
                'Content-Disposition': f'inline; filename=OP_{ordem.numero_op}.html'
            }
        )
    except Exception as e:
        logger.error(f'Erro ao exportar OP para HTML: {str(e)}')
        return jsonify({'erro': str(e)}), 500


@bp.route('/exportar-high-grade-excel', methods=['GET'])
@admin_required
def exportar_high_grade_excel():
    """
    Exporta inventário High Grade para Excel.
    Restrito a administradores. Limitado a MAX_EXPORT_LIMIT registros.
    Inclui: lotes de origem, números de remessa, datas completas.
    """
    try:
        limite = min(int(request.args.get('limite', MAX_EXPORT_LIMIT)), MAX_EXPORT_LIMIT)

        bags = BagProducao.query.join(ClassificacaoGrade).filter(
            ClassificacaoGrade.categoria == 'HIGH_GRADE',
            BagProducao.status.in_(['aberto', 'cheio', 'enviado_refinaria'])
        ).order_by(ClassificacaoGrade.nome, BagProducao.data_criacao.desc()).limit(limite).all()

        dados = []
        for bag in bags:
            classificacao = bag.classificacao_grade
            criado_por = Usuario.query.get(bag.criado_por_id) if bag.criado_por_id else None
            enviado_por = Usuario.query.get(bag.enviado_por_id) if bag.enviado_por_id else None

            lotes_str = ''
            if bag.lotes_origem:
                op_ids = bag.lotes_origem if isinstance(bag.lotes_origem, list) else []
                ordens = OrdemProducao.query.filter(OrdemProducao.id.in_(op_ids)).all()
                lotes_str = ', '.join([op.numero_op for op in ordens])

            dados.append({
                'Código Bag': bag.codigo,
                'Classificação': classificacao.nome if classificacao else 'N/A',
                'Categoria': classificacao.categoria if classificacao else 'N/A',
                'Peso Acumulado (kg)': float(bag.peso_acumulado or 0),
                'Quantidade Itens': bag.quantidade_itens or 0,
                'Status': bag.status,
                'Peso Capacidade Máx (kg)': float(bag.peso_capacidade_max or 50),
                'Preço Estimado/kg (R$)': float(classificacao.preco_estimado_kg or 0) if classificacao else 0,
                'Valor Estimado Total (R$)': float(bag.peso_acumulado or 0) * float(classificacao.preco_estimado_kg or 0) if classificacao else 0,
                'Lotes de Origem (OPs)': lotes_str,
                'Data Criação': bag.data_criacao.strftime('%d/%m/%Y %H:%M') if bag.data_criacao else '',
                'Criado Por': criado_por.nome if criado_por else 'N/A',
                'Data Envio Refinaria': bag.data_envio_refinaria.strftime('%d/%m/%Y %H:%M') if bag.data_envio_refinaria else '',
                'Enviado Por': enviado_por.nome if enviado_por else '',
                'Número Remessa': bag.numero_remessa or ''
            })

        df = pd.DataFrame(dados)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Inventário High Grade')
        output.seek(0)

        filename = f'inventario_high_grade_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f'Erro ao exportar High Grade para Excel: {str(e)}')
        return jsonify({'erro': str(e)}), 500


@bp.route('/exportar-relatorio-refinaria-excel', methods=['GET'])
@admin_required
def exportar_relatorio_refinaria_excel():
    """
    Exporta relatório de materiais prontos para refinaria em Excel.
    Restrito a administradores. Limitado a MAX_EXPORT_LIMIT registros.
    Inclui totais consolidados.
    """
    try:
        limite = min(int(request.args.get('limite', MAX_EXPORT_LIMIT)), MAX_EXPORT_LIMIT)

        bags = BagProducao.query.join(ClassificacaoGrade).filter(
            ClassificacaoGrade.categoria == 'HIGH_GRADE',
            BagProducao.status.in_(['aberto', 'cheio'])
        ).order_by(ClassificacaoGrade.nome).limit(limite).all()

        dados = []
        for bag in bags:
            classificacao = bag.classificacao_grade
            valor_estimado = float(bag.peso_acumulado or 0) * float(classificacao.preco_estimado_kg or 0) if classificacao else 0

            lotes_str = ''
            if bag.lotes_origem:
                op_ids = bag.lotes_origem if isinstance(bag.lotes_origem, list) else []
                ordens = OrdemProducao.query.filter(OrdemProducao.id.in_(op_ids)).all()
                lotes_str = ', '.join([op.numero_op for op in ordens])

            dados.append({
                'Código Bag': bag.codigo,
                'Classificação': classificacao.nome if classificacao else 'N/A',
                'Peso (kg)': float(bag.peso_acumulado or 0),
                'Quantidade Itens': bag.quantidade_itens or 0,
                'Status': 'Pronto' if bag.status == 'cheio' else 'Em Preenchimento',
                'Preço/kg (R$)': float(classificacao.preco_estimado_kg or 0) if classificacao else 0,
                'Valor Estimado (R$)': valor_estimado,
                'Lotes de Origem (OPs)': lotes_str,
                'Data Criação': bag.data_criacao.strftime('%d/%m/%Y %H:%M') if bag.data_criacao else ''
            })

        df = pd.DataFrame(dados)

        total_peso = df['Peso (kg)'].sum() if len(df) > 0 else 0
        total_valor = df['Valor Estimado (R$)'].sum() if len(df) > 0 else 0
        total_itens = df['Quantidade Itens'].sum() if len(df) > 0 else 0

        dados.append({
            'Código Bag': '',
            'Classificação': 'TOTAL',
            'Peso (kg)': total_peso,
            'Quantidade Itens': total_itens,
            'Status': '',
            'Preço/kg (R$)': '',
            'Valor Estimado (R$)': total_valor,
            'Lotes de Origem (OPs)': '',
            'Data Criação': f'Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}'
        })

        df = pd.DataFrame(dados)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Pronto para Refinaria')
        output.seek(0)

        filename = f'relatorio_refinaria_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f'Erro ao exportar relatório de refinaria para Excel: {str(e)}')
        return jsonify({'erro': str(e)}), 500