# MRX System - Gestão de Compras de Sucata Eletrônica

## Visão Geral
Sistema completo para gestão de compras de sucata eletrônica com sistema de preços por estrelas (1★, 2★, 3★), autorizações de preço e geolocalização de fornecedores.

## Arquitetura do Sistema

### Backend (Flask + SQLAlchemy + PostgreSQL)
- Python 3.12
- Flask 3.0.0
- PostgreSQL (Neon-backed)
- Socket.IO para notificações em tempo real
- JWT para autenticação

### Frontend
- Vanilla JavaScript
- Tailwind CSS
- Service Workers para PWA

## Módulo Comprador - Sistema MRX (IMPLEMENTADO)

### Funcionalidades Principais
1. **Gestão de Materiais Base** (50+ tipos de sucata eletrônica)
2. **Sistema de Preços por Estrelas** (3 tabelas: 1★, 2★, 3★)
3. **Autorização de Preços** quando negociação excede tabela
4. **Geolocalização de Fornecedores** (latitude/longitude)
5. **Importação/Exportação Excel** de materiais e preços

### Modelos de Banco de Dados

#### MaterialBase
- Catálogo de 50+ tipos de sucata eletrônica
- Campos: código, nome, classificação (leve/medio/pesado), descrição
- Relacionamento com TabelaPrecoItem (preços em cada tabela)

#### TabelaPreco
- 3 tabelas fixas: 1 Estrela, 2 Estrelas, 3 Estrelas
- Nível de estrelas define a qualidade/confiabilidade do fornecedor
- Constraint UNIQUE em nivel_estrelas

#### TabelaPrecoItem
- Preço específico de cada material em cada tabela
- Constraint UNIQUE (tabela_preco_id, material_id) - evita duplicatas
- Preço em R$/kg (Numeric 10,2)

#### SolicitacaoAutorizacaoPreco
- Solicitação gerada quando comprador negocia preço acima da tabela
- Status: pendente, aprovada, rejeitada
- Calcula diferença percentual automaticamente
- Permite promoção de fornecedor para tabela superior
- Validação contra solicitações duplicadas pendentes

#### Fornecedor (Campos Adicionados)
- tabela_preco_id: vincula fornecedor a uma das 3 tabelas
- comprador_responsavel_id: comprador que atende este fornecedor
- latitude/longitude: captura geolocalização em campo
- Novos fornecedores iniciam com Tabela 1★

### APIs Backend

#### `/api/materiais-base`
- GET: listar materiais (com filtros: busca, classificação, apenas_ativos)
- GET /:id: obter material específico
- POST: criar material (admin) + vincular preços 0.00 em todas as tabelas
- PUT /:id: atualizar material e preços
- DELETE /:id: desativar material
- POST /importar-excel: importação em massa
- GET /exportar-excel: exportação completa com 3 colunas de preços
- GET /modelo-importacao: baixar template Excel

#### `/api/tabelas-preco`
- GET: listar 3 tabelas
- GET /:id: obter tabela específica
- GET /:id/precos: listar todos os preços da tabela
- PUT /:id/precos/:material_id: atualizar preço individual
- PUT /:id/precos: atualização em massa
- POST /:id/importar-excel: importação por tabela
- GET /:id/exportar-excel: exportação por tabela

#### `/api/autorizacoes-preco`
- GET: listar autorizações (filtros: status, fornecedor, comprador)
- GET /:id: obter autorização específica
- POST: criar solicitação de autorização
  - Valida preço negociado > preço tabela
  - Calcula diferença percentual
  - Bloqueia duplicatas pendentes
  - Envia notificação WebSocket para admins
- POST /:id/aprovar: aprovar autorização (admin)
  - Permite promover fornecedor para tabela superior
  - Registra em auditoria
- POST /:id/rejeitar: rejeitar autorização (admin)
  - Motivo obrigatório
- GET /estatisticas: dashboard de autorizações

### Scripts de Seed

**seed_modulo_comprador.py**
- Cria 3 tabelas de preço (1★, 2★, 3★)
- Cadastra 50 materiais base
- Gera 150 itens de preço (3 por material, inicial R$ 0.00)
- Vincula fornecedores existentes à Tabela 1★
- **IDEMPOTENTE**: pode rodar múltiplas vezes sem duplicar dados

### Estrutura de Arquivos
```
app/
├── models.py (4 novos modelos + alteração em Fornecedor)
├── routes/
│   ├── materiais_base.py (CRUD + Excel)
│   ├── tabelas_preco.py (gestão de preços)
│   └── autorizacoes_preco.py (workflow de aprovação)
└── __init__.py (registra novos blueprints)

seed_modulo_comprador.py (população inicial)
```

### Fluxo de Trabalho - Autorização de Preço

1. **Comprador em campo**:
   - Negocia com fornecedor
   - Preço negociado > preço da tabela do fornecedor
   - Sistema automaticamente cria SolicitacaoAutorizacaoPreco

2. **Notificação**:
   - WebSocket notifica admins em tempo real
   - Dashboard mostra solicitação pendente

3. **Administrador analisa**:
   - Visualiza diferença percentual
   - Justificativa do comprador
   - Histórico do fornecedor

4. **Decisão**:
   - **Aprovar**: pode promover fornecedor para tabela superior
   - **Rejeitar**: motivo obrigatório
   - Notificação enviada ao comprador

### Migrações de Banco

Executadas via execute_sql_tool:
```sql
ALTER TABLE fornecedores ADD COLUMN tabela_preco_id INTEGER REFERENCES tabelas_preco(id);
ALTER TABLE fornecedores ADD COLUMN comprador_responsavel_id INTEGER REFERENCES usuarios(id);
ALTER TABLE fornecedores ADD COLUMN latitude DECIMAL(10, 8);
ALTER TABLE fornecedores ADD COLUMN longitude DECIMAL(11, 8);
```

### Validações de Segurança

1. **Autenticação**: @jwt_required em todos os endpoints
2. **Autorização**: @admin_required para operações sensíveis
3. **Validação de Input**:
   - Preços não podem ser negativos
   - Peso deve ser > 0
   - Preço negociado deve ser > preço tabela
   - Validação contra NaN/None em campos numéricos
4. **Integridade**:
   - Constraint UNIQUE evita duplicatas
   - Foreign keys com CASCADE
   - Validação de status (pendente/aprovada/rejeitada)
5. **Auditoria**: logs de promoção de fornecedores

### Próximos Passos (PENDENTES)

1. **Frontend**:
   - [ ] /materiais-base.html (gestão de materiais + 3 colunas de preços)
   - [ ] /tabelas-preco.html (abas 1★, 2★, 3★) - ADM apenas
   - [ ] /autorizacoes-preco.html (aprovar/rejeitar) - ADM apenas

2. **Integração**:
   - [ ] Modificar wizard de compra para validar preços
   - [ ] Auto-gerar autorizações no fluxo de compra

3. **Menu**:
   - [ ] Adicionar links para novas telas
   - [ ] Badge de notificações pendentes

## Usuários do Sistema

### Perfis e Credenciais
```
Admin: admin / senha123
Comprador: comprador / senha123
Almoxarife: almoxarife / senha123
Motorista: motorista / senha123
Financeiro: financeiro / senha123
Auditoria: auditoria / senha123
```

## Tecnologias e Dependências

### Backend
- Flask 3.0.0
- Flask-SQLAlchemy
- Flask-JWT-Extended
- Flask-SocketIO
- psycopg2-binary
- pandas
- openpyxl

### Frontend
- Tailwind CSS
- Chart.js
- Socket.IO Client

## Variáveis de Ambiente
- DATABASE_URL: PostgreSQL connection string
- SESSION_SECRET: chave para sessões
- JWT_SECRET_KEY: chave para tokens JWT

## Comandos Úteis

### Executar Seed
```bash
python seed_modulo_comprador.py
```

### Iniciar Servidor
```bash
python app.py
```

### Verificar Banco
```bash
psql $DATABASE_URL -c "SELECT COUNT(*) FROM materiais_base;"
psql $DATABASE_URL -c "SELECT COUNT(*) FROM tabelas_preco;"
psql $DATABASE_URL -c "SELECT COUNT(*) FROM tabela_preco_itens;"
```

## Estrutura do Projeto
```
workspace/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── auth.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── materiais_base.py (NOVO)
│   │   ├── tabelas_preco.py (NOVO)
│   │   ├── autorizacoes_preco.py (NOVO)
│   │   └── ...
│   ├── static/
│   └── templates/
├── seed_modulo_comprador.py (NOVO)
├── app.py
└── requirements.txt
```

## Changelog

### 2025-11-18 - Implementação Módulo Comprador (Backend)
- ✅ Criados 4 novos modelos de banco de dados
- ✅ Adicionadas 4 colunas na tabela fornecedores
- ✅ Implementadas 3 APIs completas (materiais, tabelas, autorizações)
- ✅ Criado script de seed idempotente
- ✅ Implementado sistema de Excel import/export
- ✅ Adicionadas validações de segurança e integridade
- ✅ Seed executado: 3 tabelas, 50 materiais, 150 preços
- ⏳ Frontend pendente (3 telas)

---

**Última atualização**: 18 de novembro de 2025
**Status**: Backend completo | Frontend pendente
