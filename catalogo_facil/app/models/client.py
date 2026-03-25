from app.extensions import db

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # ID do cliente
    nome = db.Column(db.String(120), nullable=False)  # Nome do cliente
    numero = db.Column(db.String(20), nullable=False)  # Telefone / celular do cliente
    cpf = db.Column(db.String(11), nullable=True)  # CPF do cliente, sem máscara
    endereco = db.Column(db.String(120), nullable=True)  # Endereço do cliente

    # Relação 1:N com Sale
    # Um cliente pode ter várias vendas registradas.
    sales = db.relationship("Sale", back_populates="client", lazy=True)

