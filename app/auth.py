import bcrypt
from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models import db, Usuario

def hash_senha(senha):
    return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verificar_senha(senha, senha_hash):
    return bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8'))

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get(usuario_id)
        
        if not usuario or usuario.tipo != 'admin':
            return jsonify({'erro': 'Acesso negado. Apenas administradores podem acessar este recurso.'}), 403
        
        return fn(*args, **kwargs)
    return wrapper

def criar_admin_padrao():
    import os
    
    admin_count = Usuario.query.filter_by(tipo='admin').count()
    
    if admin_count == 0:
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@sistema.com')
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        
        admin = Usuario(
            nome='Administrador',
            email=admin_email,
            senha_hash=hash_senha(admin_password),
            tipo='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print(f'Usuário administrador criado: {admin_email}')
        
        if admin_password == 'admin123':
            print('AVISO: Usando senha padrão! Configure ADMIN_EMAIL e ADMIN_PASSWORD nas variáveis de ambiente.')
