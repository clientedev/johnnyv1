from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Solicitacao, ItemSolicitacao, Fornecedor, TipoLote, FornecedorTipoLotePreco, db, Usuario
from app.auth import admin_required
from datetime import datetime
import os

bp = Blueprint('solicitacoes', __name__, url_prefix='/api/solicitacoes')

def calcular_valor_item(fornecedor_id, tipo_lote_id, estrelas, peso_kg):
    """Calcula o valor de um item baseado no preço configurado"""
    preco = FornecedorTipoLotePreco.query.filter_by(
        fornecedor_id=fornecedor_id,
        tipo_lote_id=tipo_lote_id,
        estrelas=estrelas
    ).first()
    
    if not preco:
        return 0.0
    
    return preco.preco_por_kg * peso_kg

@bp.route('', methods=['GET'])
@jwt_required()
def listar_solicitacoes():
    try:
        usuario_id = int(get_jwt_identity())
        usuario = Usuario.query.get(usuario_id)
        
        status = request.args.get('status', '')
        fornecedor_id = request.args.get('fornecedor_id', type=int)
        
        query = Solicitacao.query
        
        if usuario and usuario.tipo != 'admin':
            query = query.filter_by(funcionario_id=usuario.id)
        
        if status:
            query = query.filter_by(status=status)
        
        if fornecedor_id:
            query = query.filter_by(fornecedor_id=fornecedor_id)
        
        solicitacoes = query.order_by(Solicitacao.data_envio.desc()).all()
        
        resultado = []
        for sol in solicitacoes:
            sol_dict = sol.to_dict()
            sol_dict['itens'] = [item.to_dict() for item in sol.itens]
            resultado.append(sol_dict)
        
        return jsonify(resultado), 200
    
    except Exception as e:
        return jsonify({'erro': f'Erro ao listar solicitações: {str(e)}'}), 500

@bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def obter_solicitacao(id):
    try:
        solicitacao = Solicitacao.query.get(id)
        
        if not solicitacao:
            return jsonify({'erro': 'Solicitação não encontrada'}), 404
        
        sol_dict = solicitacao.to_dict()
        sol_dict['itens'] = [item.to_dict() for item in solicitacao.itens]
        
        return jsonify(sol_dict), 200
    
    except Exception as e:
        return jsonify({'erro': f'Erro ao obter solicitação: {str(e)}'}), 500

@bp.route('', methods=['POST'])
@jwt_required()
def criar_solicitacao():
    try:
        usuario_id = int(get_jwt_identity())
        usuario = Usuario.query.get(usuario_id)
        
        if not usuario:
            return jsonify({'erro': 'Usuário não encontrado'}), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({'erro': 'Dados não fornecidos'}), 400
        
        if not data.get('fornecedor_id'):
            return jsonify({'erro': 'Fornecedor é obrigatório'}), 400
        
        if not data.get('itens') or not isinstance(data['itens'], list) or len(data['itens']) == 0:
            return jsonify({'erro': 'Pelo menos um item é obrigatório'}), 400
        
        fornecedor = Fornecedor.query.get(data['fornecedor_id'])
        if not fornecedor:
            return jsonify({'erro': 'Fornecedor não encontrado'}), 404
        
        solicitacao = Solicitacao(
            funcionario_id=usuario.id,
            fornecedor_id=data['fornecedor_id'],
            tipo_retirada=data.get('tipo_retirada', 'buscar'),
            observacoes=data.get('observacoes', ''),
            status='pendente'
        )
        
        db.session.add(solicitacao)
        db.session.flush()
        
        for item_data in data['itens']:
            if not item_data.get('tipo_lote_id') or not item_data.get('peso_kg'):
                continue
            
            tipo_lote = TipoLote.query.get(item_data['tipo_lote_id'])
            if not tipo_lote:
                continue
            
            estrelas_final = item_data.get('estrelas_final', 3)
            if estrelas_final is None or not (1 <= estrelas_final <= 5):
                estrelas_final = 3
            
            valor = calcular_valor_item(
                data['fornecedor_id'],
                item_data['tipo_lote_id'],
                estrelas_final,
                item_data['peso_kg']
            )
            
            item = ItemSolicitacao(
                solicitacao_id=solicitacao.id,
                tipo_lote_id=item_data['tipo_lote_id'],
                peso_kg=item_data['peso_kg'],
                estrelas_sugeridas_ia=item_data.get('estrelas_sugeridas_ia'),
                estrelas_final=estrelas_final,
                valor_calculado=valor,
                imagem_url=item_data.get('imagem_url', ''),
                observacoes=item_data.get('observacoes', '')
            )
            
            db.session.add(item)
        
        db.session.commit()
        
        sol_dict = solicitacao.to_dict()
        sol_dict['itens'] = [item.to_dict() for item in solicitacao.itens]
        
        return jsonify(sol_dict), 201
    
    except ValueError as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao criar solicitação: {str(e)}'}), 500

@bp.route('/<int:id>/aprovar', methods=['POST'])
@admin_required
def aprovar_solicitacao(id):
    try:
        admin_id = int(get_jwt_identity())
        admin = Usuario.query.get(admin_id)
        
        solicitacao = Solicitacao.query.get(id)
        
        if not solicitacao:
            return jsonify({'erro': 'Solicitação não encontrada'}), 404
        
        if solicitacao.status != 'pendente':
            return jsonify({'erro': 'Apenas solicitações pendentes podem ser aprovadas'}), 400
        
        solicitacao.status = 'aprovada'
        solicitacao.data_confirmacao = datetime.utcnow()
        solicitacao.admin_id = admin.id if admin else None
        
        db.session.commit()
        
        return jsonify({
            'mensagem': 'Solicitação aprovada com sucesso',
            'solicitacao': solicitacao.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao aprovar solicitação: {str(e)}'}), 500

@bp.route('/<int:id>/rejeitar', methods=['POST'])
@admin_required
def rejeitar_solicitacao(id):
    try:
        solicitacao = Solicitacao.query.get(id)
        
        if not solicitacao:
            return jsonify({'erro': 'Solicitação não encontrada'}), 404
        
        if solicitacao.status != 'pendente':
            return jsonify({'erro': 'Apenas solicitações pendentes podem ser rejeitadas'}), 400
        
        data = request.get_json()
        motivo = data.get('motivo', '') if data else ''
        
        solicitacao.status = 'rejeitada'
        solicitacao.data_confirmacao = datetime.utcnow()
        if motivo:
            solicitacao.observacoes = (solicitacao.observacoes or '') + f'\nMotivo da rejeição: {motivo}'
        
        db.session.commit()
        
        return jsonify({
            'mensagem': 'Solicitação rejeitada',
            'solicitacao': solicitacao.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao rejeitar solicitação: {str(e)}'}), 500

@bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def deletar_solicitacao(id):
    try:
        usuario_id = int(get_jwt_identity())
        usuario = Usuario.query.get(usuario_id)
        
        solicitacao = Solicitacao.query.get(id)
        
        if not solicitacao:
            return jsonify({'erro': 'Solicitação não encontrada'}), 404
        
        if usuario.tipo != 'admin' and solicitacao.funcionario_id != usuario.id:
            return jsonify({'erro': 'Sem permissão para deletar esta solicitação'}), 403
        
        if solicitacao.status != 'pendente':
            return jsonify({'erro': 'Apenas solicitações pendentes podem ser deletadas'}), 400
        
        db.session.delete(solicitacao)
        db.session.commit()
        
        return jsonify({'mensagem': 'Solicitação deletada com sucesso'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao deletar solicitação: {str(e)}'}), 500
