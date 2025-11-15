from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Lote, MovimentacaoEstoque, EntradaEstoque, Usuario
from app.auth import admin_required
from datetime import datetime

bp = Blueprint('estoque', __name__, url_prefix='/api/estoque')

@bp.route('/lotes', methods=['GET'])
@jwt_required()
def listar_lotes_estoque():
    try:
        query = Lote.query
        
        status = request.args.get('status')
        if status:
            query = query.filter_by(status=status)
        
        fornecedor_id = request.args.get('fornecedor_id', type=int)
        if fornecedor_id:
            query = query.filter_by(fornecedor_id=fornecedor_id)
        
        material = request.args.get('material')
        if material:
            query = query.filter(Lote.tipo_lote.has(nome=material))
        
        com_divergencia = request.args.get('com_divergencia')
        if com_divergencia == 'true':
            query = query.filter(Lote.divergencias != None)
            query = query.filter(Lote.divergencias != [])
        
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        if data_inicio:
            query = query.filter(Lote.data_criacao >= datetime.fromisoformat(data_inicio))
        if data_fim:
            query = query.filter(Lote.data_criacao <= datetime.fromisoformat(data_fim))
        
        lotes = query.order_by(Lote.data_criacao.desc()).all()
        
        resultado = []
        for lote in lotes:
            lote_dict = lote.to_dict()
            
            if lote.movimentacoes:
                ultima_movimentacao = sorted(lote.movimentacoes, key=lambda m: m.data_movimentacao, reverse=True)[0]
                lote_dict['localizacao_atual'] = ultima_movimentacao.localizacao_destino
            else:
                lote_dict['localizacao_atual'] = 'PATIO_RECEBIMENTO'
            
            if lote.entrada_estoque:
                lote_dict['entrada_estoque'] = lote.entrada_estoque.to_dict()
            
            resultado.append(lote_dict)
        
        return jsonify(resultado), 200
    
    except Exception as e:
        return jsonify({'erro': f'Erro ao listar lotes: {str(e)}'}), 500

@bp.route('/lotes/<int:id>', methods=['GET'])
@jwt_required()
def obter_lote_estoque(id):
    try:
        lote = Lote.query.get(id)
        
        if not lote:
            return jsonify({'erro': 'Lote não encontrado'}), 404
        
        lote_dict = lote.to_dict()
        
        if lote.movimentacoes:
            lote_dict['movimentacoes'] = [m.to_dict() for m in sorted(lote.movimentacoes, key=lambda m: m.data_movimentacao, reverse=True)]
            ultima_movimentacao = lote_dict['movimentacoes'][0]
            lote_dict['localizacao_atual'] = ultima_movimentacao['localizacao_destino']
        else:
            lote_dict['movimentacoes'] = []
            lote_dict['localizacao_atual'] = 'PATIO_RECEBIMENTO'
        
        if lote.entrada_estoque:
            lote_dict['entrada_estoque'] = lote.entrada_estoque.to_dict()
        
        if lote.separacao:
            lote_dict['separacao'] = lote.separacao.to_dict()
        
        if lote.sublotes:
            lote_dict['sublotes'] = [sublote.to_dict() for sublote in lote.sublotes]
        
        if lote.conferencia:
            lote_dict['conferencia'] = lote.conferencia.to_dict()
        
        return jsonify(lote_dict), 200
    
    except Exception as e:
        return jsonify({'erro': f'Erro ao obter lote: {str(e)}'}), 500

@bp.route('/movimentacoes', methods=['GET'])
@jwt_required()
def listar_movimentacoes():
    try:
        query = MovimentacaoEstoque.query
        
        lote_id = request.args.get('lote_id', type=int)
        if lote_id:
            query = query.filter_by(lote_id=lote_id)
        
        tipo = request.args.get('tipo')
        if tipo:
            query = query.filter_by(tipo=tipo)
        
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        if data_inicio:
            query = query.filter(MovimentacaoEstoque.data_movimentacao >= datetime.fromisoformat(data_inicio))
        if data_fim:
            query = query.filter(MovimentacaoEstoque.data_movimentacao <= datetime.fromisoformat(data_fim))
        
        movimentacoes = query.order_by(MovimentacaoEstoque.data_movimentacao.desc()).limit(100).all()
        
        return jsonify([m.to_dict() for m in movimentacoes]), 200
    
    except Exception as e:
        return jsonify({'erro': f'Erro ao listar movimentações: {str(e)}'}), 500

@bp.route('/movimentacoes', methods=['POST'])
@jwt_required()
def criar_movimentacao():
    try:
        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get(usuario_id)
        
        perfil_nome = usuario.perfil.nome if usuario.perfil else None
        if perfil_nome not in ['Conferente / Estoque', 'Administrador'] and usuario.tipo != 'admin':
            return jsonify({'erro': 'Acesso negado. Apenas conferentes e administradores podem movimentar estoque'}), 403
        
        data = request.get_json()
        
        if not data or not data.get('lote_id') or not data.get('tipo') or not data.get('localizacao_destino'):
            return jsonify({'erro': 'lote_id, tipo e localizacao_destino são obrigatórios'}), 400
        
        lote = Lote.query.get(data['lote_id'])
        if not lote:
            return jsonify({'erro': 'Lote não encontrado'}), 404
        
        localizacao_origem = None
        if lote.movimentacoes:
            ultima_movimentacao = sorted(lote.movimentacoes, key=lambda m: m.data_movimentacao, reverse=True)[0]
            localizacao_origem = ultima_movimentacao.localizacao_destino
        else:
            localizacao_origem = 'PATIO_RECEBIMENTO'
        
        dados_before = {
            'lote_id': lote.id,
            'numero_lote': lote.numero_lote,
            'localizacao': localizacao_origem,
            'peso': lote.peso_total_kg
        }
        
        movimentacao = MovimentacaoEstoque(
            lote_id=data['lote_id'],
            tipo=data['tipo'],
            localizacao_origem=localizacao_origem,
            localizacao_destino=data['localizacao_destino'],
            peso=data.get('peso', lote.peso_total_kg),
            quantidade=data.get('quantidade'),
            usuario_id=usuario_id,
            observacoes=data.get('observacoes', ''),
            dados_before=dados_before,
            dados_after={
                'lote_id': lote.id,
                'numero_lote': lote.numero_lote,
                'localizacao': data['localizacao_destino'],
                'peso': data.get('peso', lote.peso_total_kg)
            },
            auditoria=[{
                'acao': 'MOVIMENTACAO_CRIADA',
                'usuario_id': usuario_id,
                'timestamp': datetime.utcnow().isoformat(),
                'ip': request.remote_addr,
                'user_agent': request.headers.get('User-Agent')
            }],
            data_movimentacao=datetime.utcnow()
        )
        
        db.session.add(movimentacao)
        db.session.commit()
        
        return jsonify({
            'mensagem': 'Movimentação registrada com sucesso',
            'movimentacao': movimentacao.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao criar movimentação: {str(e)}'}), 500

@bp.route('/estatisticas', methods=['GET'])
@jwt_required()
def obter_estatisticas_estoque():
    try:
        total_lotes = Lote.query.count()
        aguardando_separacao = Lote.query.filter_by(status='AGUARDANDO_SEPARACAO').count()
        em_separacao = Lote.query.filter_by(status='EM_SEPARACAO').count()
        processados = Lote.query.filter_by(status='PROCESSADO').count()
        bloqueados = Lote.query.filter_by(status='BLOQUEADO').count()
        
        peso_total = db.session.query(db.func.sum(Lote.peso_total_kg)).filter(
            Lote.status.in_(['AGUARDANDO_SEPARACAO', 'EM_SEPARACAO', 'APROVADO'])
        ).scalar() or 0
        
        total_movimentacoes = MovimentacaoEstoque.query.count()
        
        return jsonify({
            'total_lotes': total_lotes,
            'aguardando_separacao': aguardando_separacao,
            'em_separacao': em_separacao,
            'processados': processados,
            'bloqueados': bloqueados,
            'peso_total_estoque': float(peso_total),
            'total_movimentacoes': total_movimentacoes
        }), 200
    
    except Exception as e:
        return jsonify({'erro': f'Erro ao obter estatísticas: {str(e)}'}), 500
