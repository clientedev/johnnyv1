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
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

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
        from app.routes import (auth, usuarios, notificacoes, vendedores,
                                fornecedores, tipos_lote, dashboard, solicitacao_lotes,
                                fornecedor_tipo_lote_classificacoes, fornecedor_tipo_lote_precos,
                                perfis, veiculos, motoristas, auditoria, ordens_compra,
                                ordens_servico, conferencias, estoque, separacao, wms, pages,
                                materiais_base, tabelas_preco, autorizacoes_preco, compras,
                                fornecedor_tabela_precos, metais, conquistas, assistente, scanner, rh)
        from app.routes import solicitacoes_new as solicitacoes
        from app.routes import lotes_new as lotes
        from app.routes import entradas_new as entradas

        app.register_blueprint(auth.bp)
        app.register_blueprint(usuarios.bp)
        app.register_blueprint(vendedores.bp)
        app.register_blueprint(notificacoes.bp)
        app.register_blueprint(dashboard.bp)
        app.register_blueprint(fornecedores.bp)
        app.register_blueprint(tipos_lote.bp)
        app.register_blueprint(solicitacoes.bp)
        app.register_blueprint(lotes.bp)
        app.register_blueprint(entradas.bp)
        app.register_blueprint(solicitacao_lotes.bp)
        app.register_blueprint(fornecedor_tipo_lote_classificacoes.bp)
        app.register_blueprint(fornecedor_tipo_lote_precos.bp)
        app.register_blueprint(perfis.bp)
        app.register_blueprint(veiculos.bp, url_prefix='/api/veiculos')
        app.register_blueprint(motoristas.bp, url_prefix='/api/motoristas')
        app.register_blueprint(auditoria.bp)
        app.register_blueprint(ordens_compra.bp)
        app.register_blueprint(ordens_servico.bp, url_prefix='/api/os')
        app.register_blueprint(conferencias.bp)
        app.register_blueprint(estoque.bp)
        app.register_blueprint(separacao.bp)
        app.register_blueprint(wms.bp)
        app.register_blueprint(materiais_base.bp)
        app.register_blueprint(tabelas_preco.bp)
        app.register_blueprint(autorizacoes_preco.bp)
        app.register_blueprint(compras.bp)
        app.register_blueprint(fornecedor_tabela_precos.bp)
        app.register_blueprint(pages.bp)
        app.register_blueprint(metais.bp)
        app.register_blueprint(conquistas.bp)
        app.register_blueprint(assistente.bp)
        app.register_blueprint(scanner.bp)
        app.register_blueprint(rh.bp)

        def run_hr_migration():
            try:
                from sqlalchemy import text
                columns_to_add = [
                    ("foto_path", "VARCHAR(255)"),
                    ("percentual_comissao", "NUMERIC(5,2) DEFAULT 0"),
                    ("telefone", "VARCHAR(20)"),
                    ("cpf", "VARCHAR(14)"),
                    ("data_atualizacao", "TIMESTAMP")
                ]
                
                with db.engine.connect() as conn:
                    for column_name, column_type in columns_to_add:
                        result = conn.execute(text(f"""
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_name = 'usuarios' AND column_name = '{column_name}'
                        """))
                        
                        if result.fetchone() is None:
                            conn.execute(text(f"ALTER TABLE usuarios ADD COLUMN {column_name} {column_type}"))
                            conn.commit()
                            print(f"✓ Added column usuarios.{column_name}")
            except Exception as e:
                print(f"Migration check: {e}")

        run_hr_migration()
        db.create_all()

        # Inicializar tabelas de preço
        from app.models import TabelaPreco, Perfil, TipoLote
        tabelas_existentes = TabelaPreco.query.all()
        if len(tabelas_existentes) < 3:
            niveis_necessarios = {1, 2, 3}
            niveis_existentes = {t.nivel_estrelas for t in tabelas_existentes}
            niveis_faltantes = niveis_necessarios - niveis_existentes

            for nivel in sorted(niveis_faltantes):
                nome_estrelas = "Estrela" if nivel == 1 else "Estrelas"
                tabela = TabelaPreco(
                    nome=f'{nivel} {nome_estrelas}',
                    nivel_estrelas=nivel,
                    ativo=True
                )
                db.session.add(tabela)

            db.session.commit()
            print(f"✓ Inicializadas {len(niveis_faltantes)} tabela(s) de preço")

        # Inicializar tipo de lote padrão
        tipo_lote_padrao = TipoLote.query.first()
        if not tipo_lote_padrao:
            tipo_lote_padrao = TipoLote(
                nome='Material Eletrônico',
                descricao='Tipo de lote padrão para materiais eletrônicos'
            )
            db.session.add(tipo_lote_padrao)
            db.session.commit()
            print("✓ Inicializado tipo de lote padrão")

        from app.auth import criar_admin_padrao
        criar_admin_padrao()

    return app