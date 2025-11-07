from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.models import db, Fornecedor, Preco, Placa, Solicitacao, Entrada, Compra
from app.auth import admin_required
from sqlalchemy import func, extract
from datetime import datetime, timedelta

bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@bp.route('/stats', methods=['GET'])
@admin_required
def obter_estatisticas():
    total_pendentes = Placa.query.filter_by(status='em_analise').count()
    total_aprovados = Placa.query.filter_by(status='aprovada').count()
    total_reprovados = Placa.query.filter_by(status='reprovada').count()
    
    quilos_por_tipo = db.session.query(
        Placa.tipo_placa,
        func.sum(Placa.peso_kg).label('total_kg')
    ).filter(Placa.status == 'aprovada').group_by(Placa.tipo_placa).all()
    
    quilos = {
        'leve': 0,
        'media': 0,
        'pesada': 0
    }
    
    for tipo, total in quilos_por_tipo:
        quilos[tipo] = float(total) if total else 0
    
    valor_total = db.session.query(func.sum(Placa.valor)).filter_by(status='aprovada').scalar() or 0
    
    ranking_empresas = db.session.query(
        Fornecedor.nome,
        func.count(Placa.id).label('total_placas')
    ).join(Placa).filter(Placa.status == 'aprovada').group_by(
        Fornecedor.id, Fornecedor.nome
    ).order_by(func.count(Placa.id).desc()).limit(5).all()
    
    ranking = [{'nome': nome, 'total': total} for nome, total in ranking_empresas]
    
    return jsonify({
        'relatorios': {
            'pendentes': total_pendentes,
            'aprovados': total_aprovados,
            'reprovados': total_reprovados
        },
        'quilos_por_tipo': quilos,
        'valor_total': round(float(valor_total), 2),
        'ranking_empresas': ranking
    }), 200

@bp.route('/grafico-mensal', methods=['GET'])
@admin_required
def obter_grafico_mensal():
    ano_atual = datetime.now().year
    
    dados_mensais = db.session.query(
        extract('month', Placa.data_registro).label('mes'),
        func.count(Placa.id).label('total')
    ).filter(
        extract('year', Placa.data_registro) == ano_atual,
        Placa.status == 'aprovada'
    ).group_by(extract('month', Placa.data_registro)).all()
    
    meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    dados = [0] * 12
    
    for mes, total in dados_mensais:
        dados[int(mes) - 1] = total
    
    return jsonify({
        'labels': meses,
        'data': dados
    }), 200

@bp.route('/mapa', methods=['GET'])
@admin_required
def obter_dados_mapa():
    placas = Placa.query.filter(
        Placa.status == 'aprovada',
        Placa.localizacao_lat.isnot(None),
        Placa.localizacao_lng.isnot(None)
    ).all()
    
    marcadores = []
    for placa in placas:
        marcadores.append({
            'id': placa.id,
            'lat': placa.localizacao_lat,
            'lng': placa.localizacao_lng,
            'fornecedor': placa.fornecedor.nome,
            'funcionario': placa.funcionario.nome,
            'tipo_placa': placa.tipo_placa,
            'peso_kg': placa.peso_kg,
            'data': placa.data_registro.strftime('%d/%m/%Y %H:%M')
        })
    
    return jsonify(marcadores), 200

@bp.route('/geral', methods=['GET'])
@admin_required
def dashboard_geral():
    total_solicitacoes = Solicitacao.query.count()
    solicitacoes_pendentes = Solicitacao.query.filter_by(status='pendente').count()
    solicitacoes_aprovadas = Solicitacao.query.filter_by(status='aprovada').count()
    
    total_placas = Placa.query.count()
    placas_aprovadas = Placa.query.filter_by(status='aprovada').count()
    peso_total = db.session.query(func.sum(Placa.peso_kg)).filter_by(status='aprovada').scalar() or 0
    
    total_entradas = Entrada.query.count()
    entradas_pendentes = Entrada.query.filter_by(status='pendente').count()
    
    return jsonify({
        'solicitacoes': {
            'total': total_solicitacoes,
            'pendentes': solicitacoes_pendentes,
            'aprovadas': solicitacoes_aprovadas
        },
        'placas': {
            'total': total_placas,
            'aprovadas': placas_aprovadas,
            'peso_total_kg': float(peso_total)
        },
        'entradas': {
            'total': total_entradas,
            'pendentes': entradas_pendentes
        }
    }), 200

@bp.route('/financeiro', methods=['GET'])
@admin_required
def dashboard_financeiro():
    total_compras = db.session.query(func.sum(Compra.valor_total)).scalar() or 0
    
    compras_pendentes = db.session.query(func.sum(Compra.valor_total)).filter_by(status='pendente').scalar() or 0
    compras_pagas = db.session.query(func.sum(Compra.valor_total)).filter_by(status='pago').scalar() or 0
    
    valor_placas_aprovadas = db.session.query(func.sum(Placa.valor)).filter_by(status='aprovada').scalar() or 0
    
    lucro_liquido = float(valor_placas_aprovadas) - float(total_compras)
    
    compras_mes_atual = db.session.query(
        extract('day', Compra.data_compra).label('dia'),
        func.sum(Compra.valor_total).label('total')
    ).filter(
        extract('month', Compra.data_compra) == datetime.now().month,
        extract('year', Compra.data_compra) == datetime.now().year
    ).group_by(extract('day', Compra.data_compra)).all()
    
    return jsonify({
        'compras': float(total_compras),
        'receita': float(valor_placas_aprovadas),
        'lucro_liquido': lucro_liquido,
        'pendentes': float(compras_pendentes),
        'pagas': float(compras_pagas),
        'grafico_mensal': [{'dia': int(dia), 'valor': float(total)} for dia, total in compras_mes_atual]
    }), 200

@bp.route('/operacional', methods=['GET'])
@admin_required
def dashboard_operacional():
    entradas_aprovadas = Entrada.query.filter_by(status='aprovada').count()
    entradas_reprovadas = Entrada.query.filter_by(status='reprovada').count()
    entradas_pendentes = Entrada.query.filter_by(status='pendente').count()
    
    entradas_com_tempo = Entrada.query.filter(
        Entrada.data_processamento.isnot(None)
    ).all()
    
    if entradas_com_tempo:
        tempos = [(e.data_processamento - e.data_entrada).total_seconds() / 3600 for e in entradas_com_tempo]
        tempo_medio_horas = sum(tempos) / len(tempos)
    else:
        tempo_medio_horas = 0
    
    solicitacoes_ultimos_7_dias = Solicitacao.query.filter(
        Solicitacao.data_envio >= datetime.now() - timedelta(days=7)
    ).count()
    
    placas_por_tipo = db.session.query(
        Placa.tipo_placa,
        func.count(Placa.id).label('total')
    ).group_by(Placa.tipo_placa).all()
    
    return jsonify({
        'entradas': {
            'aprovadas': entradas_aprovadas,
            'reprovadas': entradas_reprovadas,
            'pendentes': entradas_pendentes
        },
        'tempo_medio_analise_horas': round(tempo_medio_horas, 2),
        'solicitacoes_ultimos_7_dias': solicitacoes_ultimos_7_dias,
        'placas_por_tipo': {tipo: total for tipo, total in placas_por_tipo}
    }), 200

@bp.route('/fornecedores', methods=['GET'])
@admin_required
def dashboard_fornecedores():
    top_fornecedores = db.session.query(
        Fornecedor.nome,
        func.count(Compra.id).label('total_compras'),
        func.sum(Compra.valor_total).label('valor_total')
    ).join(Compra).group_by(Fornecedor.id, Fornecedor.nome).order_by(
        func.sum(Compra.valor_total).desc()
    ).limit(10).all()
    
    ranking_fornecedores = [{
        'nome': nome,
        'total_compras': total,
        'valor_total': float(valor) if valor else 0
    } for nome, total, valor in top_fornecedores]
    
    ranking_empresas = db.session.query(
        Fornecedor.nome,
        func.count(Placa.id).label('total_placas'),
        func.sum(Placa.peso_kg).label('peso_total')
    ).join(Placa).filter(Placa.status == 'aprovada').group_by(
        Fornecedor.id, Fornecedor.nome
    ).order_by(func.count(Placa.id).desc()).limit(10).all()
    
    ranking_empresas_list = [{
        'nome': nome,
        'total_placas': total,
        'peso_total_kg': float(peso) if peso else 0
    } for nome, total, peso in ranking_empresas]
    
    total_fornecedores = Fornecedor.query.count()
    fornecedores_ativos = Fornecedor.query.filter_by(ativo=True).count()
    
    return jsonify({
        'top_fornecedores': ranking_fornecedores,
        'ranking_empresas': ranking_empresas_list,
        'total_fornecedores': total_fornecedores,
        'fornecedores_ativos': fornecedores_ativos
    }), 200
