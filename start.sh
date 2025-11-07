#!/bin/bash
set -e

echo "🚀 Iniciando aplicação..."

echo "📊 Verificando e inicializando banco de dados..."
python init_db.py || echo "⚠️  Aviso: Erro ao inicializar DB (pode ser normal se já existir)"

echo "🌐 Iniciando servidor..."
if [ -z "$PORT" ]; then
    export PORT=5000
    echo "ℹ️  PORT não definido, usando padrão: 5000"
else
    echo "ℹ️  Usando PORT: $PORT"
fi

exec gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT --timeout 120 app:application
