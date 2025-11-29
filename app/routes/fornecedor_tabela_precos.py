from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, FornecedorTabelaPrecos, AuditoriaFornecedorTabelaPrecos, Fornecedor, MaterialBase, Usuario, Notificacao
from app.auth import admin_required
import pandas as pd
from io import BytesIO
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('fornecedor_tabela_precos', __name__, url_prefix='/api/fornecedor-tabela-precos')

def verificar_acesso_fornecedor(fornecedor_id, usuario_id):
    """Verifica se o usuário tem acesso ao fornecedor (admin ou comprador responsável)"""
    usuario = Usuario.query.get(usuario_id)
    
    if not usuario:
        return False
    
    if usuario.tipo == 'admin':
        return True
    
    fornecedor = Fornecedor.query.get(fornecedor_id)
    if not fornecedor:
        return False
    
    return fornecedor.comprador_responsavel_id == usuario_id

def notificar_admins_nova_tabela(fornecedor, usuario_criador):
    """Cria notificação para todos os admins sobre nova tabela de preços"""
    admins = Usuario.query.filter_by(tipo='admin', ativo=True).all()
    
    for admin in admins:
        if admin.id == usuario_criador.id:
            continue
            
        notificacao = Notificacao(
            usuario_id=admin.id,
            titulo='Nova Tabela de Preços',
            mensagem=f'Tabela de preços adicionada para o fornecedor {fornecedor.nome} por {usuario_criador.nome}',
            tipo='tabela_precos'
        )
        db.session.add(notificacao)

@bp.route('/fornecedor/<int:fornecedor_id>', methods=['GET'])
@jwt_required()
def listar_precos_fornecedor(fornecedor_id):
    """Lista todos os preços de um fornecedor"""
    try:
        usuario_id = get_jwt_identity()
        
        if not verificar_acesso_fornecedor(fornecedor_id, usuario_id):
            return jsonify({'erro': 'Acesso negado a este fornecedor'}), 403
        
        fornecedor = Fornecedor.query.get(fornecedor_id)
        if not fornecedor:
            return jsonify({'erro': 'Fornecedor não encontrado'}), 404
        
        status = request.args.get('status', None)
        versao = request.args.get('versao', None)
        
        query = FornecedorTabelaPrecos.query.filter_by(fornecedor_id=fornecedor_id)
        
        if status:
            query = query.filter_by(status=status)
        
        if versao:
            query = query.filter_by(versao=int(versao))
        
        precos = query.order_by(FornecedorTabelaPrecos.material_id, FornecedorTabelaPrecos.versao.desc()).all()
        
        return jsonify({
            'fornecedor': {
                'id': fornecedor.id,
                'nome': fornecedor.nome
            },
            'precos': [p.to_dict() for p in precos]
        }), 200
        
    except Exception as e:
        logger.error(f'Erro ao listar preços do fornecedor: {str(e)}')
        return jsonify({'erro': f'Erro ao listar preços: {str(e)}'}), 500

@bp.route('/fornecedor/<int:fornecedor_id>', methods=['POST'])
@jwt_required()
def adicionar_preco(fornecedor_id):
    """Adiciona um novo preço para um material do fornecedor"""
    try:
        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get(usuario_id)
        
        if not verificar_acesso_fornecedor(fornecedor_id, usuario_id):
            return jsonify({'erro': 'Acesso negado a este fornecedor'}), 403
        
        fornecedor = Fornecedor.query.get(fornecedor_id)
        if not fornecedor:
            return jsonify({'erro': 'Fornecedor não encontrado'}), 404
        
        dados = request.get_json()
        
        if not dados.get('material_id'):
            return jsonify({'erro': 'Material é obrigatório'}), 400
        
        if dados.get('preco_fornecedor') is None:
            return jsonify({'erro': 'Preço é obrigatório'}), 400
        
        material = MaterialBase.query.get(dados['material_id'])
        if not material:
            return jsonify({'erro': 'Material não encontrado'}), 404
        
        preco_existente = FornecedorTabelaPrecos.query.filter_by(
            fornecedor_id=fornecedor_id,
            material_id=dados['material_id'],
            status='ativo'
        ).first()
        
        if preco_existente:
            preco_existente.status = 'inativo'
            preco_existente.updated_by = usuario_id
            nova_versao = preco_existente.versao + 1
        else:
            nova_versao = 1
        
        novo_preco = FornecedorTabelaPrecos(
            fornecedor_id=fornecedor_id,
            material_id=dados['material_id'],
            preco_fornecedor=float(dados['preco_fornecedor']),
            status='pendente_aprovacao',
            versao=nova_versao,
            created_by=usuario_id,
            arquivo_origem_id=dados.get('arquivo_origem_id')
        )
        
        db.session.add(novo_preco)
        
        notificar_admins_nova_tabela(fornecedor, usuario)
        
        db.session.commit()
        
        return jsonify(novo_preco.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erro ao adicionar preço: {str(e)}')
        return jsonify({'erro': f'Erro ao adicionar preço: {str(e)}'}), 500

@bp.route('/fornecedor/<int:fornecedor_id>/lote', methods=['POST'])
@jwt_required()
def adicionar_precos_lote(fornecedor_id):
    """Adiciona múltiplos preços de uma vez (para upload manual ou importação)"""
    try:
        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get(usuario_id)
        
        if not verificar_acesso_fornecedor(fornecedor_id, usuario_id):
            return jsonify({'erro': 'Acesso negado a este fornecedor'}), 403
        
        fornecedor = Fornecedor.query.get(fornecedor_id)
        if not fornecedor:
            return jsonify({'erro': 'Fornecedor não encontrado'}), 404
        
        dados = request.get_json()
        itens = dados.get('itens', [])
        
        if not itens:
            return jsonify({'erro': 'Nenhum item para adicionar'}), 400
        
        precos_criados = []
        erros = []
        
        for idx, item in enumerate(itens):
            try:
                if not item.get('material_id'):
                    erros.append(f'Item {idx + 1}: Material é obrigatório')
                    continue
                
                if item.get('preco_fornecedor') is None:
                    erros.append(f'Item {idx + 1}: Preço é obrigatório')
                    continue
                
                material = MaterialBase.query.get(item['material_id'])
                if not material:
                    erros.append(f'Item {idx + 1}: Material não encontrado')
                    continue
                
                preco_existente = FornecedorTabelaPrecos.query.filter_by(
                    fornecedor_id=fornecedor_id,
                    material_id=item['material_id'],
                    status='ativo'
                ).first()
                
                if preco_existente:
                    preco_existente.status = 'inativo'
                    preco_existente.updated_by = usuario_id
                    nova_versao = preco_existente.versao + 1
                else:
                    nova_versao = 1
                
                novo_preco = FornecedorTabelaPrecos(
                    fornecedor_id=fornecedor_id,
                    material_id=item['material_id'],
                    preco_fornecedor=float(item['preco_fornecedor']),
                    status='pendente_aprovacao',
                    versao=nova_versao,
                    created_by=usuario_id,
                    arquivo_origem_id=dados.get('arquivo_origem_id')
                )
                
                db.session.add(novo_preco)
                precos_criados.append(novo_preco)
                
            except Exception as e:
                erros.append(f'Item {idx + 1}: {str(e)}')
        
        if precos_criados:
            notificar_admins_nova_tabela(fornecedor, usuario)
            db.session.commit()
        
        return jsonify({
            'sucesso': len(precos_criados),
            'erros': erros,
            'precos': [p.to_dict() for p in precos_criados]
        }), 201 if precos_criados else 400
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erro ao adicionar preços em lote: {str(e)}')
        return jsonify({'erro': f'Erro ao adicionar preços: {str(e)}'}), 500

@bp.route('/fornecedor/<int:fornecedor_id>/upload', methods=['POST'])
@jwt_required()
def upload_tabela_precos(fornecedor_id):
    """Upload de arquivo CSV/XLSX com tabela de preços"""
    try:
        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get(usuario_id)
        
        if not verificar_acesso_fornecedor(fornecedor_id, usuario_id):
            return jsonify({'erro': 'Acesso negado a este fornecedor'}), 403
        
        fornecedor = Fornecedor.query.get(fornecedor_id)
        if not fornecedor:
            return jsonify({'erro': 'Fornecedor não encontrado'}), 404
        
        if 'arquivo' not in request.files:
            return jsonify({'erro': 'Arquivo não enviado'}), 400
        
        arquivo = request.files['arquivo']
        
        if arquivo.filename == '':
            return jsonify({'erro': 'Nenhum arquivo selecionado'}), 400
        
        extensao = arquivo.filename.rsplit('.', 1)[-1].lower()
        
        if extensao not in ['csv', 'xlsx', 'xls']:
            return jsonify({'erro': 'Formato de arquivo inválido. Use CSV ou XLSX'}), 400
        
        try:
            if extensao == 'csv':
                df = pd.read_csv(arquivo, encoding='utf-8')
            else:
                df = pd.read_excel(arquivo)
        except Exception as e:
            return jsonify({'erro': f'Erro ao ler arquivo: {str(e)}'}), 400
        
        colunas_obrigatorias = ['material', 'preco']
        colunas_arquivo = [col.lower().strip() for col in df.columns]
        
        coluna_material = None
        coluna_preco = None
        
        for col in df.columns:
            col_lower = col.lower().strip()
            if col_lower in ['material', 'nome_material', 'nome do material', 'material_nome']:
                coluna_material = col
            if col_lower in ['preco', 'preco_kg', 'preco por kg', 'preco_fornecedor', 'valor']:
                coluna_preco = col
        
        if not coluna_material or not coluna_preco:
            return jsonify({
                'erro': 'Colunas obrigatórias não encontradas. O arquivo deve ter colunas: material, preco'
            }), 400
        
        precos_criados = []
        erros = []
        
        for idx, row in df.iterrows():
            try:
                nome_material = str(row[coluna_material]).strip()
                preco_valor = row[coluna_preco]
                
                if pd.isna(nome_material) or nome_material == '':
                    continue
                
                if pd.isna(preco_valor):
                    erros.append(f'Linha {idx + 2}: Preço inválido para material "{nome_material}"')
                    continue
                
                material = MaterialBase.query.filter(
                    db.or_(
                        MaterialBase.nome.ilike(nome_material),
                        MaterialBase.codigo.ilike(nome_material)
                    )
                ).first()
                
                if not material:
                    erros.append(f'Linha {idx + 2}: Material "{nome_material}" não encontrado')
                    continue
                
                try:
                    preco_float = float(str(preco_valor).replace(',', '.').replace('R$', '').strip())
                except:
                    erros.append(f'Linha {idx + 2}: Preço inválido "{preco_valor}"')
                    continue
                
                if preco_float < 0:
                    erros.append(f'Linha {idx + 2}: Preço não pode ser negativo')
                    continue
                
                preco_existente = FornecedorTabelaPrecos.query.filter_by(
                    fornecedor_id=fornecedor_id,
                    material_id=material.id,
                    status='ativo'
                ).first()
                
                if preco_existente:
                    preco_existente.status = 'inativo'
                    preco_existente.updated_by = usuario_id
                    nova_versao = preco_existente.versao + 1
                else:
                    nova_versao = 1
                
                novo_preco = FornecedorTabelaPrecos(
                    fornecedor_id=fornecedor_id,
                    material_id=material.id,
                    preco_fornecedor=preco_float,
                    status='pendente_aprovacao',
                    versao=nova_versao,
                    created_by=usuario_id
                )
                
                db.session.add(novo_preco)
                precos_criados.append(novo_preco)
                
            except Exception as e:
                erros.append(f'Linha {idx + 2}: Erro ao processar - {str(e)}')
        
        if precos_criados:
            notificar_admins_nova_tabela(fornecedor, usuario)
            db.session.commit()
        
        return jsonify({
            'sucesso': len(precos_criados),
            'total_linhas': len(df),
            'erros': erros,
            'precos': [p.to_dict() for p in precos_criados]
        }), 201 if precos_criados else 400
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erro ao fazer upload de tabela: {str(e)}')
        return jsonify({'erro': f'Erro ao processar arquivo: {str(e)}'}), 500

@bp.route('/<int:preco_id>', methods=['PUT'])
@jwt_required()
def atualizar_preco(preco_id):
    """Atualiza um preço existente (enquanto ainda está em rascunho)"""
    try:
        usuario_id = get_jwt_identity()
        
        preco = FornecedorTabelaPrecos.query.get(preco_id)
        if not preco:
            return jsonify({'erro': 'Preço não encontrado'}), 404
        
        if not verificar_acesso_fornecedor(preco.fornecedor_id, usuario_id):
            return jsonify({'erro': 'Acesso negado'}), 403
        
        if preco.status not in ['pendente_aprovacao']:
            return jsonify({'erro': 'Apenas preços pendentes podem ser editados'}), 400
        
        dados = request.get_json()
        
        if 'preco_fornecedor' in dados:
            preco.preco_fornecedor = float(dados['preco_fornecedor'])
        
        preco.updated_by = usuario_id
        
        db.session.commit()
        
        return jsonify(preco.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erro ao atualizar preço: {str(e)}')
        return jsonify({'erro': f'Erro ao atualizar preço: {str(e)}'}), 500

@bp.route('/<int:preco_id>', methods=['DELETE'])
@jwt_required()
def excluir_preco(preco_id):
    """Exclui um preço (apenas se ainda estiver pendente)"""
    try:
        usuario_id = get_jwt_identity()
        
        preco = FornecedorTabelaPrecos.query.get(preco_id)
        if not preco:
            return jsonify({'erro': 'Preço não encontrado'}), 404
        
        if not verificar_acesso_fornecedor(preco.fornecedor_id, usuario_id):
            return jsonify({'erro': 'Acesso negado'}), 403
        
        if preco.status not in ['pendente_aprovacao']:
            return jsonify({'erro': 'Apenas preços pendentes podem ser excluídos'}), 400
        
        preco.updated_by = usuario_id
        db.session.delete(preco)
        db.session.commit()
        
        return jsonify({'mensagem': 'Preço excluído com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erro ao excluir preço: {str(e)}')
        return jsonify({'erro': f'Erro ao excluir preço: {str(e)}'}), 500

@bp.route('/<int:preco_id>/aprovar', methods=['PUT'])
@jwt_required()
@admin_required
def aprovar_preco(preco_id):
    """Aprova um preço pendente (apenas admin)"""
    try:
        usuario_id = get_jwt_identity()
        
        preco = FornecedorTabelaPrecos.query.get(preco_id)
        if not preco:
            return jsonify({'erro': 'Preço não encontrado'}), 404
        
        if preco.status != 'pendente_aprovacao':
            return jsonify({'erro': 'Preço não está pendente de aprovação'}), 400
        
        preco.status = 'ativo'
        preco.updated_by = usuario_id
        
        db.session.commit()
        
        criador = Usuario.query.get(preco.created_by)
        if criador:
            notificacao = Notificacao(
                usuario_id=criador.id,
                titulo='Tabela de Preços Aprovada',
                mensagem=f'Sua tabela de preços para o fornecedor {preco.fornecedor.nome} foi aprovada',
                tipo='tabela_precos_aprovada'
            )
            db.session.add(notificacao)
            db.session.commit()
        
        return jsonify(preco.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erro ao aprovar preço: {str(e)}')
        return jsonify({'erro': f'Erro ao aprovar preço: {str(e)}'}), 500

@bp.route('/<int:preco_id>/rejeitar', methods=['PUT'])
@jwt_required()
@admin_required
def rejeitar_preco(preco_id):
    """Rejeita um preço pendente (apenas admin)"""
    try:
        usuario_id = get_jwt_identity()
        
        preco = FornecedorTabelaPrecos.query.get(preco_id)
        if not preco:
            return jsonify({'erro': 'Preço não encontrado'}), 404
        
        if preco.status != 'pendente_aprovacao':
            return jsonify({'erro': 'Preço não está pendente de aprovação'}), 400
        
        dados = request.get_json() or {}
        motivo = dados.get('motivo', 'Não especificado')
        
        preco.status = 'inativo'
        preco.updated_by = usuario_id
        
        db.session.commit()
        
        criador = Usuario.query.get(preco.created_by)
        if criador:
            notificacao = Notificacao(
                usuario_id=criador.id,
                titulo='Tabela de Preços Rejeitada',
                mensagem=f'Sua tabela de preços para o fornecedor {preco.fornecedor.nome} foi rejeitada. Motivo: {motivo}',
                tipo='tabela_precos_rejeitada'
            )
            db.session.add(notificacao)
            db.session.commit()
        
        return jsonify(preco.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erro ao rejeitar preço: {str(e)}')
        return jsonify({'erro': f'Erro ao rejeitar preço: {str(e)}'}), 500

@bp.route('/fornecedor/<int:fornecedor_id>/aprovar-todos', methods=['PUT'])
@jwt_required()
@admin_required
def aprovar_todos_precos(fornecedor_id):
    """Aprova todos os preços pendentes de um fornecedor (apenas admin)"""
    try:
        usuario_id = get_jwt_identity()
        
        fornecedor = Fornecedor.query.get(fornecedor_id)
        if not fornecedor:
            return jsonify({'erro': 'Fornecedor não encontrado'}), 404
        
        precos_pendentes = FornecedorTabelaPrecos.query.filter_by(
            fornecedor_id=fornecedor_id,
            status='pendente_aprovacao'
        ).all()
        
        if not precos_pendentes:
            return jsonify({'erro': 'Nenhum preço pendente para aprovar'}), 400
        
        criadores_ids = set()
        for preco in precos_pendentes:
            preco.status = 'ativo'
            preco.updated_by = usuario_id
            if preco.created_by:
                criadores_ids.add(preco.created_by)
        
        db.session.commit()
        
        for criador_id in criadores_ids:
            criador = Usuario.query.get(criador_id)
            if criador:
                notificacao = Notificacao(
                    usuario_id=criador.id,
                    titulo='Tabela de Preços Aprovada',
                    mensagem=f'Sua tabela de preços para o fornecedor {fornecedor.nome} foi aprovada',
                    tipo='tabela_precos_aprovada'
                )
                db.session.add(notificacao)
        
        db.session.commit()
        
        return jsonify({
            'mensagem': f'{len(precos_pendentes)} preços aprovados com sucesso',
            'aprovados': len(precos_pendentes)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Erro ao aprovar preços: {str(e)}')
        return jsonify({'erro': f'Erro ao aprovar preços: {str(e)}'}), 500

@bp.route('/fornecedor/<int:fornecedor_id>/template', methods=['GET'])
@jwt_required()
def download_template(fornecedor_id):
    """Gera um template Excel para upload de preços"""
    try:
        usuario_id = get_jwt_identity()
        
        if not verificar_acesso_fornecedor(fornecedor_id, usuario_id):
            return jsonify({'erro': 'Acesso negado'}), 403
        
        fornecedor = Fornecedor.query.get(fornecedor_id)
        if not fornecedor:
            return jsonify({'erro': 'Fornecedor não encontrado'}), 404
        
        materiais = MaterialBase.query.filter_by(ativo=True).order_by(MaterialBase.nome).all()
        
        dados = []
        for m in materiais:
            dados.append({
                'Material': m.nome,
                'Código': m.codigo,
                'Classificação': m.classificacao,
                'Preço (R$/kg)': ''
            })
        
        df = pd.DataFrame(dados)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Preços')
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'template_precos_{fornecedor.nome.replace(" ", "_")}.xlsx'
        )
        
    except Exception as e:
        logger.error(f'Erro ao gerar template: {str(e)}')
        return jsonify({'erro': f'Erro ao gerar template: {str(e)}'}), 500

@bp.route('/fornecedor/<int:fornecedor_id>/auditoria', methods=['GET'])
@jwt_required()
def listar_auditoria(fornecedor_id):
    """Lista o histórico de auditoria dos preços de um fornecedor"""
    try:
        usuario_id = get_jwt_identity()
        
        if not verificar_acesso_fornecedor(fornecedor_id, usuario_id):
            return jsonify({'erro': 'Acesso negado'}), 403
        
        fornecedor = Fornecedor.query.get(fornecedor_id)
        if not fornecedor:
            return jsonify({'erro': 'Fornecedor não encontrado'}), 404
        
        precos_ids = [p.id for p in FornecedorTabelaPrecos.query.filter_by(fornecedor_id=fornecedor_id).all()]
        
        auditorias = AuditoriaFornecedorTabelaPrecos.query.filter(
            AuditoriaFornecedorTabelaPrecos.preco_id.in_(precos_ids)
        ).order_by(AuditoriaFornecedorTabelaPrecos.data_acao.desc()).limit(100).all()
        
        return jsonify([a.to_dict() for a in auditorias]), 200
        
    except Exception as e:
        logger.error(f'Erro ao listar auditoria: {str(e)}')
        return jsonify({'erro': f'Erro ao listar auditoria: {str(e)}'}), 500

@bp.route('/pendentes', methods=['GET'])
@jwt_required()
@admin_required
def listar_pendentes():
    """Lista todos os fornecedores com preços pendentes de aprovação (apenas admin)"""
    try:
        precos_pendentes = db.session.query(
            FornecedorTabelaPrecos.fornecedor_id,
            db.func.count(FornecedorTabelaPrecos.id).label('total_pendentes')
        ).filter_by(
            status='pendente_aprovacao'
        ).group_by(
            FornecedorTabelaPrecos.fornecedor_id
        ).all()
        
        resultado = []
        for fornecedor_id, total in precos_pendentes:
            fornecedor = Fornecedor.query.get(fornecedor_id)
            if fornecedor:
                resultado.append({
                    'fornecedor_id': fornecedor_id,
                    'fornecedor_nome': fornecedor.nome,
                    'total_pendentes': total
                })
        
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f'Erro ao listar pendentes: {str(e)}')
        return jsonify({'erro': f'Erro ao listar pendentes: {str(e)}'}), 500
