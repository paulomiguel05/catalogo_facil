from flask import Blueprint, render_template, current_app, send_from_directory

bp = Blueprint('main', __name__)

# -- Menu --
@bp.route('/')
def home():
    return render_template('home.html')

# Retorna imagem
@bp.route("/media/produtos/<path:filename>")
def media_produtos(filename):
    return send_from_directory(current_app.config["PRODUCT_UPLOAD_DIR"], filename)

# Retorna Catálogo
@bp.route("/media/catalogos/<path:filename>")
def media_catalogos(filename):
    return send_from_directory(current_app.config["CATALOG_UPLOAD_DIR"], filename)