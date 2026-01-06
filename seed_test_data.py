
import os
import sys

# Adiciona o diretório atual ao path para importar o app
sys.path.append(os.getcwd())

from app import create_app, db
from app.models import Fornecedor, Lote, TipoLote, Usuario

def seed_data():
    app = create_app()
    with app.app_context():
        # 1. Garantir que temos um tipo de lote
        tipo = TipoLote.query.first()
        if not tipo:
            tipo = TipoLote(nome="Sucata Eletrônica", descricao="Material eletrônico variado")
            db.session.add(tipo)
            db.session.commit()
            print("✓ Tipo de lote criado")

        # 2. Garantir que temos um usuário admin para auditoria/relacionamentos se necessário
        admin = Usuario.query.filter_by(email='admin@sistema.com').first()
        if not admin:
            print("! Admin não encontrado, verifique a inicialização do app")
            return

        # 3. Criar Fornecedores
        forn_data = [
            {"nome": "Recicla Tech Ltda", "cnpj": "12.345.678/0001-90", "tipo_documento": "cnpj"},
            {"nome": "João da Sucata", "cpf": "123.456.789-00", "tipo_documento": "cpf"},
            {"nome": "Eco Logística S.A.", "cnpj": "98.765.432/0001-10", "tipo_documento": "cnpj"}
        ]
        
        fornecedores = []
        for data in forn_data:
            if data['tipo_documento'] == 'cnpj':
                f = Fornecedor.query.filter_by(cnpj=data['cnpj']).first()
            else:
                f = Fornecedor.query.filter_by(cpf=data['cpf']).first()
                
            if not f:
                f = Fornecedor(nome=data['nome'], tipo_documento=data['tipo_documento'], ativo=True)
                if data['tipo_documento'] == 'cnpj':
                    f.cnpj = data['cnpj']
                else:
                    f.cpf = data['cpf']
                db.session.add(f)
            fornecedores.append(f)
        
        db.session.commit()
        print(f"✓ {len(fornecedores)} Fornecedores garantidos")

        # 4. Criar Lotes de Entrada
        # Lotes precisam estar em um estado que permita visualização no estoque (geralmente 'concluido' ou similar)
        import random
        from datetime import datetime

        for i in range(5):
            f = random.choice(fornecedores)
            peso = round(random.uniform(50, 500), 2)
            valor_kg = round(random.uniform(2, 15), 2)
            valor_total = round(peso * valor_kg, 2)
            
            lote = Lote(
                numero_lote=f"LT-2026-{i+1:03d}",
                fornecedor_id=f.id,
                tipo_lote_id=tipo.id,
                peso_bruto=peso + 2,
                peso_liquido=peso,
                valor_unitario=valor_kg,
                valor_total=valor_total,
                status='estoque', # Status para aparecer no estoque da produção
                data_entrada=datetime.now(),
                ativo=True
            )
            db.session.add(lote)
        
        db.session.commit()
        print("✓ 5 Lotes de teste criados no estoque")

if __name__ == "__main__":
    seed_data()
