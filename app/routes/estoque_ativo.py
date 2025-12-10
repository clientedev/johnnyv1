from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Lote, BagProducao, ItemSeparadoProducao, ClassificacaoGrade
from sqlalchemy.orm import joinedload, selectinload
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('estoque_ativo', __name__, url_prefix='/api/estoque-ativo')

LOTES_ATIVOS_STATUS = ['em_estoque', 'disponivel', 'aprovado', 'em_producao']

@bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard_estoque_ativo():
    try:
        lotes_ativos = Lote.query.filter(
            Lote.status.in_(LOTES_ATIVOS_STATUS),
            Lote.bloqueado == False,
            Lote.lote_pai_id == None
        ).count()

        em_producao = Lote.query.filter(
            Lote.status == 'em_producao',
            Lote.bloqueado == False
        ).count()

        bags_estoque = BagProducao.query.filter(
            BagProducao.status.in_(['devolvido_estoque', 'cheio', 'aberto'])
        ).count()

        peso_total_lotes = db.session.query(
            db.func.sum(db.func.coalesce(Lote.peso_liquido, Lote.peso_total_kg))
        ).filter(
            Lote.status.in_(LOTES_ATIVOS_STATUS),
            Lote.bloqueado == False,
            Lote.lote_pai_id == None
        ).scalar() or 0

        peso_total_bags = db.session.query(
            db.func.sum(BagProducao.peso_acumulado)
        ).filter(
            BagProducao.status.in_(['devolvido_estoque', 'cheio'])
        ).scalar() or 0

        return jsonify({
            'lotes_ativos': lotes_ativos,
            'em_producao': em_producao,
            'bags_estoque': bags_estoque,
            'peso_total': float(peso_total_lotes) + float(peso_total_bags)
        })
    except Exception as e:
        logger.error(f'Erro ao carregar dashboard estoque ativo: {str(e)}')
        return jsonify({'erro': str(e)}), 500


@bp.route('/lotes', methods=['GET'])
@jwt_required()
def listar_lotes_ativos():
    try:
        status = request.args.get('status')
        
        query = Lote.query.options(
            joinedload(Lote.tipo_lote),
            joinedload(Lote.fornecedor),
            selectinload(Lote.sublotes)
        ).filter(
            Lote.bloqueado == False,
            Lote.lote_pai_id == None
        )

        if status:
            query = query.filter(Lote.status == status)
        else:
            query = query.filter(Lote.status.in_(LOTES_ATIVOS_STATUS))

        lotes = query.order_by(Lote.data_criacao.desc()).limit(200).all()

        resultado = []
        for lote in lotes:
            lote_dict = lote.to_dict()
            
            sublotes_data = []
            if lote.sublotes:
                for sublote in lote.sublotes:
                    sublote_dict = sublote.to_dict()
                    sublotes_data.append(sublote_dict)
            
            lote_dict['sublotes'] = sublotes_data
            resultado.append(lote_dict)

        return jsonify(resultado)
    except Exception as e:
        logger.error(f'Erro ao listar lotes ativos: {str(e)}')
        return jsonify({'erro': str(e)}), 500


@bp.route('/bags', methods=['GET'])
@jwt_required()
def listar_bags_estoque():
    try:
        status = request.args.get('status')
        categoria = request.args.get('categoria')
        
        query = BagProducao.query.options(
            joinedload(BagProducao.classificacao_grade),
            joinedload(BagProducao.criado_por)
        )

        if status:
            query = query.filter(BagProducao.status == status)
        else:
            query = query.filter(BagProducao.status.in_(['devolvido_estoque', 'cheio', 'aberto', 'enviado_refinaria']))

        if categoria:
            query = query.join(ClassificacaoGrade).filter(ClassificacaoGrade.categoria == categoria)

        bags = query.order_by(BagProducao.data_criacao.desc()).limit(200).all()

        resultado = []
        for bag in bags:
            bag_dict = bag.to_dict()
            
            itens = ItemSeparadoProducao.query.filter_by(bag_id=bag.id).all()
            itens_data = []
            tem_lotes_origem = False
            
            for item in itens:
                item_dict = item.to_dict()
                itens_data.append(item_dict)
                if item.ordem_producao_id:
                    tem_lotes_origem = True
            
            bag_dict['itens'] = itens_data
            bag_dict['origem_lotes'] = tem_lotes_origem
            resultado.append(bag_dict)

        return jsonify(resultado)
    except Exception as e:
        logger.error(f'Erro ao listar bags do estoque: {str(e)}')
        return jsonify({'erro': str(e)}), 500


@bp.route('/lotes/<int:lote_id>/sublotes', methods=['GET'])
@jwt_required()
def obter_sublotes(lote_id):
    try:
        lote = Lote.query.get_or_404(lote_id)
        
        sublotes = Lote.query.options(
            joinedload(Lote.tipo_lote),
            joinedload(Lote.fornecedor)
        ).filter_by(lote_pai_id=lote_id).all()
        
        resultado = [sublote.to_dict() for sublote in sublotes]
        return jsonify(resultado)
    except Exception as e:
        logger.error(f'Erro ao obter sublotes do lote {lote_id}: {str(e)}')
        return jsonify({'erro': str(e)}), 500


@bp.route('/bags/<int:bag_id>/itens', methods=['GET'])
@jwt_required()
def obter_itens_bag(bag_id):
    try:
        bag = BagProducao.query.get_or_404(bag_id)
        
        itens = ItemSeparadoProducao.query.options(
            joinedload(ItemSeparadoProducao.classificacao_grade),
            joinedload(ItemSeparadoProducao.ordem_producao)
        ).filter_by(bag_id=bag_id).all()
        
        resultado = [item.to_dict() for item in itens]
        return jsonify(resultado)
    except Exception as e:
        logger.error(f'Erro ao obter itens do bag {bag_id}: {str(e)}')
        return jsonify({'erro': str(e)}), 500
