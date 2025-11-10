from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
from typing import Any

db = SQLAlchemy()

class Usuario(db.Model):  # type: ignore
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    solicitacoes = db.relationship('Solicitacao', backref='funcionario', lazy=True, cascade='all, delete-orphan', foreign_keys='Solicitacao.funcionario_id')
    notificacoes = db.relationship('Notificacao', backref='usuario', lazy=True, cascade='all, delete-orphan')
    entradas_processadas = db.relationship('EntradaEstoque', backref='admin', lazy=True, foreign_keys='EntradaEstoque.admin_id')
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'tipo': self.tipo,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None,
            'ativo': self.ativo
        }

class Vendedor(db.Model):  # type: ignore
    __tablename__ = 'vendedores'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True)
    telefone = db.Column(db.String(20))
    cpf = db.Column(db.String(14), unique=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    fornecedores = db.relationship('Fornecedor', backref='vendedor', lazy=True)
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
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

class TipoLote(db.Model):  # type: ignore
    __tablename__ = 'tipos_lote'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.String(300))
    codigo = db.Column(db.String(20), unique=True)
    classificacao = db.Column(db.String(10), default='media', nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    fornecedor_precos = db.relationship('FornecedorTipoLotePreco', backref='tipo_lote', lazy=True, cascade='all, delete-orphan')
    itens_solicitacao = db.relationship('ItemSolicitacao', backref='tipo_lote', lazy=True)
    lotes = db.relationship('Lote', backref='tipo_lote', lazy=True)
    precos_estrela = db.relationship('TipoLotePrecoEstrela', backref='tipo_lote', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs: Any) -> None:
        if 'classificacao' in kwargs and kwargs['classificacao'] not in ['leve', 'media', 'pesada']:
            raise ValueError('Classificação deve ser: leve, media ou pesada')
        super().__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'codigo': self.codigo,
            'classificacao': self.classificacao,
            'ativo': self.ativo,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }

class TipoLotePrecoEstrela(db.Model):  # type: ignore
    __tablename__ = 'tipo_lote_preco_estrelas'
    __table_args__ = (
        db.UniqueConstraint('tipo_lote_id', 'estrelas', name='uq_tipo_lote_estrelas'),
        db.Index('idx_tipo_lote_estrelas', 'tipo_lote_id', 'estrelas'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    tipo_lote_id = db.Column(db.Integer, db.ForeignKey('tipos_lote.id'), nullable=False)
    estrelas = db.Column(db.Integer, nullable=False)
    preco_por_kg = db.Column(db.Float, nullable=False, default=0.0)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs: Any) -> None:
        if 'estrelas' in kwargs and (kwargs['estrelas'] < 1 or kwargs['estrelas'] > 5):
            raise ValueError('Estrelas deve estar entre 1 e 5')
        super().__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'tipo_lote_id': self.tipo_lote_id,
            'tipo_lote_nome': self.tipo_lote.nome if self.tipo_lote else None,
            'estrelas': self.estrelas,
            'preco_por_kg': self.preco_por_kg,
            'ativo': self.ativo,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }

class Fornecedor(db.Model):  # type: ignore
    __tablename__ = 'fornecedores'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    nome_social = db.Column(db.String(200))
    cnpj = db.Column(db.String(18), unique=True)
    cpf = db.Column(db.String(14), unique=True)
    
    rua = db.Column(db.String(200))
    numero = db.Column(db.String(20))
    cidade = db.Column(db.String(100))
    cep = db.Column(db.String(10))
    estado = db.Column(db.String(2))
    bairro = db.Column(db.String(100))
    complemento = db.Column(db.String(200))
    
    tem_outro_endereco = db.Column(db.Boolean, default=False)
    outro_rua = db.Column(db.String(200))
    outro_numero = db.Column(db.String(20))
    outro_cidade = db.Column(db.String(100))
    outro_cep = db.Column(db.String(10))
    outro_estado = db.Column(db.String(2))
    outro_bairro = db.Column(db.String(100))
    outro_complemento = db.Column(db.String(200))
    
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    
    vendedor_id = db.Column(db.Integer, db.ForeignKey('vendedores.id'), nullable=True)
    
    conta_bancaria = db.Column(db.String(50))
    agencia = db.Column(db.String(20))
    chave_pix = db.Column(db.String(100))
    banco = db.Column(db.String(100))
    
    condicao_pagamento = db.Column(db.String(50), default='avista')
    forma_pagamento = db.Column(db.String(50), default='pix')
    
    observacoes = db.Column(db.Text)
    
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    precos = db.relationship('FornecedorTipoLotePreco', backref='fornecedor', lazy=True, cascade='all, delete-orphan')
    solicitacoes = db.relationship('Solicitacao', backref='fornecedor', lazy=True, cascade='all, delete-orphan')
    lotes = db.relationship('Lote', backref='fornecedor', lazy=True)
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'nome_social': self.nome_social,
            'cnpj': self.cnpj,
            'cpf': self.cpf,
            'rua': self.rua,
            'numero': self.numero,
            'cidade': self.cidade,
            'cep': self.cep,
            'estado': self.estado,
            'bairro': self.bairro,
            'complemento': self.complemento,
            'tem_outro_endereco': self.tem_outro_endereco,
            'outro_rua': self.outro_rua,
            'outro_numero': self.outro_numero,
            'outro_cidade': self.outro_cidade,
            'outro_cep': self.outro_cep,
            'outro_estado': self.outro_estado,
            'outro_bairro': self.outro_bairro,
            'outro_complemento': self.outro_complemento,
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
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None,
            'ativo': self.ativo
        }

class FornecedorTipoLotePreco(db.Model):  # type: ignore
    __tablename__ = 'fornecedor_tipo_lote_precos'
    __table_args__ = (
        db.UniqueConstraint('fornecedor_id', 'tipo_lote_id', 'estrelas', name='uq_fornecedor_tipo_estrelas'),
        db.Index('idx_fornecedor_tipo_estrelas', 'fornecedor_id', 'tipo_lote_id', 'estrelas'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedores.id'), nullable=False)
    tipo_lote_id = db.Column(db.Integer, db.ForeignKey('tipos_lote.id'), nullable=False)
    estrelas = db.Column(db.Integer, nullable=False)
    preco_por_kg = db.Column(db.Float, nullable=False, default=0.0)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs: Any) -> None:
        if 'estrelas' in kwargs and (kwargs['estrelas'] < 1 or kwargs['estrelas'] > 5):
            raise ValueError('Estrelas deve estar entre 1 e 5')
        super().__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'fornecedor_id': self.fornecedor_id,
            'fornecedor_nome': self.fornecedor.nome if self.fornecedor else None,
            'tipo_lote_id': self.tipo_lote_id,
            'tipo_lote_nome': self.tipo_lote.nome if self.tipo_lote else None,
            'estrelas': self.estrelas,
            'preco_por_kg': self.preco_por_kg,
            'ativo': self.ativo,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }

class FornecedorTipoLoteClassificacao(db.Model):  # type: ignore
    __tablename__ = 'fornecedor_tipo_lote_classificacao'
    __table_args__ = (
        db.UniqueConstraint('fornecedor_id', 'tipo_lote_id', name='uq_fornecedor_tipo_classificacao'),
        db.Index('idx_fornecedor_tipo_class', 'fornecedor_id', 'tipo_lote_id'),
        db.Index('idx_fornecedor_class_ativo', 'fornecedor_id', 'ativo'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedores.id'), nullable=False)
    tipo_lote_id = db.Column(db.Integer, db.ForeignKey('tipos_lote.id'), nullable=False)
    leve_estrelas = db.Column(db.Integer, nullable=False, default=1)
    medio_estrelas = db.Column(db.Integer, nullable=False, default=3)
    pesado_estrelas = db.Column(db.Integer, nullable=False, default=5)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    fornecedor = db.relationship('Fornecedor', backref='classificacoes_tipo_lote')
    tipo_lote = db.relationship('TipoLote', backref='classificacoes_fornecedor')
    
    def __init__(self, **kwargs: Any) -> None:
        for campo in ['leve_estrelas', 'medio_estrelas', 'pesado_estrelas']:
            if campo in kwargs and (kwargs[campo] < 1 or kwargs[campo] > 5):
                raise ValueError(f'{campo} deve estar entre 1 e 5')
        super().__init__(**kwargs)
    
    def get_estrelas_por_classificacao(self, classificacao: str) -> int:
        if classificacao == 'leve':
            return self.leve_estrelas
        elif classificacao == 'medio':
            return self.medio_estrelas
        elif classificacao == 'pesado':
            return self.pesado_estrelas
        else:
            return self.medio_estrelas
    
    def to_dict(self):
        return {
            'id': self.id,
            'fornecedor_id': self.fornecedor_id,
            'fornecedor_nome': self.fornecedor.nome if self.fornecedor else None,
            'tipo_lote_id': self.tipo_lote_id,
            'tipo_lote_nome': self.tipo_lote.nome if self.tipo_lote else None,
            'leve_estrelas': self.leve_estrelas,
            'medio_estrelas': self.medio_estrelas,
            'pesado_estrelas': self.pesado_estrelas,
            'ativo': self.ativo,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }

class Solicitacao(db.Model):  # type: ignore
    __tablename__ = 'solicitacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    funcionario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedores.id'), nullable=False)
    tipo_retirada = db.Column(db.String(20), default='buscar', nullable=False)
    status = db.Column(db.String(20), default='pendente', nullable=False)
    observacoes = db.Column(db.Text)
    data_envio = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    data_confirmacao = db.Column(db.DateTime, nullable=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    
    rua = db.Column(db.String(200))
    numero = db.Column(db.String(20))
    cep = db.Column(db.String(10))
    localizacao_lat = db.Column(db.Float, nullable=True)
    localizacao_lng = db.Column(db.Float, nullable=True)
    endereco_completo = db.Column(db.String(500))
    
    itens = db.relationship('ItemSolicitacao', backref='solicitacao', lazy=True, cascade='all, delete-orphan')
    admin = db.relationship('Usuario', foreign_keys=[admin_id], backref='solicitacoes_aprovadas_por_mim')
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def to_dict(self):
        itens_list = list(self.itens) if self.itens else []
        total_peso = sum(item.peso_kg for item in itens_list)
        total_valor = sum(item.valor_calculado for item in itens_list)
        
        return {
            'id': self.id,
            'funcionario_id': self.funcionario_id,
            'funcionario_nome': self.funcionario.nome if self.funcionario else None,
            'fornecedor_id': self.fornecedor_id,
            'fornecedor_nome': self.fornecedor.nome if self.fornecedor else None,
            'tipo_retirada': self.tipo_retirada,
            'status': self.status,
            'observacoes': self.observacoes,
            'rua': self.rua,
            'numero': self.numero,
            'cep': self.cep,
            'localizacao_lat': self.localizacao_lat,
            'localizacao_lng': self.localizacao_lng,
            'endereco_completo': self.endereco_completo,
            'data_envio': self.data_envio.isoformat() if self.data_envio else None,
            'data_confirmacao': self.data_confirmacao.isoformat() if self.data_confirmacao else None,
            'admin_id': self.admin_id,
            'admin_nome': self.admin.nome if self.admin else None,
            'total_itens': len(itens_list),
            'total_peso_kg': round(total_peso, 2),
            'total_valor': round(total_valor, 2)
        }

class ItemSolicitacao(db.Model):  # type: ignore
    __tablename__ = 'itens_solicitacao'
    
    id = db.Column(db.Integer, primary_key=True)
    solicitacao_id = db.Column(db.Integer, db.ForeignKey('solicitacoes.id'), nullable=False)
    tipo_lote_id = db.Column(db.Integer, db.ForeignKey('tipos_lote.id'), nullable=False)
    peso_kg = db.Column(db.Float, nullable=False)
    estrelas_sugeridas_ia = db.Column(db.Integer, nullable=True)
    estrelas_final = db.Column(db.Integer, nullable=False, default=3)
    classificacao = db.Column(db.String(10), nullable=True)
    classificacao_sugerida_ia = db.Column(db.String(10), nullable=True)
    valor_calculado = db.Column(db.Float, nullable=False, default=0.0)
    imagem_url = db.Column(db.String(500))
    observacoes = db.Column(db.Text)
    data_registro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    lote_id = db.Column(db.Integer, db.ForeignKey('lotes.id'), nullable=True)
    
    def __init__(self, **kwargs: Any) -> None:
        if 'estrelas_final' in kwargs and (kwargs['estrelas_final'] < 1 or kwargs['estrelas_final'] > 5):
            raise ValueError('Estrelas deve estar entre 1 e 5')
        if 'classificacao' in kwargs and kwargs['classificacao'] and kwargs['classificacao'] not in ['leve', 'medio', 'pesado']:
            raise ValueError('Classificação deve ser: leve, medio ou pesado')
        super().__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'solicitacao_id': self.solicitacao_id,
            'tipo_lote_id': self.tipo_lote_id,
            'tipo_lote_nome': self.tipo_lote.nome if self.tipo_lote else None,
            'peso_kg': self.peso_kg,
            'estrelas_sugeridas_ia': self.estrelas_sugeridas_ia,
            'estrelas_final': self.estrelas_final,
            'classificacao': self.classificacao,
            'classificacao_sugerida_ia': self.classificacao_sugerida_ia,
            'valor_calculado': self.valor_calculado,
            'imagem_url': self.imagem_url,
            'observacoes': self.observacoes,
            'data_registro': self.data_registro.isoformat() if self.data_registro else None,
            'lote_id': self.lote_id,
            'lote_numero': self.lote.numero_lote if self.lote else None
        }

class Lote(db.Model):  # type: ignore
    __tablename__ = 'lotes'
    __table_args__ = (
        db.Index('idx_numero_lote', 'numero_lote'),
        db.Index('idx_fornecedor_tipo_status', 'fornecedor_id', 'tipo_lote_id', 'status'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    numero_lote = db.Column(db.String(50), unique=True, nullable=False, default=lambda: str(uuid.uuid4()).upper())
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedores.id'), nullable=False)
    tipo_lote_id = db.Column(db.Integer, db.ForeignKey('tipos_lote.id'), nullable=False)
    solicitacao_origem_id = db.Column(db.Integer, db.ForeignKey('solicitacoes.id'), nullable=True)
    
    peso_total_kg = db.Column(db.Float, nullable=False, default=0.0)
    valor_total = db.Column(db.Float, nullable=False, default=0.0)
    quantidade_itens = db.Column(db.Integer, default=0)
    estrelas_media = db.Column(db.Float, nullable=True)
    classificacao_predominante = db.Column(db.String(10), nullable=True)
    
    status = db.Column(db.String(20), default='aberto', nullable=False)
    tipo_retirada = db.Column(db.String(20))
    
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    data_fechamento = db.Column(db.DateTime, nullable=True)
    data_aprovacao = db.Column(db.DateTime, nullable=True)
    
    observacoes = db.Column(db.Text)
    
    itens = db.relationship('ItemSolicitacao', backref='lote', lazy=True)
    solicitacao_origem = db.relationship('Solicitacao', backref='lotes_gerados', foreign_keys=[solicitacao_origem_id])
    entrada_estoque = db.relationship('EntradaEstoque', backref='lote', uselist=False, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'numero_lote': self.numero_lote,
            'fornecedor_id': self.fornecedor_id,
            'fornecedor_nome': self.fornecedor.nome if self.fornecedor else None,
            'tipo_lote_id': self.tipo_lote_id,
            'tipo_lote_nome': self.tipo_lote.nome if self.tipo_lote else None,
            'solicitacao_origem_id': self.solicitacao_origem_id,
            'peso_total_kg': self.peso_total_kg,
            'valor_total': self.valor_total,
            'quantidade_itens': self.quantidade_itens,
            'estrelas_media': self.estrelas_media,
            'classificacao_predominante': self.classificacao_predominante,
            'status': self.status,
            'tipo_retirada': self.tipo_retirada,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_fechamento': self.data_fechamento.isoformat() if self.data_fechamento else None,
            'data_aprovacao': self.data_aprovacao.isoformat() if self.data_aprovacao else None,
            'observacoes': self.observacoes
        }

class EntradaEstoque(db.Model):  # type: ignore
    __tablename__ = 'entradas_estoque'
    
    id = db.Column(db.Integer, primary_key=True)
    lote_id = db.Column(db.Integer, db.ForeignKey('lotes.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    
    status = db.Column(db.String(20), default='pendente', nullable=False)
    data_entrada = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    data_processamento = db.Column(db.DateTime, nullable=True)
    observacoes = db.Column(db.Text)
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def to_dict(self):
        lote_dict = self.lote.to_dict() if self.lote else {}
        
        return {
            'id': self.id,
            'lote_id': self.lote_id,
            'lote': lote_dict,
            'admin_id': self.admin_id,
            'admin_nome': self.admin.nome if self.admin else None,
            'status': self.status,
            'data_entrada': self.data_entrada.isoformat() if self.data_entrada else None,
            'data_processamento': self.data_processamento.isoformat() if self.data_processamento else None,
            'observacoes': self.observacoes
        }

class Notificacao(db.Model):  # type: ignore
    __tablename__ = 'notificacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    lida = db.Column(db.Boolean, default=False, nullable=False)
    data_envio = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'titulo': self.titulo,
            'mensagem': self.mensagem,
            'lida': self.lida,
            'data_envio': self.data_envio.isoformat() if self.data_envio else None
        }

class Configuracao(db.Model):  # type: ignore
    __tablename__ = 'configuracoes'
    
    id = db.Column(db.Integer, primary_key=True)
    chave = db.Column(db.String(100), unique=True, nullable=False)
    valor = db.Column(db.Text, nullable=False)
    descricao = db.Column(db.String(200))
    tipo = db.Column(db.String(50), default='texto')
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'chave': self.chave,
            'valor': self.valor,
            'descricao': self.descricao,
            'tipo': self.tipo,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }
