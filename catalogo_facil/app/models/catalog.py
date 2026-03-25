from app.extensions import db

class Catalog(db.Model):
    __tablename__ = "catalog"

    id = db.Column(db.Integer, primary_key=True) #ID Catálago
    shop_id = db.Column(db.Integer, db.ForeignKey("shop.id"), nullable=False) # ID relacionamento da Loja

    nome = db.Column(db.String(120), nullable=False) # Nome do catálogo
    descricao = db.Column(db.Text, nullable=False, default="") # Descrição do catálogo

    logo = db.Column(db.String(255), nullable=False, default="") # Logo do catálogo
    cabecalho_titulo = db.Column(db.String(120), nullable=False, default="") # Cabeçalho titulo do catálogo
    cabecalho_subtitulo = db.Column(db.String(255), nullable=False, default="") # Cabeçalho subtitulo do catálogo

    mostrar_preco = db.Column(db.Boolean, nullable=False, default=True) #Opção de vitrine do catálogo, preço on / off

    # Cores do catálogo

    cor_fundo = db.Column(db.String(7), default="#f5f5f7") 
    cor_superficie = db.Column(db.String(7), default="#ffffff")
    cor_superficie_secundaria = db.Column(db.String(7), default="#f8fafc")
    cor_texto = db.Column(db.String(7), default="#1f2937")
    cor_texto_secundario = db.Column(db.String(7), default="#6b7280")
    cor_borda = db.Column(db.String(7), default="#e5e7eb")
    cor_cabecalho = db.Column(db.String(7), default="#111827")
    cor_cabecalho_detalhe = db.Column(db.String(7), default="#7c3aed")
    cor_texto_cabecalho = db.Column(db.String(7), default="#ffffff")
    cor_botao_primario = db.Column(db.String(7), default="#7c3aed")
    cor_botao_primario_hover = db.Column(db.String(7), default="#6d28d9")
    cor_botao_secundario = db.Column(db.String(7), default="#374151")
    cor_botao_secundario_hover = db.Column(db.String(7), default="#1f2937")
    cor_preco = db.Column(db.String(7), default="#111827")
    cor_destaque = db.Column(db.String(7), default="#7c3aed")
    
    icone_carrinho_cor = db.Column(db.String(20), default="branco") # Opção branco ou preto de carrinho. 

    # Relacionamento de 1:N com a informações da loja.
    shop = db.relationship("Shop", back_populates="catalogs") 

    items = db.relationship(
        "CatalogItem",
        back_populates="catalog",
        cascade="all, delete-orphan",
        lazy=True,
    )

    def __repr__(self):
        return f"<Catalog id={self.id} nome='{self.nome}'>"

class CatalogItem(db.Model):
    __tablename__ = "catalog_item"

    id = db.Column(db.Integer, primary_key=True) # ID de item no catálogo
    catalog_id = db.Column(db.Integer, db.ForeignKey("catalog.id"), nullable=False) # ID relacionamento catálogo
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False) # ID produto catálogo
    ordem = db.Column(db.Integer, nullable=False, default=0) # Ordem dos produtos 

    # Relacionamento item com catálogo de 1:N
    catalog = db.relationship("Catalog", back_populates="items") 
    # Relacionamento de produtos a itens do catágo de 1:1
    product = db.relationship("Product", back_populates="catalog_items")

    def __repr__(self):
        return (
            f"<CatalogItem id={self.id} catalog_id={self.catalog_id} "
            f"product_id={self.product_id} ordem={self.ordem}>"
        )