#!/usr/bin/env python3
"""Script para inicializar o banco de dados com todas as tabelas necessárias."""

from app import create_app
from app.models import db
import sys
import os

def init_database(drop_existing=False):
    """Cria todas as tabelas no banco de dados.

    Args:
        drop_existing: Se True, remove todas as tabelas antes de criar (padrão: False)
    """
    try:
        # Verifica se DATABASE_URL está definido
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ ERRO: DATABASE_URL não está definido!")
            print("   Configure o PostgreSQL no Railway")
            return False

        print(f"🔗 Conectando ao banco de dados...")
        print(f"   URL: {database_url[:30]}...")

        app = create_app()

        with app.app_context():
            if drop_existing:
                print("⚠️  Removendo tabelas antigas...")
                db.drop_all()
                print("✅ Tabelas antigas removidas!")

            print("📊 Criando tabelas no banco de dados...")
            db.create_all()
            print("✅ Tabelas criadas/verificadas com sucesso!")

            # Lista as tabelas criadas
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📋 Tabelas no banco: {', '.join(tables)}")

            try:
                from app.auth import criar_admin_padrao
                criar_admin_padrao()
                print("✅ Usuário admin verificado!")
            except Exception as e:
                print(f"⚠️  Aviso ao criar admin: {e}")

        return True
    except Exception as e:
        print(f"❌ Erro ao inicializar banco de dados: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    # Verifica se deve fazer drop das tabelas
    drop = '--drop' in sys.argv or os.environ.get('DROP_TABLES', '').lower() == 'true'

    if drop:
        print("⚠️  MODO DESTRUTIVO: Todas as tabelas serão removidas e recriadas!")

    success = init_database(drop_existing=drop)
    sys.exit(0 if success else 1)