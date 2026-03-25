from decimal import Decimal
from datetime import datetime

from app.extensions import db


class Sale(db.Model):
    __tablename__ = "sale"

    id = db.Column(db.Integer, primary_key=True) # ID de Venda
    data = db.Column(db.DateTime, nullable=False, default=datetime.now) # Data da venda
    total = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("0.00")) # Valor total da venda
    status = db.Column(db.String(20), nullable=False, default="pendente") # Status do pagamento de venda
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=True) # ID de cliente
    lucro = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("0.00")) # Lucro de venda 
    
    # Relacionamento de cliente com a venda de 1:1
    client = db.relationship("Client", back_populates="sales")

    items = db.relationship(
        "SaleItem",
        back_populates="sale",
        cascade="all, delete-orphan",
        lazy=True,
    )

    # Funções muito basica para criar um utils
    def recalcular_total(self):
        self.total = sum((item.subtotal for item in self.items), Decimal("0.00"))
        return self.total

    def recalcular_lucro(self):
        self.lucro = sum((item.calcular_lucro() for item in self.items), Decimal("0.00"))
        return self.lucro

    def __repr__(self):
        return f"<Sale id={self.id} total={self.total:.2f} status='{self.status}'>"


class SaleItem(db.Model):
    __tablename__ = "sale_item"

   
    id = db.Column(db.Integer, primary_key=True) # ID de produto em venda
    sale_id = db.Column(db.Integer, db.ForeignKey("sale.id"), nullable=False) # Relacionamento ID da venda completa

    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=True) # Relacionamento ID do produto na venda (não some se apagar produto do estoque)

    quantidade = db.Column(db.Integer, nullable=False)

    # Dados do produto para histórico de venda (snapshot)
    nome_produto = db.Column(db.String(120), nullable=False)
    preco_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    custo_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    categoria_produto = db.Column(db.String(120), nullable=False)

    subtotal = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("0.00"))

    sale = db.relationship("Sale", back_populates="items")
    product = db.relationship("Product", back_populates="sale_items")

    def preencher_snapshot_produto(self):
        # Copia os dados do produto para o item da venda.
        if not self.product:
            raise ValueError("SaleItem precisa de um produto para gerar o snapshot.")

        self.nome_produto = self.product.nome
        self.preco_unitario = Decimal(str(self.product.preco))
        self.custo_unitario = Decimal(str(self.product.p_custo))
        self.categoria_produto = self.product.category.nome if self.product.category else "Sem categoria"
        self.calcular_subtotal()

    def calcular_subtotal(self):
        self.subtotal = Decimal(str(self.quantidade)) * Decimal(str(self.preco_unitario))
        return self.subtotal

    def calcular_lucro(self):
        custo_total = Decimal(str(self.quantidade)) * Decimal(str(self.custo_unitario))
        lucro = Decimal(str(self.subtotal)) - custo_total
        return lucro

    def __repr__(self):
        return (
            f"<SaleItem id={self.id} sale_id={self.sale_id} "
            f"product_id={self.product_id} nome='{self.nome_produto}' qtd={self.quantidade}>"
        )