
"""
Script para criar usuários de teste para validação do sistema RBAC
"""
import os
os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/mrx_db')

from app import create_app
from app.models import db, Usuario, Perfil
from app.auth import hash_senha

def criar_usuarios_teste():
    app = create_app()
    
    with app.app_context():
        # Mapear perfis
        perfis = {
            'Administrador': 'admin@teste.com',
            'Comprador (PJ)': 'comprador@teste.com',
            'Conferente / Estoque': 'conferente@teste.com',
            'Separação': 'separacao@teste.com',
            'Motorista': 'motorista@teste.com',
            'Financeiro': 'financeiro@teste.com',
            'Auditoria / BI': 'auditoria@teste.com'
        }
        
        print("🔧 Criando usuários de teste para RBAC...\n")
        
        for perfil_nome, email in perfis.items():
            # Verificar se já existe
            usuario_existente = Usuario.query.filter_by(email=email).first()
            if usuario_existente:
                print(f"⚠️  Usuário {email} já existe. Pulando...")
                continue
            
            # Buscar perfil
            perfil = Perfil.query.filter_by(nome=perfil_nome).first()
            if not perfil:
                print(f"❌ Perfil '{perfil_nome}' não encontrado!")
                continue
            
            # Criar usuário
            usuario = Usuario(
                nome=perfil_nome,
                email=email,
                senha_hash=hash_senha('teste123'),
                tipo='funcionario' if perfil_nome != 'Administrador' else 'admin',
                perfil_id=perfil.id,
                ativo=True
            )
            
            db.session.add(usuario)
            print(f"✅ Criado: {email} | Perfil: {perfil_nome} | Senha: teste123")
        
        db.session.commit()
        
        print("\n" + "="*60)
        print("🎉 USUÁRIOS DE TESTE CRIADOS COM SUCESSO!")
        print("="*60)
        print("\nCredenciais para Login:")
        print("-" * 60)
        for perfil_nome, email in perfis.items():
            print(f"📧 {email:30} | Senha: teste123")
        print("-" * 60)
        print("\n💡 Use estas credenciais para testar diferentes perfis no sistema")

if __name__ == '__main__':
    criar_usuarios_teste()
