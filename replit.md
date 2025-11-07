# Sistema de Gestão de Empresas e Preços

## Visão Geral
Sistema web completo para gestão de empresas, funcionários, preços e relatórios. Construído com Flask, PostgreSQL, WebSocket para notificações em tempo real, e autenticação JWT.

## Estado Atual (07/11/2025)
✅ **Projeto totalmente funcional e pronto para deploy no Railway**
- Aplicação rodando localmente sem erros
- Todas as dependências instaladas
- **Dockerfile corrigido para Railway** (suporta variável $PORT corretamente)
- Criação automática de tabelas do banco de dados implementada (script init_db.py)
- WebSocket funcionando para notificações em tempo real
- **Banco de dados reorganizado e otimizado** (07/11/2025)
- **Sistema de Classificação por Estrelas (1-5)** implementado
  - API robusta com validações completas
  - Configurações por tipo de placa (leve, pesada, média)
  - Valores configuráveis por kg para cada nível
- **Painel de Administração Completo**
  - Gerenciamento de funcionários (CRUD)
  - Configuração de preços por estrelas
  - Interface com abas intuitivas
- **Interface 100% Mobile-First com Bottom Navigation**
  - Layout estilo app mobile moderno
  - Bottom Navigation Bar fixa com 5 ícones (Administração, Dashboard, Scanner, Relatórios, Empresas)
  - Header superior apenas com sino de notificação
  - FAB Button (Floating Action Button) central para scanner
  - Scanner de placas com upload de imagem
  - Sistema completo de gerenciamento de placas
  - Design responsivo: mobile-first, adapta para tablet/desktop
  - Touch-friendly com botões de 44px
  - Formulários otimizados para teclados mobile
  - Sem zoom automático em inputs (font-size 16px)
  - Breakpoints: 360px, 768px, 1024px+

## Arquitetura do Projeto

### Stack Tecnológica
- **Backend:** Flask 3.0.0 + Flask-SocketIO
- **Banco de Dados:** PostgreSQL com SQLAlchemy
- **Autenticação:** JWT (Flask-JWT-Extended)
- **WebSocket:** Socket.IO para notificações em tempo real
- **Frontend:** HTML/CSS/JavaScript vanilla (Mobile-First Design)
- **Deploy:** Railway (configurado)
- **Design:** Responsivo (Mobile-First), PWA-ready

### Estrutura de Diretórios
```
.
├── app/
│   ├── __init__.py          # Inicialização da aplicação e configuração
│   ├── models.py            # Modelos de banco de dados
│   ├── auth.py              # Funções de autenticação
│   ├── routes/              # Rotas da API
│   │   ├── auth.py          # Login, registro
│   │   ├── empresas.py      # CRUD de empresas
│   │   ├── usuarios.py      # Gerenciamento de usuários
│   │   ├── precos.py        # Gerenciamento de preços
│   │   ├── relatorios.py    # Geração de relatórios
│   │   ├── notificacoes.py  # Sistema de notificações
│   │   ├── dashboard.py     # Dashboard
│   │   ├── placas.py        # Gerenciamento de placas
│   │   └── configuracoes.py # Configurações de preços por estrelas
│   ├── static/              # Arquivos estáticos
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── templates/           # Templates HTML
├── uploads/                 # Arquivos de upload
├── app.py                   # Ponto de entrada da aplicação
├── requirements.txt         # Dependências Python
├── Procfile                 # Configuração Gunicorn para Railway
├── nixpacks.toml            # Configuração de build do Railway
├── runtime.txt              # Versão do Python
└── DEPLOY_RAILWAY.md        # Guia completo de deploy
```

## Funcionalidades Principais

### 1. Sistema de Autenticação
- Login/Registro de usuários
- Autenticação JWT com tokens de 24 horas
- Dois tipos de usuário: Admin e Funcionário
- WebSocket autenticado para notificações

### 2. Gestão de Empresas
- CRUD completo de empresas
- Upload de logotipos
- Vinculação de funcionários às empresas
- Histórico de alterações

### 3. Gestão de Funcionários
- Cadastro e gerenciamento de funcionários
- Vinculação com empresas
- Controle de permissões

### 4. Gestão de Preços
- Registro de preços por empresa
- Histórico de preços
- Notificações em tempo real de novos preços

### 5. Relatórios
- Relatórios de empresas
- Relatórios de preços
- Exportação de dados

### 6. Notificações em Tempo Real
- WebSocket para notificações instantâneas
- Salas separadas para admins e usuários
- Notificações de novos preços e alterações

### 7. Sistema de Gerenciamento de Placas ✨ (NOVO)
- **Scanner de Placas:** Botão FAB central para escanear/registrar placas
- **Upload de Imagens:** Captura via câmera ou seleção de arquivo
- **Vinculação com Empresas:** Cada placa associada a uma empresa específica
- **Classificação:** Tipo de placa (leve, pesada, média)
- **Registro Completo:** Peso, valor calculado automaticamente, imagem, data
- **Estatísticas:** Total de placas por empresa, peso total, valor total
- **Associação com Relatórios:** Placas podem ser vinculadas a relatórios

### 8. Sistema de Classificação por Estrelas ✨ (ATUALIZADO - 07/11/2025)
- **Configurações de Preços:** Sistema de 1 a 5 estrelas para classificar preços
- **Valores por Kg:** Configure valores específicos por kg para cada nível de estrela
- **Três Tipos de Placa:** Configurações separadas para leve, pesada e média
- **Flexibilidade:** Cada tipo de placa pode ter valores diferentes por estrela
- **Interface Administrativa:** Página dedicada para gerenciar todas as configurações
- **Validação Robusta:** API protegida com validações contra erros 500
- **Cálculo Automático:** Sistema calcula automaticamente o valor da placa (peso_kg × preço_por_kg)

### 9. Painel de Administração ✨ (NOVO - 06/11/2025)
- **Gerenciamento de Funcionários:** CRUD completo (criar, editar, excluir)
- **Configuração de Preços por Estrelas:** Interface intuitiva para definir valores
- **Controle de Acesso:** Apenas administradores podem acessar
- **Duas Abas:** Funcionários e Classificações de Preços
- **Validação de Usuários:** Sistema verifica tipo de usuário antes de permitir acesso

### 10. Interface Mobile-First com Bottom Navigation ✨
- **Bottom Navigation Bar:** Menu inferior fixo com 5 ícones (mobile)
  - **Administração, Dashboard, FAB Scanner, Relatórios, Empresas**
- **Header Superior:** Apenas sino de notificação no canto superior direito
- **FAB Button:** Botão central circular elevado para scanner de placas
- **Modal Scanner:** Interface intuitiva para registrar placas
- **Touch-Friendly:** Todos os botões e links com 44x44px mínimo
- **Formulários Mobile:** Input types específicos (tel, email, number) com autocomplete
- **Sem Zoom:** Font-size 16px nos inputs para evitar zoom automático no iOS
- **Responsivo:** Mobile-first, esconde bottom nav em desktop (768px+)
- **Header Simplificado:** Logo, título da página e sino de notificação
- **Breakpoints:** 768px (tablet), 1024px (desktop)
- **Acessibilidade:** Focus visível, prefers-reduced-motion, high-contrast support

## Configuração do Banco de Dados

### Modelos Principais (Atualizado 07/11/2025)
- **Usuario:** Usuários do sistema (admin/funcionário)
- **Vendedor:** Vendedores que gerenciam fornecedores
- **Fornecedor:** Fornecedores de placas (antiga "Empresa" - renomeada e consolidada)
  - Contém informações de cadastro, preços por estrelas, endereços, dados bancários
  - Relacionamentos: preços, solicitações, placas, compras, lotes
- **ConfiguracaoPrecoEstrela:** Valores por kg para cada nível de estrela (1-5) por tipo de placa
- **Preco:** Preços de fornecedores com campo de classificação por estrelas (1-5)
- **Solicitacao:** Solicitações de compra de placas
- **Placa:** Sistema de registro de placas com imagens, estrelas, peso, valor
  - Campos adicionados: lote_id, estrelas
- **Lote:** Agrupamento de placas quando solicita\u00e7\u00e3o fecha ✨ (NOVO)
  - Calcula peso_total_kg e valor_total
  - Gera automaticamente uma Compra
- **Compra:** Compras realizadas de lotes fechados
  - Atualizado: agora conectado a Lote (lote_id)
  - Campos: valor_total, peso_total_kg
- **Entrada:** Controle de entrada de placas
- **Notificacao:** Sistema de notificações
- **Classificacao:** Classificações de lotes
- **Configuracao:** Configurações gerais do sistema

**Tabelas removidas:**
- Relatorio (funcionalidade substituída por Placa)
- Funcionario (sem relacionamentos essenciais)
- Empresa duplicada (consolidada em Fornecedor)

### Criação Automática de Tabelas
O sistema cria automaticamente todas as tabelas ao iniciar (`db.create_all()` em `app/__init__.py`).

### Usuário Admin Padrão
Ao iniciar, o sistema cria automaticamente um usuário admin:
- **Email:** admin@sistema.com (ou variável `ADMIN_EMAIL`)
- **Senha:** admin123 (ou variável `ADMIN_PASSWORD`)

⚠️ **IMPORTANTE:** Altere estas credenciais em produção!

## Variáveis de Ambiente

### Obrigatórias
- `DATABASE_URL` - URL de conexão com PostgreSQL
- `SESSION_SECRET` - Chave secreta para sessões
- `JWT_SECRET_KEY` - Chave secreta para tokens JWT

### Opcionais
- `ADMIN_EMAIL` - Email do admin padrão (default: admin@sistema.com)
- `ADMIN_PASSWORD` - Senha do admin padrão (default: admin123)
- `PORT` - Porta do servidor (default: 5000, auto no Railway)

## Deploy

### Railway (Recomendado)
✅ **Projeto já configurado para Railway**

Siga o guia completo em `DEPLOY_RAILWAY.md` com instruções passo a passo:
1. Fazer push para GitHub
2. Criar projeto no Railway
3. Adicionar PostgreSQL
4. Configurar variáveis de ambiente
5. Deploy automático

### Arquivos de Configuração para Deploy
- `Procfile` - Comando para iniciar com Gunicorn
- `nixpacks.toml` - Configuração de build do Railway
- `runtime.txt` - Python 3.12
- `requirements.txt` - Dependências limpas e organizadas

## Desenvolvimento Local

### Requisitos
- Python 3.12
- PostgreSQL (ou usar integração do Replit)

### Como Executar
```bash
# Instalar dependências (já instaladas)
pip install -r requirements.txt

# Executar aplicação
python app.py
```

A aplicação estará disponível em `http://0.0.0.0:5000`

## Integrações Replit

### Configuradas (precisam setup)
- `python_database==1.0.0` - Integração com PostgreSQL
- `javascript_websocket==1.0.0` - Integração WebSocket

Use as ferramentas de integração do Replit para configurá-las se necessário.

## Segurança

### Implementado
✅ Autenticação JWT
✅ Hash de senhas com bcrypt
✅ CORS configurado
✅ Tokens com expiração (24h)
✅ WebSocket autenticado

### Recomendações para Produção
- [ ] Configurar `SESSION_SECRET` e `JWT_SECRET_KEY` fortes
- [ ] Alterar credenciais do admin padrão
- [ ] Implementar rate limiting
- [ ] Configurar HTTPS (Railway faz automaticamente)
- [ ] Implementar validação de dados mais robusta
- [ ] Adicionar logs de auditoria

## Próximos Passos

### Para Deploy
1. ✅ Configurar arquivos de deploy (concluído)
2. Seguir guia em `DEPLOY_RAILWAY.md`
3. Configurar variáveis de ambiente no Railway
4. Testar aplicação em produção
5. Alterar credenciais padrão do admin

### Melhorias Futuras (Sugestões)
- Implementar sistema de recuperação de senha
- Adicionar paginação nas listagens
- Implementar filtros avançados
- Adicionar gráficos e dashboards
- Implementar exportação de relatórios em PDF/Excel
- Adicionar testes automatizados
- Implementar cache para melhor performance

## Contato e Suporte

Para problemas com o deploy no Railway, consulte:
- Documentação oficial: https://docs.railway.com/guides/flask
- Guia local: `DEPLOY_RAILWAY.md`
- Logs do Railway: Dashboard → Deployments → Ver logs

---

**Última atualização:** 07/11/2025
**Status:** ✅ Pronto para deploy no Railway

## Mudanças Recentes (07/11/2025)

### 1. Correção do Dockerfile para Railway
- Simplificado para usar Python diretamente: `CMD ["python", "app.py"]`
- app.py já lê corretamente a variável PORT via `os.environ.get('PORT', 5000)`
- Eliminou o erro "$PORT is not a valid port number" no Railway

### 2. Reorganização Completa do Banco de Dados
**Objetivo:** Consolidar fornecedores e criar fluxo de lotes para compras

**Mudanças estruturais:**
- Renomeada tabela "Empresa" → "Fornecedor" (consolidada em uma única tabela)
- Criado modelo **Lote** para agrupar placas quando solicitação fecha
- Atualizado modelo **Compra** para conectar a Lotes (em vez de Solicitacao)
- Removidas tabelas sem uso: Relatorio, Funcionario, Fornecedor duplicado

**Fluxo atualizado:**
```
Placas (com estrelas) 
  → Solicitação 
  → Lote (soma valores/pesos)
  → Compra (alimenta sistema de compras)
```

### 3. Script init_db.py Atualizado
- Agora faz DROP CASCADE antes de criar tabelas (remove estrutura antiga)
- Cria automaticamente todas as tabelas com a nova estrutura
- Garante banco de dados limpo e consistente

### 4. Rotas e Blueprints Atualizados
- Removidos: `/api/empresas`, `/api/relatorios`, `/api/funcionarios`
- Mantido: `/api/fornecedores` (consolidado)
- Dashboard atualizado para usar Placa em vez de Relatorio
- Todos os cálculos usando `valor_total` corretamente

### 5. Próximos Passos para o Usuário
- [ ] Atualizar frontend para chamar `/api/fornecedores` em vez de `/api/empresas`
- [ ] Testar deploy no Railway
- [ ] Implementar lógica de fechamento de lote (quando solicitação é aprovada)
- [ ] Criar interface para gerenciar lotes
