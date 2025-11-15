from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
from typing import Any

db = SQLAlchemy()

class Perfil(db.Model):  # type: ignore
    __tablename__ = 'perfis'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), unique=True, nullable=False)
    descricao = db.Column(db.Text)
    permissoes = db.Column(db.JSON, nullable=False, default=dict)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    usuarios = db.relationship('Usuario', backref='perfil', lazy=True)
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'permissoes': self.permissoes,
            'ativo': self.ativo,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }
    
    def has_permission(self, permission: str) -> bool:
        return self.permissoes.get(permission, False) if self.permissoes else False

class Usuario(db.Model):  # type: ignore
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    perfil_id = db.Column(db.Integer, db.ForeignKey('perfis.id'), nullable=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    criado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    
    solicitacoes = db.relationship('Solicitacao', backref='funcionario', lazy=True, cascade='all, delete-orphan', foreign_keys='Solicitacao.funcionario_id')
    notificacoes = db.relationship('Notificacao', backref='usuario', lazy=True, cascade='all, delete-orphan')
    entradas_processadas = db.relationship('EntradaEstoque', backref='admin', lazy=True, foreign_keys='EntradaEstoque.admin_id')
    criador = db.relationship('Usuario', remote_side=[id], backref='usuarios_criados')
    logs_auditoria = db.relationship('AuditoriaLog', backref='usuario', lazy=True, foreign_keys='AuditoriaLog.usuario_id')
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'tipo': self.tipo,
            'perfil_id': self.perfil_id,
            'perfil_nome': self.perfil.nome if self.perfil else None,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None,
            'ativo': self.ativo,
            'criado_por': self.criado_por,
            'criador_nome': self.criador.nome if self.criador else None
        }
    
    def has_permission(self, permission: str) -> bool:
        if self.perfil:
            return self.perfil.has_permission(permission)
        return self.tipo == 'admin'

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
    classificacao = db.Column(db.String(10), default=None, nullable=True)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    fornecedor_precos = db.relationship('FornecedorTipoLotePreco', backref='tipo_lote', lazy=True, cascade='all, delete-orphan')
    itens_solicitacao = db.relationship('ItemSolicitacao', backref='tipo_lote', lazy=True)
    lotes = db.relationship('Lote', backref='tipo_lote', lazy=True)
    precos = db.relationship('TipoLotePreco', backref='tipo_lote', lazy=True, cascade='all, delete-orphan')
    fornecedor_tipos = db.relationship('FornecedorTipoLote', backref='tipo_lote', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs: Any) -> None:
        if 'classificacao' in kwargs and kwargs['classificacao'] is not None and kwargs['classificacao'] not in ['leve', 'media', 'pesada']:
            raise ValueError('Classificação deve ser: leve, media ou pesada')
        super().__init__(**kwargs)
    
    def to_dict(self):
        precos_dict = {}
        if self.precos:
            for preco in self.precos:
                if preco.classificacao not in precos_dict:
                    precos_dict[preco.classificacao] = {}
                precos_dict[preco.classificacao][preco.estrelas] = preco.preco_por_kg
        
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'codigo': self.codigo,
            'classificacao': self.classificacao if self.classificacao else None,
            'ativo': self.ativo,
            'precos': precos_dict,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }

class TipoLotePreco(db.Model):  # type: ignore
    """Tabela unificada para armazenar preços por classificação e estrelas"""
    __tablename__ = 'tipo_lote_precos'
    __table_args__ = (
        db.UniqueConstraint('tipo_lote_id', 'classificacao', 'estrelas', name='uq_tipo_lote_class_estrelas'),
        db.Index('idx_tipo_lote_class_estrelas', 'tipo_lote_id', 'classificacao', 'estrelas'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    tipo_lote_id = db.Column(db.Integer, db.ForeignKey('tipos_lote.id'), nullable=False)
    classificacao = db.Column(db.String(10), nullable=False)
    estrelas = db.Column(db.Integer, nullable=False)
    preco_por_kg = db.Column(db.Float, nullable=False, default=0.0)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs: Any) -> None:
        if 'classificacao' in kwargs and kwargs['classificacao'] not in ['leve', 'medio', 'pesado']:
            raise ValueError('Classificação deve ser: leve, medio ou pesado')
        if 'estrelas' in kwargs and (kwargs['estrelas'] < 1 or kwargs['estrelas'] > 5):
            raise ValueError('Estrelas deve estar entre 1 e 5')
        if 'preco_por_kg' in kwargs and kwargs['preco_por_kg'] < 0:
            raise ValueError('Preço por kg deve ser maior ou igual a zero')
        super().__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'tipo_lote_id': self.tipo_lote_id,
            'tipo_lote_nome': self.tipo_lote.nome if self.tipo_lote else None,
            'classificacao': self.classificacao,
            'estrelas': self.estrelas,
            'preco_por_kg': self.preco_por_kg,
            'ativo': self.ativo,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }

class FornecedorTipoLote(db.Model):  # type: ignore
    """Relação N:N entre Fornecedor e TipoLote - quais tipos o fornecedor vende"""
    __tablename__ = 'fornecedor_tipo_lote'
    __table_args__ = (
        db.UniqueConstraint('fornecedor_id', 'tipo_lote_id', name='uq_fornecedor_tipo'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedores.id'), nullable=False)
    tipo_lote_id = db.Column(db.Integer, db.ForeignKey('tipos_lote.id'), nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'fornecedor_id': self.fornecedor_id,
            'tipo_lote_id': self.tipo_lote_id,
            'tipo_lote_nome': self.tipo_lote.nome if self.tipo_lote else None,
            'ativo': self.ativo
        }

class FornecedorClassificacaoEstrela(db.Model):  # type: ignore
    """Configuração de quantas estrelas vale cada classificação para um fornecedor"""
    __tablename__ = 'fornecedor_classificacao_estrela'
    __table_args__ = (
        db.UniqueConstraint('fornecedor_id', 'classificacao', name='uq_fornecedor_classificacao'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedores.id'), nullable=False)
    classificacao = db.Column(db.String(10), nullable=False)
    estrelas = db.Column(db.Integer, nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs: Any) -> None:
        if 'classificacao' in kwargs and kwargs['classificacao'] not in ['leve', 'medio', 'pesado']:
            raise ValueError('Classificação deve ser: leve, medio ou pesado')
        if 'estrelas' in kwargs and (kwargs['estrelas'] < 1 or kwargs['estrelas'] > 5):
            raise ValueError('Estrelas deve estar entre 1 e 5')
        super().__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'fornecedor_id': self.fornecedor_id,
            'classificacao': self.classificacao,
            'estrelas': self.estrelas,
            'ativo': self.ativo
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
    criado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    
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
    tipos_lote = db.relationship('FornecedorTipoLote', backref='fornecedor', lazy=True, cascade='all, delete-orphan')
    classificacao_estrelas = db.relationship('FornecedorClassificacaoEstrela', backref='fornecedor', lazy=True, cascade='all, delete-orphan')
    criado_por = db.relationship('Usuario', foreign_keys=[criado_por_id], backref='fornecedores_criados')
    
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
            'criado_por_id': self.criado_por_id,
            'criado_por_nome': self.criado_por.nome if self.criado_por else None,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None,
            'ativo': self.ativo
        }

class FornecedorFuncionarioAtribuicao(db.Model):  # type: ignore
    """Tabela de atribuição de fornecedores a funcionários (admin atribui fornecedores a funcionários)"""
    __tablename__ = 'fornecedor_funcionario_atribuicao'
    __table_args__ = (
        db.UniqueConstraint('fornecedor_id', 'funcionario_id', name='uq_fornecedor_funcionario'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedores.id'), nullable=False)
    funcionario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    data_atribuicao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    atribuido_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    
    fornecedor = db.relationship('Fornecedor', backref='atribuicoes')
    funcionario = db.relationship('Usuario', foreign_keys=[funcionario_id], backref='fornecedores_atribuidos')
    atribuido_por = db.relationship('Usuario', foreign_keys=[atribuido_por_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'fornecedor_id': self.fornecedor_id,
            'fornecedor_nome': self.fornecedor.nome if self.fornecedor else None,
            'funcionario_id': self.funcionario_id,
            'funcionario_nome': self.funcionario.nome if self.funcionario else None,
            'data_atribuicao': self.data_atribuicao.isoformat() if self.data_atribuicao else None,
            'atribuido_por_id': self.atribuido_por_id,
            'atribuido_por_nome': self.atribuido_por.nome if self.atribuido_por else None
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
    ordem_compra = db.relationship('OrdemCompra', back_populates='solicitacao', uselist=False, cascade='all, delete-orphan')
    
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
    justificativa_ia = db.Column(db.Text, nullable=True)
    valor_calculado = db.Column(db.Float, nullable=False, default=0.0)
    preco_por_kg_snapshot = db.Column(db.Float, nullable=True)
    estrelas_snapshot = db.Column(db.Integer, nullable=True)
    imagem_url = db.Column(db.String(500))
    observacoes = db.Column(db.Text)
    data_registro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    lote_id = db.Column(db.Integer, db.ForeignKey('lotes.id'), nullable=True)
    
    def __init__(self, **kwargs: Any) -> None:
        if 'estrelas_final' in kwargs and (kwargs['estrelas_final'] < 1 or kwargs['estrelas_final'] > 5):
            raise ValueError('Estrelas deve estar entre 1 e 5')
        if 'classificacao' in kwargs and kwargs['classificacao'] and kwargs['classificacao'] not in ['leve', 'medio', 'pesado']:
            raise ValueError('Classificação deve ser: leve, medio ou pesado')
        if 'valor_calculado' in kwargs and kwargs['valor_calculado'] is not None and kwargs['valor_calculado'] < 0:
            raise ValueError('Valor calculado não pode ser negativo')
        if 'peso_kg' in kwargs and (kwargs['peso_kg'] is None or kwargs['peso_kg'] <= 0):
            raise ValueError('Peso deve ser maior que zero')
        # Garantir que valor_calculado nunca seja None (usar 0.0 como padrão)
        if 'valor_calculado' not in kwargs or kwargs['valor_calculado'] is None:
            kwargs['valor_calculado'] = 0.0
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
            'justificativa_ia': self.justificativa_ia,
            'valor_calculado': self.valor_calculado,
            'preco_por_kg_snapshot': self.preco_por_kg_snapshot,
            'estrelas_snapshot': self.estrelas_snapshot,
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
    tipo = db.Column(db.String(50), nullable=True, default=None)
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
            'tipo': self.tipo,
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

class Veiculo(db.Model):  # type: ignore
    __tablename__ = 'veiculos'
    
    id = db.Column(db.Integer, primary_key=True)
    placa = db.Column(db.String(10), unique=True, nullable=False)
    renavam = db.Column(db.String(20), unique=True)
    tipo = db.Column(db.String(50), nullable=False)
    capacidade = db.Column(db.Float)
    marca = db.Column(db.String(50))
    modelo = db.Column(db.String(50))
    ano = db.Column(db.Integer)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    criado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    
    motoristas = db.relationship('Motorista', backref='veiculo', lazy=True)
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'placa': self.placa,
            'renavam': self.renavam,
            'tipo': self.tipo,
            'capacidade': self.capacidade,
            'marca': self.marca,
            'modelo': self.modelo,
            'ano': self.ano,
            'ativo': self.ativo,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None,
            'criado_por': self.criado_por
        }

class Motorista(db.Model):  # type: ignore
    __tablename__ = 'motoristas'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), unique=True, nullable=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    cnh = db.Column(db.String(20), unique=True)
    categoria_cnh = db.Column(db.String(5))
    veiculo_id = db.Column(db.Integer, db.ForeignKey('veiculos.id'), nullable=True)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    criado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    
    usuario = db.relationship('Usuario', foreign_keys=[usuario_id], backref='motorista_profile')
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'usuario_nome': self.usuario.nome if self.usuario else None,
            'usuario_email': self.usuario.email if self.usuario else None,
            'nome': self.nome,
            'cpf': self.cpf,
            'telefone': self.telefone,
            'email': self.email,
            'cnh': self.cnh,
            'categoria_cnh': self.categoria_cnh,
            'veiculo_id': self.veiculo_id,
            'veiculo_placa': self.veiculo.placa if self.veiculo else None,
            'ativo': self.ativo,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None,
            'criado_por': self.criado_por
        }

class AuditoriaLog(db.Model):  # type: ignore
    __tablename__ = 'auditoria_logs'
    __table_args__ = (
        db.Index('idx_usuario_data', 'usuario_id', 'data_acao'),
        db.Index('idx_entidade_acao', 'entidade_tipo', 'acao'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    acao = db.Column(db.String(50), nullable=False)
    entidade_tipo = db.Column(db.String(50), nullable=False)
    entidade_id = db.Column(db.Integer)
    detalhes = db.Column(db.JSON)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(500))
    data_acao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'usuario_nome': self.usuario.nome if self.usuario else 'Sistema',
            'usuario_email': self.usuario.email if self.usuario else None,
            'acao': self.acao,
            'entidade_tipo': self.entidade_tipo,
            'entidade_id': self.entidade_id,
            'detalhes': self.detalhes,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'data_acao': self.data_acao.isoformat() if self.data_acao else None
        }

class OrdemCompra(db.Model):  # type: ignore
    __tablename__ = 'ordens_compra'
    __table_args__ = (
        db.UniqueConstraint('solicitacao_id', name='uq_oc_solicitacao'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    solicitacao_id = db.Column(db.Integer, db.ForeignKey('solicitacoes.id'), nullable=False, unique=True)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedores.id'), nullable=False)
    valor_total = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(50), default='em_analise', nullable=False)
    aprovado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    aprovado_em = db.Column(db.DateTime, nullable=True)
    observacao = db.Column(db.Text)
    ip_aprovacao = db.Column(db.String(50))
    gps_aprovacao = db.Column(db.String(100))
    device_info = db.Column(db.String(100))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    criado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    solicitacao = db.relationship('Solicitacao', back_populates='ordem_compra', foreign_keys=[solicitacao_id], uselist=False)
    fornecedor = db.relationship('Fornecedor', backref='ordens_compra', foreign_keys=[fornecedor_id])
    aprovador = db.relationship('Usuario', foreign_keys=[aprovado_por], backref='ocs_aprovadas')
    criador = db.relationship('Usuario', foreign_keys=[criado_por], backref='ocs_criadas')
    auditorias = db.relationship('AuditoriaOC', backref='ordem_compra', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'solicitacao_id': self.solicitacao_id,
            'fornecedor_id': self.fornecedor_id,
            'fornecedor_nome': self.fornecedor.nome if self.fornecedor else None,
            'valor_total': round(self.valor_total, 2),
            'status': self.status,
            'aprovado_por': self.aprovado_por,
            'aprovador_nome': self.aprovador.nome if self.aprovador else None,
            'aprovado_em': self.aprovado_em.isoformat() if self.aprovado_em else None,
            'observacao': self.observacao,
            'ip_aprovacao': self.ip_aprovacao,
            'gps_aprovacao': self.gps_aprovacao,
            'device_info': self.device_info,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'criado_por': self.criado_por,
            'criador_nome': self.criador.nome if self.criador else None
        }

class AuditoriaOC(db.Model):  # type: ignore
    __tablename__ = 'auditoria_oc'
    __table_args__ = (
        db.Index('idx_oc_data', 'oc_id', 'data'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    oc_id = db.Column(db.Integer, db.ForeignKey('ordens_compra.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    acao = db.Column(db.String(50), nullable=False)
    status_anterior = db.Column(db.String(50))
    status_novo = db.Column(db.String(50))
    observacao = db.Column(db.Text)
    ip = db.Column(db.String(50))
    gps = db.Column(db.String(100))
    dispositivo = db.Column(db.String(500))
    data = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    usuario = db.relationship('Usuario', backref='auditorias_oc', foreign_keys=[usuario_id])
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'oc_id': self.oc_id,
            'usuario_id': self.usuario_id,
            'usuario_nome': self.usuario.nome if self.usuario else 'Sistema',
            'acao': self.acao,
            'status_anterior': self.status_anterior,
            'status_novo': self.status_novo,
            'observacao': self.observacao,
            'ip': self.ip,
            'gps': self.gps,
            'dispositivo': self.dispositivo,
            'data': self.data.isoformat() if self.data else None
        }

class OrdemServico(db.Model):  # type: ignore
    __tablename__ = 'ordens_servico'
    
    id = db.Column(db.Integer, primary_key=True)
    oc_id = db.Column(db.Integer, db.ForeignKey('ordens_compra.id'), nullable=False)
    numero_os = db.Column(db.String(50), unique=True, nullable=False)
    fornecedor_snapshot = db.Column(db.JSON, nullable=False)
    tipo = db.Column(db.String(20), nullable=False, default='COLETA')
    janela_coleta_inicio = db.Column(db.DateTime, nullable=True)
    janela_coleta_fim = db.Column(db.DateTime, nullable=True)
    motorista_id = db.Column(db.Integer, db.ForeignKey('motoristas.id'), nullable=True)
    veiculo_id = db.Column(db.Integer, db.ForeignKey('veiculos.id'), nullable=True)
    rota = db.Column(db.JSON, nullable=True)
    status = db.Column(db.String(50), default='PENDENTE', nullable=False)
    gps_logs = db.Column(db.JSON, default=lambda: [], nullable=True)
    attachments = db.Column(db.JSON, default=lambda: [], nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    auditoria = db.Column(db.JSON, default=lambda: [], nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    ordem_compra = db.relationship('OrdemCompra', backref='ordens_servico', foreign_keys=[oc_id])
    motorista = db.relationship('Motorista', backref='ordens_servico', foreign_keys=[motorista_id])
    veiculo = db.relationship('Veiculo', backref='ordens_servico', foreign_keys=[veiculo_id])
    criador = db.relationship('Usuario', foreign_keys=[created_by], backref='os_criadas')
    eventos_gps = db.relationship('GPSLog', backref='ordem_servico', lazy=True, cascade='all, delete-orphan')
    rotas_operacionais = db.relationship('RotaOperacional', backref='ordem_servico', lazy=True, cascade='all, delete-orphan')
    conferencias = db.relationship('ConferenciaRecebimento', backref='ordem_servico', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'oc_id': self.oc_id,
            'numero_os': self.numero_os,
            'fornecedor_snapshot': self.fornecedor_snapshot,
            'tipo': self.tipo,
            'janela_coleta_inicio': self.janela_coleta_inicio.isoformat() if self.janela_coleta_inicio else None,
            'janela_coleta_fim': self.janela_coleta_fim.isoformat() if self.janela_coleta_fim else None,
            'motorista_id': self.motorista_id,
            'motorista_nome': self.motorista.usuario.nome if self.motorista and self.motorista.usuario else None,
            'veiculo_id': self.veiculo_id,
            'veiculo_placa': self.veiculo.placa if self.veiculo else None,
            'rota': self.rota,
            'status': self.status,
            'gps_logs': self.gps_logs,
            'attachments': self.attachments,
            'created_by': self.created_by,
            'criador_nome': self.criador.nome if self.criador else None,
            'auditoria': self.auditoria,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None
        }

class RotaOperacional(db.Model):  # type: ignore
    __tablename__ = 'rotas_operacionais'
    
    id = db.Column(db.Integer, primary_key=True)
    os_id = db.Column(db.Integer, db.ForeignKey('ordens_servico.id'), nullable=False)
    motorista_id = db.Column(db.Integer, db.ForeignKey('motoristas.id'), nullable=False)
    veiculo_id = db.Column(db.Integer, db.ForeignKey('veiculos.id'), nullable=False)
    pontos = db.Column(db.JSON, nullable=False)
    km_estimado = db.Column(db.Float, nullable=True)
    km_real = db.Column(db.Float, nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    finalizado_em = db.Column(db.DateTime, nullable=True)
    
    motorista = db.relationship('Motorista', backref='rotas_operacionais', foreign_keys=[motorista_id])
    veiculo = db.relationship('Veiculo', backref='rotas_operacionais', foreign_keys=[veiculo_id])
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'os_id': self.os_id,
            'motorista_id': self.motorista_id,
            'motorista_nome': self.motorista.usuario.nome if self.motorista and self.motorista.usuario else None,
            'veiculo_id': self.veiculo_id,
            'veiculo_placa': self.veiculo.placa if self.veiculo else None,
            'pontos': self.pontos,
            'km_estimado': self.km_estimado,
            'km_real': self.km_real,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'finalizado_em': self.finalizado_em.isoformat() if self.finalizado_em else None
        }

class GPSLog(db.Model):  # type: ignore
    __tablename__ = 'gps_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    os_id = db.Column(db.Integer, db.ForeignKey('ordens_servico.id'), nullable=False)
    evento = db.Column(db.String(50), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    precisao = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    device_id = db.Column(db.String(255), nullable=True)
    ip = db.Column(db.String(50), nullable=True)
    dados_adicionais = db.Column(db.JSON, nullable=True)
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'os_id': self.os_id,
            'evento': self.evento,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'precisao': self.precisao,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'device_id': self.device_id,
            'ip': self.ip,
            'dados_adicionais': self.dados_adicionais
        }

class ConferenciaRecebimento(db.Model):  # type: ignore
    __tablename__ = 'conferencias_recebimento'
    
    id = db.Column(db.Integer, primary_key=True)
    os_id = db.Column(db.Integer, db.ForeignKey('ordens_servico.id'), nullable=False)
    oc_id = db.Column(db.Integer, db.ForeignKey('ordens_compra.id'), nullable=False)
    peso_fornecedor = db.Column(db.Float, nullable=True)
    peso_real = db.Column(db.Float, nullable=True)
    quantidade_prevista = db.Column(db.Integer, nullable=True)
    quantidade_real = db.Column(db.Integer, nullable=True)
    fotos_pesagem = db.Column(db.JSON, default=lambda: [], nullable=True)
    qualidade = db.Column(db.String(50), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    divergencia = db.Column(db.Boolean, default=False, nullable=False)
    tipo_divergencia = db.Column(db.String(50), nullable=True)
    percentual_diferenca = db.Column(db.Float, nullable=True)
    conferencia_status = db.Column(db.String(50), default='PENDENTE', nullable=False)
    conferente_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    auditoria = db.Column(db.JSON, default=lambda: [], nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    decisao_adm = db.Column(db.String(50), nullable=True)
    decisao_adm_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    decisao_adm_em = db.Column(db.DateTime, nullable=True)
    decisao_adm_motivo = db.Column(db.Text, nullable=True)
    gps_conferencia = db.Column(db.JSON, nullable=True)
    device_id_conferencia = db.Column(db.String(255), nullable=True)
    
    ordem_compra = db.relationship('OrdemCompra', backref='conferencias', foreign_keys=[oc_id])
    conferente = db.relationship('Usuario', foreign_keys=[conferente_id], backref='conferencias_realizadas')
    decisor_adm = db.relationship('Usuario', foreign_keys=[decisao_adm_por], backref='decisoes_conferencia')
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'os_id': self.os_id,
            'oc_id': self.oc_id,
            'peso_fornecedor': self.peso_fornecedor,
            'peso_real': self.peso_real,
            'quantidade_prevista': self.quantidade_prevista,
            'quantidade_real': self.quantidade_real,
            'fotos_pesagem': self.fotos_pesagem,
            'qualidade': self.qualidade,
            'observacoes': self.observacoes,
            'divergencia': self.divergencia,
            'tipo_divergencia': self.tipo_divergencia,
            'percentual_diferenca': self.percentual_diferenca,
            'conferencia_status': self.conferencia_status,
            'conferente_id': self.conferente_id,
            'conferente_nome': self.conferente.nome if self.conferente else None,
            'auditoria': self.auditoria,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None,
            'decisao_adm': self.decisao_adm,
            'decisao_adm_por': self.decisao_adm_por,
            'decisao_adm_por_nome': self.decisor_adm.nome if self.decisor_adm else None,
            'decisao_adm_em': self.decisao_adm_em.isoformat() if self.decisao_adm_em else None,
            'decisao_adm_motivo': self.decisao_adm_motivo,
            'gps_conferencia': self.gps_conferencia,
            'device_id_conferencia': self.device_id_conferencia
        }
