from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Fornecedor, Notificacao, Solicitacao, ItemSolicitacao, Usuario, TipoLote, FornecedorTipoLotePreco, FornecedorTipoLoteClassificacao, Lote, OrdemCompra, AuditoriaOC, Perfil, db
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
        
        print(f"\n{'='*60}")
        print(f"🆕 NOVA SOLICITAÇÃO #{solicitacao.id} CRIADA")
        print(f"   Fornecedor: {fornecedor.nome}")
        print(f"   Total de itens: {len(data.get('itens', []))}")
        print(f"{'='*60}")
        
        if 'itens' in data and isinstance(data['itens'], list):
            for item_data in data['itens']:
                print(f"\n📦 Dados recebidos do frontend:")
                print(f"   {item_data}")
                
                tipo_lote_id = item_data.get('tipo_lote_id')
                peso_kg = item_data.get('peso_kg', 0)
                classificacao = item_data.get('classificacao', 'medio')
                estrelas_final = item_data.get('estrelas_final', 3)
                
                print(f"\n🔍 DEBUG - Processando item:")
                print(f"   Tipo Lote ID: {tipo_lote_id}")
                print(f"   Peso: {peso_kg} kg")
                print(f"   Classificação: {classificacao}")
                print(f"   Estrelas (frontend): {estrelas_final}")
                
                if not tipo_lote_id or peso_kg is None or peso_kg <= 0:
                    print(f"   ⚠️ Item inválido - pulando")
                    continue
                
                tipo_lote = TipoLote.query.get(tipo_lote_id)
                if not tipo_lote:
                    print(f"   ❌ Tipo de lote não encontrado")
                    continue
                
                print(f"   ✅ Tipo de lote: {tipo_lote.nome}")
                
                # Buscar configuração de preço por classificação
                from app.models import FornecedorTipoLoteClassificacao
                classificacao_config = FornecedorTipoLoteClassificacao.query.filter_by(
                    fornecedor_id=fornecedor_id,
                    tipo_lote_id=tipo_lote_id,
                    ativo=True
                ).first()
                
                # Se existe configuração de classificação, usar as estrelas correspondentes
                if classificacao_config:
                    estrelas_final = classificacao_config.get_estrelas_por_classificacao(classificacao)
                    print(f"   ✅ Configuração de classificação encontrada")
                    print(f"   ⭐ Estrelas (backend): {estrelas_final}")
                else:
                    print(f"   ⚠️ Nenhuma configuração de classificação encontrada - usando estrelas do frontend")
                
                # Buscar preço baseado nas estrelas
                preco_config = FornecedorTipoLotePreco.query.filter_by(
                    fornecedor_id=fornecedor_id,
                    tipo_lote_id=tipo_lote_id,
                    estrelas=estrelas_final,
                    ativo=True
                ).first()
                
                valor_calculado = 0.0
                preco_por_kg = 0.0
                if preco_config:
                    preco_por_kg = preco_config.preco_por_kg
                    valor_calculado = peso_kg * preco_por_kg
                    print(f"   ✅ Preço encontrado: R$ {preco_por_kg}/kg")
                    print(f"   💰 Valor calculado: R$ {valor_calculado:.2f}")
                else:
                    print(f"   ❌ PROBLEMA: Preço não encontrado para {estrelas_final} estrelas!")
                    print(f"   🔍 Buscando preços disponíveis para este tipo de lote...")
                    precos_disponiveis = FornecedorTipoLotePreco.query.filter_by(
                        fornecedor_id=fornecedor_id,
                        tipo_lote_id=tipo_lote_id,
                        ativo=True
                    ).all()
                    if precos_disponiveis:
                        print(f"   📋 Preços disponíveis:")
                        for p in precos_disponiveis:
                            print(f"      - {p.estrelas} estrelas: R$ {p.preco_por_kg}/kg")
                    else:
                        print(f"   ⚠️ Nenhum preço cadastrado para este fornecedor e tipo de lote!")
                
                item = ItemSolicitacao(
                    solicitacao_id=solicitacao.id,
                    tipo_lote_id=tipo_lote_id,
                    peso_kg=peso_kg,
                    classificacao=classificacao,
                    estrelas_sugeridas_ia=item_data.get('estrelas_sugeridas_ia'),
                    estrelas_final=estrelas_final,
                    valor_calculado=valor_calculado,
                    preco_por_kg_snapshot=preco_por_kg,
                    estrelas_snapshot=estrelas_final,
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
        print(f"\n{'='*60}")
        print(f"🔄 INICIANDO APROVAÇÃO DA SOLICITAÇÃO #{id}")
        print(f"{'='*60}")
        
        usuario_id = get_jwt_identity()
        data = request.get_json() or {}
        
        print(f"\n🔒 Adquirindo lock na solicitação...")
        # Usar lock FOR UPDATE na solicitação para evitar condições de corrida
        # Isso garante que apenas uma thread processe esta solicitação por vez
        solicitacao = Solicitacao.query.filter_by(id=id).with_for_update().first()
        
        if not solicitacao:
            print(f"❌ Solicitação #{id} não encontrada")
            return jsonify({'erro': 'Solicitação não encontrada'}), 404
        
        print(f"✅ Lock adquirido: Solicitação #{solicitacao.id}")
        print(f"   Status atual: {solicitacao.status}")
        print(f"   Fornecedor: {solicitacao.fornecedor.nome if solicitacao.fornecedor else 'N/A'}")
        
        # Verificar status após obter o lock
        if solicitacao.status != 'pendente':
            print(f"❌ Status inválido: {solicitacao.status}")
            return jsonify({'erro': f'Solicitação já foi processada (status: {solicitacao.status})'}), 400
        
        # Verificar se tem itens
        if not solicitacao.itens or len(solicitacao.itens) == 0:
            print(f"❌ Solicitação sem itens")
            return jsonify({'erro': 'Solicitação não possui itens'}), 400
        
        print(f"✅ Solicitação possui {len(solicitacao.itens)} itens")
        
        # Validar que todos os itens têm valores calculados (aceita zero, rejeita None e negativos)
        itens_sem_preco = [item for item in solicitacao.itens if item.valor_calculado is None or item.valor_calculado < 0]
        if itens_sem_preco:
            print(f"❌ Existem {len(itens_sem_preco)} itens sem preço configurado ou com valor inválido")
            return jsonify({
                'erro': f'Existem {len(itens_sem_preco)} itens sem preço configurado ou com valor inválido. Configure os preços antes de aprovar.',
                'itens_sem_preco': len(itens_sem_preco)
            }), 400
        
        # Verificar se já existe OC (proteção adicional ao constraint do banco)
        oc_existente = OrdemCompra.query.filter_by(solicitacao_id=id).first()
        if oc_existente:
            print(f"⚠️ Já existe OC #{oc_existente.id} para esta solicitação")
            return jsonify({
                'erro': f'Já existe uma ordem de compra (#{oc_existente.id}) para esta solicitação',
                'oc_id': oc_existente.id
            }), 400
        
        print(f"\n📝 ETAPA 1: Atualizando status da solicitação...")
        # ETAPA 1: Aprovar a solicitação
        solicitacao.status = 'aprovada'
        solicitacao.data_confirmacao = datetime.utcnow()
        solicitacao.admin_id = usuario_id
        print(f"✅ Status atualizado para: aprovada")
        
        print(f"\n📦 ETAPA 2: Criando lotes...")
        # ETAPA 2: Criar lotes
        lotes_por_tipo = {}
        for item in solicitacao.itens:
            chave = (item.tipo_lote_id, item.estrelas_final)
            if chave not in lotes_por_tipo:
                lotes_por_tipo[chave] = []
            lotes_por_tipo[chave].append(item)
        
        lotes_criados = []
        for (tipo_lote_id, estrelas), itens in lotes_por_tipo.items():
            peso_total = sum(item.peso_kg for item in itens)
            valor_total = sum((item.valor_calculado or 0.0) for item in itens)
            estrelas_media = sum((item.estrelas_final or 3) for item in itens) / len(itens)
            
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
            
            print(f"   ✅ Lote criado: {lote.numero_lote} (Tipo: {tipo_lote_id}, Estrelas: {estrelas})")
            lotes_criados.append(lote.numero_lote)
            
            for item in itens:
                item.lote_id = lote.id
        
        print(f"✅ {len(lotes_criados)} lote(s) criado(s): {', '.join(lotes_criados)}")
        
        print(f"\n💰 ETAPA 3: Criando Ordem de Compra...")
        # ETAPA 3: Criar OC
        valor_total_oc = sum((item.valor_calculado or 0.0) for item in solicitacao.itens)
        print(f"   Valor total calculado: R$ {valor_total_oc:.2f}")
        
        if valor_total_oc < 0:
            raise ValueError('Valor total da OC não pode ser negativo')
        
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
        
        print(f"✅ OC #{oc.id} criada com sucesso")
        print(f"   Status: {oc.status}")
        print(f"   Valor: R$ {oc.valor_total:.2f}")
        
        print(f"\n📋 ETAPA 4: Registrando auditoria...")
        # ETAPA 4: Registrar auditoria
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
        print(f"✅ Auditoria registrada")
        
        print(f"\n🔔 ETAPA 5: Criando notificações...")
        # ETAPA 5: Criar notificações
        notificacao_funcionario = Notificacao(
            usuario_id=solicitacao.funcionario_id,
            titulo='Solicitação Aprovada',
            mensagem=f'Sua solicitação #{solicitacao.id} foi aprovada, os lotes foram criados e a Ordem de Compra #{oc.id} foi gerada automaticamente.'
        )
        db.session.add(notificacao_funcionario)
        print(f"   ✅ Notificação para funcionário criada")
        
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
        
        print(f"   ✅ {len(usuarios_ids_notificados)} notificações para financeiro/admin criadas")
        
        print(f"\n💾 ETAPA 6: Salvando no banco de dados...")
        # ETAPA 6: Commit final
        db.session.commit()
        print(f"✅ Todas as alterações salvas com sucesso!")
        
        print(f"\n📡 ETAPA 7: Enviando notificações WebSocket...")
        # ETAPA 7: Emitir eventos WebSocket
        socketio.emit('nova_notificacao', {'tipo': 'solicitacao_aprovada', 'solicitacao_id': id}, room='funcionarios')
        socketio.emit('nova_notificacao', {'tipo': 'nova_oc', 'oc_id': oc.id}, room='admins')
        print(f"✅ Notificações WebSocket enviadas")
        
        print(f"\n{'='*60}")
        print(f"🎉 APROVAÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"{'='*60}")
        print(f"   Solicitação: #{solicitacao.id} (aprovada)")
        print(f"   Lotes criados: {len(lotes_criados)}")
        print(f"   OC criada: #{oc.id} (em_analise)")
        print(f"   Valor total: R$ {oc.valor_total:.2f}")
        print(f"{'='*60}\n")
        
        return jsonify({
            'mensagem': 'Solicitação aprovada, lotes criados e Ordem de Compra gerada com sucesso',
            'solicitacao': solicitacao.to_dict(),
            'oc_id': oc.id,
            'oc_status': oc.status,
            'lotes_criados': lotes_criados,
            'valor_total': oc.valor_total
        }), 200
    
    except Exception as e:
        db.session.rollback()
        print(f"\n{'='*60}")
        print(f"❌ ERRO AO APROVAR SOLICITAÇÃO #{id}")
        print(f"{'='*60}")
        print(f"Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        print(f"{'='*60}\n")
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

@bp.route('/debug/<int:id>', methods=['GET'])
@admin_required
def diagnostico_solicitacao(id):
    """
    Endpoint de diagnóstico para verificar o estado completo de uma solicitação
    Retorna informações detalhadas sobre status, OC associada, valores e preços
    """
    try:
        solicitacao = Solicitacao.query.get(id)
        
        if not solicitacao:
            return jsonify({'erro': 'Solicitação não encontrada'}), 404
        
        # Verificar OC associada
        oc = OrdemCompra.query.filter_by(solicitacao_id=id).first()
        
        # Analisar itens
        itens_info = []
        valor_total_calculado = 0.0
        itens_com_problema = []
        
        for item in solicitacao.itens:
            # Buscar preço configurado atual
            preco_config = FornecedorTipoLotePreco.query.filter_by(
                fornecedor_id=solicitacao.fornecedor_id,
                tipo_lote_id=item.tipo_lote_id,
                estrelas=item.estrelas_final,
                ativo=True
            ).first()
            
            item_dict = {
                'id': item.id,
                'tipo_lote_id': item.tipo_lote_id,
                'tipo_lote_nome': item.tipo_lote.nome if item.tipo_lote else None,
                'peso_kg': item.peso_kg,
                'estrelas_final': item.estrelas_final,
                'classificacao': item.classificacao,
                'valor_calculado': item.valor_calculado,
                'preco_por_kg_snapshot': item.preco_por_kg_snapshot,
                'preco_atual_configurado': preco_config.preco_por_kg if preco_config else None,
                'preco_config_existe': preco_config is not None,
                'tem_problema': item.valor_calculado is None or item.valor_calculado < 0
            }
            
            if item.valor_calculado is not None and item.valor_calculado >= 0:
                valor_total_calculado += item.valor_calculado
            else:
                itens_com_problema.append(item.id)
            
            itens_info.append(item_dict)
        
        # Diagnóstico geral
        diagnostico = {
            'solicitacao': {
                'id': solicitacao.id,
                'status': solicitacao.status,
                'fornecedor_id': solicitacao.fornecedor_id,
                'fornecedor_nome': solicitacao.fornecedor.nome if solicitacao.fornecedor else None,
                'data_envio': solicitacao.data_envio.isoformat() if solicitacao.data_envio else None,
                'data_confirmacao': solicitacao.data_confirmacao.isoformat() if solicitacao.data_confirmacao else None,
                'total_itens': len(solicitacao.itens)
            },
            'ordem_compra': {
                'existe': oc is not None,
                'id': oc.id if oc else None,
                'valor_total': float(oc.valor_total) if oc else None,
                'status': oc.status if oc else None
            },
            'itens': itens_info,
            'analise': {
                'valor_total_calculado': valor_total_calculado,
                'itens_com_problema': len(itens_com_problema),
                'ids_itens_problema': itens_com_problema,
                'pode_aprovar': len(itens_com_problema) == 0 and solicitacao.status == 'pendente',
                'motivo_bloqueio': None
            }
        }
        
        # Determinar motivo de bloqueio
        if solicitacao.status != 'pendente':
            diagnostico['analise']['motivo_bloqueio'] = f'Status não é pendente: {solicitacao.status}'
        elif len(itens_com_problema) > 0:
            diagnostico['analise']['motivo_bloqueio'] = f'{len(itens_com_problema)} itens sem preço válido'
        elif oc:
            diagnostico['analise']['motivo_bloqueio'] = f'Já existe OC #{oc.id} para esta solicitação'
        
        return jsonify(diagnostico), 200
    
    except Exception as e:
        return jsonify({'erro': f'Erro ao executar diagnóstico: {str(e)}'}), 500
