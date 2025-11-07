#!/bin/bash
set -e

echo "🚀 Iniciando aplicação..."

# Define PORT com fallback para 8000
export PORT=${PORT:-8000}
echo "ℹ️  Usando PORT: $PORT"

# Verifica se DATABASE_URL está definido
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  AVISO: DATABASE_URL não está definido!"
else
    echo "✅ DATABASE_URL está configurado"
fi

# Inicializa o banco de dados
echo "📊 Inicializando banco de dados..."
python init_db.py || echo "⚠️  Aviso: Erro ao inicializar DB (pode ser normal se já existir)"

# Inicia o servidor Gunicorn
echo "🌐 Iniciando servidor Gunicorn na porta $PORT..."
exec gunicorn --worker-class eventlet -w 1 --bind "0.0.0.0:$PORT" --timeout 120 app:application
