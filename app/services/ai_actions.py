from app.models import (
    db, Usuario, Fornecedor, Solicitacao, Lote, TipoLote,
    Notificacao, EntradaEstoque, OrdemCompra, ItemSolicitacao
)
from datetime import datetime
import json
import re

SYSTEM_ACTIONS = {
    'criar_fornecedor': {
        'descricao': 'Criar um novo fornecedor no sistema',
        'parametros': ['nome', 'cnpj_ou_cpf', 'telefone', 'email', 'cidade', 'estado'],
        'exemplo': 'Criar fornecedor João Silva, CPF 123.456.789-00, telefone 11999999999'
    },
    'criar_notificacao': {
        'descricao': 'Enviar notificação para um usuário',
        'parametros': ['usuario_id_ou_tipo', 'titulo', 'mensagem'],
        'exemplo': 'Notificar admin sobre nova solicitação pendente'
    },
    'listar_fornecedores': {
        'descricao': 'Listar fornecedores ativos',
        'parametros': ['limite'],
        'exemplo': 'Listar os 10 últimos fornecedores'
    },
    'listar_solicitacoes': {
        'descricao': 'Listar solicitações pendentes ou por status',
        'parametros': ['status', 'limite'],
        'exemplo': 'Mostrar solicitações pendentes'
    },
    'resumo_sistema': {
        'descricao': 'Gerar resumo completo do sistema',
        'parametros': [],
        'exemplo': 'Me dê um resumo do sistema'
    },
    'dica_operacional': {
        'descricao': 'Fornecer dica baseada nos dados atuais',
        'parametros': ['area'],
        'exemplo': 'Me dê dicas para melhorar as operações'
    }
}

def detectar_intencao_acao(mensagem):
    mensagem_lower = mensagem.lower()
    
    if any(p in mensagem_lower for p in ['criar fornecedor', 'cadastrar fornecedor', 'novo fornecedor', 'adicionar fornecedor']):
        return 'criar_fornecedor'
    
    if any(p in mensagem_lower for p in ['notificar', 'enviar notificacao', 'avisar', 'alertar']):
        return 'criar_notificacao'
    
    if any(p in mensagem_lower for p in ['listar fornecedor', 'mostrar fornecedor', 'quais fornecedor', 'ver fornecedor']):
        return 'listar_fornecedores'
    
    if any(p in mensagem_lower for p in ['listar solicitac', 'mostrar solicitac', 'pedidos pendente', 'solicitacoes pendente']):
        return 'listar_solicitacoes'
    
    if any(p in mensagem_lower for p in ['resumo', 'status geral', 'visao geral', 'como esta o sistema']):
        return 'resumo_sistema'
    
    if any(p in mensagem_lower for p in ['dica', 'sugestao', 'melhorar', 'otimizar', 'recomendacao']):
        return 'dica_operacional'
    
    return None

def executar_acao(acao, mensagem, usuario_id):
    try:
        if acao == 'criar_fornecedor':
            return criar_fornecedor_por_texto(mensagem, usuario_id)
        elif acao == 'criar_notificacao':
            return criar_notificacao_por_texto(mensagem, usuario_id)
        elif acao == 'listar_fornecedores':
            return listar_fornecedores_acao()
        elif acao == 'listar_solicitacoes':
            return listar_solicitacoes_acao(mensagem)
        elif acao == 'resumo_sistema':
            return gerar_resumo_sistema()
        elif acao == 'dica_operacional':
            return gerar_dicas_operacionais()
        else:
            return None, 'Ação não reconhecida'
    except Exception as e:
        return None, f'Erro ao executar ação: {str(e)}'

def criar_fornecedor_por_texto(mensagem, usuario_id):
    nome_match = re.search(r'(?:fornecedor|nome)[:\s]+([A-Za-zÀ-ú\s]+?)(?:,|cpf|cnpj|telefone|email|$)', mensagem, re.IGNORECASE)
    cpf_match = re.search(r'cpf[:\s]*(\d{3}\.?\d{3}\.?\d{3}-?\d{2})', mensagem, re.IGNORECASE)
    cnpj_match = re.search(r'cnpj[:\s]*(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})', mensagem, re.IGNORECASE)
    telefone_match = re.search(r'(?:telefone|tel|fone)[:\s]*(\(?\d{2}\)?\s?\d{4,5}-?\d{4})', mensagem, re.IGNORECASE)
    email_match = re.search(r'email[:\s]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', mensagem, re.IGNORECASE)
    cidade_match = re.search(r'cidade[:\s]+([A-Za-zÀ-ú\s]+?)(?:,|estado|$)', mensagem, re.IGNORECASE)
    
    if not nome_match:
        return None, 'Não consegui identificar o nome do fornecedor. Por favor, forneça: "Criar fornecedor [NOME], CPF/CNPJ [NUMERO]"'
    
    nome = nome_match.group(1).strip()
    
    fornecedor = Fornecedor(
        nome=nome,
        cnpj=cnpj_match.group(1) if cnpj_match else None,
        cpf=cpf_match.group(1) if cpf_match else None,
        tipo_documento='cnpj' if cnpj_match else 'cpf' if cpf_match else None,
        telefone=telefone_match.group(1) if telefone_match else None,
        email=email_match.group(1) if email_match else None,
        cidade=cidade_match.group(1).strip() if cidade_match else None,
        criado_por_id=usuario_id
    )
    
    db.session.add(fornecedor)
    db.session.commit()
    
    resultado = f"""Fornecedor criado com sucesso!

**Dados cadastrados:**
- ID: {fornecedor.id}
- Nome: {fornecedor.nome}
- Documento: {fornecedor.cnpj or fornecedor.cpf or 'Não informado'}
- Telefone: {fornecedor.telefone or 'Não informado'}
- Email: {fornecedor.email or 'Não informado'}
- Cidade: {fornecedor.cidade or 'Não informada'}

O fornecedor já está disponível no sistema para receber solicitações."""
    
    return {'fornecedor_id': fornecedor.id, 'dados': fornecedor.to_dict()}, resultado

def criar_notificacao_por_texto(mensagem, usuario_id):
    titulo_match = re.search(r'(?:titulo|assunto)[:\s]+([^,\.]+)', mensagem, re.IGNORECASE)
    msg_match = re.search(r'(?:mensagem|texto)[:\s]+(.+?)(?:$|para)', mensagem, re.IGNORECASE)
    
    admin_destinatario = 'admin' in mensagem.lower() or 'administrador' in mensagem.lower()
    todos_destinatario = 'todos' in mensagem.lower()
    
    titulo = titulo_match.group(1).strip() if titulo_match else 'Notificação do Assistente'
    conteudo = msg_match.group(1).strip() if msg_match else mensagem[:200]
    
    destinatarios = []
    
    if admin_destinatario:
        admins = Usuario.query.filter_by(tipo='admin', ativo=True).all()
        destinatarios = [u.id for u in admins]
    elif todos_destinatario:
        usuarios = Usuario.query.filter_by(ativo=True).limit(50).all()
        destinatarios = [u.id for u in usuarios]
    else:
        destinatarios = [usuario_id]
    
    count = 0
    for dest_id in destinatarios:
        notif = Notificacao(
            usuario_id=dest_id,
            titulo=titulo,
            mensagem=conteudo,
            tipo='assistente'
        )
        db.session.add(notif)
        count += 1
    
    db.session.commit()
    
    resultado = f"""Notificação enviada com sucesso!

**Detalhes:**
- Título: {titulo}
- Destinatários: {count} usuário(s)
- Mensagem: {conteudo[:100]}{'...' if len(conteudo) > 100 else ''}"""
    
    return {'notificacoes_enviadas': count}, resultado

def listar_fornecedores_acao(limite=10):
    fornecedores = Fornecedor.query.filter_by(ativo=True).order_by(
        Fornecedor.data_cadastro.desc()
    ).limit(limite).all()
    
    if not fornecedores:
        return {'total': 0}, 'Não há fornecedores cadastrados no sistema.'
    
    lista = []
    for f in fornecedores:
        lista.append(f"- **{f.nome}** (ID: {f.id}) - {f.cidade or 'Cidade não informada'}")
    
    resultado = f"""**Fornecedores Ativos ({len(fornecedores)} mais recentes):**

{chr(10).join(lista)}

Total de fornecedores ativos: {Fornecedor.query.filter_by(ativo=True).count()}"""
    
    return {'fornecedores': [f.to_dict() for f in fornecedores]}, resultado

def listar_solicitacoes_acao(mensagem):
    status = 'pendente'
    if 'aprovad' in mensagem.lower():
        status = 'aprovado'
    elif 'rejeitad' in mensagem.lower() or 'recusad' in mensagem.lower():
        status = 'rejeitado'
    elif 'todas' in mensagem.lower():
        status = None
    
    query = Solicitacao.query
    if status:
        query = query.filter_by(status=status)
    
    solicitacoes = query.order_by(Solicitacao.data_solicitacao.desc()).limit(10).all()
    
    if not solicitacoes:
        return {'total': 0}, f'Não há solicitações {status or "no sistema"}.'
    
    lista = []
    for s in solicitacoes:
        fornecedor_nome = s.fornecedor.nome if s.fornecedor else 'Não informado'
        lista.append(f"- **#{s.id}** - {fornecedor_nome} - Status: {s.status.upper()}")
    
    resultado = f"""**Solicitações {status.upper() if status else 'TODAS'} ({len(solicitacoes)} mais recentes):**

{chr(10).join(lista)}

Total com status '{status or 'todos'}': {query.count()}"""
    
    return {'solicitacoes': [s.to_dict() for s in solicitacoes]}, resultado

def gerar_resumo_sistema():
    total_fornecedores = Fornecedor.query.filter_by(ativo=True).count()
    total_solicitacoes = Solicitacao.query.count()
    solicitacoes_pendentes = Solicitacao.query.filter_by(status='pendente').count()
    solicitacoes_aprovadas = Solicitacao.query.filter_by(status='aprovado').count()
    total_lotes = Lote.query.count()
    total_entradas = EntradaEstoque.query.count()
    total_ocs = OrdemCompra.query.count()
    total_usuarios = Usuario.query.filter_by(ativo=True).count()
    
    try:
        ocs_abertas = OrdemCompra.query.filter(OrdemCompra.status.in_(['pendente', 'em_transito', 'em_analise'])).count()
    except:
        ocs_abertas = 0
    
    resultado = f"""**RESUMO GERAL DO SISTEMA MRX**

**Fornecedores:**
- Ativos: {total_fornecedores}

**Solicitações:**
- Total: {total_solicitacoes}
- Pendentes: {solicitacoes_pendentes}
- Aprovadas: {solicitacoes_aprovadas}

**Operações:**
- Lotes registrados: {total_lotes}
- Entradas no estoque: {total_entradas}
- Ordens de Compra: {total_ocs} ({ocs_abertas} em aberto)

**Usuários:**
- Ativos: {total_usuarios}

O sistema está funcionando normalmente. Use comandos como "listar fornecedores" ou "solicitações pendentes" para mais detalhes."""
    
    return {
        'fornecedores': total_fornecedores,
        'solicitacoes': total_solicitacoes,
        'pendentes': solicitacoes_pendentes,
        'lotes': total_lotes,
        'usuarios': total_usuarios
    }, resultado

def gerar_dicas_operacionais():
    solicitacoes_pendentes = Solicitacao.query.filter_by(status='pendente').count()
    fornecedores_sem_email = Fornecedor.query.filter_by(ativo=True, email=None).count()
    
    try:
        ocs_abertas = OrdemCompra.query.filter(OrdemCompra.status.in_(['pendente', 'em_analise'])).count()
    except:
        ocs_abertas = 0
    
    dicas = []
    
    if solicitacoes_pendentes > 5:
        dicas.append(f"Há **{solicitacoes_pendentes} solicitações pendentes**. Considere revisar e aprovar as mais antigas para manter o fluxo de compras ativo.")
    
    if fornecedores_sem_email > 0:
        dicas.append(f"Existem **{fornecedores_sem_email} fornecedores sem email** cadastrado. Complete os dados para melhorar a comunicação.")
    
    if ocs_abertas > 3:
        dicas.append(f"Há **{ocs_abertas} ordens de compra em aberto**. Verifique se há alguma pendência para finalização.")
    
    if not dicas:
        dicas.append("Parabéns! O sistema está em dia. Continue monitorando as operações regularmente.")
        dicas.append("Dica: Use o scanner de placas para classificar materiais rapidamente.")
        dicas.append("Dica: Acompanhe as cotações de metais para tomar melhores decisões de compra.")
    
    resultado = f"""**DICAS OPERACIONAIS**

{chr(10).join(['- ' + d for d in dicas])}

Posso ajudar com mais alguma análise?"""
    
    return {'dicas': dicas}, resultado

def obter_contexto_completo_ia():
    dados = gerar_resumo_sistema()[0]
    
    contexto = f"""Você é o assistente inteligente do sistema MRX Systems - um ERP completo para gestão de compra e venda de materiais eletrônicos para reciclagem de metais preciosos.

VOCÊ PODE EXECUTAR AÇÕES NO SISTEMA:
1. Criar fornecedores - Diga: "Criar fornecedor [nome], CPF [numero], telefone [numero]"
2. Enviar notificações - Diga: "Notificar admin sobre [assunto]"
3. Listar dados - Diga: "Listar fornecedores" ou "Mostrar solicitações pendentes"
4. Gerar resumos - Diga: "Resumo do sistema" ou "Status geral"
5. Obter dicas - Diga: "Me dê dicas" ou "Como melhorar as operações"

DADOS ATUAIS DO SISTEMA:
- Fornecedores ativos: {dados.get('fornecedores', 0)}
- Solicitações: {dados.get('solicitacoes', 0)} (pendentes: {dados.get('pendentes', 0)})
- Lotes: {dados.get('lotes', 0)}
- Usuários: {dados.get('usuarios', 0)}

MÓDULOS DISPONÍVEIS:
- Fornecedores, Solicitações, Lotes, Estoque, Ordens de Compra
- Dashboard, Conferências, Logística, Cotações de Metais
- Scanner de Placas (classifica PCBs com IA)
- Notificações em tempo real

COMO RESPONDER:
- Em português brasileiro, claro e objetivo
- Ofereça insights baseados nos dados
- Execute ações quando solicitado
- Forneça dicas proativas
- Se não souber algo específico, sugira onde encontrar

IMPORTANTE: Você tem capacidade de INSERIR e MODIFICAR dados no sistema quando solicitado pelo usuário."""
    
    return contexto
