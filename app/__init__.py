from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from app.models import db
import os

socketio = SocketIO()

def create_app():
    app = Flask(__name__, 
                static_folder='static',
                static_url_path='/static',
                template_folder='templates')
    
    from datetime import timedelta
    
    app.config['SECRET_KEY'] = os.getenv('SESSION_SECRET', 'dev-secret-key')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', os.getenv('SESSION_SECRET', 'jwt-secret-key'))
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    
    database_url = os.getenv('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    app.config['UPLOAD_FOLDER'] = 'uploads'
    
    db.init_app(app)
    CORS(app)
    jwt = JWTManager(app)
    socketio.init_app(app, cors_allowed_origins="*")
    
    from flask import jsonify
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'erro': 'Token expirado',
            'mensagem': 'Por favor, faça login novamente'
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'erro': 'Token inválido',
            'mensagem': 'Por favor, faça login novamente'
        }), 401
    
    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        return jsonify({
            'erro': 'Token não fornecido',
            'mensagem': 'Por favor, faça login'
        }), 401
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'erro': 'Token revogado',
            'mensagem': 'Por favor, faça login novamente'
        }), 401
    
    with app.app_context():
        from app.routes import (auth, usuarios, precos, notificacoes, 
                                dashboard, placas, configuracoes, vendedores, solicitacoes, entradas,
                                fornecedores, compras, classificacoes, validacao, consulta, tabelas, lotes, produtos)
        
        app.register_blueprint(auth.bp)
        app.register_blueprint(usuarios.bp)
        app.register_blueprint(precos.bp)
        app.register_blueprint(solicitacoes.bp)
        app.register_blueprint(entradas.bp)
        app.register_blueprint(vendedores.bp)
        app.register_blueprint(notificacoes.bp)
        app.register_blueprint(dashboard.bp)
        app.register_blueprint(placas.placas_bp)
        app.register_blueprint(configuracoes.bp)
        app.register_blueprint(fornecedores.bp)
        app.register_blueprint(produtos.bp)
        app.register_blueprint(compras.bp)
        app.register_blueprint(classificacoes.bp)
        app.register_blueprint(validacao.bp)
        app.register_blueprint(consulta.bp)
        app.register_blueprint(tabelas.bp)
        app.register_blueprint(lotes.bp)
        
        db.create_all()
        
        from app.auth import criar_admin_padrao
        criar_admin_padrao()
        
        from app.utils.seed_produtos import criar_produtos_exemplo
        criar_produtos_exemplo()
    
    return app
