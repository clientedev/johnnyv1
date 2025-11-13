from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Solicitacao, ItemSolicitacao, Fornecedor, TipoLote, FornecedorTipoLotePreco, FornecedorTipoLoteClassificacao, db, Usuario
from app.auth import admin_required
from datetime import datetime
import os

bp = Blueprint('solicitacoes', __name__, url_prefix='/api/solicitacoes')

def calcular_valor_item(fornecedor_id, tipo_lote_id, classificacao, estrelas_from_frontend, peso_kg):
    """Calcula o valor de um item baseado no preço configurado
    
    Args:
        fornecedor_id: ID do fornecedor
        tipo_lote_id: ID do tipo de lote
        classificacao: Classificação do item (leve/medio/pesado)
        estrelas_from_frontend: Estrelas sugeridas pelo frontend (fallback)
        peso_kg: Peso em kg
    
    Returns:
        tuple: (valor_calculado, preco_por_kg, estrelas_usadas)
    """
    # Primeiro tenta usar a configuração de classificação do fornecedor
    estrelas_final = estrelas_from_frontend
    
    classificacao_config = FornecedorTipoLoteClassificacao.query.filter_by(
        fornecedor_id=fornecedor_id,
        tipo_lote_id=tipo_lote_id,
        ativo=True
    ).first()
    
    if classificacao_config and classificacao:
        estrelas_final = classificacao_config.get_estrelas_por_classificacao(classificacao)
        print(f"      ✅ Usando estrelas da configuração: {estrelas_final} (classificação: {classificacao})")
    else:
        print(f"      ⚠️ Usando estrelas do frontend: {estrelas_final}")
    
    # Busca o preço configurado
    preco = FornecedorTipoLotePreco.query.filter_by(
        fornecedor_id=fornecedor_id,
        tipo_lote_id=tipo_lote_id,
        estrelas=estrelas_final,
        ativo=True
    ).first()
    
    if not preco:
        print(f"      ❌ Preço não encontrado para {estrelas_final} estrelas!")
        return (0.0, 0.0, estrelas_final)
    
    valor = preco.preco_por_kg * float(peso_kg)
    print(f"      ✅ Preço encontrado: R$ {preco.preco_por_kg}/kg × {peso_kg}kg = R$ {valor:.2f}")
    
    return (valor, preco.preco_por_kg, estrelas_final)

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
        
        print(f"\n{'='*60}")
        print(f"🆕 CRIANDO SOLICITAÇÃO #{solicitacao.id}")
        print(f"   Fornecedor: {fornecedor.nome}")
        print(f"   Total de itens recebidos: {len(data['itens'])}")
        print(f"{'='*60}")
        
        for item_data in data['itens']:
            print(f"\n📦 Item recebido do frontend:")
            print(f"   {item_data}")
            
            if not item_data.get('tipo_lote_id') or not item_data.get('peso_kg'):
                print(f"   ⚠️ Item inválido - pulando")
                continue
            
            tipo_lote = TipoLote.query.get(item_data['tipo_lote_id'])
            if not tipo_lote:
                print(f"   ❌ Tipo de lote não encontrado")
                continue
            
            print(f"   ✅ Tipo de lote: {tipo_lote.nome}")
            
            classificacao = item_data.get('classificacao', 'medio')
            estrelas_final = item_data.get('estrelas_final', 3)
            if estrelas_final is None or not (1 <= estrelas_final <= 5):
                estrelas_final = 3
            
            print(f"   📋 Classificação: {classificacao}")
            print(f"   ⭐ Estrelas (frontend): {estrelas_final}")
            print(f"   🔍 Calculando valor...")
            
            valor, preco_por_kg, estrelas_usadas = calcular_valor_item(
                data['fornecedor_id'],
                item_data['tipo_lote_id'],
                classificacao,
                estrelas_final,
                item_data['peso_kg']
            )
            
            print(f"   💰 Valor final: R$ {valor:.2f}")
            print(f"   ⭐ Estrelas usadas: {estrelas_usadas}")
            
            item = ItemSolicitacao(
                solicitacao_id=solicitacao.id,
                tipo_lote_id=item_data['tipo_lote_id'],
                peso_kg=float(item_data['peso_kg']),
                classificacao=classificacao,
                estrelas_sugeridas_ia=item_data.get('estrelas_sugeridas_ia'),
                estrelas_final=estrelas_usadas,
                valor_calculado=valor,
                preco_por_kg_snapshot=preco_por_kg,
                estrelas_snapshot=estrelas_usadas,
                imagem_url=item_data.get('imagem_url', ''),
                observacoes=item_data.get('observacoes', '')
            )
            
            print(f"   ✅ Item salvo: Valor=R$ {item.valor_calculado:.2f}, Classificação={item.classificacao}, Estrelas={item.estrelas_final}")
            
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
