from decimal import Decimal
from flask import request

from app.extensions import db


class Product(db.Model):
    __tablename__ = "product"

    id = db.Column(db.Integer, primary_key=True) # ID Produto
    nome = db.Column(db.String(120), nullable=False) # Nome produto
    descricao = db.Column(db.Text, nullable=False, default="") # Descrição de produto
    p_custo = db.Column(db.Numeric(10, 2), nullable=False) # Preço de custo de produto
    preco = db.Column(db.Numeric(10, 2), nullable=False) # Preço de venda do produto
    lucro = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("0.00")) # Lucro de venda do produto unitario
    estoque = db.Column(db.Integer, nullable=False, default=0) # Estoque produto
    imagem = db.Column(db.String(255), nullable=False, default="") # Imagem em Base64 do produto
    ativo = db.Column(db.Boolean, nullable=False, default=True) # Valor de ativo ou desativado de produto

    # Relacionamento com categorias de 1:N
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=True) 

    # Relacionamento produto com venda de N:1
    sale_items = db.relationship("SaleItem", back_populates="product", lazy=True)
    
    # Relacionamento de produto com item catalogo 
    catalog_items = db.relationship("CatalogItem", back_populates="product", lazy=True)
