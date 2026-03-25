from app.extensions import db

class Shop(db.Model):
    __tablename__ = "shop"

    id = db.Column(db.Integer, primary_key=True) # ID loja 
    nome = db.Column(db.String(120), nullable=False) # Nome da loja
    numero = db.Column(db.String(20), nullable=False) # Numero de telefone de loja
    instagram = db.Column(db.String(100), nullable=True) # Link ou @ do instagram da loja
    facebook = db.Column(db.String(255), nullable=True) # Link Facebook da loja
    email = db.Column(db.String(120), nullable=True) # E-mail da loja
    atividade = db.Column(db.JSON, nullable=True) # Atividade de Seg. Ter. Qua. Qui. Sex. Sáb. Dom.
    
    # Relacionamento de 1:N com catálogo
    catalogs = db.relationship(
        "Catalog",
        back_populates="shop",
        lazy=True,
    )

    def __repr__(self):
        return f"<Shop id={self.id} nome='{self.nome}'>"
