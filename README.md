# ⚙️ MetalGest - Gestão de Metais e Eletrônicos

Sistema profissional completo para controlar compras de metais e eletrônicos feitas por funcionários em diferentes empresas, com registro de fotos, localização GPS, peso dos materiais e aprovação administrativa.

## ✨ Funcionalidades

### Para Administradores
- ✅ Dashboard completo com estatísticas em tempo real
- ✅ Gerenciamento de empresas, funcionários e preços
- ✅ Aprovação/reprovação de relatórios de compra
- ✅ Gráficos mensais de movimentação (Chart.js)
- ✅ Mapa interativo com geolocalização (Leaflet.js)
- ✅ Notificações em tempo real via WebSocket
- ✅ Ranking de empresas com mais movimentação

### Para Funcionários
- ✅ Criar relatórios de compra com:
  - Upload de foto da placa
  - Seleção de tipo (leve, média, pesada)
  - Peso em kg
  - Captura automática de GPS
  - Observações
- ✅ Visualizar histórico de relatórios
- ✅ Receber notificações de aprovação/reprovação

### PWA (Progressive Web App)
- ✅ Instalável em dispositivos móveis
- ✅ Ícone na tela inicial
- ✅ Service Worker para cache
- ✅ Popup de instalação automático

## 🚀 Como Usar

### 1. Acessar o Sistema

Abra o navegador e acesse o sistema. Você verá a tela de login.

**Credenciais padrão (desenvolvimento):**
- Email: `admin@sistema.com`
- Senha: `admin123`

### 2. Como Administrador

Após fazer login como administrador, você terá acesso a:

- **Dashboard:** Visualize estatísticas, gráficos e mapa
- **Relatórios:** Aprove ou reprove relatórios pendentes
- **Empresas:** Cadastre empresas e tabelas de preços
- **Funcionários:** Crie contas para funcionários
- **Notificações:** Receba alertas de novos relatórios

### 3. Como Funcionário

Após fazer login como funcionário:

1. Clique em "Novo Relatório"
2. Selecione a empresa
3. Escolha o tipo de placa
4. Informe o peso em kg
5. Faça upload da foto
6. Adicione observações (opcional)
7. O sistema capturará automaticamente sua localização GPS
8. Envie o relatório e aguarde aprovação

### 4. Instalar como App (Mobile)

Em dispositivos móveis:

1. Acesse o sistema pelo navegador
2. Clique no banner "Instalar App"
3. O app será adicionado à tela inicial
4. Acesse rapidamente sem abrir o navegador

## 🛠️ Tecnologias

- **Backend:** Python 3.11 + Flask
- **Banco de Dados:** PostgreSQL
- **ORM:** SQLAlchemy
- **Autenticação:** JWT + bcrypt
- **WebSocket:** Flask-SocketIO
- **Frontend:** HTML5, CSS3, JavaScript
- **Gráficos:** Chart.js
- **Mapas:** Leaflet.js
- **PWA:** Service Worker + Manifest

## 📦 Deploy no Railway

### Passo 1: Preparar Variáveis de Ambiente

Configure as seguintes variáveis no Railway:

```
DATABASE_URL=<automático>
JWT_SECRET_KEY=<gere uma senha forte>
SESSION_SECRET=<gere uma senha forte>
ADMIN_EMAIL=seu-email@empresa.com
ADMIN_PASSWORD=<senha forte e segura>
```

**⚠️ IMPORTANTE:** Nunca use as credenciais padrão em produção!

### Passo 2: Deploy

1. Conecte seu repositório ao Railway
2. O Railway detectará automaticamente o `Procfile`
3. Configure as variáveis de ambiente
4. Faça o deploy

O sistema será executado com:
```bash
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app
```

## 📊 Estrutura do Banco de Dados

- **usuarios:** Administradores e funcionários
- **empresas:** Locais de compra de placas
- **precos:** Tabela de preços por tipo de placa
- **relatorios:** Relatórios de compra com fotos e GPS
- **notificacoes:** Sistema de notificações

## 🔐 Segurança

- Senhas criptografadas com bcrypt
- Autenticação JWT
- Proteção de rotas por middleware
- Credenciais via variáveis de ambiente
- Validação de tipos de arquivo para upload

## 📝 Melhorias Futuras

- Reconhecimento automático de tipo de placa via ML/IA
- Exportação de relatórios em PDF/CSV
- Filtros avançados por período e empresa
- Perfil de usuário com alteração de senha
- Modo offline completo

## 📄 Licença

Este projeto foi desenvolvido para gestão interna de compras de placas eletrônicas.

---

**Desenvolvido em:** 06/11/2025
