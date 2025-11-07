# Guia de Deploy no Railway

## Arquivos de Configuração

Este projeto usa **Docker** para deployment no Railway:
- `Dockerfile` - Configuração principal de build
- `railway.json` - Configuração do Railway
- `start.py` - Script de inicialização

## Passo a Passo para Deploy

### 1. Conectar o Repositório ao Railway
- Acesse [railway.app](https://railway.app)
- Crie um novo projeto
- Conecte seu repositório GitHub

### 2. Adicionar PostgreSQL
- No dashboard do Railway, clique em "New" > "Database" > "PostgreSQL"
- Railway criará automaticamente a variável `DATABASE_URL`

### 3. Configurar Variáveis de Ambiente
Adicione estas variáveis no Railway (aba "Variables"):

```
SESSION_SECRET=sua-chave-secreta-aleatoria-aqui
JWT_SECRET_KEY=sua-chave-jwt-aleatoria-aqui
```

**IMPORTANTE**: Gere chaves fortes e únicas! Use este comando para gerar:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Deploy Automático
- Railway detectará o `Dockerfile` automaticamente
- O build será iniciado automaticamente
- Railway definirá a variável `PORT` automaticamente

### 5. Verificar o Deploy
Após o deploy, verifique os logs:
- As tabelas do banco serão criadas automaticamente
- O usuário admin padrão será criado
- O servidor Gunicorn iniciará na porta configurada pelo Railway

## Estrutura de Inicialização

1. `Dockerfile` executa `start.py`
2. `start.py` executa `init_db.py` para criar tabelas
3. `start.py` inicia o Gunicorn com eventlet worker
4. A aplicação fica disponível na porta definida por Railway

## Solução de Problemas

### Erro: "$PORT is not a valid port number"
- ✅ **RESOLVIDO**: Removidos Procfile e start.sh conflitantes
- O Dockerfile agora usa shell form (`CMD python start.py`) para expansão correta de variáveis

### Tabelas não sendo criadas
- ✅ **RESOLVIDO**: DATABASE_URL agora converte `postgres://` para `postgresql://`
- `init_db.py` é executado antes do servidor iniciar
- `db.create_all()` também é chamado no `app/__init__.py`

### Database Connection Issues
- Verifique se a variável `DATABASE_URL` está configurada no Railway
- Verifique se o serviço PostgreSQL está ativo

## Comandos Úteis

### Criar tabelas manualmente (se necessário)
```bash
python init_db.py
```

### Recriar todas as tabelas (CUIDADO: apaga dados)
```bash
python init_db.py --drop
```

### Testar localmente com Docker
```bash
docker build -t app .
docker run -p 5000:5000 -e PORT=5000 -e DATABASE_URL=sua_url app
```

## Arquivos Importantes

- `Dockerfile` - Build da imagem Docker
- `railway.json` - Configuração do Railway
- `start.py` - Script de inicialização
- `init_db.py` - Script de criação de tabelas
- `app/__init__.py` - Configuração da aplicação Flask
- `requirements.txt` - Dependências Python
