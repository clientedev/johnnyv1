# Sistema MRX - Gestão de Compra de Placas Eletrônicas

## Visão Geral
Sistema completo para gerenciamento de compras de placas eletrônicas com rastreamento por lote, classificação por qualidade (estrelas), controle de fornecedores, e workflow automatizado desde solicitação até entrada em estoque.

## Estado Atual (10/11/2025)
✅ **Sistema Completo de Lotes com Classificação por IA**
- Módulo de solicitação de lotes com análise IA (Gemini) implementado
- Sistema de classificação leve/médio/pesado funcionando
- Configuração de estrelas por fornecedor/tipo/classificação
- Validação obrigatória de configuração antes de criar solicitações
- Fluxo completo: solicitação → aprovação → entrada
- Telas frontend completas para todo o workflow
- Backend com validação robusta (bloqueia valores zerados)
- Servidor rodando sem erros

## Arquitetura do Projeto

### Stack Tecnológica
- **Backend:** Flask 3.0.0 + SQLAlchemy
- **Banco de Dados:** PostgreSQL (Replit Database)
- **Autenticação:** JWT (Flask-JWT-Extended) - usa ID numérico
- **IA:** Google Gemini para classificação automática de placas
- **WebSocket:** Socket.IO para notificações em tempo real
- **Frontend:** HTML/CSS/JavaScript (em atualização)

### Estrutura de Dados Principal

**Nova Estrutura (09/11/2025):**
```
TipoLote (até 150 tipos configuráveis)
   ├─> FornecedorTipoLotePreco (preços por fornecedor/tipo/estrelas)
   └─> ItemSolicitacao (itens de solicitações)

Fornecedor
   ├─> FornecedorTipoLotePreco
   ├─> Solicitacao
   └─> Lote

Solicitacao (funcionário solicita compra)
   ├─> ItemSolicitacao (múltiplos itens, cada um com tipo_lote + peso + estrelas)
   └─> [aprovação admin] → Lote

Lote (agrupamento por fornecedor/tipo/estrelas)
   ├─> ItemSolicitacao (vários itens)
   └─> [aprovação admin] → EntradaEstoque

EntradaEstoque (entrada final no estoque)
```

### Fluxo Completo do Sistema
```
1. Funcionário cria SOLICITAÇÃO
   - Escolhe FORNECEDOR
   - Para cada item:
     * Seleciona TIPO DE LOTE
     * Tira FOTO da placa
     * IA sugere ESTRELAS (1-5) baseado em % verde
     * Funcionário pode ACEITAR ou OVERRIDE
     * Insere PESO (kg)
     * Sistema CALCULA VALOR automaticamente

2. Admin APROVA ou REJEITA solicitação

3. Sistema cria LOTES automaticamente
   - Agrupa itens por fornecedor/tipo/estrelas
   - Cada lote tem ID único rastreável
   - Calcula peso total e valor total

4. Admin APROVA lotes

5. Sistema cria ENTRADA DE ESTOQUE
   - Registra entrada no estoque
   - Mantém rastreabilidade completa
```

## Modelos de Dados

### TipoLote
Tipos configuráveis de placas (até 150):
- nome, codigo, descricao
- unidade_medida (kg padrão)
- ativo (booleano)

### FornecedorTipoLotePreco
Matriz de preços (até 750 pontos por fornecedor):
- fornecedor_id
- tipo_lote_id
- estrelas (1-5)
- preco_por_kg

### Solicitacao
Solicitações de compra:
- funcionario_id, fornecedor_id
- tipo_retirada (buscar/entregar)
- status (pendente/aprovada/rejeitada)
- observacoes
- data_envio, data_confirmacao, admin_id

### ItemSolicitacao
Itens individuais de solicitação:
- solicitacao_id, tipo_lote_id
- peso_kg
- estrelas_sugeridas_ia (1-5)
- estrelas_final (1-5)
- valor_calculado
- imagem_url, observacoes
- lote_id (quando agrupado)

### Lote
Agrupamento de itens:
- numero_lote (ID único rastreável)
- fornecedor_id, tipo_lote_id
- solicitacao_origem_id
- peso_total_kg, valor_total
- quantidade_itens, estrelas_media
- status (aberto/aprovado/rejeitado)
- tipo_retirada

### EntradaEstoque
Entradas finais:
- lote_id
- status (pendente/processada)
- data_entrada, data_processamento
- admin_id, observacoes

## API Endpoints

### Autenticação
- `POST /api/auth/login` - Login (retorna JWT)
- `GET /api/auth/me` - Dados do usuário atual

### Dashboard
- `GET /api/dashboard/stats` - Estatísticas gerais [ADMIN]

### Tipos de Lote
- `GET /api/tipos-lote` - Listar tipos (limite: 150)
- `POST /api/tipos-lote` - Criar tipo [ADMIN]
- `GET /api/tipos-lote/<id>` - Obter tipo
- `PUT /api/tipos-lote/<id>` - Atualizar tipo [ADMIN]
- `DELETE /api/tipos-lote/<id>` - Deletar tipo [ADMIN]

### Fornecedores
- `GET /api/fornecedores` - Listar fornecedores
- `POST /api/fornecedores` - Criar fornecedor [ADMIN]
- `GET /api/fornecedores/<id>` - Obter fornecedor
- `PUT /api/fornecedores/<id>` - Atualizar fornecedor [ADMIN]
- `GET /api/fornecedores/cnpj/<cnpj>` - Buscar por CNPJ
- `GET /api/fornecedores/<id>/precos` - Listar preços configurados
- `POST /api/fornecedores/<id>/precos` - Configurar preço [ADMIN]
- `PUT /api/fornecedores/<id>/precos` - Atualizar preço [ADMIN]

### Solicitações
- `GET /api/solicitacoes` - Listar solicitações (filtros: status, fornecedor)
- `POST /api/solicitacoes` - Criar solicitação
- `GET /api/solicitacoes/<id>` - Obter solicitação
- `POST /api/solicitacoes/<id>/aprovar` - Aprovar [ADMIN]
- `POST /api/solicitacoes/<id>/rejeitar` - Rejeitar [ADMIN]
- `DELETE /api/solicitacoes/<id>` - Deletar (apenas pendentes)

### Lotes
- `GET /api/lotes` - Listar lotes (filtros: status, fornecedor, tipo)
- `GET /api/lotes/<id>` - Obter lote com itens
- `POST /api/lotes/criar-de-solicitacao/<id>` - Criar lotes de solicitação aprovada [ADMIN]
- `PUT /api/lotes/<id>` - Atualizar lote [ADMIN]
- `POST /api/lotes/<id>/aprovar` - Aprovar lote [ADMIN]
- `POST /api/lotes/<id>/rejeitar` - Rejeitar lote [ADMIN]
- `DELETE /api/lotes/<id>` - Deletar lote [ADMIN]

### Entradas de Estoque
- `GET /api/entradas` - Listar entradas (filtros: status, fornecedor)
- `GET /api/entradas/<id>` - Obter entrada
- `POST /api/entradas` - Criar entrada de lote aprovado [ADMIN]
- `POST /api/entradas/<id>/processar` - Processar entrada [ADMIN]
- `PUT /api/entradas/<id>` - Atualizar entrada [ADMIN]
- `DELETE /api/entradas/<id>` - Deletar entrada [ADMIN]

## Configuração e Deploy

### Variáveis de Ambiente
```bash
DATABASE_URL      # PostgreSQL connection string
SESSION_SECRET    # Chave para sessões
JWT_SECRET_KEY    # Chave para JWT
GEMINI_API_KEY    # Chave da API Gemini (opcional)
ADMIN_EMAIL       # Email admin (default: admin@sistema.com)
ADMIN_PASSWORD    # Senha admin (default: admin123)
```

### Credenciais Padrão
- **Email:** admin@sistema.com
- **Senha:** admin123
⚠️ Altere em produção!

### Banco de Dados
O sistema cria automaticamente:
- Todas as tabelas necessárias
- 20 tipos de lote padrão
- Usuário admin

### Executar Localmente
```bash
python app.py
```
Servidor roda em `http://0.0.0.0:5000`

## Segurança
✅ Autenticação JWT com ID numérico (não expõe PII)
✅ Hash de senhas com bcrypt
✅ Validação de permissões (admin_required)
✅ CORS configurado
✅ Tokens com expiração de 24h

## Templates Frontend (Atualizados em 10/11/2025)

### ✅ fornecedores.html
- Cadastro e edição de fornecedores com CNPJ/CPF
- Busca automática de dados pela Receita Federal
- **Matriz de preços:** Configuração de até 150 tipos de lote × 5 estrelas
- Interface intuitiva para definir preço_por_kg para cada combinação
- Listagem com filtros e ações de editar/excluir

### ✅ solicitacoes.html
- Criação de solicitações com **múltiplos itens**
- Cada item possui:
  * Seleção de tipo de lote (dos 150 disponíveis)
  * Peso em kg
  * Classificação por estrelas (1-5)
  * Campo para foto (preparado para IA Gemini)
  * Observações individuais
- **Captura de localização:** GPS (lat/lng) + endereço manual (rua, número, CEP)
- Cálculo automático de valores baseado na matriz de preços
- Resumo em tempo real (total de itens, peso total, valor total)
- Aprovação/rejeição de solicitações (admin)

### ✅ lotes.html
- Listagem de lotes com filtros (status, fornecedor)
- Exibição de rastreamento completo:
  * Número único do lote (UUID)
  * Fornecedor e tipo de lote
  * Solicitação de origem
  * Quantidade de itens, peso total, estrelas média
- Estatísticas: Lotes abertos, aprovados, rejeitados, valor total
- Aprovação/rejeição de lotes (admin)
- Detalhes com lista de todos os itens do lote

### ✅ entradas.html
- Listagem de entradas de estoque vinculadas a lotes
- **Rastreabilidade completa:**
  * Número do lote origem
  * Fornecedor e tipo de lote
  * Solicitação original
  * Datas de criação e aprovação
- Processamento de entradas (admin)
- Estatísticas: Pendentes, processadas, valor total

### ✅ administracao.html
- Painel central com cards de acesso rápido a:
  * Fornecedores
  * Solicitações
  * Lotes
  * Entradas de Estoque
  * Consulta Avançada
  * Tipos de Lote
  * **Configurar Estrelas** (NOVO)
  * Configurações
- Gerenciamento de funcionários
- Configurações do sistema

### ✅ configurar_estrelas.html (NOVO - 10/11/2025)
- Tela administrativa para configurar estrelas por fornecedor
- Interface intuitiva com seletores visuais (1-5 estrelas)
- Configuração de leve/médio/pesado para cada combinação:
  * Fornecedor + Tipo de Lote
- Listagem de todas as configurações existentes
- Validação em tempo real
- Acessível via painel de administração

## Módulo de Lotes com Classificação IA ✅ (10/11/2025)

### Implementado
- ✅ Modelo `FornecedorTipoLoteClassificacao` (configuração de estrelas)
- ✅ Integração com Google Gemini AI para análise de imagens
- ✅ Sistema de classificação leve/médio/pesado
- ✅ Cálculo automático: `valor_base * estrelas * peso_kg`
- ✅ Validação obrigatória de configuração
- ✅ Bloqueio de valores zerados
- ✅ Telas completas: solicitação, aprovação, entradas
- ✅ Tela de configuração administrativa
- ✅ Migração de banco de dados
- ✅ Scripts de deploy para Railway

### Arquivos do Módulo
- `app/routes/solicitacao_lotes.py` - Rotas backend
- `app/templates/solicitacao_compra.html` - Criar solicitação
- `app/templates/aprovar_solicitacoes.html` - Aprovar/rejeitar
- `app/templates/lotes_aprovados.html` - Lotes aprovados
- `app/templates/configurar_estrelas.html` - Configuração admin
- `migrations/004_add_classificacao_lotes.sql` - Migration
- `railway_reset_database.sql` - Deploy Railway

## Próximos Passos

### Melhorias Futuras
- [ ] Dashboard com gráficos de análise por classificação
- [ ] Exportação de relatórios (PDF/Excel)
- [ ] Sistema de notificações em tempo real (WebSocket)
- [ ] Paginação nas listagens
- [ ] Testes automatizados
- [ ] Histórico de alterações de classificação

## Integrações Replit
- `python_database==1.0.0` (NEEDS SETUP)
- `javascript_websocket==1.0.0` (NEEDS SETUP)
- `python_gemini==1.0.0` (NEEDS SETUP)

---

**Última atualização:** 10/11/2025
**Status:** ✅ Sistema completo com módulo de lotes por classificação IA funcionando
