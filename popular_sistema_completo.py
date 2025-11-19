#!/usr/bin/env python3
"""
Script completo para popular o sistema MRX com dados falsos
para testar todas as funcionalidades e dashboard
"""

from app import create_app
from app.models import (
    db, Usuario, Perfil, Fornecedor, Vendedor, TipoLote, Solicitacao,
    ItemSolicitacao, Lote, Veiculo, Motorista, Notificacao, EntradaEstoque,
    OrdemCompra, AuditoriaLog, TabelaPreco, MaterialBase, FornecedorTipoLote,
    FornecedorClassificacaoEstrela, ConferenciaRecebimento, OrdemServico,
    LoteSeparacao, MovimentacaoEstoque, SolicitacaoAutorizacaoPreco
)
from app.auth import hash_senha
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import random

app = create_app()

# Dados para geração
NOMES = ['Silva', 'Santos', 'Oliveira', 'Souza', 'Pereira', 'Costa', 'Rodrigues', 'Almeida', 'Nascimento', 'Lima']
PRENOMES = ['João', 'Maria', 'José', 'Ana', 'Carlos', 'Fernanda', 'Pedro', 'Juliana', 'Paulo', 'Beatriz']
CIDADES = ['São Paulo', 'Rio de Janeiro', 'Belo Horizonte', 'Curitiba', 'Porto Alegre', 'Salvador', 'Recife', 'Fortaleza', 'Brasília', 'Campinas']
ESTADOS = ['SP', 'RJ', 'MG', 'PR', 'RS', 'BA', 'PE', 'CE', 'DF', 'SP']
MARCAS_VEICULOS = ['Volkswagen', 'Fiat', 'Ford', 'Chevrolet', 'Mercedes-Benz', 'Scania', 'Volvo', 'Iveco']
MODELOS_VEICULOS = ['Delivery', 'Cargo', 'Accelo', 'Atego', 'Daily', 'Sprinter', 'Ducato', 'Master']

def gerar_cpf():
    """Gera CPF falso mas válido"""
    return f"{random.randint(100, 999)}{random.randint(100, 999)}{random.randint(100, 999)}{random.randint(10, 99)}"

def gerar_cnpj():
    """Gera CNPJ falso"""
    return f"{random.randint(10, 99)}{random.randint(100, 999)}{random.randint(100, 999)}{random.randint(1000, 9999)}{random.randint(10, 99)}"

def gerar_telefone():
    """Gera telefone falso"""
    return f"(11) 9{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"

def popular_sistema_completo():
    """Popula todo o sistema com dados de teste"""
    print("=" * 80)
    print("🚀 POPULANDO SISTEMA COMPLETO COM DADOS DE TESTE")
    print("=" * 80)
    
    with app.app_context():
        try:
            # Buscar usuários existentes
            admin = Usuario.query.filter_by(tipo='admin').first()
            if not admin:
                print("❌ Erro: Usuário admin não encontrado!")
                return
            
            # ==================== LIMPEZA DE DADOS ANTERIORES ====================
            print("\n🗑️  Limpando dados de teste anteriores...")
            
            # Deletar registros na ordem correta respeitando foreign keys
            AuditoriaLog.query.delete()
            Notificacao.query.delete()
            EntradaEstoque.query.delete()
            MovimentacaoEstoque.query.delete()
            LoteSeparacao.query.delete()
            ItemSolicitacao.query.delete()
            OrdemServico.query.delete()
            OrdemCompra.query.delete()
            Lote.query.delete()
            Solicitacao.query.delete()
            SolicitacaoAutorizacaoPreco.query.delete()
            ConferenciaRecebimento.query.delete()
            FornecedorClassificacaoEstrela.query.delete()
            FornecedorTipoLote.query.delete()
            
            # Deletar motoristas que não são usuários do sistema
            Motorista.query.filter(Motorista.usuario_id == None).delete()
            
            # Deletar fornecedores de teste (emails começando com contato)
            Fornecedor.query.filter(Fornecedor.email.like('contato%')).delete()
            
            # Deletar vendedores de teste
            Vendedor.query.filter(Vendedor.email.like('vendedor%')).delete()
            
            # Deletar veículos criados pelo script
            Veiculo.query.filter(Veiculo.criado_por == admin.id).delete()
            
            # Deletar tipos de lote de teste (não deletar os padrões do sistema)
            TipoLote.query.filter(TipoLote.codigo.in_(['PMD', 'PMN', 'PVH', 'PVE', 'PRI', 'PRA', 'MD4', 'MD3', 'SSD', 'HDD', 'FAT', 'PRD', 'COO', 'GAB'])).delete()
            
            db.session.commit()
            print("✅ Dados anteriores limpos com sucesso")
            
            # ==================== VENDEDORES ====================
            print("\n👤 Criando vendedores...")
            vendedores = []
            for i in range(8):
                nome = f"{random.choice(PRENOMES)} {random.choice(NOMES)}"
                vendedor = Vendedor(
                    nome=nome,
                    email=f"vendedor{i+1}@email.com",
                    telefone=gerar_telefone(),
                    cpf=gerar_cpf(),
                    ativo=random.choice([True, True, True, False])
                )
                db.session.add(vendedor)
                vendedores.append(vendedor)
            db.session.commit()
            print(f"✅ {len(vendedores)} vendedores criados")
            
            # ==================== FORNECEDORES ====================
            print("\n🏢 Criando fornecedores...")
            nomes_empresas = [
                "TechParts Brasil", "Eletrônica Premium", "Componentes XYZ", 
                "Reciclagem Digital", "PlacaMãe & Cia", "InfoParts LTDA",
                "MegaComponentes", "TechSupply Nacional", "Eletrônicos ABC",
                "Parts & Solutions", "TechRecycle BR", "Componentes Gold",
                "Eletrônica Master", "Digital Parts", "TechWorld Supply"
            ]
            
            fornecedores = []
            tabelas_preco = TabelaPreco.query.all()
            
            for i, nome in enumerate(nomes_empresas):
                fornecedor = Fornecedor(
                    nome=nome,
                    nome_social=nome + " LTDA",
                    tipo_documento='cnpj',
                    cnpj=gerar_cnpj(),
                    rua=f"Rua {random.choice(NOMES)}, {random.randint(100, 9999)}",
                    numero=str(random.randint(1, 999)),
                    cidade=random.choice(CIDADES),
                    estado=random.choice(ESTADOS),
                    cep=f"{random.randint(10000, 99999)}-{random.randint(100, 999)}",
                    bairro=f"Bairro {random.choice(['Centro', 'Industrial', 'Comercial', 'Vila Nova'])}",
                    telefone=gerar_telefone(),
                    email=f"contato{i+1}@{nome.lower().replace(' ', '')}.com.br",
                    vendedor_id=random.choice(vendedores).id if vendedores else None,
                    tabela_preco_id=random.choice(tabelas_preco).id if tabelas_preco else 1,
                    comprador_responsavel_id=admin.id,
                    latitude=float(f"-23.{random.randint(10, 99)}"),
                    longitude=float(f"-46.{random.randint(10, 99)}"),
                    conta_bancaria=f"{random.randint(10000, 99999)}-{random.randint(0, 9)}",
                    agencia=f"{random.randint(1000, 9999)}",
                    chave_pix=gerar_cnpj(),
                    banco=random.choice(['Banco do Brasil', 'Itaú', 'Bradesco', 'Santander', 'Caixa']),
                    condicao_pagamento=random.choice(['avista', '7dias', '15dias', '30dias']),
                    forma_pagamento=random.choice(['pix', 'boleto', 'transferencia']),
                    observacoes=f"Fornecedor cadastrado em {datetime.now().strftime('%d/%m/%Y')}",
                    criado_por_id=admin.id,
                    ativo=random.choice([True, True, True, False])
                )
                db.session.add(fornecedor)
                fornecedores.append(fornecedor)
            db.session.commit()
            print(f"✅ {len(fornecedores)} fornecedores criados")
            
            # ==================== TIPOS DE LOTE ====================
            print("\n📦 Criando tipos de lote...")
            tipos_lote_data = [
                ("Placa Mãe Desktop", "PMD", "media", "Placas mãe de desktops"),
                ("Placa Mãe Notebook", "PMN", "leve", "Placas mãe de notebooks"),
                ("Placa de Vídeo High-End", "PVH", "pesada", "Placas de vídeo premium"),
                ("Placa de Vídeo Entry", "PVE", "media", "Placas de vídeo básicas"),
                ("Processador Intel", "PRI", "pesada", "CPUs Intel"),
                ("Processador AMD", "PRA", "pesada", "CPUs AMD"),
                ("Memória DDR4", "MD4", "leve", "Memória RAM DDR4"),
                ("Memória DDR3", "MD3", "leve", "Memória RAM DDR3"),
                ("SSD/NVMe", "SSD", "media", "Discos sólidos"),
                ("HD Mecânico", "HDD", "media", "Discos rígidos"),
                ("Fonte ATX", "FAT", "pesada", "Fontes de alimentação"),
                ("Placa de Rede", "PRD", "leve", "Placas ethernet/wifi"),
                ("Coolers e Dissipadores", "COO", "leve", "Sistema de refrigeração"),
                ("Gabinetes", "GAB", "media", "Cases de computador")
            ]
            
            tipos_lote = []
            for nome, codigo, classificacao, descricao in tipos_lote_data:
                tipo = TipoLote(
                    nome=nome,
                    codigo=codigo,
                    classificacao=classificacao,
                    descricao=descricao,
                    ativo=True
                )
                db.session.add(tipo)
                tipos_lote.append(tipo)
            db.session.commit()
            print(f"✅ {len(tipos_lote)} tipos de lote criados")
            
            # Vincular fornecedores aos tipos de lote
            print("\n🔗 Vinculando fornecedores aos tipos de lote...")
            for fornecedor in fornecedores:
                # Cada fornecedor trabalha com 3-7 tipos de lote
                tipos_selecionados = random.sample(tipos_lote, random.randint(3, 7))
                for tipo in tipos_selecionados:
                    vinculo = FornecedorTipoLote(
                        fornecedor_id=fornecedor.id,
                        tipo_lote_id=tipo.id,
                        ativo=True
                    )
                    db.session.add(vinculo)
                
                # Configurar estrelas por classificação para este fornecedor (UMA VEZ POR FORNECEDOR)
                for classificacao in ['leve', 'medio', 'pesado']:
                    config_estrelas = FornecedorClassificacaoEstrela(
                        fornecedor_id=fornecedor.id,
                        classificacao=classificacao,
                        estrelas=random.randint(2, 5),
                        ativo=True
                    )
                    db.session.add(config_estrelas)
            db.session.commit()
            print(f"✅ Fornecedores vinculados aos tipos de lote")
            
            # ==================== VEÍCULOS ====================
            print("\n🚛 Criando veículos...")
            veiculos = []
            for i in range(10):
                veiculo = Veiculo(
                    placa=f"ABC{random.randint(1000, 9999)}",
                    renavam=f"{random.randint(10000000000, 99999999999)}",
                    tipo=random.choice(['Caminhão', 'Van', 'Utilitário', 'Truck']),
                    capacidade=random.choice([500, 1000, 1500, 2000, 3000, 5000]),
                    marca=random.choice(MARCAS_VEICULOS),
                    modelo=random.choice(MODELOS_VEICULOS),
                    ano=random.randint(2015, 2024),
                    ativo=random.choice([True, True, True, False]),
                    criado_por=admin.id
                )
                db.session.add(veiculo)
                veiculos.append(veiculo)
            db.session.commit()
            print(f"✅ {len(veiculos)} veículos criados")
            
            # ==================== MOTORISTAS ====================
            print("\n🚗 Criando motoristas...")
            motoristas = []
            for i in range(8):
                nome = f"{random.choice(PRENOMES)} {random.choice(NOMES)}"
                motorista = Motorista(
                    nome=nome,
                    cpf=gerar_cpf(),
                    telefone=gerar_telefone(),
                    email=f"motorista{i+1}@email.com",
                    cnh=f"{random.randint(10000000000, 99999999999)}",
                    categoria_cnh=random.choice(['B', 'C', 'D', 'E']),
                    veiculo_id=random.choice(veiculos).id if veiculos else None,
                    ativo=random.choice([True, True, True, False]),
                    criado_por=admin.id
                )
                db.session.add(motorista)
                motoristas.append(motorista)
            db.session.commit()
            print(f"✅ {len(motoristas)} motoristas criados")
            
            # ==================== SOLICITAÇÕES, ITENS E LOTES ====================
            print("\n📋 Criando solicitações, itens e lotes (últimos 6 meses)...")
            
            hoje = datetime.now()
            total_solicitacoes = 0
            total_itens = 0
            total_lotes = 0
            total_ocs = 0
            
            # Criar 60+ solicitações nos últimos 6 meses
            for mes_offset in range(5, -1, -1):
                data_mes = hoje - relativedelta(months=mes_offset)
                
                # 10-15 solicitações por mês
                num_solicitacoes = random.randint(10, 15)
                
                for _ in range(num_solicitacoes):
                    dia = random.randint(1, 28)
                    hora = random.randint(8, 18)
                    data_envio = datetime(data_mes.year, data_mes.month, dia, hora, random.randint(0, 59))
                    
                    fornecedor = random.choice(fornecedores)
                    status = random.choices(
                        ['pendente', 'aprovada', 'rejeitada', 'em_analise'],
                        weights=[20, 60, 10, 10]
                    )[0]
                    
                    solicitacao = Solicitacao(
                        funcionario_id=admin.id,
                        fornecedor_id=fornecedor.id,
                        tipo_retirada=random.choice(['buscar', 'entregar', 'buscar']),
                        modalidade_frete=random.choice(['FOB', 'CIF']),
                        status=status,
                        observacoes=f"Solicitação {total_solicitacoes + 1} - {data_envio.strftime('%B/%Y')}",
                        data_envio=data_envio,
                        data_confirmacao=data_envio + timedelta(days=random.randint(1, 5)) if status in ['aprovada', 'rejeitada'] else None,
                        admin_id=admin.id if status in ['aprovada', 'rejeitada'] else None,
                        rua=f"Rua {random.choice(NOMES)}",
                        numero=str(random.randint(1, 999)),
                        cep=f"{random.randint(10000, 99999)}-{random.randint(100, 999)}",
                        endereco_completo=f"Rua {random.choice(NOMES)}, {random.randint(1, 999)}, {random.choice(CIDADES)} - {random.choice(ESTADOS)}"
                    )
                    db.session.add(solicitacao)
                    db.session.flush()
                    
                    # Criar 2-5 itens por solicitação
                    num_itens = random.randint(2, 5)
                    valor_total_solicitacao = 0
                    
                    for _ in range(num_itens):
                        tipo_lote = random.choice(tipos_lote)
                        peso_kg = round(random.uniform(5.0, 100.0), 2)
                        estrelas = random.randint(1, 5)
                        preco_kg = random.uniform(10.0, 80.0)
                        valor_item = round(peso_kg * preco_kg, 2)
                        valor_total_solicitacao += valor_item
                        
                        class_map = {"media": "medio", "pesada": "pesado", "leve": "leve"}
                        classificacao = class_map.get(tipo_lote.classificacao, "medio")
                        
                        item = ItemSolicitacao(
                            solicitacao_id=solicitacao.id,
                            tipo_lote_id=tipo_lote.id,
                            peso_kg=peso_kg,
                            estrelas_final=estrelas,
                            estrelas_sugeridas_ia=random.randint(1, 5),
                            classificacao=classificacao,
                            classificacao_sugerida_ia=random.choice(['leve', 'medio', 'pesado']),
                            valor_calculado=valor_item,
                            preco_por_kg_snapshot=preco_kg,
                            estrelas_snapshot=estrelas,
                            observacoes=f"Item {total_itens + 1} - {tipo_lote.nome}"
                        )
                        db.session.add(item)
                        total_itens += 1
                    
                    total_solicitacoes += 1
                    
                    # Se aprovada, criar OC e lote
                    if status == 'aprovada':
                        # Criar Ordem de Compra
                        oc = OrdemCompra(
                            solicitacao_id=solicitacao.id,
                            fornecedor_id=fornecedor.id,
                            valor_total=valor_total_solicitacao,
                            status=random.choice(['aprovada', 'em_analise', 'aprovada', 'aprovada']),
                            aprovado_por=admin.id,
                            aprovado_em=data_envio + timedelta(hours=random.randint(1, 48)),
                            criado_por=admin.id,
                            observacao=f"OC automática - {data_envio.strftime('%d/%m/%Y')}"
                        )
                        db.session.add(oc)
                        db.session.flush()
                        total_ocs += 1
                        
                        # Criar lote
                        tipo_lote = random.choice(tipos_lote)
                        peso_total = round(random.uniform(100.0, 1000.0), 2)
                        valor_total = round(peso_total * random.uniform(20.0, 70.0), 2)
                        data_criacao = data_envio + timedelta(days=random.randint(1, 7))
                        
                        lote = Lote(
                            numero_lote=f"LT{data_mes.year}{data_mes.month:02d}{random.randint(1000, 9999)}",
                            fornecedor_id=fornecedor.id,
                            tipo_lote_id=tipo_lote.id,
                            solicitacao_origem_id=solicitacao.id,
                            oc_id=oc.id,
                            peso_total_kg=peso_total,
                            valor_total=valor_total,
                            quantidade_itens=num_itens,
                            estrelas_media=float(random.randint(25, 45) / 10),
                            classificacao_predominante=random.choice(['leve', 'medio', 'pesado']),
                            status=random.choice(['aprovado', 'em_conferencia', 'em_separacao', 'disponivel', 'aprovado', 'aprovado']),
                            tipo_retirada=solicitacao.tipo_retirada,
                            localizacao_atual=f"Prateleira {random.choice(['A', 'B', 'C'])}-{random.randint(1, 50)}",
                            data_criacao=data_criacao,
                            data_aprovacao=data_criacao + timedelta(hours=random.randint(1, 24)),
                            conferente_id=admin.id,
                            observacoes=f"Lote {total_lotes + 1} - {tipo_lote.nome}"
                        )
                        db.session.add(lote)
                        db.session.flush()  # Flush para obter o ID do lote
                        total_lotes += 1
                        
                        # Criar entrada de estoque para alguns lotes
                        if random.random() > 0.3:
                            entrada = EntradaEstoque(
                                lote_id=lote.id,
                                admin_id=admin.id,
                                status=random.choice(['processada', 'pendente', 'processada', 'processada']),
                                data_entrada=data_criacao,
                                data_processamento=data_criacao + timedelta(hours=random.randint(1, 12)) if random.random() > 0.3 else None,
                                observacoes=f"Entrada automática - Lote {lote.numero_lote}"
                            )
                            db.session.add(entrada)
            
            db.session.commit()
            print(f"✅ {total_solicitacoes} solicitações criadas")
            print(f"✅ {total_itens} itens de solicitação criados")
            print(f"✅ {total_lotes} lotes criados")
            print(f"✅ {total_ocs} ordens de compra criadas")
            
            # ==================== NOTIFICAÇÕES ====================
            print("\n🔔 Criando notificações...")
            tipos_notificacao = [
                ('Nova solicitação aprovada', 'Sua solicitação #{} foi aprovada', 'sucesso'),
                ('Lote disponível', 'Lote {} está disponível para retirada', 'info'),
                ('Conferência pendente', 'Lote {} aguarda conferência', 'alerta'),
                ('Pagamento processado', 'Pagamento do lote {} foi processado', 'sucesso'),
                ('Entrega agendada', 'Entrega do lote {} agendada para {}', 'info'),
                ('Documento pendente', 'Documentação do fornecedor {} pendente', 'alerta'),
            ]
            
            usuarios = Usuario.query.all()
            total_notificacoes = 0
            
            for _ in range(50):
                titulo_template, mensagem_template, tipo = random.choice(tipos_notificacao)
                data_notif = hoje - timedelta(days=random.randint(0, 180))
                
                notificacao = Notificacao(
                    usuario_id=random.choice(usuarios).id,
                    titulo=titulo_template.format(random.randint(1000, 9999)),
                    mensagem=mensagem_template.format(random.randint(1000, 9999), data_notif.strftime('%d/%m/%Y')),
                    tipo=tipo,
                    lida=random.choice([True, False, False, True]),
                    data_envio=data_notif
                )
                db.session.add(notificacao)
                total_notificacoes += 1
            
            db.session.commit()
            print(f"✅ {total_notificacoes} notificações criadas")
            
            # ==================== LOGS DE AUDITORIA ====================
            print("\n📝 Criando logs de auditoria...")
            acoes = ['criar', 'editar', 'excluir', 'aprovar', 'rejeitar', 'visualizar']
            entidades = ['solicitacao', 'lote', 'fornecedor', 'usuario', 'ordem_compra', 'veiculo']
            
            total_logs = 0
            for _ in range(100):
                data_acao = hoje - timedelta(days=random.randint(0, 180))
                
                log = AuditoriaLog(
                    usuario_id=random.choice(usuarios).id if random.random() > 0.1 else None,
                    acao=random.choice(acoes),
                    entidade_tipo=random.choice(entidades),
                    entidade_id=random.randint(1, 100),
                    detalhes={
                        'campo_alterado': random.choice(['status', 'valor', 'observacao']),
                        'valor_anterior': random.choice(['pendente', '100.00', 'Observação antiga']),
                        'valor_novo': random.choice(['aprovada', '150.00', 'Observação nova'])
                    },
                    ip_address=f"192.168.1.{random.randint(1, 255)}",
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
                    data_acao=data_acao
                )
                db.session.add(log)
                total_logs += 1
            
            db.session.commit()
            print(f"✅ {total_logs} logs de auditoria criados")
            
            # ==================== RESUMO FINAL ====================
            print("\n" + "=" * 80)
            print("✅ SISTEMA POPULADO COM SUCESSO!")
            print("=" * 80)
            print("\n📊 RESUMO DOS DADOS CRIADOS:")
            print("-" * 80)
            print(f"  👤 Vendedores:              {len(vendedores)}")
            print(f"  🏢 Fornecedores:            {len(fornecedores)}")
            print(f"  📦 Tipos de Lote:           {len(tipos_lote)}")
            print(f"  🚛 Veículos:                {len(veiculos)}")
            print(f"  🚗 Motoristas:              {len(motoristas)}")
            print(f"  📋 Solicitações:            {total_solicitacoes}")
            print(f"  📄 Itens de Solicitação:    {total_itens}")
            print(f"  📦 Lotes:                   {total_lotes}")
            print(f"  📄 Ordens de Compra:        {total_ocs}")
            print(f"  🔔 Notificações:            {total_notificacoes}")
            print(f"  📝 Logs de Auditoria:       {total_logs}")
            print("-" * 80)
            print("\n🎉 Agora você pode acessar o dashboard e testar todas as funcionalidades!")
            print("   Os dados estão distribuídos nos últimos 6 meses para análise realista.\n")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Erro ao popular sistema: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    popular_sistema_completo()
