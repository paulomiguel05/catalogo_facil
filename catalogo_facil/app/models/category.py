from app.extensions import db

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # ID da categoria
    nome = db.Column(db.String(120), nullable=False, unique=True)  # Nome único da categoria

    # Relação 1:N
    # Uma categoria pode possuir vários produtos.
    produtos = db.relationship("Product", backref="categoria", lazy=True)
