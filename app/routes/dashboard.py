from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.models import db, Fornecedor, Solicitacao, Lote, EntradaEstoque, FornecedorTipoLotePreco, ItemSolicitacao
from app.auth import admin_required
from sqlalchemy import func
from datetime import datetime

bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@bp.route('/stats', methods=['GET'])
@admin_required
def obter_estatisticas():
    total_pendentes = Solicitacao.query.filter_by(status='pendente').count()
    total_aprovados = Solicitacao.query.filter_by(status='aprovada').count()
    total_rejeitados = Solicitacao.query.filter_by(status='rejeitada').count()
    
    total_lotes = Lote.query.count()
    lotes_abertos = Lote.query.filter_by(status='aberto').count()
    lotes_aprovados = Lote.query.filter_by(status='aprovado').count()
    
    peso_total = db.session.query(func.sum(Lote.peso_total_kg)).scalar() or 0
    valor_total = db.session.query(func.sum(Lote.valor_total)).scalar() or 0
    
    ranking_fornecedores = db.session.query(
        Fornecedor.nome,
        func.count(Lote.id).label('total_lotes'),
        func.sum(Lote.valor_total).label('valor_total')
    ).join(Lote).group_by(
        Fornecedor.id, Fornecedor.nome
    ).order_by(func.sum(Lote.valor_total).desc()).limit(5).all()
    
    ranking = [{
        'nome': nome, 
        'total_lotes': int(total), 
        'valor_total': round(float(valor) if valor else 0, 2)
    } for nome, total, valor in ranking_fornecedores]
    
    return jsonify({
        'solicitacoes': {
            'pendentes': total_pendentes,
            'aprovadas': total_aprovados,
            'rejeitadas': total_rejeitados
        },
        'lotes': {
            'total': total_lotes,
            'abertos': lotes_abertos,
            'aprovados': lotes_aprovados
        },
        'peso_total_kg': round(float(peso_total), 2),
        'valor_total': round(float(valor_total), 2),
        'ranking_fornecedores': ranking
    }), 200
