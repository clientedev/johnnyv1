from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Lote, MovimentacaoEstoque, Inventario, InventarioContagem, Usuario
from app.auth import admin_required
from datetime import datetime
import json

bp = Blueprint('wms', __name__, url_prefix='/api/wms')

# ==================== LOTES WMS ====================

@bp.route('/lotes', methods=['GET'])
@jwt_required()
def listar_lotes_wms():
    try:
        status = request.args.get('status')
        fornecedor_id = request.args.get('fornecedor_id', type=int)
        tipo_lote_id = request.args.get('tipo_lote_id', type=int)
        localizacao = request.args.get('localizacao')
        bloqueado = request.args.get('bloqueado')
        reservado = request.args.get('reservado')
        divergente = request.args.get('divergente')
        
        query = Lote.query
        
        if status:
            query = query.filter_by(status=status)
        if fornecedor_id:
            query = query.filter_by(fornecedor_id=fornecedor_id)
        if tipo_lote_id:
            query = query.filter_by(tipo_lote_id=tipo_lote_id)
        if localizacao:
            query = query.filter_by(localizacao_atual=localizacao)
        if bloqueado is not None:
            query = query.filter_by(bloqueado=bloqueado.lower() == 'true')
        if reservado is not None:
            query = query.filter_by(reservado=reservado.lower() == 'true')
        if divergente is not None:
            if divergente.lower() == 'true':
                query = query.filter(Lote.divergencias != None, Lote.divergencias != '[]')
        
        lotes = query.order_by(Lote.data_criacao.desc()).all()
        
        resultado = []
        for lote in lotes:
            lote_dict = lote.to_dict()
            lote_dict['itens_count'] = len(lote.itens)
            lote_dict['sublotes_count'] = len(lote.sublotes)
            resultado.append(lote_dict)
        
        return jsonify(resultado), 200
    
    except Exception as e:
        return jsonify({'erro': f'Erro ao listar lotes: {str(e)}'}), 500

@bp.route('/lotes/<int:lote_id>', methods=['GET'])
@jwt_required()
def obter_lote_detalhado(lote_id):
    try:
        lote = Lote.query.get(lote_id)
        
        if not lote:
            return jsonify({'erro': 'Lote não encontrado'}), 404
        
        lote_dict = lote.to_dict()
        lote_dict['itens'] = [item.to_dict() for item in lote.itens]
        lote_dict['sublotes'] = [sublote.to_dict() for sublote in lote.sublotes]
        lote_dict['movimentacoes'] = [mov.to_dict() for mov in lote.movimentacoes]
        
        if lote.solicitacao_origem:
            lote_dict['solicitacao_origem'] = lote.solicitacao_origem.to_dict()
        if lote.ordem_compra:
            lote_dict['ordem_compra'] = lote.ordem_compra.to_dict()
        if lote.ordem_servico:
            lote_dict['ordem_servico'] = lote.ordem_servico.to_dict()
        if lote.conferencia:
            lote_dict['conferencia'] = lote.conferencia.to_dict()
        if lote.separacao:
            lote_dict['separacao'] = lote.separacao.to_dict()
        
        return jsonify(lote_dict), 200
    
    except Exception as e:
        return jsonify({'erro': f'Erro ao obter lote: {str(e)}'}), 500

@bp.route('/lotes/<int:lote_id>/bloquear', methods=['POST'])
@admin_required
def bloquear_lote(lote_id):
    try:
        lote = Lote.query.get(lote_id)
        if not lote:
            return jsonify({'erro': 'Lote não encontrado'}), 404
        
        if lote.bloqueado:
            return jsonify({'erro': 'Lote já está bloqueado'}), 400
        
        data = request.get_json()
        tipo_bloqueio = data.get('tipo_bloqueio', 'QC')
        motivo = data.get('motivo', '')
        
        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get(usuario_id)
        
        dados_before = lote.to_dict()
        
        lote.bloqueado = True
        lote.tipo_bloqueio = tipo_bloqueio
        lote.motivo_bloqueio = motivo
        lote.bloqueado_por_id = usuario_id
        lote.bloqueado_em = datetime.utcnow()
        
        auditoria = lote.auditoria or []
        auditoria.append({
            'acao': 'BLOQUEAR_LOTE',
            'usuario_id': usuario_id,
            'usuario_nome': usuario.nome,
            'tipo_bloqueio': tipo_bloqueio,
            'motivo': motivo,
            'timestamp': datetime.utcnow().isoformat(),
            'ip': request.remote_addr,
            'dados_before': dados_before
        })
        lote.auditoria = auditoria
        
        db.session.commit()
        
        return jsonify({
            'mensagem': f'Lote bloqueado para {tipo_bloqueio}',
            'lote': lote.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao bloquear lote: {str(e)}'}), 500

@bp.route('/lotes/<int:lote_id>/desbloquear', methods=['POST'])
@admin_required
def desbloquear_lote(lote_id):
    try:
        lote = Lote.query.get(lote_id)
        if not lote:
            return jsonify({'erro': 'Lote não encontrado'}), 404
        
        if not lote.bloqueado:
            return jsonify({'erro': 'Lote não está bloqueado'}), 400
        
        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get(usuario_id)
        
        dados_before = lote.to_dict()
        tipo_bloqueio_anterior = lote.tipo_bloqueio
        
        lote.bloqueado = False
        lote.tipo_bloqueio = None
        lote.motivo_bloqueio = None
        
        auditoria = lote.auditoria or []
        auditoria.append({
            'acao': 'DESBLOQUEAR_LOTE',
            'usuario_id': usuario_id,
            'usuario_nome': usuario.nome,
            'tipo_bloqueio_anterior': tipo_bloqueio_anterior,
            'timestamp': datetime.utcnow().isoformat(),
            'ip': request.remote_addr,
            'dados_before': dados_before
        })
        lote.auditoria = auditoria
        
        db.session.commit()
        
        return jsonify({
            'mensagem': 'Lote desbloqueado com sucesso',
            'lote': lote.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao desbloquear lote: {str(e)}'}), 500

@bp.route('/lotes/<int:lote_id>/reservar', methods=['POST'])
@jwt_required()
def reservar_lote(lote_id):
    try:
        lote = Lote.query.get(lote_id)
        if not lote:
            return jsonify({'erro': 'Lote não encontrado'}), 404
        
        if lote.reservado:
            return jsonify({'erro': 'Lote já está reservado'}), 400
        
        if lote.bloqueado:
            return jsonify({'erro': 'Não é possível reservar lote bloqueado'}), 400
        
        data = request.get_json()
        reservado_para = data.get('reservado_para', '')
        
        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get(usuario_id)
        
        dados_before = lote.to_dict()
        
        lote.reservado = True
        lote.reservado_para = reservado_para
        lote.reservado_por_id = usuario_id
        lote.reservado_em = datetime.utcnow()
        
        auditoria = lote.auditoria or []
        auditoria.append({
            'acao': 'RESERVAR_LOTE',
            'usuario_id': usuario_id,
            'usuario_nome': usuario.nome,
            'reservado_para': reservado_para,
            'timestamp': datetime.utcnow().isoformat(),
            'ip': request.remote_addr,
            'dados_before': dados_before
        })
        lote.auditoria = auditoria
        
        db.session.commit()
        
        return jsonify({
            'mensagem': 'Lote reservado com sucesso',
            'lote': lote.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao reservar lote: {str(e)}'}), 500

@bp.route('/lotes/<int:lote_id>/liberar-reserva', methods=['POST'])
@jwt_required()
def liberar_reserva_lote(lote_id):
    try:
        lote = Lote.query.get(lote_id)
        if not lote:
            return jsonify({'erro': 'Lote não encontrado'}), 404
        
        if not lote.reservado:
            return jsonify({'erro': 'Lote não está reservado'}), 400
        
        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get(usuario_id)
        
        dados_before = lote.to_dict()
        reservado_para_anterior = lote.reservado_para
        
        lote.reservado = False
        lote.reservado_para = None
        lote.reservado_por_id = None
        lote.reservado_em = None
        
        auditoria = lote.auditoria or []
        auditoria.append({
            'acao': 'LIBERAR_RESERVA',
            'usuario_id': usuario_id,
            'usuario_nome': usuario.nome,
            'reservado_para_anterior': reservado_para_anterior,
            'timestamp': datetime.utcnow().isoformat(),
            'ip': request.remote_addr,
            'dados_before': dados_before
        })
        lote.auditoria = auditoria
        
        db.session.commit()
        
        return jsonify({
            'mensagem': 'Reserva liberada com sucesso',
            'lote': lote.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao liberar reserva: {str(e)}'}), 500

# ==================== MOVIMENTAÇÕES ====================

@bp.route('/lotes/<int:lote_id>/movimentar', methods=['POST'])
@jwt_required()
def movimentar_lote(lote_id):
    try:
        lote = Lote.query.get(lote_id)
        if not lote:
            return jsonify({'erro': 'Lote não encontrado'}), 404
        
        if lote.bloqueado:
            return jsonify({'erro': 'Não é possível movimentar lote bloqueado'}), 400
        
        data = request.get_json()
        tipo = data.get('tipo', 'transferencia')
        localizacao_destino = data.get('localizacao_destino')
        quantidade = data.get('quantidade')
        peso = data.get('peso')
        observacoes = data.get('observacoes', '')
        gps = data.get('gps')
        
        if not localizacao_destino:
            return jsonify({'erro': 'Localização destino é obrigatória'}), 400
        
        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get(usuario_id)
        
        dados_before = lote.to_dict()
        
        movimentacao = MovimentacaoEstoque(
            lote_id=lote_id,
            tipo=tipo,
            localizacao_origem=lote.localizacao_atual,
            localizacao_destino=localizacao_destino,
            quantidade=quantidade,
            peso=peso,
            usuario_id=usuario_id,
            observacoes=observacoes,
            dados_before=dados_before
        )
        
        lote.localizacao_atual = localizacao_destino
        
        movimentacao.dados_after = lote.to_dict()
        
        auditoria_mov = [{
            'usuario_id': usuario_id,
            'usuario_nome': usuario.nome,
            'timestamp': datetime.utcnow().isoformat(),
            'ip': request.remote_addr,
            'gps': gps,
            'device_id': data.get('device_id')
        }]
        movimentacao.auditoria = auditoria_mov
        
        auditoria_lote = lote.auditoria or []
        auditoria_lote.append({
            'acao': 'MOVIMENTACAO',
            'usuario_id': usuario_id,
            'usuario_nome': usuario.nome,
            'tipo': tipo,
            'localizacao_origem': movimentacao.localizacao_origem,
            'localizacao_destino': localizacao_destino,
            'timestamp': datetime.utcnow().isoformat(),
            'ip': request.remote_addr,
            'gps': gps
        })
        lote.auditoria = auditoria_lote
        
        db.session.add(movimentacao)
        db.session.commit()
        
        return jsonify({
            'mensagem': 'Movimentação registrada com sucesso',
            'movimentacao': movimentacao.to_dict(),
            'lote': lote.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao movimentar lote: {str(e)}'}), 500

@bp.route('/movimentacoes', methods=['GET'])
@jwt_required()
def listar_movimentacoes():
    try:
        lote_id = request.args.get('lote_id', type=int)
        tipo = request.args.get('tipo')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        query = MovimentacaoEstoque.query
        
        if lote_id:
            query = query.filter_by(lote_id=lote_id)
        if tipo:
            query = query.filter_by(tipo=tipo)
        if data_inicio:
            query = query.filter(MovimentacaoEstoque.data_movimentacao >= datetime.fromisoformat(data_inicio))
        if data_fim:
            query = query.filter(MovimentacaoEstoque.data_movimentacao <= datetime.fromisoformat(data_fim))
        
        movimentacoes = query.order_by(MovimentacaoEstoque.data_movimentacao.desc()).limit(100).all()
        
        return jsonify([mov.to_dict() for mov in movimentacoes]), 200
    
    except Exception as e:
        return jsonify({'erro': f'Erro ao listar movimentações: {str(e)}'}), 500

@bp.route('/movimentacoes/<int:mov_id>/reverter', methods=['POST'])
@admin_required
def reverter_movimentacao(mov_id):
    try:
        movimentacao = MovimentacaoEstoque.query.get(mov_id)
        if not movimentacao:
            return jsonify({'erro': 'Movimentação não encontrada'}), 404
        
        lote = movimentacao.lote
        
        data = request.get_json()
        motivo = data.get('motivo', '')
        
        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get(usuario_id)
        
        nova_movimentacao = MovimentacaoEstoque(
            lote_id=lote.id,
            tipo='reversao',
            localizacao_origem=movimentacao.localizacao_destino,
            localizacao_destino=movimentacao.localizacao_origem,
            quantidade=movimentacao.quantidade,
            peso=movimentacao.peso,
            usuario_id=usuario_id,
            observacoes=f'Reversão da movimentação #{mov_id}. Motivo: {motivo}',
            dados_before={'movimentacao_revertida_id': mov_id}
        )
        
        lote.localizacao_atual = movimentacao.localizacao_origem
        
        nova_movimentacao.dados_after = lote.to_dict()
        
        auditoria_mov = [{
            'usuario_id': usuario_id,
            'usuario_nome': usuario.nome,
            'acao': 'REVERSAO',
            'movimentacao_revertida_id': mov_id,
            'motivo': motivo,
            'timestamp': datetime.utcnow().isoformat(),
            'ip': request.remote_addr
        }]
        nova_movimentacao.auditoria = auditoria_mov
        
        db.session.add(nova_movimentacao)
        db.session.commit()
        
        return jsonify({
            'mensagem': 'Movimentação revertida com sucesso',
            'movimentacao': nova_movimentacao.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao reverter movimentação: {str(e)}'}), 500

# ==================== INVENTÁRIO ====================

@bp.route('/inventarios', methods=['POST'])
@admin_required
def iniciar_inventario():
    try:
        data = request.get_json()
        tipo = data.get('tipo', 'GERAL')
        localizacao = data.get('localizacao')
        observacoes = data.get('observacoes', '')
        
        usuario_id = get_jwt_identity()
        
        inventario = Inventario(
            tipo=tipo,
            localizacao=localizacao,
            criado_por_id=usuario_id,
            observacoes=observacoes
        )
        
        auditoria = [{
            'acao': 'CRIAR_INVENTARIO',
            'usuario_id': usuario_id,
            'timestamp': datetime.utcnow().isoformat(),
            'ip': request.remote_addr,
            'tipo': tipo,
            'localizacao': localizacao
        }]
        inventario.auditoria = auditoria
        
        if localizacao:
            lotes = Lote.query.filter_by(localizacao_atual=localizacao).all()
        else:
            lotes = Lote.query.filter(Lote.status.in_(['EM_ESTOQUE', 'BLOQUEADO_QC', 'BLOQUEADO_INVENTARIO'])).all()
        
        for lote in lotes:
            lote.bloqueado = True
            lote.tipo_bloqueio = 'INVENTARIO'
            lote.motivo_bloqueio = f'Inventário {inventario.numero_inventario}'
            lote.bloqueado_por_id = usuario_id
            lote.bloqueado_em = datetime.utcnow()
        
        db.session.add(inventario)
        db.session.commit()
        
        return jsonify({
            'mensagem': f'Inventário iniciado. {len(lotes)} lotes bloqueados.',
            'inventario': inventario.to_dict(),
            'lotes_bloqueados': len(lotes)
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao iniciar inventário: {str(e)}'}), 500

@bp.route('/inventarios/<int:inv_id>/contagem', methods=['POST'])
@jwt_required()
def registrar_contagem(inv_id):
    try:
        inventario = Inventario.query.get(inv_id)
        if not inventario:
            return jsonify({'erro': 'Inventário não encontrado'}), 404
        
        if inventario.status != 'EM_ANDAMENTO':
            return jsonify({'erro': 'Inventário não está em andamento'}), 400
        
        data = request.get_json()
        lote_id = data.get('lote_id')
        numero_contagem = data.get('numero_contagem', 1)
        quantidade_contada = data.get('quantidade_contada')
        peso_contado = data.get('peso_contado')
        localizacao_encontrada = data.get('localizacao_encontrada')
        observacoes = data.get('observacoes', '')
        fotos = data.get('fotos', [])
        gps = data.get('gps')
        device_id = data.get('device_id')
        
        if not lote_id:
            return jsonify({'erro': 'lote_id é obrigatório'}), 400
        
        if numero_contagem < 1 or numero_contagem > 3:
            return jsonify({'erro': 'Número da contagem deve ser 1, 2 ou 3'}), 400
        
        lote = Lote.query.get(lote_id)
        if not lote:
            return jsonify({'erro': 'Lote não encontrado'}), 404
        
        usuario_id = get_jwt_identity()
        
        contagem_existente = InventarioContagem.query.filter_by(
            inventario_id=inv_id,
            lote_id=lote_id,
            numero_contagem=numero_contagem
        ).first()
        
        if contagem_existente:
            return jsonify({'erro': f'Contagem {numero_contagem} já foi registrada para este lote'}), 400
        
        contagem = InventarioContagem(
            inventario_id=inv_id,
            lote_id=lote_id,
            numero_contagem=numero_contagem,
            quantidade_contada=quantidade_contada,
            peso_contado=peso_contado,
            localizacao_encontrada=localizacao_encontrada,
            contador_id=usuario_id,
            observacoes=observacoes,
            fotos=fotos,
            gps=gps,
            device_id=device_id
        )
        
        db.session.add(contagem)
        db.session.commit()
        
        return jsonify({
            'mensagem': f'Contagem {numero_contagem} registrada com sucesso',
            'contagem': contagem.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao registrar contagem: {str(e)}'}), 500

@bp.route('/inventarios/<int:inv_id>/finalizar', methods=['POST'])
@admin_required
def finalizar_inventario(inv_id):
    try:
        inventario = Inventario.query.get(inv_id)
        if not inventario:
            return jsonify({'erro': 'Inventário não encontrado'}), 404
        
        if inventario.status != 'EM_ANDAMENTO':
            return jsonify({'erro': 'Inventário não está em andamento'}), 400
        
        usuario_id = get_jwt_identity()
        
        inventario.status = 'FINALIZADO'
        inventario.data_finalizacao = datetime.utcnow()
        inventario.finalizado_por_id = usuario_id
        
        if inventario.localizacao:
            lotes = Lote.query.filter_by(
                localizacao_atual=inventario.localizacao,
                bloqueado=True,
                tipo_bloqueio='INVENTARIO'
            ).all()
        else:
            lotes = Lote.query.filter_by(
                bloqueado=True,
                tipo_bloqueio='INVENTARIO'
            ).all()
        
        for lote in lotes:
            if lote.motivo_bloqueio and inventario.numero_inventario in lote.motivo_bloqueio:
                lote.bloqueado = False
                lote.tipo_bloqueio = None
                lote.motivo_bloqueio = None
        
        auditoria = inventario.auditoria or []
        auditoria.append({
            'acao': 'FINALIZAR_INVENTARIO',
            'usuario_id': usuario_id,
            'timestamp': datetime.utcnow().isoformat(),
            'ip': request.remote_addr,
            'lotes_desbloqueados': len(lotes)
        })
        inventario.auditoria = auditoria
        
        db.session.commit()
        
        return jsonify({
            'mensagem': f'Inventário finalizado. {len(lotes)} lotes desbloqueados.',
            'inventario': inventario.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao finalizar inventário: {str(e)}'}), 500

@bp.route('/inventarios/<int:inv_id>/consolidar', methods=['POST'])
@admin_required
def consolidar_inventario(inv_id):
    try:
        inventario = Inventario.query.get(inv_id)
        if not inventario:
            return jsonify({'erro': 'Inventário não encontrado'}), 404
        
        contagens = InventarioContagem.query.filter_by(inventario_id=inv_id).all()
        
        lotes_contados = {}
        for contagem in contagens:
            if contagem.lote_id not in lotes_contados:
                lotes_contados[contagem.lote_id] = {
                    'lote_numero': contagem.lote.numero_lote,
                    'contagens': {}
                }
            
            lotes_contados[contagem.lote_id]['contagens'][contagem.numero_contagem] = {
                'quantidade': contagem.quantidade_contada,
                'peso': contagem.peso_contado,
                'localizacao': contagem.localizacao_encontrada,
                'contador': contagem.contador.nome
            }
        
        divergencias = []
        for lote_id, dados in lotes_contados.items():
            contagens_dict = dados['contagens']
            
            if len(contagens_dict) >= 2:
                contagem_1 = contagens_dict.get(1, {}).get('peso')
                contagem_2 = contagens_dict.get(2, {}).get('peso')
                contagem_3 = contagens_dict.get(3, {}).get('peso')
                
                lote = Lote.query.get(lote_id)
                peso_sistema = lote.peso_total_kg if lote else 0
                
                if contagem_1 != contagem_2:
                    divergencias.append({
                        'lote_id': lote_id,
                        'lote_numero': dados['lote_numero'],
                        'peso_sistema': peso_sistema,
                        'contagem_1': contagem_1,
                        'contagem_2': contagem_2,
                        'contagem_3': contagem_3,
                        'status': 'DIVERGENTE'
                    })
        
        inventario.divergencias_consolidadas = divergencias
        
        auditoria = inventario.auditoria or []
        auditoria.append({
            'acao': 'CONSOLIDAR_INVENTARIO',
            'usuario_id': get_jwt_identity(),
            'timestamp': datetime.utcnow().isoformat(),
            'ip': request.remote_addr,
            'total_divergencias': len(divergencias)
        })
        inventario.auditoria = auditoria
        
        db.session.commit()
        
        return jsonify({
            'mensagem': 'Inventário consolidado',
            'total_lotes': len(lotes_contados),
            'divergencias': divergencias
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao consolidar inventário: {str(e)}'}), 500

@bp.route('/inventarios', methods=['GET'])
@jwt_required()
def listar_inventarios():
    try:
        status = request.args.get('status')
        
        query = Inventario.query
        
        if status:
            query = query.filter_by(status=status)
        
        inventarios = query.order_by(Inventario.data_inicio.desc()).all()
        
        resultado = []
        for inv in inventarios:
            inv_dict = inv.to_dict()
            inv_dict['total_contagens'] = len(inv.contagens)
            resultado.append(inv_dict)
        
        return jsonify(resultado), 200
    
    except Exception as e:
        return jsonify({'erro': f'Erro ao listar inventários: {str(e)}'}), 500

@bp.route('/inventarios/<int:inv_id>', methods=['GET'])
@jwt_required()
def obter_inventario(inv_id):
    try:
        inventario = Inventario.query.get(inv_id)
        if not inventario:
            return jsonify({'erro': 'Inventário não encontrado'}), 404
        
        inv_dict = inventario.to_dict()
        inv_dict['contagens'] = [c.to_dict() for c in inventario.contagens]
        
        return jsonify(inv_dict), 200
    
    except Exception as e:
        return jsonify({'erro': f'Erro ao obter inventário: {str(e)}'}), 500

# ==================== AUDITORIA ====================

@bp.route('/auditoria/lotes/<int:lote_id>', methods=['GET'])
@jwt_required()
def obter_auditoria_lote(lote_id):
    try:
        lote = Lote.query.get(lote_id)
        if not lote:
            return jsonify({'erro': 'Lote não encontrado'}), 404
        
        return jsonify({
            'lote_id': lote_id,
            'numero_lote': lote.numero_lote,
            'auditoria': lote.auditoria or []
        }), 200
    
    except Exception as e:
        return jsonify({'erro': f'Erro ao obter auditoria: {str(e)}'}), 500

# ==================== ESTATÍSTICAS ====================

@bp.route('/estatisticas', methods=['GET'])
@jwt_required()
def obter_estatisticas():
    try:
        total_lotes = Lote.query.count()
        lotes_bloqueados = Lote.query.filter_by(bloqueado=True).count()
        lotes_reservados = Lote.query.filter_by(reservado=True).count()
        lotes_divergentes = Lote.query.filter(Lote.divergencias != None, Lote.divergencias != '[]').count()
        
        peso_total = db.session.query(db.func.sum(Lote.peso_total_kg)).scalar() or 0
        
        lotes_por_status = db.session.query(
            Lote.status,
            db.func.count(Lote.id)
        ).group_by(Lote.status).all()
        
        lotes_por_localizacao = db.session.query(
            Lote.localizacao_atual,
            db.func.count(Lote.id),
            db.func.sum(Lote.peso_total_kg)
        ).group_by(Lote.localizacao_atual).all()
        
        movimentacoes_recentes = MovimentacaoEstoque.query.order_by(
            MovimentacaoEstoque.data_movimentacao.desc()
        ).limit(20).all()
        
        return jsonify({
            'total_lotes': total_lotes,
            'lotes_bloqueados': lotes_bloqueados,
            'lotes_reservados': lotes_reservados,
            'lotes_divergentes': lotes_divergentes,
            'peso_total_kg': round(peso_total, 2),
            'lotes_por_status': [{'status': s, 'quantidade': q} for s, q in lotes_por_status],
            'lotes_por_localizacao': [
                {'localizacao': loc or 'SEM_LOCALIZACAO', 'quantidade': q, 'peso_kg': round(p or 0, 2)}
                for loc, q, p in lotes_por_localizacao
            ],
            'movimentacoes_recentes': [mov.to_dict() for mov in movimentacoes_recentes]
        }), 200
    
    except Exception as e:
        return jsonify({'erro': f'Erro ao obter estatísticas: {str(e)}'}), 500
