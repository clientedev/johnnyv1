# ⚙️ MetalGest - Gestão de Metais e Eletrônicos

## Visão Geral
Sistema profissional completo para controlar compras de metais e eletrônicos feitas por funcionários em diferentes empresas. O sistema permite registro de fotos, localização GPS, peso dos materiais e aprovação administrativa de cada compra.

## Tecnologias Utilizadas
- **Backend:** Python 3.11 + Flask
- **Banco de Dados:** PostgreSQL (via Replit Database)
- **ORM:** SQLAlchemy
- **Autenticação:** JWT (Flask-JWT-Extended)
- **Senha:** bcrypt
- **WebSocket:** Flask-SocketIO (notificações em tempo real)
- **Frontend:** HTML5, CSS3, JavaScript vanilla
- **Gráficos:** Chart.js
- **Mapas:** Leaflet.js
- **PWA:** Service Worker + Manifest.json

## Estrutura do Projeto
```
.
├── app/
│   ├── __init__.py           # Inicialização do Flask
│   ├── models.py             # Modelos do banco de dados
│   ├── auth.py               # Autenticação e decoradores
│   ├── routes/               # Rotas da API REST
│   │   ├── auth.py
│   │   ├── empresas.py
│   │   ├── usuarios.py
│   │   ├── precos.py
│   │   ├── relatorios.py
│   │   ├── notificacoes.py
│   │   └── dashboard.py
│   ├── static/               # Arquivos estáticos
│   │   ├── css/
│   │   │   └── style.css
│   │   ├── js/
│   │   │   ├── app.js
│   │   │   └── sw.js (Service Worker)
│   │   ├── images/           # Ícones PWA
│   │   └── manifest.json
│   └── templates/            # Templates HTML
│       ├── index.html
│       ├── dashboard.html
│       ├── funcionario.html
│       ├── relatorios.html
│       ├── empresas.html
│       ├── funcionarios.html
│       ├── empresas-lista.html
│       └── notificacoes.html
├── uploads/                  # Fotos enviadas
├── app.py                    # Arquivo principal
└── requirements.txt
```

## Funcionalidades Principais

### Administrador
- ✅ CRUD completo de empresas, funcionários e tabelas de preços
- ✅ Visualização e aprovação/reprovação de relatórios
- ✅ Dashboard com estatísticas:
  - Contadores de relatórios (pendentes/aprovados/reprovados)
  - Quilos totais por tipo de placa
  - Valor total movimentado
  - Ranking de empresas
  - Gráfico mensal de movimentação
  - Mapa interativo com geolocalização
- ✅ Notificações em tempo real (novos relatórios)

### Funcionário
- ✅ Login com email e senha
- ✅ Visualização de empresas cadastradas
- ✅ Criação de relatórios com:
  - Upload de foto
  - Seleção de tipo de placa (leve/média/pesada)
  - Peso em kg
  - Captura automática de GPS
  - Observações
- ✅ Visualização de histórico de relatórios
- ✅ Notificações em tempo real (aprovação/reprovação)

### PWA (Progressive Web App)
- ✅ Manifest.json configurado
- ✅ Service Worker para cache básico
- ✅ Banner de instalação em dispositivos móveis
- ✅ Ícones para tela inicial

## Banco de Dados

### Tabelas
- **usuarios:** id, nome, email, senha_hash, tipo
- **empresas:** id, nome, cnpj, endereco, telefone, observacoes
- **precos:** id, empresa_id, tipo_placa, preco_por_kg
- **relatorios:** id, funcionario_id, empresa_id, tipo_placa, peso_kg, foto_url, localizacao_lat, localizacao_lng, status, observacoes, data_envio
- **notificacoes:** id, usuario_id, titulo, mensagem, lida, data_envio

## Credenciais Padrão
- **Administrador:** 
  - Email: admin@sistema.com
  - Senha: admin123

## Como Usar

1. **Acessar o sistema:** Abra o navegador e faça login
2. **Administrador:** Acesse o dashboard para gerenciar empresas, funcionários e aprovar relatórios
3. **Funcionário:** Crie relatórios de compra com foto e GPS
4. **Notificações:** Ambos recebem notificações em tempo real via WebSocket
5. **PWA:** Em dispositivos móveis, clique em "Instalar" para adicionar à tela inicial

## Deploy (Railway)

### Variáveis de Ambiente Necessárias
- `DATABASE_URL`: URL do banco PostgreSQL (automático no Railway)
- `JWT_SECRET_KEY`: Chave secreta para tokens JWT (gerar senha forte)
- `SESSION_SECRET`: Chave secreta para sessões (gerar senha forte)
- `ADMIN_EMAIL`: Email do administrador (padrão: admin@sistema.com)
- `ADMIN_PASSWORD`: Senha do administrador (OBRIGATÓRIO mudar em produção!)

### Configuração
- O sistema usa Gunicorn com worker eventlet para WebSocket
- Porta: 5000 (configurável via PORT)
- WebSocket configurado para notificações em tempo real
- **IMPORTANTE:** Configure ADMIN_EMAIL e ADMIN_PASSWORD no Railway antes do deploy!

### Comandos para Deploy
```bash
# O Procfile já está configurado
# Railway executará automaticamente: gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app
```

## Melhorias Futuras
- Reconhecimento automático de tipo de placa via ML/IA
- Exportação de relatórios em PDF/CSV
- Filtros avançados por período, empresa, status
- Perfil de usuário com alteração de senha
- Modo offline completo para criação de relatórios

## Última Atualização
06/11/2025 - Sistema completo implementado com todas as funcionalidades MVP
