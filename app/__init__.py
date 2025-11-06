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
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    app.config['UPLOAD_FOLDER'] = 'uploads'
    
    db.init_app(app)
    CORS(app)
    JWTManager(app)
    socketio.init_app(app, cors_allowed_origins="*")
    
    with app.app_context():
        from app.routes import auth, empresas, usuarios, precos, relatorios, notificacoes, dashboard
        
        app.register_blueprint(auth.bp)
        app.register_blueprint(empresas.bp)
        app.register_blueprint(usuarios.bp)
        app.register_blueprint(precos.bp)
        app.register_blueprint(relatorios.bp)
        app.register_blueprint(notificacoes.bp)
        app.register_blueprint(dashboard.bp)
        
        db.create_all()
        
        from app.auth import criar_admin_padrao
        criar_admin_padrao()
    
    return app
