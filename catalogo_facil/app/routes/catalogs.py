import os

from flask import (Blueprint, current_app, flash, make_response, redirect, render_template, request, url_for,
)

from app.extensions import db
from app.models import Catalog, Category, Product, Shop
from app.utils import (
    _apply_catalog_color_defaults,
    _build_catalog_payload,
    _build_form_catalog_state,
    _caminho_imagem_produto,
    _caminho_logo_catalogo,
    _get_selected_products,
    _montar_contexto_catalogo,
    _montar_ids_produtos,
    _parse_selected_ids,
    _replace_catalog_items,
    logo_para_base64,
    produto_para_base64,
    remover_logo_catalogo,
    salvar_logo_catalogo,
)

bp = Blueprint("catalogs", __name__, url_prefix="/catalogos")


def _get_products_and_categories():
    products = Product.query.filter_by(ativo=True).order_by(Product.nome.asc()).all()
    categories = Category.query.order_by(Category.nome.asc()).all()
    return products, categories


def _render_catalog_form(
    *,
    catalog=None,
    products=None,
    categories=None,
    selected_products=None,
    selected_category_ids=None,
):
    return render_template(
        "catalog/form.html",
        catalog=catalog,
        products=products or [],
        categories=categories or [],
        selected_products=selected_products or [],
        selected_category_ids=selected_category_ids or [],
    )

def _montar_contexto_icone_carrinho(catalog, exportar=False):
    cor = (getattr(catalog, "icone_carrinho_cor", "branco") or "branco").strip().lower()

    carrinho_icon_file = (
        "img/carrinho-preto.png"
        if cor == "preto"
        else "img/carrinho-branco.png"
    )

    carrinho_icon_src = None

    if exportar:
        caminho_icone = os.path.join(current_app.static_folder, carrinho_icon_file)
        if os.path.isfile(caminho_icone):
            carrinho_icon_src = logo_para_base64(caminho_icone, largura_maxima=128)

    return carrinho_icon_file, carrinho_icon_src

# -- LIST CATALOGS --
@bp.route("/")
def list_catalogs():
    catalogs = Catalog.query.order_by(Catalog.id.desc()).all()
    return render_template("catalog/list.html", catalogs=catalogs)


# -- CREATE CATALOG --
@bp.route("/novo", methods=["GET", "POST"])
def create_catalog():
    products, categories = _get_products_and_categories()
    shop = Shop.query.first()

    if not shop:
        flash("Cadastre os dados da loja antes de criar um catálogo.", "warning")
        return redirect(url_for("shops.manage_shop"))

    if request.method == "POST":
        form_catalog = _build_form_catalog_state(is_edit=False)

        try:
            category_ids_raw, product_ids_raw, selected_category_ids, selected_product_ids = _parse_selected_ids()
            selected_products = _get_selected_products(selected_product_ids)
            payload = _build_catalog_payload()

            if not payload["nome"]:
                flash("Informe o nome do catálogo.", "danger")
                return _render_catalog_form(
                    catalog=form_catalog,
                    products=products,
                    categories=categories,
                    selected_products=selected_products,
                    selected_category_ids=selected_category_ids,
                )

            final_product_ids = _montar_ids_produtos(selected_category_ids, product_ids_raw)

            if not final_product_ids:
                flash("Selecione pelo menos uma categoria ou um produto.", "danger")
                return _render_catalog_form(
                    catalog=form_catalog,
                    products=products,
                    categories=categories,
                    selected_products=selected_products,
                    selected_category_ids=selected_category_ids,
                )

            upload_folder = current_app.config["CATALOG_UPLOAD_DIR"]
            logo_file = request.files.get("logo")
            logo_nome = ""

            if logo_file and logo_file.filename:
                logo_nome = salvar_logo_catalogo(logo_file, upload_folder)

            catalog = Catalog(
                shop_id=shop.id,
                logo=logo_nome,
                **payload,
            )
            db.session.add(catalog)
            db.session.flush()

            _replace_catalog_items(db, catalog.id, final_product_ids)

            db.session.commit()
            flash("Catálogo criado com sucesso.", "success")
            return redirect(url_for("catalogs.list_catalogs"))

        except ValueError as e:
            db.session.rollback()
            flash(str(e), "danger")
            return _render_catalog_form(
                catalog=form_catalog,
                products=products,
                categories=categories,
                selected_products=_get_selected_products(
                    [int(pid) for pid in request.form.getlist("product_id[]") if pid.isdigit()]
                ),
                selected_category_ids=[
                    int(cat_id) for cat_id in request.form.getlist("category_id[]") if cat_id.isdigit()
                ],
            )

        except Exception:
            db.session.rollback()
            flash("Erro ao criar catálogo. ⚠️", "danger")
            return _render_catalog_form(
                catalog=form_catalog,
                products=products,
                categories=categories,
                selected_products=_get_selected_products(
                    [int(pid) for pid in request.form.getlist("product_id[]") if pid.isdigit()]
                ),
                selected_category_ids=[
                    int(cat_id) for cat_id in request.form.getlist("category_id[]") if cat_id.isdigit()
                ],
            )

    return _render_catalog_form(
        catalog=None,
        products=products,
        categories=categories,
        selected_products=[],
        selected_category_ids=[],
    )


# -- EDIT CATALOG --
@bp.route("/<int:catalog_id>/editar", methods=["GET", "POST"])
def edit_catalog(catalog_id):
    catalog = Catalog.query.get_or_404(catalog_id)
    products, categories = _get_products_and_categories()

    if request.method == "POST":
        form_catalog = _build_form_catalog_state(base_catalog=catalog, is_edit=True)

        try:
            category_ids_raw, product_ids_raw, selected_category_ids, selected_product_ids = _parse_selected_ids()
            selected_products = _get_selected_products(selected_product_ids)
            payload = _build_catalog_payload()

            if not payload["nome"]:
                flash("Informe o nome do catálogo.", "danger")
                return _render_catalog_form(
                    catalog=form_catalog,
                    products=products,
                    categories=categories,
                    selected_products=selected_products,
                    selected_category_ids=selected_category_ids,
                )

            final_product_ids = _montar_ids_produtos(selected_category_ids, product_ids_raw)

            if not final_product_ids:
                flash("Selecione pelo menos uma categoria ou um produto.", "danger")
                return _render_catalog_form(
                    catalog=form_catalog,
                    products=products,
                    categories=categories,
                    selected_products=selected_products,
                    selected_category_ids=selected_category_ids,
                )

            upload_folder = current_app.config["CATALOG_UPLOAD_DIR"]
            logo_file = request.files.get("logo")
            remover_logo = request.form.get("remover_logo") == "1"

            if remover_logo and catalog.logo:
                remover_logo_catalogo(catalog.logo, upload_folder)
                catalog.logo = ""

            if logo_file and logo_file.filename:
                if catalog.logo:
                    remover_logo_catalogo(catalog.logo, upload_folder)
                catalog.logo = salvar_logo_catalogo(logo_file, upload_folder)

            for field, value in payload.items():
                setattr(catalog, field, value)

            _replace_catalog_items(db, catalog.id, final_product_ids)

            db.session.commit()
            flash("Catálogo atualizado com sucesso.", "success")
            return redirect(url_for("catalogs.list_catalogs"))

        except ValueError as e:
            db.session.rollback()
            flash(str(e), "danger")
            return _render_catalog_form(
                catalog=form_catalog,
                products=products,
                categories=categories,
                selected_products=_get_selected_products(
                    [int(pid) for pid in request.form.getlist("product_id[]") if pid.isdigit()]
                ),
                selected_category_ids=[
                    int(cat_id) for cat_id in request.form.getlist("category_id[]") if cat_id.isdigit()
                ],
            )

        except Exception as e:
            db.session.rollback()
            current_app.logger.exception("Erro ao atualizar catálogo. ⚠️")
            flash(f"Erro ao atualizar catálogo: {e}", "danger")
            return _render_catalog_form(
                catalog=form_catalog,
                products=products,
                categories=categories,
                selected_products=_get_selected_products(
                    [int(pid) for pid in request.form.getlist("product_id[]") if pid.isdigit()]),
                selected_category_ids=[int(cat_id) for cat_id in request.form.getlist("category_id[]") if cat_id.isdigit()],
            )

    selected_products = [item.product for item in catalog.items if item.product]
    selected_category_ids = list({
        product.category_id
        for product in selected_products
        if product.category_id
    })

    _apply_catalog_color_defaults(catalog)

    return _render_catalog_form(
        catalog=catalog,
        products=products,
        categories=categories,
        selected_products=selected_products,
        selected_category_ids=selected_category_ids,
    )


# -- DELETE CATALOG --
@bp.route("/<int:catalog_id>/excluir", methods=["POST"])
def delete_catalog(catalog_id):
    catalog = Catalog.query.get_or_404(catalog_id)

    if catalog.logo:
        upload_folder = current_app.config["CATALOG_UPLOAD_DIR"]
        remover_logo_catalogo(catalog.logo, upload_folder)

    db.session.delete(catalog)
    db.session.commit()

    flash("Catálogo excluído com sucesso.", "success")
    return redirect(url_for("catalogs.list_catalogs"))

# -- SHOW CATALOG --
@bp.route("/<int:catalog_id>")
def printable_catalog(catalog_id):
    catalog = Catalog.query.get_or_404(catalog_id)

    items, categorias_map, shop, whatsapp_link = _montar_contexto_catalogo(catalog)
    carrinho_icon_file, carrinho_icon_src = _montar_contexto_icone_carrinho(catalog)

    return render_template(
        "catalog/printable.html",
        catalog=catalog,
        shop=shop,
        whatsapp_link=whatsapp_link,
        items=items,
        categorias_map=categorias_map,
        modo_exportacao=False,
        logo_src=None,
        imagens_produtos={},
        icone_whatsapp_src=None,
        icone_instagram_src=None,
        icone_facebook_src=None,
        carrinho_icon_file=carrinho_icon_file,
        carrinho_icon_src=carrinho_icon_src,
    )

# -- EXPORT CATALOG AS HTML --
@bp.route("/<int:catalog_id>/exportar-html")
def export_catalog_html(catalog_id):
    catalog = Catalog.query.get_or_404(catalog_id)

    items, categorias_map, shop, whatsapp_link = _montar_contexto_catalogo(catalog)
    carrinho_icon_file, carrinho_icon_src = _montar_contexto_icone_carrinho(catalog, exportar=True)

    logo_src = None
    caminho_logo = _caminho_logo_catalogo(catalog.logo)
    if caminho_logo:
        logo_src = logo_para_base64(caminho_logo, largura_maxima=600)

    imagens_produtos = {}
    for item in items:
        product = item.product
        if not product or not product.imagem:
            continue

        caminho_imagem = _caminho_imagem_produto(product.imagem)
        if not caminho_imagem:
            continue

        imagens_produtos[product.id] = produto_para_base64(
            caminho_imagem,
            largura_maxima=1400,
            qualidade=90,
        )

    icone_whatsapp_src = None
    icone_instagram_src = None
    icone_facebook_src = None

    caminho_icone_whatsapp = os.path.join(current_app.static_folder, "img", "whatsapp.png")
    caminho_icone_instagram = os.path.join(current_app.static_folder, "img", "instagram.png")
    caminho_icone_facebook = os.path.join(current_app.static_folder, "img", "facebook.png")

    if os.path.isfile(caminho_icone_whatsapp):
        icone_whatsapp_src = logo_para_base64(caminho_icone_whatsapp, largura_maxima=128)

    if os.path.isfile(caminho_icone_instagram):
        icone_instagram_src = logo_para_base64(caminho_icone_instagram, largura_maxima=128)

    if os.path.isfile(caminho_icone_facebook):
        icone_facebook_src = logo_para_base64(caminho_icone_facebook, largura_maxima=128)

    html = render_template(
        "catalog/printable.html",
        catalog=catalog,
        shop=shop,
        whatsapp_link=whatsapp_link,
        items=items,
        categorias_map=categorias_map,
        modo_exportacao=True,
        logo_src=logo_src,
        imagens_produtos=imagens_produtos,
        icone_whatsapp_src=icone_whatsapp_src,
        icone_instagram_src=icone_instagram_src,
        icone_facebook_src=icone_facebook_src,
        carrinho_icon_file=carrinho_icon_file,
        carrinho_icon_src=carrinho_icon_src,
    )

    response = make_response(html)
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    response.headers["Content-Disposition"] = f'attachment; filename="catalogo-{catalog.nome}-{shop.nome}.html"'
    return response