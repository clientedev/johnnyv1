"""
WSGI entry point para Gunicorn
"""
from app import create_app, socketio

# Cria a aplicação
application = create_app()
app = application

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
