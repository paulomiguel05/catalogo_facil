import os
import re

from flask import current_app, request
from .formatters import gerar_link_whatsapp
from app.models import CatalogItem, Product, Shop

HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
CART_ICON_ALLOWED = {"branco", "preto"}
CART_ICON_DEFAULT = "branco"

COLOR_DEFAULTS = {
    "cor_fundo": "#f5f5f7",
    "cor_superficie": "#ffffff",
    "cor_superficie_secundaria": "#f8fafc",
    "cor_texto": "#1f2937",
    "cor_texto_secundario": "#6b7280",
    "cor_borda": "#e5e7eb",
    "cor_cabecalho": "#111827",
    "cor_cabecalho_detalhe": "#7c3aed",
    "cor_texto_cabecalho": "#ffffff",
    "cor_botao_primario": "#7c3aed",
    "cor_botao_primario_hover": "#6d28d9",
    "cor_botao_secundario": "#374151",
    "cor_botao_secundario_hover": "#1f2937",
    "cor_preco": "#111827",
    "cor_destaque": "#7c3aed",
}

# Funções para gerar o catalogo costumizado.

class FormCatalogState:
    def __init__(self, is_edit=False, **kwargs):
        self._is_edit = is_edit
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __bool__(self):
        return self._is_edit


def _is_hex_color(value):
    return bool(HEX_COLOR_RE.fullmatch((value or "").strip()))


def _get_color_from_form(name):
    raw_value = request.form.get(name, "").strip()
    return raw_value if _is_hex_color(raw_value) else COLOR_DEFAULTS[name]


def _get_cart_icon_color_from_form(default=CART_ICON_DEFAULT):
    raw_value = (request.form.get("icone_carrinho_cor", default) or default).strip().lower()
    return raw_value if raw_value in CART_ICON_ALLOWED else default


def _build_form_catalog_state(base_catalog=None, is_edit=False):
    base_catalog = base_catalog or FormCatalogState()

    data = {
        "id": getattr(base_catalog, "id", None),
        "shop_id": getattr(base_catalog, "shop_id", None),
        "logo": getattr(base_catalog, "logo", ""),
        "nome": request.form.get("nome", getattr(base_catalog, "nome", "")).strip(),
        "descricao": request.form.get("descricao", getattr(base_catalog, "descricao", "")).strip(),
        "cabecalho_titulo": request.form.get(
            "cabecalho_titulo",
            getattr(base_catalog, "cabecalho_titulo", ""),
        ).strip(),
        "cabecalho_subtitulo": request.form.get(
            "cabecalho_subtitulo",
            getattr(base_catalog, "cabecalho_subtitulo", ""),
        ).strip(),
        "mostrar_preco": request.form.get(
            "mostrar_preco",
            "1" if getattr(base_catalog, "mostrar_preco", True) else "0",
        ) == "1",
        "icone_carrinho_cor": _get_cart_icon_color_from_form(
            getattr(base_catalog, "icone_carrinho_cor", CART_ICON_DEFAULT)
        ),
    }

    for color_name in COLOR_DEFAULTS:
        data[color_name] = _get_color_from_form(color_name)

    return FormCatalogState(is_edit=is_edit, **data)


def _build_catalog_payload():
    payload = {
        "nome": request.form.get("nome", "").strip(),
        "descricao": request.form.get("descricao", "").strip(),
        "cabecalho_titulo": request.form.get("cabecalho_titulo", "").strip(),
        "cabecalho_subtitulo": request.form.get("cabecalho_subtitulo", "").strip(),
        "mostrar_preco": request.form.get("mostrar_preco") == "1",
        "icone_carrinho_cor": _get_cart_icon_color_from_form(),
    }

    for color_name in COLOR_DEFAULTS:
        payload[color_name] = _get_color_from_form(color_name)

    return payload


def _parse_selected_ids():
    category_ids_raw = request.form.getlist("category_id[]")
    product_ids_raw = request.form.getlist("product_id[]")

    try:
        selected_category_ids = [int(cat_id) for cat_id in category_ids_raw if cat_id]
        selected_product_ids = [int(pid) for pid in product_ids_raw if pid]
    except ValueError:
        raise ValueError("Há categorias ou produtos inválidos na seleção.")

    return category_ids_raw, product_ids_raw, selected_category_ids, selected_product_ids


def _get_selected_products(selected_product_ids):
    if not selected_product_ids:
        return []

    return (
        Product.query
        .filter(Product.id.in_(selected_product_ids))
        .order_by(Product.nome.asc())
        .all()
    )


def _replace_catalog_items(db, catalog_id, final_product_ids):
    CatalogItem.query.filter_by(catalog_id=catalog_id).delete()

    produtos_por_id = {
        product.id: product
        for product in Product.query.filter(Product.id.in_(final_product_ids)).all()
    }

    for ordem, product_id in enumerate(final_product_ids, start=1):
        product = produtos_por_id.get(product_id)
        if not product:
            continue

        db.session.add(
            CatalogItem(
                catalog_id=catalog_id,
                product_id=product.id,
                ordem=ordem,
            )
        )


def _apply_catalog_color_defaults(catalog):
    for color_name, default_value in COLOR_DEFAULTS.items():
        current_value = getattr(catalog, color_name, None)
        if not current_value or not _is_hex_color(current_value):
            setattr(catalog, color_name, default_value)


def _caminho_logo_catalogo(nome_arquivo):
    if not nome_arquivo:
        return None

    caminho = os.path.join(
        current_app.config["CATALOG_UPLOAD_DIR"],
        nome_arquivo,
    )

    return caminho if os.path.isfile(caminho) else None


def _caminho_imagem_produto(nome_arquivo):
    if not nome_arquivo:
        return None

    caminho = os.path.join(
        current_app.config["PRODUCT_UPLOAD_DIR"],
        nome_arquivo,
    )

    return caminho if os.path.isfile(caminho) else None


def _montar_contexto_catalogo(catalog):
    items = sorted(
        [item for item in catalog.items if item.product and item.product.ativo],
        key=lambda item: item.ordem,
    )

    categorias_map = {}
    for item in items:
        categoria_nome = (
            item.product.categoria.nome
            if getattr(item.product, "categoria", None)
            else "Outros produtos"
        )

        if categoria_nome not in categorias_map:
            categorias_map[categoria_nome] = []

        categorias_map[categoria_nome].append(item)

    shop = getattr(catalog, "shop", None) or Shop.query.first()
    whatsapp_link = gerar_link_whatsapp(shop.numero if shop else None)

    return items, categorias_map, shop, whatsapp_link

def _montar_ids_produtos(category_ids, product_ids):
    product_ids_ordenados = []
    vistos = set()

    for product_id in product_ids:
        product_id = str(product_id).strip()
        if not product_id:
            continue

        pid = int(product_id)
        if pid not in vistos:
            vistos.add(pid)
            product_ids_ordenados.append(pid)

    if category_ids:
        products_from_categories = (
            Product.query.filter(
                Product.category_id.in_(category_ids),
                Product.ativo.is_(True),
            )
            .order_by(Product.nome.asc())
            .all()
        )

        for product in products_from_categories:
            if product.id not in vistos:
                vistos.add(product.id)
                product_ids_ordenados.append(product.id)

    return product_ids_ordenados