from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Solicitacao, ItemSolicitacao, Fornecedor, TipoLote, FornecedorTipoLotePreco, FornecedorTipoLoteClassificacao, db, Usuario, Lote, OrdemCompra, Notificacao, Perfil
from app.auth import admin_required
from app.utils.auditoria import registrar_auditoria_oc
from app import socketio
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
    from app.models import TipoLotePreco

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

    # Busca o preço na tabela TipoLotePreco (tabela global de preços)
    preco = TipoLotePreco.query.filter_by(
        tipo_lote_id=tipo_lote_id,
        classificacao=classificacao,
        estrelas=estrelas_final,
        ativo=True
    ).first()

    if not preco:
        print(f"      ❌ Preço não encontrado em TipoLotePreco!")
        print(f"      🔍 Buscando preços disponíveis para tipo_lote={tipo_lote_id}, classificacao={classificacao}...")

        # Lista todos os preços disponíveis para debug
        precos_disponiveis = TipoLotePreco.query.filter_by(
            tipo_lote_id=tipo_lote_id,
            classificacao=classificacao,
            ativo=True
        ).all()

        if precos_disponiveis:
            print(f"      📋 Preços cadastrados para classificação '{classificacao}':")
            for p in precos_disponiveis:
                print(f"         - {p.estrelas} estrelas: R$ {p.preco_por_kg}/kg")
        else:
            print(f"      ⚠️ Nenhum preço cadastrado para tipo_lote={tipo_lote_id}, classificacao={classificacao}")

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
    oc = None
    lotes_criados = []
    solicitacao = None
    
    try:
        print(f"\n{'='*60}")
        print(f"🔄 INICIANDO APROVAÇÃO DA SOLICITAÇÃO #{id}")
        print(f"{'='*60}")
        
        usuario_id = get_jwt_identity()
        data = request.get_json(silent=True) or {}
        
        print(f"\n🔍 FASE 1: Validações preliminares (SEM modificar dados)...")
        
        solicitacao = Solicitacao.query.get(id)
        
        if not solicitacao:
            print(f"❌ Solicitação #{id} não encontrada")
            return jsonify({'erro': 'Solicitação não encontrada'}), 404
        
        print(f"✅ Solicitação encontrada: #{solicitacao.id}")
        print(f"   Status atual: {solicitacao.status}")
        print(f"   Fornecedor: {solicitacao.fornecedor.nome if solicitacao.fornecedor else 'N/A'}")
        
        if solicitacao.status != 'pendente':
            print(f"❌ Status inválido: {solicitacao.status}")
            return jsonify({'erro': f'Solicitação já foi processada (status: {solicitacao.status})'}), 400
        
        if not solicitacao.itens or len(solicitacao.itens) == 0:
            print(f"❌ Solicitação sem itens")
            return jsonify({'erro': 'Solicitação não possui itens'}), 400
        
        print(f"✅ Solicitação possui {len(solicitacao.itens)} itens")
        
        itens_sem_preco = [item for item in solicitacao.itens if item.valor_calculado is None or item.valor_calculado < 0]
        if itens_sem_preco:
            print(f"❌ Existem {len(itens_sem_preco)} itens sem preço configurado ou com valor inválido")
            return jsonify({'erro': f'Existem {len(itens_sem_preco)} itens sem preço configurado ou com valor inválido. Configure os preços antes de aprovar.'}), 400
        
        oc_existente = OrdemCompra.query.filter_by(solicitacao_id=id).first()
        if oc_existente:
            print(f"⚠️ Já existe OC #{oc_existente.id} para esta solicitação")
            return jsonify({'erro': f'Já existe uma ordem de compra (#{oc_existente.id}) para esta solicitação'}), 400
        
        valor_total_oc = sum((item.valor_calculado or 0.0) for item in solicitacao.itens)
        print(f"💰 Valor total calculado: R$ {valor_total_oc:.2f}")
        
        if valor_total_oc < 0:
            print(f"❌ Valor total negativo")
            return jsonify({'erro': 'Valor total da OC não pode ser negativo'}), 400
        
        print(f"✅ Todas as validações passaram!")
        
        print(f"\n💾 FASE 2: Salvando alterações no banco...")
        
        print(f"\n📝 ETAPA 1: Atualizando status da solicitação...")
        solicitacao.status = 'aprovada'
        solicitacao.data_confirmacao = datetime.utcnow()
        solicitacao.admin_id = usuario_id
        print(f"✅ Status atualizado para: aprovada")
        
        print(f"\n💰 ETAPA 2: Criando Ordem de Compra...")
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
        
        print(f"\n📦 ETAPA 3: Criando lotes...")
        lotes_por_tipo = {}
        for item in solicitacao.itens:
            chave = (item.tipo_lote_id, item.estrelas_final)
            if chave not in lotes_por_tipo:
                lotes_por_tipo[chave] = []
            lotes_por_tipo[chave].append(item)
        
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
        
        print(f"\n📋 ETAPA 4: Registrando auditoria da OC...")
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
        
        print(f"\n💾 Salvando TODAS as alterações no banco...")
        db.session.commit()
        print(f"✅ COMMIT REALIZADO - Dados persistidos no banco")
        
        print(f"\n🔍 VERIFICAÇÃO: Consultando OC no banco...")
        oc_verificacao = OrdemCompra.query.filter_by(id=oc.id).first()
        if oc_verificacao:
            print(f"   ✅ OC #{oc_verificacao.id} CONFIRMADA no banco de dados")
            print(f"      Solicitação ID: {oc_verificacao.solicitacao_id}")
            print(f"      Valor: R$ {oc_verificacao.valor_total:.2f}")
        else:
            print(f"   ❌ ERRO CRÍTICO: OC NÃO encontrada no banco após commit!")
        
        print(f"\n🔔 ETAPA 5: Criando notificações...")
        notificacao_funcionario = Notificacao(
            usuario_id=solicitacao.funcionario_id,
            titulo='Solicitação Aprovada',
            mensagem=f'Sua solicitação #{solicitacao.id} foi aprovada! OC #{oc.id} criada (R$ {oc.valor_total:.2f}) e {len(lotes_criados)} lote(s) gerado(s).'
        )
        db.session.add(notificacao_funcionario)
        print(f"   ✅ Notificação para funcionário criada")
        
        usuarios_financeiro = Usuario.query.filter(
            db.and_(
                Usuario.ativo == True,
                db.or_(
                    Usuario.tipo == 'admin',
                    Usuario.perfil.has(Perfil.nome.in_(['Administrador', 'Financeiro']))
                )
            )
        ).all()
        
        usuarios_ids_notificados = set()
        for usuario_fin in usuarios_financeiro:
            if usuario_fin.id not in usuarios_ids_notificados and usuario_fin.id != solicitacao.funcionario_id:
                notificacao_financeiro = Notificacao(
                    usuario_id=usuario_fin.id,
                    titulo='Nova Ordem de Compra - Aprovação Pendente',
                    mensagem=f'OC #{oc.id} gerada (R$ {oc.valor_total:.2f}) da Solicitação #{solicitacao.id} - Fornecedor: {solicitacao.fornecedor.nome}. Aguardando sua aprovação!'
                )
                db.session.add(notificacao_financeiro)
                usuarios_ids_notificados.add(usuario_fin.id)
        
        print(f"   ✅ {len(usuarios_ids_notificados)} notificações para financeiro/admin criadas")
        
        db.session.commit()
        print(f"\n💾 Transação commitada com sucesso!")
        
        print(f"\n📡 FASE 3: Enviando notificações WebSocket...")
        try:
            socketio.emit('nova_notificacao', {
                'tipo': 'solicitacao_aprovada',
                'solicitacao_id': id,
                'oc_id': oc.id,
                'valor_total': float(oc.valor_total)
            }, room='funcionarios')
            
            socketio.emit('nova_notificacao', {
                'tipo': 'nova_oc',
                'oc_id': oc.id,
                'solicitacao_id': id,
                'valor_total': float(oc.valor_total),
                'fornecedor': solicitacao.fornecedor.nome
            }, room='admins')
            
            print(f"✅ Notificações WebSocket enviadas")
        except Exception as ws_error:
            print(f"⚠️ Erro ao enviar WebSocket (não crítico): {str(ws_error)}")
        
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