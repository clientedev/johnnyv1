from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    
    relatorios = db.relationship('Relatorio', backref='funcionario', lazy=True, cascade='all, delete-orphan')
    notificacoes = db.relationship('Notificacao', backref='usuario', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'tipo': self.tipo
        }

class Empresa(db.Model):
    __tablename__ = 'empresas'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    cnpj = db.Column(db.String(18), unique=True, nullable=False)
    endereco = db.Column(db.String(300))
    telefone = db.Column(db.String(20))
    observacoes = db.Column(db.Text)
    
    precos = db.relationship('Preco', backref='empresa', lazy=True, cascade='all, delete-orphan')
    relatorios = db.relationship('Relatorio', backref='empresa', lazy=True, cascade='all, delete-orphan')
    placas = db.relationship('Placa', backref='empresa', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'cnpj': self.cnpj,
            'endereco': self.endereco,
            'telefone': self.telefone,
            'observacoes': self.observacoes
        }

class ConfiguracaoPrecoEstrela(db.Model):
    __tablename__ = 'configuracao_preco_estrelas'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo_placa = db.Column(db.String(20), nullable=False, unique=True)
    valor_1_estrela = db.Column(db.Float, nullable=False, default=0.0)
    valor_2_estrelas = db.Column(db.Float, nullable=False, default=0.0)
    valor_3_estrelas = db.Column(db.Float, nullable=False, default=0.0)
    valor_4_estrelas = db.Column(db.Float, nullable=False, default=0.0)
    valor_5_estrelas = db.Column(db.Float, nullable=False, default=0.0)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'tipo_placa': self.tipo_placa,
            'valor_1_estrela': self.valor_1_estrela,
            'valor_2_estrelas': self.valor_2_estrelas,
            'valor_3_estrelas': self.valor_3_estrelas,
            'valor_4_estrelas': self.valor_4_estrelas,
            'valor_5_estrelas': self.valor_5_estrelas,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }

class Preco(db.Model):
    __tablename__ = 'precos'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    tipo_placa = db.Column(db.String(20), nullable=False)
    preco_por_kg = db.Column(db.Float, nullable=False)
    classificacao_estrelas = db.Column(db.Integer, nullable=True, default=3)
    
    def to_dict(self):
        return {
            'id': self.id,
            'empresa_id': self.empresa_id,
            'tipo_placa': self.tipo_placa,
            'preco_por_kg': self.preco_por_kg,
            'classificacao_estrelas': self.classificacao_estrelas
        }

class Relatorio(db.Model):
    __tablename__ = 'relatorios'
    
    id = db.Column(db.Integer, primary_key=True)
    funcionario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    tipo_placa = db.Column(db.String(20), nullable=False)
    peso_kg = db.Column(db.Float, nullable=False)
    foto_url = db.Column(db.String(500))
    localizacao_lat = db.Column(db.Float)
    localizacao_lng = db.Column(db.Float)
    endereco_completo = db.Column(db.String(500))
    status = db.Column(db.String(20), default='pendente', nullable=False)
    observacoes = db.Column(db.Text)
    data_envio = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'funcionario_id': self.funcionario_id,
            'funcionario_nome': self.funcionario.nome if self.funcionario else None,
            'empresa_id': self.empresa_id,
            'empresa_nome': self.empresa.nome if self.empresa else None,
            'tipo_placa': self.tipo_placa,
            'peso_kg': self.peso_kg,
            'foto_url': self.foto_url,
            'localizacao_lat': self.localizacao_lat,
            'localizacao_lng': self.localizacao_lng,
            'endereco_completo': self.endereco_completo,
            'status': self.status,
            'observacoes': self.observacoes,
            'data_envio': self.data_envio.isoformat() if self.data_envio else None
        }

class Placa(db.Model):
    __tablename__ = 'placas'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    funcionario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    relatorio_id = db.Column(db.Integer, db.ForeignKey('relatorios.id'), nullable=True)
    tipo_placa = db.Column(db.String(20), nullable=False)
    peso_kg = db.Column(db.Float, nullable=False)
    valor = db.Column(db.Float, nullable=False)
    imagem_url = db.Column(db.String(500))
    data_registro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    observacoes = db.Column(db.Text)
    
    funcionario = db.relationship('Usuario', backref='placas')
    relatorio = db.relationship('Relatorio', backref='placas')
    
    def to_dict(self):
        return {
            'id': self.id,
            'empresa_id': self.empresa_id,
            'empresa_nome': self.empresa.nome if self.empresa else None,
            'funcionario_id': self.funcionario_id,
            'funcionario_nome': self.funcionario.nome if self.funcionario else None,
            'relatorio_id': self.relatorio_id,
            'tipo_placa': self.tipo_placa,
            'peso_kg': self.peso_kg,
            'valor': self.valor,
            'imagem_url': self.imagem_url,
            'data_registro': self.data_registro.isoformat() if self.data_registro else None,
            'observacoes': self.observacoes
        }

class Notificacao(db.Model):
    __tablename__ = 'notificacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    lida = db.Column(db.Boolean, default=False, nullable=False)
    data_envio = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'titulo': self.titulo,
            'mensagem': self.mensagem,
            'lida': self.lida,
            'data_envio': self.data_envio.isoformat() if self.data_envio else None
        }
