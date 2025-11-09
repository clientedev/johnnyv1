from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models import TipoLote, db
from app.auth import admin_required

bp = Blueprint('tipos_lote', __name__, url_prefix='/api/tipos-lote')

@bp.route('', methods=['GET'])
@jwt_required()
def listar_tipos_lote():
    try:
        busca = request.args.get('busca', '')
        apenas_ativos = request.args.get('apenas_ativos', 'true').lower() == 'true'
        
        query = TipoLote.query
        
        if apenas_ativos:
            query = query.filter_by(ativo=True)
        
        if busca:
            query = query.filter(
                db.or_(
                    TipoLote.nome.ilike(f'%{busca}%'),
                    TipoLote.codigo.ilike(f'%{busca}%'),
                    TipoLote.descricao.ilike(f'%{busca}%')
                )
            )
        
        tipos = query.order_by(TipoLote.nome).all()
        return jsonify([tipo.to_dict() for tipo in tipos]), 200
    
    except Exception as e:
        return jsonify({'erro': f'Erro ao listar tipos de lote: {str(e)}'}), 500

@bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def obter_tipo_lote(id):
    try:
        tipo = TipoLote.query.get(id)
        
        if not tipo:
            return jsonify({'erro': 'Tipo de lote não encontrado'}), 404
        
        return jsonify(tipo.to_dict()), 200
    
    except Exception as e:
        return jsonify({'erro': f'Erro ao obter tipo de lote: {str(e)}'}), 500

@bp.route('', methods=['POST'])
@admin_required
def criar_tipo_lote():
    try:
        data = request.get_json()
        
        if not data or not data.get('nome'):
            return jsonify({'erro': 'Nome é obrigatório'}), 400
        
        tipo_existente = TipoLote.query.filter_by(nome=data['nome']).first()
        if tipo_existente:
            return jsonify({'erro': 'Já existe um tipo de lote com este nome'}), 400
        
        if data.get('codigo'):
            codigo_existente = TipoLote.query.filter_by(codigo=data['codigo']).first()
            if codigo_existente:
                return jsonify({'erro': 'Já existe um tipo de lote com este código'}), 400
        
        total_tipos = TipoLote.query.count()
        if total_tipos >= 150:
            return jsonify({'erro': 'Limite máximo de 150 tipos de lote atingido'}), 400
        
        tipo = TipoLote(
            nome=data['nome'],
            descricao=data.get('descricao', ''),
            codigo=data.get('codigo', ''),
            ativo=data.get('ativo', True)
        )
        
        db.session.add(tipo)
        db.session.commit()
        
        return jsonify(tipo.to_dict()), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao criar tipo de lote: {str(e)}'}), 500

@bp.route('/<int:id>', methods=['PUT'])
@admin_required
def atualizar_tipo_lote(id):
    try:
        tipo = TipoLote.query.get(id)
        
        if not tipo:
            return jsonify({'erro': 'Tipo de lote não encontrado'}), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({'erro': 'Dados não fornecidos'}), 400
        
        if data.get('nome') and data['nome'] != tipo.nome:
            tipo_existente = TipoLote.query.filter_by(nome=data['nome']).first()
            if tipo_existente:
                return jsonify({'erro': 'Já existe um tipo de lote com este nome'}), 400
            tipo.nome = data['nome']
        
        if data.get('codigo') and data['codigo'] != tipo.codigo:
            codigo_existente = TipoLote.query.filter_by(codigo=data['codigo']).first()
            if codigo_existente:
                return jsonify({'erro': 'Já existe um tipo de lote com este código'}), 400
            tipo.codigo = data['codigo']
        
        if 'descricao' in data:
            tipo.descricao = data['descricao']
        
        if 'ativo' in data:
            tipo.ativo = data['ativo']
        
        db.session.commit()
        
        return jsonify(tipo.to_dict()), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao atualizar tipo de lote: {str(e)}'}), 500

@bp.route('/<int:id>', methods=['DELETE'])
@admin_required
def deletar_tipo_lote(id):
    try:
        tipo = TipoLote.query.get(id)
        
        if not tipo:
            return jsonify({'erro': 'Tipo de lote não encontrado'}), 404
        
        if len(tipo.itens_solicitacao) > 0 or len(tipo.lotes) > 0:
            return jsonify({'erro': 'Não é possível deletar tipo de lote com solicitações ou lotes associados. Desative-o em vez disso.'}), 400
        
        db.session.delete(tipo)
        db.session.commit()
        
        return jsonify({'mensagem': 'Tipo de lote deletado com sucesso'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao deletar tipo de lote: {str(e)}'}), 500
