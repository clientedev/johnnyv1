#!/usr/bin/env python3
"""Script para inicializar o banco de dados com todas as tabelas necessárias."""

from app import create_app
from app.models import db
import sys

def init_database():
    """Cria todas as tabelas no banco de dados."""
    try:
        app = create_app()
        
        with app.app_context():
            print("Criando todas as tabelas no banco de dados...")
            db.create_all()
            print("✅ Tabelas criadas com sucesso!")
            
            from app.auth import criar_admin_padrao
            criar_admin_padrao()
            print("✅ Usuário admin verificado!")
            
        return True
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = init_database()
    sys.exit(0 if success else 1)
