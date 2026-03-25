from app.routes.main import bp as main_bp
from app.routes.shops import bp as shops_bp
from app.routes.products import bp as products_bp
from app.routes.clients import bp as clients_bp
from app.routes.sales import bp as sales_bp
from app.routes.categories import bp as categories_bp
from app.routes.catalogs import bp as catalogs_bp


def register_blueprints(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(shops_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(catalogs_bp)
