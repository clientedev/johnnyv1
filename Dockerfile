FROM python:3.12-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro (cache)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o resto do código
COPY . .

# Criar diretórios necessários
RUN mkdir -p uploads

# Expor porta
EXPOSE 5000

# Comando de inicialização
CMD gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT --timeout 120 app:application
