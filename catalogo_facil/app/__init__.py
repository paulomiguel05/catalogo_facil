from flask import Flask
from app.extensions import db
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    from app import models
    from app.routes import register_blueprints
    register_blueprints(app)

    @app.context_processor
    def inject_links():
        return {
            "celular_link": app.config.get("CELULAR_LINK"),
            "local_link": app.config.get("LOCAL_LINK"),
        }

    return app