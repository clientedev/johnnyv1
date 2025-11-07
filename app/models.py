from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    
    solicitacoes = db.relationship('Solicitacao', backref='funcionario', lazy=True, cascade='all, delete-orphan')
    relatorios = db.relationship('Relatorio', backref='funcionario_relatorio', lazy=True, cascade='all, delete-orphan', foreign_keys='Relatorio.funcionario_id')
    notificacoes = db.relationship('Notificacao', backref='usuario', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'tipo': self.tipo
        }

class Vendedor(db.Model):
    __tablename__ = 'vendedores'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True)
    telefone = db.Column(db.String(20))
    cpf = db.Column(db.String(14), unique=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    empresas = db.relationship('Empresa', backref='vendedor', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'telefone': self.telefone,
            'cpf': self.cpf,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None,
            'ativo': self.ativo
        }

class Empresa(db.Model):
    __tablename__ = 'empresas'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    nome_social = db.Column(db.String(200))
    cnpj = db.Column(db.String(18), unique=True, nullable=False)
    cpf = db.Column(db.String(14))
    
    endereco_coleta = db.Column(db.String(300))
    endereco_emissao = db.Column(db.String(300))
    
    rua = db.Column(db.String(200))
    numero = db.Column(db.String(20))
    cidade = db.Column(db.String(100))
    cep = db.Column(db.String(10))
    estado = db.Column(db.String(2))
    
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    
    vendedor_id = db.Column(db.Integer, db.ForeignKey('vendedores.id'), nullable=True)
    
    conta_bancaria = db.Column(db.String(50))
    agencia = db.Column(db.String(20))
    chave_pix = db.Column(db.String(100))
    banco = db.Column(db.String(100))
    
    condicao_pagamento = db.Column(db.String(20), default='avista')
    forma_pagamento = db.Column(db.String(20), default='pix')
    
    observacoes = db.Column(db.Text)
    estrelas_leve = db.Column(db.Integer, default=3)
    estrelas_pesada = db.Column(db.Integer, default=3)
    estrelas_media = db.Column(db.Integer, default=3)
    
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    precos = db.relationship('Preco', backref='empresa', lazy=True, cascade='all, delete-orphan')
    solicitacoes = db.relationship('Solicitacao', backref='empresa', lazy=True, cascade='all, delete-orphan')
    relatorios = db.relationship('Relatorio', backref='empresa_relatorio', lazy=True, cascade='all, delete-orphan', foreign_keys='Relatorio.empresa_id')
    placas = db.relationship('Placa', backref='empresa', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'nome_social': self.nome_social,
            'cnpj': self.cnpj,
            'cpf': self.cpf,
            'endereco_coleta': self.endereco_coleta,
            'endereco_emissao': self.endereco_emissao,
            'rua': self.rua,
            'numero': self.numero,
            'cidade': self.cidade,
            'cep': self.cep,
            'estado': self.estado,
            'telefone': self.telefone,
            'email': self.email,
            'vendedor_id': self.vendedor_id,
            'vendedor_nome': self.vendedor.nome if self.vendedor else None,
            'conta_bancaria': self.conta_bancaria,
            'agencia': self.agencia,
            'chave_pix': self.chave_pix,
            'banco': self.banco,
            'condicao_pagamento': self.condicao_pagamento,
            'forma_pagamento': self.forma_pagamento,
            'observacoes': self.observacoes,
            'estrelas_leve': self.estrelas_leve,
            'estrelas_pesada': self.estrelas_pesada,
            'estrelas_media': self.estrelas_media,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None
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

class Solicitacao(db.Model):
    __tablename__ = 'solicitacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    funcionario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    status = db.Column(db.String(20), default='pendente', nullable=False)
    observacoes = db.Column(db.Text)
    data_envio = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    data_confirmacao = db.Column(db.DateTime, nullable=True)
    
    placas = db.relationship('Placa', backref='solicitacao', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'funcionario_id': self.funcionario_id,
            'funcionario_nome': self.funcionario.nome if self.funcionario else None,
            'empresa_id': self.empresa_id,
            'empresa_nome': self.empresa.nome if self.empresa else None,
            'status': self.status,
            'observacoes': self.observacoes,
            'data_envio': self.data_envio.isoformat() if self.data_envio else None,
            'data_confirmacao': self.data_confirmacao.isoformat() if self.data_confirmacao else None,
            'total_placas': len(self.placas) if self.placas else 0
        }

class Placa(db.Model):
    __tablename__ = 'placas'
    
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String(50), unique=True, nullable=False, default=lambda: str(uuid.uuid4())[:8].upper())
    
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    funcionario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    solicitacao_id = db.Column(db.Integer, db.ForeignKey('solicitacoes.id'), nullable=True)
    
    tipo_placa = db.Column(db.String(20), nullable=False)
    peso_kg = db.Column(db.Float, nullable=False)
    valor = db.Column(db.Float, nullable=False)
    
    imagem_url = db.Column(db.String(500))
    localizacao_lat = db.Column(db.Float)
    localizacao_lng = db.Column(db.Float)
    endereco_completo = db.Column(db.String(500))
    
    status = db.Column(db.String(20), default='em_analise', nullable=False)
    
    data_compra = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    data_registro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    data_aprovacao = db.Column(db.DateTime, nullable=True)
    
    observacoes = db.Column(db.Text)
    
    funcionario = db.relationship('Usuario', backref='placas')
    
    def to_dict(self):
        return {
            'id': self.id,
            'tag': self.tag,
            'empresa_id': self.empresa_id,
            'empresa_nome': self.empresa.nome if self.empresa else None,
            'funcionario_id': self.funcionario_id,
            'funcionario_nome': self.funcionario.nome if self.funcionario else None,
            'solicitacao_id': self.solicitacao_id,
            'tipo_placa': self.tipo_placa,
            'peso_kg': self.peso_kg,
            'valor': self.valor,
            'imagem_url': self.imagem_url,
            'localizacao_lat': self.localizacao_lat,
            'localizacao_lng': self.localizacao_lng,
            'endereco_completo': self.endereco_completo,
            'status': self.status,
            'data_compra': self.data_compra.isoformat() if self.data_compra else None,
            'data_registro': self.data_registro.isoformat() if self.data_registro else None,
            'data_aprovacao': self.data_aprovacao.isoformat() if self.data_aprovacao else None,
            'observacoes': self.observacoes
        }

class Entrada(db.Model):
    __tablename__ = 'entradas'
    
    id = db.Column(db.Integer, primary_key=True)
    solicitacao_id = db.Column(db.Integer, db.ForeignKey('solicitacoes.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    
    status = db.Column(db.String(20), default='pendente', nullable=False)
    data_entrada = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    data_processamento = db.Column(db.DateTime, nullable=True)
    observacoes = db.Column(db.Text)
    
    solicitacao = db.relationship('Solicitacao', backref='entradas')
    admin = db.relationship('Usuario', backref='entradas_processadas', foreign_keys=[admin_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'solicitacao_id': self.solicitacao_id,
            'admin_id': self.admin_id,
            'admin_nome': self.admin.nome if self.admin else None,
            'status': self.status,
            'data_entrada': self.data_entrada.isoformat() if self.data_entrada else None,
            'data_processamento': self.data_processamento.isoformat() if self.data_processamento else None,
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
    
    funcionario = db.relationship('Usuario', foreign_keys=[funcionario_id], overlaps="funcionario_relatorio,relatorios")
    empresa = db.relationship('Empresa', foreign_keys=[empresa_id], overlaps="empresa_relatorio,relatorios")
    
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

class Funcionario(db.Model):
    __tablename__ = 'funcionarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    telefone = db.Column(db.String(20))
    cargo = db.Column(db.String(100))
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=True)
    vendedor_id = db.Column(db.Integer, db.ForeignKey('vendedores.id'), nullable=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    empresa = db.relationship('Empresa', backref='funcionarios')
    vendedor = db.relationship('Vendedor', backref='funcionarios')
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'cpf': self.cpf,
            'telefone': self.telefone,
            'cargo': self.cargo,
            'empresa_id': self.empresa_id,
            'empresa_nome': self.empresa.nome if self.empresa else None,
            'vendedor_id': self.vendedor_id,
            'vendedor_nome': self.vendedor.nome if self.vendedor else None,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None,
            'ativo': self.ativo
        }

class Fornecedor(db.Model):
    __tablename__ = 'fornecedores'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    nome_social = db.Column(db.String(200))
    cnpj = db.Column(db.String(18), unique=True)
    cpf = db.Column(db.String(14), unique=True)
    
    endereco_coleta = db.Column(db.String(300))
    endereco_emissao = db.Column(db.String(300))
    
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    
    conta_bancaria = db.Column(db.String(50))
    agencia = db.Column(db.String(20))
    chave_pix = db.Column(db.String(100))
    banco = db.Column(db.String(100))
    
    condicao_pagamento = db.Column(db.String(50))
    forma_pagamento = db.Column(db.String(50))
    
    observacoes = db.Column(db.Text)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    compras = db.relationship('Compra', backref='fornecedor', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'nome_social': self.nome_social,
            'cnpj': self.cnpj,
            'cpf': self.cpf,
            'endereco_coleta': self.endereco_coleta,
            'endereco_emissao': self.endereco_emissao,
            'telefone': self.telefone,
            'email': self.email,
            'conta_bancaria': self.conta_bancaria,
            'agencia': self.agencia,
            'chave_pix': self.chave_pix,
            'banco': self.banco,
            'condicao_pagamento': self.condicao_pagamento,
            'forma_pagamento': self.forma_pagamento,
            'observacoes': self.observacoes,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None,
            'ativo': self.ativo
        }

class Compra(db.Model):
    __tablename__ = 'compras'
    
    id = db.Column(db.Integer, primary_key=True)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedores.id'), nullable=False)
    solicitacao_id = db.Column(db.Integer, db.ForeignKey('solicitacoes.id'), nullable=True)
    
    material = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(20), default='compra', nullable=False)
    valor = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pendente', nullable=False)
    
    comprovante_url = db.Column(db.String(500))
    observacoes = db.Column(db.Text)
    
    data_compra = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    data_pagamento = db.Column(db.DateTime, nullable=True)
    
    solicitacao = db.relationship('Solicitacao', backref='compras')
    
    def to_dict(self):
        return {
            'id': self.id,
            'fornecedor_id': self.fornecedor_id,
            'fornecedor_nome': self.fornecedor.nome if self.fornecedor else None,
            'solicitacao_id': self.solicitacao_id,
            'material': self.material,
            'tipo': self.tipo,
            'valor': self.valor,
            'status': self.status,
            'comprovante_url': self.comprovante_url,
            'observacoes': self.observacoes,
            'data_compra': self.data_compra.isoformat() if self.data_compra else None,
            'data_pagamento': self.data_pagamento.isoformat() if self.data_pagamento else None
        }

class Classificacao(db.Model):
    __tablename__ = 'classificacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    tipo_lote = db.Column(db.String(20), nullable=False)
    peso_minimo = db.Column(db.Float, default=0.0)
    peso_maximo = db.Column(db.Float, default=999999.0)
    observacoes = db.Column(db.Text)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'tipo_lote': self.tipo_lote,
            'peso_minimo': self.peso_minimo,
            'peso_maximo': self.peso_maximo,
            'observacoes': self.observacoes,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None
        }

class Configuracao(db.Model):
    __tablename__ = 'configuracoes'
    
    id = db.Column(db.Integer, primary_key=True)
    chave = db.Column(db.String(100), unique=True, nullable=False)
    valor = db.Column(db.Text, nullable=False)
    descricao = db.Column(db.String(200))
    tipo = db.Column(db.String(50), default='texto')
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'chave': self.chave,
            'valor': self.valor,
            'descricao': self.descricao,
            'tipo': self.tipo,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }
