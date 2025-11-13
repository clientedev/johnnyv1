from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Fornecedor, Notificacao, Solicitacao, ItemSolicitacao, Usuario, TipoLote, FornecedorTipoLotePreco, Lote, OrdemCompra, AuditoriaOC, Perfil, db
from app.auth import admin_required
from app.utils.auditoria import registrar_auditoria_oc
from app import socketio
from datetime import datetime

bp = Blueprint('solicitacoes', __name__, url_prefix='/api/solicitacoes')

@bp.route('', methods=['GET'])
@jwt_required()
def listar_solicitacoes():
    usuario_id = get_jwt_identity()
    usuario = Usuario.query.get(usuario_id)
    
    status = request.args.get('status')
    fornecedor_id = request.args.get('fornecedor_id', type=int)
    busca = request.args.get('busca', '')
    
    query = Solicitacao.query
    
    if usuario.tipo == 'funcionario':
        query = query.filter_by(funcionario_id=usuario_id)
    
    if status:
        query = query.filter_by(status=status)
    
    if fornecedor_id:
        query = query.filter_by(fornecedor_id=fornecedor_id)
    
    if busca:
        query = query.join(Fornecedor).join(Usuario).filter(
            db.or_(
                Fornecedor.nome.ilike(f'%{busca}%'),
                Usuario.nome.ilike(f'%{busca}%')
            )
        )
    
    solicitacoes = query.order_by(Solicitacao.data_envio.desc()).all()
    
    return jsonify([solicitacao.to_dict() for solicitacao in solicitacoes]), 200

@bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def obter_solicitacao(id):
    try:
        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get(usuario_id)
        
        solicitacao = Solicitacao.query.get(id)
        
        if not solicitacao:
            return jsonify({'erro': 'Solicitação não encontrada'}), 404
        
        if usuario.tipo == 'funcionario' and solicitacao.funcionario_id != usuario_id:
            return jsonify({'erro': 'Acesso negado'}), 403
        
        solicitacao_dict = solicitacao.to_dict()
        solicitacao_dict['itens'] = [item.to_dict() for item in solicitacao.itens]
        
        return jsonify(solicitacao_dict), 200
    except Exception as e:
        return jsonify({'erro': f'Erro ao obter solicitação: {str(e)}'}), 500

@bp.route('', methods=['POST'])
@jwt_required()
def criar_solicitacao():
    try:
        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get(usuario_id)
        
        if usuario.tipo != 'funcionario':
            return jsonify({'erro': 'Apenas funcionários podem criar solicitações'}), 403
        
        data = request.get_json()
        
        if not data:
            return jsonify({'erro': 'Dados não fornecidos'}), 400
        
        fornecedor_id = data.get('fornecedor_id')
        if not fornecedor_id:
            return jsonify({'erro': 'Fornecedor é obrigatório'}), 400
        
        fornecedor = Fornecedor.query.get(fornecedor_id)
        if not fornecedor:
            return jsonify({'erro': 'Fornecedor não encontrado'}), 404
        
        solicitacao = Solicitacao(
            funcionario_id=usuario_id,
            fornecedor_id=fornecedor_id,
            tipo_retirada=data.get('tipo_retirada', 'buscar'),
            observacoes=data.get('observacoes', ''),
            rua=data.get('rua', ''),
            numero=data.get('numero', ''),
            cep=data.get('cep', ''),
            localizacao_lat=data.get('localizacao_lat'),
            localizacao_lng=data.get('localizacao_lng'),
            endereco_completo=data.get('endereco_completo', ''),
            status='pendente'
        )
        
        db.session.add(solicitacao)
        db.session.commit()
        
        if 'itens' in data and isinstance(data['itens'], list):
            for item_data in data['itens']:
                tipo_lote_id = item_data.get('tipo_lote_id')
                peso_kg = item_data.get('peso_kg', 0)
                estrelas_final = item_data.get('estrelas_final', 3)
                
                if not tipo_lote_id or peso_kg is None or peso_kg <= 0:
                    continue
                
                tipo_lote = TipoLote.query.get(tipo_lote_id)
                if not tipo_lote:
                    continue
                
                preco_config = FornecedorTipoLotePreco.query.filter_by(
                    fornecedor_id=fornecedor_id,
                    tipo_lote_id=tipo_lote_id,
                    estrelas=estrelas_final
                ).first()
                
                valor_calculado = 0.0
                if preco_config:
                    valor_calculado = peso_kg * preco_config.preco_por_kg
                
                item = ItemSolicitacao(
                    solicitacao_id=solicitacao.id,
                    tipo_lote_id=tipo_lote_id,
                    peso_kg=peso_kg,
                    estrelas_sugeridas_ia=item_data.get('estrelas_sugeridas_ia'),
                    estrelas_final=estrelas_final,
                    valor_calculado=valor_calculado,
                    imagem_url=item_data.get('imagem_url', ''),
                    observacoes=item_data.get('observacoes', '')
                )
                db.session.add(item)
            
            db.session.commit()
        
        admins = Usuario.query.filter_by(tipo='admin').all()
        for admin in admins:
            notificacao = Notificacao(
                usuario_id=admin.id,
                titulo='Nova Solicitação Criada',
                mensagem=f'{usuario.nome} criou uma nova solicitação para o fornecedor {fornecedor.nome}.'
            )
            db.session.add(notificacao)
        
        db.session.commit()
        
        socketio.emit('nova_notificacao', {'tipo': 'nova_solicitacao'}, room='admins')
        
        solicitacao_dict = solicitacao.to_dict()
        solicitacao_dict['itens'] = [item.to_dict() for item in solicitacao.itens]
        
        return jsonify(solicitacao_dict), 201
    
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
        solicitacao = Solicitacao.query.get(id)
        
        if not solicitacao:
            return jsonify({'erro': 'Solicitação não encontrada'}), 404
        
        if solicitacao.status != 'pendente':
            return jsonify({'erro': 'Solicitação já foi processada'}), 400
        
        if not solicitacao.itens or len(solicitacao.itens) == 0:
            return jsonify({'erro': 'Solicitação não possui itens'}), 400
        
        oc_existente = OrdemCompra.query.filter_by(solicitacao_id=id).first()
        if oc_existente:
            return jsonify({'erro': 'Já existe uma ordem de compra para esta solicitação'}), 400
        
        usuario_id = get_jwt_identity()
        data = request.get_json() or {}
        
        solicitacao.status = 'aprovada'
        solicitacao.data_confirmacao = datetime.utcnow()
        solicitacao.admin_id = usuario_id
        
        lotes_por_tipo = {}
        for item in solicitacao.itens:
            chave = (item.tipo_lote_id, item.estrelas_final)
            if chave not in lotes_por_tipo:
                lotes_por_tipo[chave] = []
            lotes_por_tipo[chave].append(item)
        
        for (tipo_lote_id, estrelas), itens in lotes_por_tipo.items():
            peso_total = sum(item.peso_kg for item in itens)
            valor_total = sum(item.valor_calculado for item in itens)
            estrelas_media = sum(item.estrelas_final for item in itens) / len(itens)
            
            lote = Lote(
                fornecedor_id=solicitacao.fornecedor_id,
                tipo_lote_id=tipo_lote_id,
                solicitacao_origem_id=solicitacao.id,
                peso_total_kg=peso_total,
                valor_total=valor_total,
                quantidade_itens=len(itens),
                estrelas_media=estrelas_media,
                tipo_retirada=solicitacao.tipo_retirada,
                status='aberto'
            )
            db.session.add(lote)
            db.session.flush()
            
            for item in itens:
                item.lote_id = lote.id
        
        valor_total_oc = sum((item.valor_calculado or 0.0) for item in solicitacao.itens)
        
        oc = OrdemCompra(
            solicitacao_id=id,
            fornecedor_id=solicitacao.fornecedor_id,
            valor_total=valor_total_oc,
            status='em_analise',
            criado_por=usuario_id,
            observacao=data.get('observacao', f'OC gerada automaticamente pela aprovação da solicitação #{id}')
        )
        db.session.add(oc)
        db.session.flush()
        
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        gps = data.get('gps')
        dispositivo = request.headers.get('User-Agent', '')
        
        registrar_auditoria_oc(
            oc_id=oc.id,
            usuario_id=usuario_id,
            acao='criacao',
            status_anterior=None,
            status_novo='em_analise',
            observacao=f'OC criada automaticamente pela aprovação da solicitação #{id}',
            ip=ip,
            gps=gps,
            dispositivo=dispositivo
        )
        
        notificacao_funcionario = Notificacao(
            usuario_id=solicitacao.funcionario_id,
            titulo='Solicitação Aprovada',
            mensagem=f'Sua solicitação #{solicitacao.id} foi aprovada, os lotes foram criados e a Ordem de Compra #{oc.id} foi gerada automaticamente.'
        )
        db.session.add(notificacao_funcionario)
        
        usuarios_financeiro = Usuario.query.join(Perfil).filter(
            db.or_(
                Usuario.tipo == 'admin',
                Perfil.nome.in_(['Administrador', 'Financeiro'])
            )
        ).all()
        
        usuarios_ids_notificados = set()
        for usuario_fin in usuarios_financeiro:
            if usuario_fin.id not in usuarios_ids_notificados and usuario_fin.id != solicitacao.funcionario_id:
                notificacao_financeiro = Notificacao(
                    usuario_id=usuario_fin.id,
                    titulo='Nova Ordem de Compra',
                    mensagem=f'Nova Ordem de Compra #{oc.id} criada automaticamente e aguardando aprovação (Solicitação #{solicitacao.id}).'
                )
                db.session.add(notificacao_financeiro)
                usuarios_ids_notificados.add(usuario_fin.id)
        
        db.session.commit()
        
        socketio.emit('nova_notificacao', {'tipo': 'solicitacao_aprovada', 'solicitacao_id': id}, room='funcionarios')
        socketio.emit('nova_notificacao', {'tipo': 'nova_oc', 'oc_id': oc.id}, room='admins')
        
        return jsonify({
            'mensagem': 'Solicitação aprovada, lotes criados e Ordem de Compra gerada com sucesso',
            'solicitacao': solicitacao.to_dict(),
            'oc_id': oc.id,
            'oc_status': oc.status
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
            return jsonify({'erro': 'Solicitação já foi processada'}), 400
        
        usuario_id = get_jwt_identity()
        data = request.get_json() or {}
        
        solicitacao.status = 'rejeitada'
        solicitacao.data_confirmacao = datetime.utcnow()
        solicitacao.admin_id = usuario_id
        solicitacao.observacoes = (solicitacao.observacoes or '') + '\n' + data.get('motivo_rejeicao', '')
        
        db.session.commit()
        
        notificacao = Notificacao(
            usuario_id=solicitacao.funcionario_id,
            titulo='Solicitação Rejeitada',
            mensagem=f'Sua solicitação #{solicitacao.id} foi rejeitada. Motivo: {data.get("motivo_rejeicao", "Não especificado")}'
        )
        db.session.add(notificacao)
        db.session.commit()
        
        socketio.emit('nova_notificacao', {'tipo': 'solicitacao_rejeitada', 'solicitacao_id': id}, room='funcionarios')
        
        return jsonify({
            'mensagem': 'Solicitação rejeitada com sucesso',
            'solicitacao': solicitacao.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao rejeitar solicitação: {str(e)}'}), 500

@bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def deletar_solicitacao(id):
    try:
        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get(usuario_id)
        
        solicitacao = Solicitacao.query.get(id)
        
        if not solicitacao:
            return jsonify({'erro': 'Solicitação não encontrada'}), 404
        
        if usuario.tipo == 'funcionario' and solicitacao.funcionario_id != usuario_id:
            return jsonify({'erro': 'Acesso negado'}), 403
        
        if solicitacao.status != 'pendente':
            return jsonify({'erro': 'Apenas solicitações pendentes podem ser deletadas'}), 400
        
        db.session.delete(solicitacao)
        db.session.commit()
        
        return jsonify({'mensagem': 'Solicitação deletada com sucesso'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao deletar solicitação: {str(e)}'}), 500
