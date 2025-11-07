#!/usr/bin/env python3
"""Script de inicialização para Railway/produção"""
import os
import sys
import subprocess

def main():
    print("🚀 Iniciando aplicação...")
    
    print("📊 Verificando e inicializando banco de dados...")
    try:
        subprocess.run([sys.executable, "init_db.py"], check=False)
    except Exception as e:
        print(f"⚠️  Aviso ao inicializar DB: {e}")
    
    print("🌐 Iniciando servidor...")
    port = os.environ.get('PORT', '5000')
    print(f"ℹ️  Usando PORT: {port}")
    
    cmd = [
        "gunicorn",
        "--worker-class", "eventlet",
        "-w", "1",
        "--bind", f"0.0.0.0:{port}",
        "--timeout", "120",
        "app:application"
    ]
    
    print(f"📡 Executando: {' '.join(cmd)}")
    os.execvp("gunicorn", cmd)

if __name__ == "__main__":
    main()
