from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Notificacao

bp = Blueprint('notificacoes', __name__, url_prefix='/api/notificacoes')

@bp.route('', methods=['GET'])
@jwt_required()
def listar_notificacoes():
    usuario_id = get_jwt_identity()
    
    notificacoes = Notificacao.query.filter_by(
        usuario_id=usuario_id
    ).order_by(Notificacao.data_envio.desc()).all()
    
    return jsonify([notificacao.to_dict() for notificacao in notificacoes]), 200

@bp.route('/nao-lidas', methods=['GET'])
@jwt_required()
def contar_nao_lidas():
    usuario_id = get_jwt_identity()
    
    count = Notificacao.query.filter_by(
        usuario_id=usuario_id,
        lida=False
    ).count()
    
    return jsonify({'count': count}), 200

@bp.route('/<int:id>/marcar-lida', methods=['PUT'])
@jwt_required()
def marcar_como_lida(id):
    usuario_id = get_jwt_identity()
    
    notificacao = Notificacao.query.get(id)
    
    if not notificacao:
        return jsonify({'erro': 'Notificação não encontrada'}), 404
    
    if notificacao.usuario_id != usuario_id:
        return jsonify({'erro': 'Acesso negado'}), 403
    
    notificacao.lida = True
    db.session.commit()
    
    return jsonify(notificacao.to_dict()), 200

@bp.route('/marcar-todas-lidas', methods=['PUT'])
@jwt_required()
def marcar_todas_como_lidas():
    usuario_id = get_jwt_identity()
    
    Notificacao.query.filter_by(
        usuario_id=usuario_id,
        lida=False
    ).update({'lida': True})
    
    db.session.commit()
    
    return jsonify({'mensagem': 'Todas as notificações foram marcadas como lidas'}), 200
