import os
import psycopg2
from urllib.parse import urlparse

database_url = os.getenv('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

result = urlparse(database_url)
username = result.username
password = result.password
database = result.path[1:]
hostname = result.hostname
port = result.port

try:
    conn = psycopg2.connect(
        database=database,
        user=username,
        password=password,
        host=hostname,
        port=port
    )
    
    cursor = conn.cursor()
    
    with open('migrations/010_add_logistica_tables.sql', 'r') as f:
        sql = f.read()
        
    cursor.execute(sql)
    conn.commit()
    
    print("✅ Migração executada com sucesso!")
    print("Tabelas criadas:")
    print("  - ordens_servico")
    print("  - rotas_operacionais")
    print("  - gps_logs")
    print("  - conferencias_recebimento")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Erro ao executar migração: {str(e)}")
    import traceback
    traceback.print_exc()
