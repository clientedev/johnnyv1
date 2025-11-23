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

@bp.route('/gastos-comprador', methods=['GET'])
@admin_required
def obter_gastos_comprador():
    """Retorna gastos por comprador com filtro de período"""
    from dateutil.relativedelta import relativedelta
    from sqlalchemy import and_
    
    periodo = request.args.get('periodo', 'mes')  # dia, semana, mes, ano
    
    hoje = datetime.now()
    
    if periodo == 'dia':
        data_inicio = datetime(hoje.year, hoje.month, hoje.day, 0, 0, 0)
    elif periodo == 'semana':
        data_inicio = hoje - timedelta(days=7)
    elif periodo == 'mes':
        data_inicio = hoje - relativedelta(months=1)
    else:  # ano
        data_inicio = hoje - relativedelta(years=1)
    
    # Buscar gastos por comprador
    from app.models import Usuario, OrdemCompra
    
    gastos = db.session.query(
        Usuario.id,
        Usuario.nome,
        func.count(OrdemCompra.id).label('total_ocs'),
        func.sum(OrdemCompra.valor_total).label('valor_total'),
        func.avg(OrdemCompra.valor_total).label('ticket_medio')
    ).join(
        OrdemCompra, OrdemCompra.criado_por == Usuario.id
    ).filter(
        and_(
            OrdemCompra.criado_em >= data_inicio,
            OrdemCompra.status.in_(['aprovada', 'em_analise'])
        )
    ).group_by(
        Usuario.id, Usuario.nome
    ).order_by(
        func.sum(OrdemCompra.valor_total).desc()
    ).all()
    
    return jsonify({
        'periodo': periodo,
        'compradores': [
            {
                'id': g.id,
                'nome': g.nome,
                'total_ocs': g.total_ocs,
                'valor_total': float(g.valor_total or 0),
                'ticket_medio': float(g.ticket_medio or 0)
            } for g in gastos
        ]
    }), 200

@bp.route('/gastos-diarios', methods=['GET'])
@admin_required
def obter_gastos_diarios():
    """Retorna gastos diários dos últimos 30 dias"""
    from dateutil.relativedelta import relativedelta
    from app.models import OrdemCompra
    
    hoje = datetime.now()
    data_inicio = hoje - timedelta(days=30)
    
    # Buscar OCs dos últimos 30 dias
    ocs = OrdemCompra.query.filter(
        OrdemCompra.criado_em >= data_inicio,
        OrdemCompra.status.in_(['aprovada', 'em_analise'])
    ).all()
    
    # Agrupar por dia
    gastos_por_dia = {}
    for oc in ocs:
        dia = oc.criado_em.strftime('%Y-%m-%d')
        if dia not in gastos_por_dia:
            gastos_por_dia[dia] = 0
        gastos_por_dia[dia] += float(oc.valor_total or 0)
    
    # Ordenar por data
    labels = sorted(gastos_por_dia.keys())
    valores = [gastos_por_dia[dia] for dia in labels]
    
    # Formatar labels para exibição
    labels_formatados = [datetime.strptime(d, '%Y-%m-%d').strftime('%d/%m') for d in labels]
    
    return jsonify({
        'labels': labels_formatados,
        'valores': valores
    }), 200

@bp.route('/km-motoristas', methods=['GET'])
@admin_required
def obter_km_motoristas():
    """Retorna KM rodados por motorista"""
    from app.models import Motorista, RotaOperacional
    
    periodo = request.args.get('periodo', 'mes')
    
    hoje = datetime.now()
    
    if periodo == 'dia':
        data_inicio = datetime(hoje.year, hoje.month, hoje.day, 0, 0, 0)
    elif periodo == 'semana':
        data_inicio = hoje - timedelta(days=7)
    elif periodo == 'mes':
        data_inicio = hoje - relativedelta(months=1)
    else:  # ano
        data_inicio = hoje - relativedelta(years=1)
    
    # Buscar KM por motorista
    km_motoristas = db.session.query(
        Motorista.id,
        Motorista.nome,
        func.sum(RotaOperacional.km_real).label('km_total'),
        func.count(RotaOperacional.id).label('total_rotas'),
        func.avg(RotaOperacional.km_real).label('km_medio')
    ).join(
        RotaOperacional, RotaOperacional.motorista_id == Motorista.id
    ).filter(
        RotaOperacional.criado_em >= data_inicio
    ).group_by(
        Motorista.id, Motorista.nome
    ).order_by(
        func.sum(RotaOperacional.km_real).desc()
    ).all()
    
    return jsonify({
        'periodo': periodo,
        'motoristas': [
            {
                'id': m.id,
                'nome': m.nome,
                'km_total': float(m.km_total or 0),
                'total_rotas': m.total_rotas,
                'km_medio': float(m.km_medio or 0)
            } for m in km_motoristas
        ]
    }), 200

@bp.route('/cotacao-dolar', methods=['GET'])
@admin_required
def obter_cotacao_dolar():
    """Retorna cotação atual do dólar"""
    import requests
    
    try:
        # Usando API pública do Banco Central
        response = requests.get(
            'https://economia.awesomeapi.com.br/json/last/USD-BRL',
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            dolar = data.get('USDBRL', {})
            
            return jsonify({
                'cotacao': float(dolar.get('bid', 0)),
                'variacao': float(dolar.get('varBid', 0)),
                'data_hora': dolar.get('create_date', ''),
                'alta': float(dolar.get('high', 0)),
                'baixa': float(dolar.get('low', 0))
            }), 200
        else:
            return jsonify({
                'cotacao': 5.00,
                'variacao': 0,
                'data_hora': datetime.now().isoformat(),
                'alta': 5.00,
                'baixa': 5.00,
                'erro': 'API indisponível'
            }), 200
            
    except Exception as e:
        return jsonify({
            'cotacao': 5.00,
            'variacao': 0,
            'data_hora': datetime.now().isoformat(),
            'alta': 5.00,
            'baixa': 5.00,
            'erro': str(e)
        }), 200

@bp.route('/eficiencia-operacional', methods=['GET'])
@admin_required
def obter_eficiencia_operacional():
    """Retorna indicadores de eficiência operacional"""
    from app.models import OrdemCompra, ConferenciaRecebimento
    
    hoje = datetime.now()
    mes_atual = hoje - relativedelta(months=1)
    
    # Tempo médio de aprovação de OC
    ocs_aprovadas = OrdemCompra.query.filter(
        OrdemCompra.status == 'aprovada',
        OrdemCompra.aprovado_em >= mes_atual
    ).all()
    
    tempo_aprovacao = []
    for oc in ocs_aprovadas:
        if oc.aprovado_em and oc.criado_em:
            delta = oc.aprovado_em - oc.criado_em
            tempo_aprovacao.append(delta.total_seconds() / 3600)  # em horas
    
    tempo_medio_aprovacao = sum(tempo_aprovacao) / len(tempo_aprovacao) if tempo_aprovacao else 0
    
    # Taxa de aprovação
    total_solicitacoes = Solicitacao.query.filter(
        Solicitacao.data_envio >= mes_atual
    ).count()
    
    solicitacoes_aprovadas = Solicitacao.query.filter(
        Solicitacao.data_envio >= mes_atual,
        Solicitacao.status == 'aprovada'
    ).count()
    
    taxa_aprovacao = (solicitacoes_aprovadas / total_solicitacoes * 100) if total_solicitacoes > 0 else 0
    
    # Divergências
    total_conferencias = ConferenciaRecebimento.query.filter(
        ConferenciaRecebimento.criado_em >= mes_atual
    ).count()
    
    conferencias_divergentes = ConferenciaRecebimento.query.filter(
        ConferenciaRecebimento.criado_em >= mes_atual,
        ConferenciaRecebimento.divergencia == True
    ).count()
    
    taxa_divergencia = (conferencias_divergentes / total_conferencias * 100) if total_conferencias > 0 else 0
    
    return jsonify({
        'tempo_medio_aprovacao_horas': round(tempo_medio_aprovacao, 2),
        'taxa_aprovacao_percent': round(taxa_aprovacao, 2),
        'total_solicitacoes': total_solicitacoes,
        'solicitacoes_aprovadas': solicitacoes_aprovadas,
        'taxa_divergencia_percent': round(taxa_divergencia, 2),
        'total_conferencias': total_conferencias,
        'conferencias_divergentes': conferencias_divergentes
    }), 200

@bp.route('/analise-fornecedores', methods=['GET'])
@admin_required
def obter_analise_fornecedores():
    """Retorna análise detalhada de fornecedores"""
    from app.models import ConferenciaRecebimento
    
    # Fornecedores com mais divergências
    divergencias = db.session.query(
        Fornecedor.id,
        Fornecedor.nome,
        func.count(ConferenciaRecebimento.id).label('total_conferencias'),
        func.sum(func.cast(ConferenciaRecebimento.divergencia, db.Integer)).label('total_divergencias'),
        func.avg(ConferenciaRecebimento.percentual_diferenca).label('percentual_medio')
    ).join(
        OrdemCompra, OrdemCompra.fornecedor_id == Fornecedor.id
    ).join(
        ConferenciaRecebimento, ConferenciaRecebimento.oc_id == OrdemCompra.id
    ).group_by(
        Fornecedor.id, Fornecedor.nome
    ).order_by(
        func.sum(func.cast(ConferenciaRecebimento.divergencia, db.Integer)).desc()
    ).limit(10).all()
    
    return jsonify({
        'fornecedores_divergencias': [
            {
                'id': d.id,
                'nome': d.nome,
                'total_conferencias': d.total_conferencias,
                'total_divergencias': d.total_divergencias or 0,
                'taxa_divergencia': round((d.total_divergencias or 0) / d.total_conferencias * 100, 2) if d.total_conferencias > 0 else 0,
                'percentual_medio_diferenca': round(float(d.percentual_medio or 0), 2)
            } for d in divergencias
        ]
    }), 200
