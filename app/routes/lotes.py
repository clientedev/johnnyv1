from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Lote, TipoLote, Fornecedor, OrdemCompra, OrdemServico, ConferenciaRecebimento
from sqlalchemy.orm import joinedload
from datetime import datetime

bp = Blueprint('lotes', __name__, url_prefix='/api/lotes')

@bp.route('', methods=['GET'])
@jwt_required()
def listar_lotes():
    status = request.args.get('status')
    fornecedor_id = request.args.get('fornecedor_id', type=int)
    tipo_material = request.args.get('tipo_material')

    query = Lote.query

    if status:
        query = query.filter_by(status=status)

    if fornecedor_id:
        query = query.filter_by(fornecedor_id=fornecedor_id)

    if tipo_material:
        query = query.filter_by(tipo_material=tipo_material)

    lotes = query.order_by(Lote.data_criacao.desc()).all()

    return jsonify([lote.to_dict() for lote in lotes]), 200

@bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def obter_lote(id):
    try:
        lote = Lote.query.options(
            joinedload(Lote.tipo_lote),
            joinedload(Lote.fornecedor),
            joinedload(Lote.ordem_compra),
            joinedload(Lote.ordem_servico),
            joinedload(Lote.conferencia),
            joinedload(Lote.itens),
            joinedload(Lote.entrada_estoque),
            joinedload(Lote.separacao),
            joinedload(Lote.solicitacao_origem)
        ).filter_by(id=id).first()

        if not lote:
            return jsonify({'erro': 'Lote não encontrado'}), 404

        # Preparar dados completos do lote usando o método to_dict() que já existe
        lote_data = lote.to_dict()

        # Adicionar informações dos itens
        if lote.itens:
            lote_data['itens'] = [item.to_dict() for item in lote.itens]
        else:
            lote_data['itens'] = []

        # Adicionar entrada de estoque se existir
        if lote.entrada_estoque:
            lote_data['entrada_estoque'] = {
                'id': lote.entrada_estoque.id,
                'status': lote.entrada_estoque.status,
                'data_entrada': lote.entrada_estoque.data_entrada.isoformat() if lote.entrada_estoque.data_entrada else None
            }

        # Adicionar separação se existir
        if lote.separacao:
            lote_data['separacao'] = {
                'id': lote.separacao.id,
                'status': lote.separacao.status,
                'percentual_aproveitamento': lote.separacao.percentual_aproveitamento
            }

        # Adicionar conferência se existir
        if lote.conferencia:
            lote_data['conferencia'] = {
                'id': lote.conferencia.id,
                'conferencia_status': lote.conferencia.conferencia_status,
                'peso_real': lote.conferencia.peso_real,
                'qualidade': lote.conferencia.qualidade
            }

        # Adicionar ordem de compra se existir
        if lote.ordem_compra:
            lote_data['ordem_compra'] = {
                'id': lote.ordem_compra.id,
                'status': lote.ordem_compra.status,
                'valor_total': lote.ordem_compra.valor_total
            }

        # Adicionar ordem de serviço se existir
        if lote.ordem_servico:
            lote_data['ordem_servico'] = {
                'id': lote.ordem_servico.id,
                'numero_os': lote.ordem_servico.numero_os,
                'status': lote.ordem_servico.status
            }

        return jsonify(lote_data), 200

    except Exception as e:
        print(f"❌ Erro ao obter lote {id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'erro': f'Erro ao carregar detalhes do lote: {str(e)}'}), 500

@bp.route('/<int:id>/aprovar', methods=['PUT'])
@admin_required
def aprovar_lote(id):
    usuario_id = get_jwt_identity()

    lote = Lote.query.get(id)

    if not lote:
        return jsonify({'erro': 'Lote não encontrado'}), 404

    if lote.status != 'aberto':
        return jsonify({'erro': 'Apenas lotes com status "aberto" podem ser aprovados'}), 400

    lote.status = 'aprovado'
    lote.data_fechamento = datetime.utcnow()

    compra = Compra(
        lote_id=lote.id,
        fornecedor_id=lote.fornecedor_id,
        material=f"{lote.tipo_material.capitalize()} - {lote.numero_lote}",
        peso_total_kg=lote.peso_total_kg,
        valor_total=lote.valor_total,
        status='pendente'
    )

    db.session.add(compra)
    db.session.commit()

    return jsonify({
        'lote': lote.to_dict(),
        'compra': compra.to_dict()
    }), 200

@bp.route('/<int:id>/rejeitar', methods=['PUT'])
@admin_required
def rejeitar_lote(id):
    data = request.get_json()

    lote = Lote.query.get(id)

    if not lote:
        return jsonify({'erro': 'Lote não encontrado'}), 404

    if lote.status != 'aberto':
        return jsonify({'erro': 'Apenas lotes com status "aberto" podem ser rejeitados'}), 400

    lote.status = 'rejeitado'
    lote.data_fechamento = datetime.utcnow()
    lote.observacoes = data.get('observacoes', 'Lote rejeitado')

    for placa in lote.placas:
        placa.status = 'reprovada'
        placa.lote_id = None

    db.session.commit()

    return jsonify(lote.to_dict()), 200

@bp.route('/estatisticas', methods=['GET'])
@jwt_required()
def obter_estatisticas():
    total_abertos = Lote.query.filter_by(status='aberto').count()
    total_aprovados = Lote.query.filter_by(status='aprovado').count()
    total_rejeitados = Lote.query.filter_by(status='rejeitado').count()

    peso_total = db.session.query(db.func.sum(Lote.peso_total_kg)).filter_by(status='aprovado').scalar() or 0
    valor_total = db.session.query(db.func.sum(Lote.valor_total)).filter_by(status='aprovado').scalar() or 0

    return jsonify({
        'lotes_abertos': total_abertos,
        'lotes_aprovados': total_aprovados,
        'lotes_rejeitados': total_rejeitados,
        'peso_total_kg': float(peso_total),
        'valor_total': float(valor_total)
    }), 200