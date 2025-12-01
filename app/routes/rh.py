from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Usuario, Solicitacao, Fornecedor, AuditoriaLog, Perfil
from app.auth import admin_required, hash_senha
from app.utils.auditoria import registrar_criacao, registrar_atualizacao, registrar_exclusao
from datetime import datetime, timedelta
from sqlalchemy import func, and_
import os
import io
from werkzeug.utils import secure_filename

bp = Blueprint('rh', __name__, url_prefix='/api/rh')

UPLOAD_FOLDER = 'uploads/usuarios'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_upload_folder():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

@bp.route('/usuarios', methods=['GET'])
@admin_required
def listar_usuarios_rh():
    usuarios = Usuario.query.all()
    return jsonify([u.to_dict() for u in usuarios]), 200

@bp.route('/usuarios/<int:id>', methods=['GET'])
@admin_required
def obter_usuario_rh(id):
    usuario = Usuario.query.get(id)
    if not usuario:
        return jsonify({'erro': 'Usuário não encontrado'}), 404
    return jsonify(usuario.to_dict()), 200

@bp.route('/usuarios', methods=['POST'])
@admin_required
def criar_usuario_rh():
    admin_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('nome') or not data.get('email'):
        return jsonify({'erro': 'Nome e email são obrigatórios'}), 400
    
    if not data.get('perfil_id'):
        return jsonify({'erro': 'Perfil é obrigatório'}), 400
    
    usuario_existente = Usuario.query.filter_by(email=data['email']).first()
    if usuario_existente:
        return jsonify({'erro': 'Email já cadastrado'}), 400
    
    perfil = Perfil.query.get(data['perfil_id'])
    if not perfil:
        return jsonify({'erro': 'Perfil não encontrado'}), 404
    
    tipo = 'admin' if perfil.nome == 'Administrador' else 'funcionario'
    
    senha = data.get('senha')
    if not senha:
        cpf = data.get('cpf', '')
        senha = cpf[-4:] if len(cpf) >= 4 else '123456'
    
    usuario = Usuario(
        nome=data['nome'],
        email=data['email'],
        senha_hash=hash_senha(senha),
        tipo=tipo,
        perfil_id=data['perfil_id'],
        ativo=data.get('ativo', True),
        telefone=data.get('telefone'),
        cpf=data.get('cpf'),
        percentual_comissao=data.get('percentual_comissao', 0.0),
        criado_por=admin_id
    )
    
    db.session.add(usuario)
    db.session.commit()
    
    registrar_criacao(admin_id, 'Usuario', usuario.id, {
        'nome': usuario.nome,
        'email': usuario.email,
        'perfil': perfil.nome,
        'percentual_comissao': usuario.percentual_comissao,
        'ativo': usuario.ativo
    })
    
    return jsonify(usuario.to_dict()), 201

@bp.route('/usuarios/<int:id>', methods=['PUT'])
@admin_required
def atualizar_usuario_rh(id):
    admin_id = get_jwt_identity()
    usuario = Usuario.query.get(id)
    
    if not usuario:
        return jsonify({'erro': 'Usuário não encontrado'}), 404
    
    data = request.get_json()
    alteracoes = {'antes': {}, 'depois': {}}
    
    if data.get('nome'):
        alteracoes['antes']['nome'] = usuario.nome
        usuario.nome = data['nome']
        alteracoes['depois']['nome'] = data['nome']
    
    if data.get('email'):
        if data['email'] != usuario.email:
            existente = Usuario.query.filter_by(email=data['email']).first()
            if existente:
                return jsonify({'erro': 'Email já está em uso'}), 400
        alteracoes['antes']['email'] = usuario.email
        usuario.email = data['email']
        alteracoes['depois']['email'] = data['email']
    
    if data.get('senha'):
        usuario.senha_hash = hash_senha(data['senha'])
        alteracoes['depois']['senha_alterada'] = True
    
    if data.get('perfil_id'):
        perfil = Perfil.query.get(data['perfil_id'])
        if not perfil:
            return jsonify({'erro': 'Perfil não encontrado'}), 404
        
        alteracoes['antes']['perfil'] = usuario.perfil.nome if usuario.perfil else None
        usuario.perfil_id = data['perfil_id']
        usuario.tipo = 'admin' if perfil.nome == 'Administrador' else 'funcionario'
        alteracoes['depois']['perfil'] = perfil.nome
    
    if 'ativo' in data:
        alteracoes['antes']['ativo'] = usuario.ativo
        usuario.ativo = data['ativo']
        alteracoes['depois']['ativo'] = data['ativo']
    
    if 'telefone' in data:
        alteracoes['antes']['telefone'] = usuario.telefone
        usuario.telefone = data['telefone']
        alteracoes['depois']['telefone'] = data['telefone']
    
    if 'cpf' in data:
        alteracoes['antes']['cpf'] = usuario.cpf
        usuario.cpf = data['cpf']
        alteracoes['depois']['cpf'] = data['cpf']
    
    if 'percentual_comissao' in data:
        alteracoes['antes']['percentual_comissao'] = usuario.percentual_comissao
        usuario.percentual_comissao = float(data['percentual_comissao'])
        alteracoes['depois']['percentual_comissao'] = float(data['percentual_comissao'])
    
    db.session.commit()
    
    registrar_atualizacao(admin_id, 'Usuario', usuario.id, alteracoes)
    
    return jsonify(usuario.to_dict()), 200

@bp.route('/usuarios/<int:id>', methods=['DELETE'])
@admin_required
def deletar_usuario_rh(id):
    admin_id = get_jwt_identity()
    usuario = Usuario.query.get(id)
    
    if not usuario:
        return jsonify({'erro': 'Usuário não encontrado'}), 404
    
    if usuario.tipo == 'admin':
        admins = Usuario.query.filter_by(tipo='admin').count()
        if admins <= 1:
            return jsonify({'erro': 'Não é possível deletar o único administrador do sistema'}), 400
    
    registrar_exclusao(admin_id, 'Usuario', usuario.id, {
        'nome': usuario.nome,
        'email': usuario.email,
        'perfil': usuario.perfil.nome if usuario.perfil else None
    })
    
    db.session.delete(usuario)
    db.session.commit()
    
    return jsonify({'mensagem': 'Usuário deletado com sucesso'}), 200

@bp.route('/usuarios/<int:id>/foto', methods=['POST'])
@admin_required
def upload_foto_usuario(id):
    admin_id = get_jwt_identity()
    usuario = Usuario.query.get(id)
    
    if not usuario:
        return jsonify({'erro': 'Usuário não encontrado'}), 404
    
    if 'foto' not in request.files:
        return jsonify({'erro': 'Nenhuma foto enviada'}), 400
    
    file = request.files['foto']
    
    if file.filename == '':
        return jsonify({'erro': 'Nenhum arquivo selecionado'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'erro': 'Tipo de arquivo não permitido. Use PNG, JPG, JPEG, GIF ou WEBP'}), 400
    
    ensure_upload_folder()
    
    if usuario.foto_path and os.path.exists(usuario.foto_path):
        try:
            os.remove(usuario.foto_path)
        except Exception:
            pass
    
    filename = secure_filename(f"usuario_{id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file.filename.rsplit('.', 1)[1].lower()}")
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    foto_anterior = usuario.foto_path
    usuario.foto_path = filepath
    db.session.commit()
    
    registrar_atualizacao(admin_id, 'Usuario', usuario.id, {
        'antes': {'foto_path': foto_anterior},
        'depois': {'foto_path': filepath}
    })
    
    return jsonify({
        'mensagem': 'Foto atualizada com sucesso',
        'foto_path': filepath
    }), 200

@bp.route('/usuarios/<int:id>/foto', methods=['DELETE'])
@admin_required
def remover_foto_usuario(id):
    admin_id = get_jwt_identity()
    usuario = Usuario.query.get(id)
    
    if not usuario:
        return jsonify({'erro': 'Usuário não encontrado'}), 404
    
    if usuario.foto_path and os.path.exists(usuario.foto_path):
        try:
            os.remove(usuario.foto_path)
        except Exception:
            pass
    
    foto_anterior = usuario.foto_path
    usuario.foto_path = None
    db.session.commit()
    
    registrar_atualizacao(admin_id, 'Usuario', usuario.id, {
        'antes': {'foto_path': foto_anterior},
        'depois': {'foto_path': None}
    })
    
    return jsonify({'mensagem': 'Foto removida com sucesso'}), 200

@bp.route('/comissoes/usuario/<int:usuario_id>', methods=['GET'])
@admin_required
def calcular_comissao_usuario(usuario_id):
    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        return jsonify({'erro': 'Usuário não encontrado'}), 404
    
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    fornecedor_id = request.args.get('fornecedor_id')
    
    query = Solicitacao.query.filter(
        Solicitacao.funcionario_id == usuario_id,
        Solicitacao.status == 'aprovada'
    )
    
    if data_inicio:
        try:
            dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            query = query.filter(Solicitacao.data_envio >= dt_inicio)
        except ValueError:
            pass
    
    if data_fim:
        try:
            dt_fim = datetime.strptime(data_fim, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Solicitacao.data_envio < dt_fim)
        except ValueError:
            pass
    
    if fornecedor_id:
        query = query.filter(Solicitacao.fornecedor_id == int(fornecedor_id))
    
    solicitacoes = query.all()
    
    percentual = usuario.percentual_comissao or 0.0
    
    solicitacoes_data = []
    total_valor = 0.0
    total_comissao = 0.0
    
    for sol in solicitacoes:
        valor_solicitacao = sum(item.valor_calculado for item in sol.itens) if sol.itens else 0
        comissao = valor_solicitacao * (percentual / 100)
        
        total_valor += valor_solicitacao
        total_comissao += comissao
        
        solicitacoes_data.append({
            'id': sol.id,
            'data_envio': sol.data_envio.isoformat() if sol.data_envio else None,
            'data_confirmacao': sol.data_confirmacao.isoformat() if sol.data_confirmacao else None,
            'fornecedor_id': sol.fornecedor_id,
            'fornecedor_nome': sol.fornecedor.nome if sol.fornecedor else None,
            'valor_total': round(valor_solicitacao, 2),
            'comissao': round(comissao, 2),
            'status': sol.status
        })
    
    return jsonify({
        'usuario': usuario.to_dict(),
        'percentual_comissao': percentual,
        'total_solicitacoes': len(solicitacoes),
        'total_valor': round(total_valor, 2),
        'total_comissao': round(total_comissao, 2),
        'solicitacoes': solicitacoes_data
    }), 200

@bp.route('/comissoes/resumo', methods=['GET'])
@admin_required
def resumo_comissoes():
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    usuarios = Usuario.query.filter(Usuario.percentual_comissao > 0).all()
    
    resumo = []
    
    for usuario in usuarios:
        query = Solicitacao.query.filter(
            Solicitacao.funcionario_id == usuario.id,
            Solicitacao.status == 'aprovada'
        )
        
        if data_inicio:
            try:
                dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
                query = query.filter(Solicitacao.data_envio >= dt_inicio)
            except ValueError:
                pass
        
        if data_fim:
            try:
                dt_fim = datetime.strptime(data_fim, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(Solicitacao.data_envio < dt_fim)
            except ValueError:
                pass
        
        solicitacoes = query.all()
        
        total_valor = 0.0
        for sol in solicitacoes:
            valor_solicitacao = sum(item.valor_calculado for item in sol.itens) if sol.itens else 0
            total_valor += valor_solicitacao
        
        comissao = total_valor * (usuario.percentual_comissao / 100)
        
        resumo.append({
            'usuario_id': usuario.id,
            'usuario_nome': usuario.nome,
            'perfil': usuario.perfil.nome if usuario.perfil else None,
            'percentual_comissao': usuario.percentual_comissao,
            'total_solicitacoes': len(solicitacoes),
            'total_valor': round(total_valor, 2),
            'total_comissao': round(comissao, 2)
        })
    
    resumo.sort(key=lambda x: x['total_comissao'], reverse=True)
    
    return jsonify({
        'resumo': resumo,
        'total_geral_comissoes': round(sum(r['total_comissao'] for r in resumo), 2)
    }), 200

@bp.route('/comissoes/exportar', methods=['GET'])
@admin_required
def exportar_comissoes():
    try:
        import pandas as pd
        from io import BytesIO
    except ImportError:
        return jsonify({'erro': 'Biblioteca pandas não disponível'}), 500
    
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    usuario_id = request.args.get('usuario_id')
    formato = request.args.get('formato', 'xlsx')
    
    query = Solicitacao.query.filter(Solicitacao.status == 'aprovada')
    
    if usuario_id:
        query = query.filter(Solicitacao.funcionario_id == int(usuario_id))
    
    if data_inicio:
        try:
            dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            query = query.filter(Solicitacao.data_envio >= dt_inicio)
        except ValueError:
            pass
    
    if data_fim:
        try:
            dt_fim = datetime.strptime(data_fim, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Solicitacao.data_envio < dt_fim)
        except ValueError:
            pass
    
    solicitacoes = query.all()
    
    dados = []
    for sol in solicitacoes:
        usuario = sol.funcionario
        percentual = usuario.percentual_comissao or 0.0
        valor_total = sum(item.valor_calculado for item in sol.itens) if sol.itens else 0
        comissao = valor_total * (percentual / 100)
        
        dados.append({
            'ID Solicitação': sol.id,
            'Data': sol.data_envio.strftime('%d/%m/%Y') if sol.data_envio else '',
            'Funcionário': usuario.nome if usuario else '',
            'Email': usuario.email if usuario else '',
            'Perfil': usuario.perfil.nome if usuario and usuario.perfil else '',
            'Fornecedor': sol.fornecedor.nome if sol.fornecedor else '',
            'Valor Total (R$)': round(valor_total, 2),
            '% Comissão': percentual,
            'Comissão (R$)': round(comissao, 2)
        })
    
    df = pd.DataFrame(dados)
    
    output = BytesIO()
    
    if formato == 'csv':
        df.to_csv(output, index=False, encoding='utf-8-sig')
        output.seek(0)
        mimetype = 'text/csv'
        filename = f'relatorio_comissoes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    else:
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        filename = f'relatorio_comissoes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    
    return send_file(
        output,
        mimetype=mimetype,
        as_attachment=True,
        download_name=filename
    )

@bp.route('/auditoria/usuarios', methods=['GET'])
@admin_required
def auditoria_usuarios():
    usuario_id = request.args.get('usuario_id')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    limite = request.args.get('limite', 100, type=int)
    
    query = AuditoriaLog.query.filter(AuditoriaLog.entidade_tipo == 'Usuario')
    
    if usuario_id:
        query = query.filter(AuditoriaLog.entidade_id == int(usuario_id))
    
    if data_inicio:
        try:
            dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            query = query.filter(AuditoriaLog.data_acao >= dt_inicio)
        except ValueError:
            pass
    
    if data_fim:
        try:
            dt_fim = datetime.strptime(data_fim, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(AuditoriaLog.data_acao < dt_fim)
        except ValueError:
            pass
    
    logs = query.order_by(AuditoriaLog.data_acao.desc()).limit(limite).all()
    
    return jsonify([log.to_dict() for log in logs]), 200

@bp.route('/perfis', methods=['GET'])
@admin_required
def listar_perfis():
    perfis = Perfil.query.filter_by(ativo=True).all()
    return jsonify([p.to_dict() for p in perfis]), 200

@bp.route('/fornecedores', methods=['GET'])
@admin_required
def listar_fornecedores_rh():
    fornecedores = Fornecedor.query.filter_by(ativo=True).all()
    return jsonify([{'id': f.id, 'nome': f.nome} for f in fornecedores]), 200

@bp.route('/dashboard', methods=['GET'])
@admin_required
def dashboard_rh():
    total_usuarios = Usuario.query.count()
    usuarios_ativos = Usuario.query.filter_by(ativo=True).count()
    usuarios_inativos = Usuario.query.filter_by(ativo=False).count()
    usuarios_com_comissao = Usuario.query.filter(Usuario.percentual_comissao > 0).count()
    
    mes_atual = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    proximo_mes = (mes_atual + timedelta(days=32)).replace(day=1)
    
    solicitacoes_mes = Solicitacao.query.filter(
        Solicitacao.status == 'aprovada',
        Solicitacao.data_envio >= mes_atual,
        Solicitacao.data_envio < proximo_mes
    ).all()
    
    total_valor_mes = 0.0
    total_comissao_mes = 0.0
    
    for sol in solicitacoes_mes:
        valor = sum(item.valor_calculado for item in sol.itens) if sol.itens else 0
        total_valor_mes += valor
        if sol.funcionario and sol.funcionario.percentual_comissao:
            total_comissao_mes += valor * (sol.funcionario.percentual_comissao / 100)
    
    por_perfil = db.session.query(
        Perfil.nome,
        func.count(Usuario.id)
    ).join(Usuario, Usuario.perfil_id == Perfil.id).group_by(Perfil.nome).all()
    
    return jsonify({
        'total_usuarios': total_usuarios,
        'usuarios_ativos': usuarios_ativos,
        'usuarios_inativos': usuarios_inativos,
        'usuarios_com_comissao': usuarios_com_comissao,
        'total_valor_mes': round(total_valor_mes, 2),
        'total_comissao_mes': round(total_comissao_mes, 2),
        'solicitacoes_aprovadas_mes': len(solicitacoes_mes),
        'usuarios_por_perfil': [{'perfil': p[0], 'quantidade': p[1]} for p in por_perfil]
    }), 200
