from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.models import db, Fornecedor, Solicitacao, Lote, EntradaEstoque, FornecedorTipoLotePreco, ItemSolicitacao, TipoLote
from app.auth import admin_required
from sqlalchemy import func, extract
from datetime import datetime, timedelta

bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@bp.route('/stats', methods=['GET'])
@admin_required
def obter_estatisticas():
    """Retorna estatísticas gerais do sistema"""
    # Estatísticas de Solicitações/Relatórios
    total_pendentes = Solicitacao.query.filter_by(status='pendente').count()
    total_aprovados = Solicitacao.query.filter_by(status='aprovada').count()
    total_reprovados = Solicitacao.query.filter_by(status='rejeitada').count()
    
    # Valor total de lotes aprovados
    valor_total = db.session.query(func.sum(Lote.valor_total)).filter(
        Lote.status == 'aprovado'
    ).scalar() or 0
    
    # Quilos por tipo de lote
    quilos_leve = db.session.query(func.sum(Lote.peso_total_kg)).join(
        TipoLote, Lote.tipo_lote_id == TipoLote.id
    ).filter(
        TipoLote.classificacao == 'leve'
    ).scalar() or 0
    
    quilos_media = db.session.query(func.sum(Lote.peso_total_kg)).join(
        TipoLote, Lote.tipo_lote_id == TipoLote.id
    ).filter(
        TipoLote.classificacao == 'media'
    ).scalar() or 0
    
    quilos_pesada = db.session.query(func.sum(Lote.peso_total_kg)).join(
        TipoLote, Lote.tipo_lote_id == TipoLote.id
    ).filter(
        TipoLote.classificacao == 'pesada'
    ).scalar() or 0
    
    # Ranking de fornecedores (top 10)
    ranking = db.session.query(
        Fornecedor.id,
        Fornecedor.nome,
        func.count(Solicitacao.id).label('total')
    ).join(
        Solicitacao, Solicitacao.fornecedor_id == Fornecedor.id
    ).filter(
        Solicitacao.status == 'aprovada'
    ).group_by(
        Fornecedor.id, Fornecedor.nome
    ).order_by(
        func.count(Solicitacao.id).desc()
    ).limit(10).all()
    
    ranking_empresas = [
        {
            'id': r.id,
            'nome': r.nome,
            'total': r.total
        } for r in ranking
    ]
    
    return jsonify({
        'relatorios': {
            'pendentes': total_pendentes,
            'aprovados': total_aprovados,
            'reprovados': total_reprovados
        },
        'valor_total': float(valor_total),
        'quilos_por_tipo': {
            'leve': float(quilos_leve),
            'media': float(quilos_media),
            'pesada': float(quilos_pesada)
        },
        'ranking_empresas': ranking_empresas
    }), 200

@bp.route('/grafico-mensal', methods=['GET'])
@admin_required
def obter_grafico_mensal():
    """Retorna dados de movimentação mensal para gráficos"""
    from dateutil.relativedelta import relativedelta
    
    # Últimos 6 meses
    hoje = datetime.now()
    meses = []
    dados = []
    
    # Nome do mês em português
    nomes_meses = ['', 'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 
                  'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    
    for i in range(5, -1, -1):
        # Calcular o mês corretamente usando relativedelta
        mes_data = hoje - relativedelta(months=i)
        mes_num = mes_data.month
        ano = mes_data.year
        
        meses.append(nomes_meses[mes_num])
        
        # Calcular início e fim do mês para filtro correto
        inicio_mes = datetime(ano, mes_num, 1)
        if mes_num == 12:
            fim_mes = datetime(ano + 1, 1, 1)
        else:
            fim_mes = datetime(ano, mes_num + 1, 1)
        
        # Contar solicitações aprovadas no mês usando range de datas
        count = Solicitacao.query.filter(
            Solicitacao.data_envio >= inicio_mes,
            Solicitacao.data_envio < fim_mes,
            Solicitacao.status == 'aprovada'
        ).count()
        
        dados.append(count)
    
    return jsonify({
        'labels': meses,
        'data': dados
    }), 200
