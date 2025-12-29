from app import create_app, socketio
from flask import send_from_directory, render_template, make_response
from flask_socketio import join_room
from flask_jwt_extended import decode_token
from app.models import Usuario
import os

application = create_app()
app = application
app.config['SCANNER_URL'] = os.environ.get('SCANNER_URL', 'https://scanv1-production.up.railway.app/')

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    response = make_response(send_from_directory(UPLOAD_FOLDER, filename))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/logistica')
def logistica():
    return render_template('logistica.html')

@app.route('/kanban')
def kanban():
    return render_template('kanban.html')

@app.route('/app-motorista')
def app_motorista():
    return render_template('app-motorista.html')

@app.route('/conferencia')
def conferencia():
    return render_template('conferencia.html')

@app.route('/conferencias')
def conferencias():
    return render_template('conferencias.html')

@app.route('/conferencia-form/<int:id>')
def conferencia_form(id):
    return render_template('conferencia-form.html')

@app.route('/conferencia-decisao-adm/<int:id>')
def conferencia_decisao_adm(id):
    return render_template('conferencia-decisao-adm.html')

@app.route('/cotacoes-metais')
def cotacoes_metais():
    return render_template('cotacoes-metais.html')

@app.route('/rh-admin')
def rh_admin():
    return render_template('rh-admin.html')

@app.route('/<path:path>')
def serve_page(path):
    if path.startswith('api/'):
        from flask import abort
        abort(404)
    if path.endswith('.html'):
        try:
            return render_template(path)
        except:
            return render_template('index.html')
    return render_template('index.html')

@socketio.on('connect')
def handle_connect(auth):
    try:
        from flask_jwt_extended import decode_token
        
        token = auth.get('token') if auth else None
        if not token:
            return False
        
        decoded = decode_token(token)
        usuario_id = decoded['sub']
        
        usuario = Usuario.query.get(usuario_id)
        
        if usuario:
            if usuario.tipo == 'admin':
                join_room('admins')
            else:
                join_room(f'user_{usuario_id}')
            print(f'Usuário {usuario.nome} conectado via WebSocket e entrou na sala')
            return True
    except Exception as e:
        print(f'Erro ao conectar WebSocket: {e}')
        return False

@app.route('/scanner-view')
def scanner_view():
    scanner_url = os.environ.get('SCANNER_URL', 'https://scanv1-production.up.railway.app/')
    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Scanner - MRX Systems</title>
        <style>
            body, html {{ margin: 0; padding: 0; height: 100%; overflow: hidden; font-family: sans-serif; }}
            .back-button {{
                position: fixed;
                top: 15px;
                left: 15px;
                z-index: 10000;
                background: #059669;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                cursor: pointer;
                font-weight: bold;
                box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                display: flex;
                align-items: center;
                gap: 8px;
                text-decoration: none;
                transition: transform 0.2s;
            }}
            .back-button:hover {{ transform: scale(1.05); background: #047857; }}
            iframe {{ width: 100%; height: 100%; border: none; }}
        </style>
    </head>
    <body>
        <a href="javascript:history.back()" class="back-button">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="19" y1="12" x2="5" y2="12"></line>
                <polyline points="12 19 5 12 12 5"></polyline>
            </svg>
            Voltar para o Sistema
        </a>
        <iframe src="{scanner_url}"></iframe>
    </body>
    </html>
    """

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
