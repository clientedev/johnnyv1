from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.models import db, Relatorio, Empresa, Preco
from app.auth import admin_required
from sqlalchemy import func, extract
from datetime import datetime

bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@bp.route('/stats', methods=['GET'])
@admin_required
def obter_estatisticas():
    total_pendentes = Relatorio.query.filter_by(status='pendente').count()
    total_aprovados = Relatorio.query.filter_by(status='aprovado').count()
    total_reprovados = Relatorio.query.filter_by(status='reprovado').count()
    
    quilos_por_tipo = db.session.query(
        Relatorio.tipo_placa,
        func.sum(Relatorio.peso_kg).label('total_kg')
    ).filter(Relatorio.status == 'aprovado').group_by(Relatorio.tipo_placa).all()
    
    quilos = {
        'leve': 0,
        'media': 0,
        'pesada': 0
    }
    
    for tipo, total in quilos_por_tipo:
        quilos[tipo] = float(total) if total else 0
    
    valor_total = 0
    relatorios_aprovados = Relatorio.query.filter_by(status='aprovado').all()
    
    for relatorio in relatorios_aprovados:
        preco = Preco.query.filter_by(
            empresa_id=relatorio.empresa_id,
            tipo_placa=relatorio.tipo_placa
        ).first()
        
        if preco:
            valor_total += relatorio.peso_kg * preco.preco_por_kg
    
    ranking_empresas = db.session.query(
        Empresa.nome,
        func.count(Relatorio.id).label('total_relatorios')
    ).join(Relatorio).filter(Relatorio.status == 'aprovado').group_by(
        Empresa.id, Empresa.nome
    ).order_by(func.count(Relatorio.id).desc()).limit(5).all()
    
    ranking = [{'nome': nome, 'total': total} for nome, total in ranking_empresas]
    
    return jsonify({
        'relatorios': {
            'pendentes': total_pendentes,
            'aprovados': total_aprovados,
            'reprovados': total_reprovados
        },
        'quilos_por_tipo': quilos,
        'valor_total': round(valor_total, 2),
        'ranking_empresas': ranking
    }), 200

@bp.route('/grafico-mensal', methods=['GET'])
@admin_required
def obter_grafico_mensal():
    ano_atual = datetime.now().year
    
    dados_mensais = db.session.query(
        extract('month', Relatorio.data_envio).label('mes'),
        func.count(Relatorio.id).label('total')
    ).filter(
        extract('year', Relatorio.data_envio) == ano_atual,
        Relatorio.status == 'aprovado'
    ).group_by(extract('month', Relatorio.data_envio)).all()
    
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
    relatorios = Relatorio.query.filter(
        Relatorio.status == 'aprovado',
        Relatorio.localizacao_lat.isnot(None),
        Relatorio.localizacao_lng.isnot(None)
    ).all()
    
    marcadores = []
    for relatorio in relatorios:
        marcadores.append({
            'id': relatorio.id,
            'lat': relatorio.localizacao_lat,
            'lng': relatorio.localizacao_lng,
            'empresa': relatorio.empresa.nome,
            'funcionario': relatorio.funcionario.nome,
            'tipo_placa': relatorio.tipo_placa,
            'peso_kg': relatorio.peso_kg,
            'data': relatorio.data_envio.strftime('%d/%m/%Y %H:%M')
        })
    
    return jsonify(marcadores), 200
