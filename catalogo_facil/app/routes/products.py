import os
from decimal import Decimal
from flask import Blueprint, flash, redirect, render_template, request, url_for, current_app, jsonify
from werkzeug.utils import secure_filename
from sqlalchemy import or_
from app.extensions import db
from ..models import Product, Category
from ..utils import parse_sort, toggle_sort, salvar_imagem_produto, remover_imagem_produto

bp = Blueprint('products', __name__, url_prefix='/produtos')

# -- LIST -- 
@bp.route("/")
def list_products():
    search = request.args.get("search", "").strip()
    sort = request.args.get("sort", "").strip()
    page = request.args.get("page", 1, type=int)

    sort_items, sort_map = parse_sort(sort)
    query = Product.query

    if search:
        query = query.outerjoin(Category, Product.category_id == Category.id).filter(
            or_(
                Product.nome.ilike(f"%{search}%"),
                Product.descricao.ilike(f"%{search}%"),
                Category.nome.ilike(f"%{search}%")
            )
        )

    join_category = any(campo == "categoria" for campo, _ in sort_items)
    if join_category and not search:
        query = query.outerjoin(Category, Product.category_id == Category.id)

    ordem_colunas = []

    for campo, direcao in sort_items:
        if campo == "nome":
            ordem_colunas.append(Product.nome.asc() if direcao == "asc" else Product.nome.desc())
        elif campo == "preco":
            ordem_colunas.append(Product.preco.asc() if direcao == "asc" else Product.preco.desc())
        elif campo == "estoque":
            ordem_colunas.append(Product.estoque.asc() if direcao == "asc" else Product.estoque.desc())
        elif campo == "categoria":
            ordem_colunas.append(Category.nome.asc() if direcao == "asc" else Category.nome.desc())
        elif campo == "p_custo":
            ordem_colunas.append(Product.p_custo.asc() if direcao == "asc" else Product.p_custo.desc())

    if not ordem_colunas:
        ordem_colunas = [Product.id.desc()]

    pagination = query.order_by(*ordem_colunas).paginate(
        page=page,
        per_page=12,
        error_out=False
    )

    build_sort_url = lambda campo: toggle_sort(sort, campo)

    return render_template(
        "products/list.html",
        products=pagination.items,
        pagination=pagination,
        search=search,
        sort=sort,
        sort_map=sort_map,
        build_sort_url=build_sort_url,
    )

# -- CREATE --
@bp.route("/novo", methods=["GET", "POST"])
def create_product():
    categorias = Category.query.order_by(Category.nome.asc()).all()

    if request.method == "POST":
        try:
            nome = request.form.get("nome", "").strip()
            descricao = request.form.get("descricao", "").strip()
            p_custo = Decimal(request.form["p_custo"].replace(",", "."))
            preco = Decimal(request.form["preco"].replace(",", "."))
            lucro = preco - p_custo
            estoque = int(request.form.get("estoque", 1))

            category_id = request.form.get("category_id")
            category_id = int(category_id) if category_id else None

            ativo = "ativo" in request.form

            if not nome:
                flash("Informe o nome do produto.", "danger")
                return render_template(
                    "products/form.html",
                    product=None,
                    categorias=categorias
                )

            imagem = None
            imagem_file = request.files.get("imagem")

            if imagem_file and imagem_file.filename:
                imagem = salvar_imagem_produto(
                    imagem_file,
                    current_app.config["PRODUCT_UPLOAD_DIR"]
                )

            product = Product(
                nome=nome,
                descricao=descricao,
                p_custo=p_custo,
                preco=preco,
                lucro=lucro,
                estoque=estoque,
                category_id=category_id,
                imagem=imagem,
                ativo=ativo
            )

            db.session.add(product)
            db.session.commit()

            flash("Produto salvo com sucesso.", "success")
            return redirect(url_for("products.list_products"))

        except ValueError as e:
            db.session.rollback()
            flash(str(e), "danger")

        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao salvar produto: {e}", "danger")

    return render_template(
        "products/form.html",
        product=None,
        categorias=categorias
    )

# -- UPDATE --
@bp.route("/<int:product_id>/editar", methods=["GET", "POST"])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    categorias = Category.query.order_by(Category.nome.asc()).all()

    if request.method == "POST":
        try:
            nome = request.form.get("nome", "").strip()
            descricao = request.form.get("descricao", "").strip()
            p_custo = Decimal(request.form["p_custo"].replace(",", "."))
            preco = Decimal(request.form["preco"].replace(",", "."))
            lucro = preco - p_custo
            estoque = int(request.form.get("estoque", 0))

            category_id = request.form.get("category_id")
            category_id = int(category_id) if category_id else None

            ativo = "ativo" in request.form

            if not nome:
                flash("Informe o nome do produto.", "danger")
                return render_template(
                    "products/form.html",
                    product=product,
                    categorias=categorias
                )

            imagem_file = request.files.get("imagem")

            if imagem_file and imagem_file.filename:
                if product.imagem:
                    remover_imagem_produto(
                        product.imagem,
                        current_app.config["PRODUCT_UPLOAD_DIR"]
                    )

                product.imagem = salvar_imagem_produto(
                    imagem_file,
                    current_app.config["PRODUCT_UPLOAD_DIR"]
                )

            product.nome = nome
            product.descricao = descricao
            product.p_custo = p_custo
            product.preco = preco
            product.lucro = lucro
            product.estoque = estoque
            product.category_id = category_id
            product.ativo = ativo

            db.session.commit()

            flash("Produto atualizado com sucesso.", "success")
            return redirect(url_for("products.list_products"))

        except ValueError as e:
            db.session.rollback()
            flash(str(e), "danger")

        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar produto: {e}", "danger")

    return render_template(
        "products/form.html",
        product=product,
        categorias=categorias
    )

# -- DELETE --
@bp.route('/<int:product_id>/excluir', methods=['POST'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)

    try:
        if product.imagem:
            remover_imagem_produto(
                product.imagem,
                current_app.config["PRODUCT_UPLOAD_DIR"]
            )

        db.session.delete(product)
        db.session.commit()
        flash('Produto excluído com sucesso.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir produto: {e}', 'danger')

    return redirect(url_for('products.list_products'))

# -- SEARCH PRODUCTS --
@bp.route('/busca')
def search_products():
    q = request.args.get('q', '').strip()

    if not q:
        return jsonify([])

    products = (
        Product.query
        .filter(Product.ativo == True, Product.nome.ilike(f'%{q}%'))
        .order_by(Product.nome.asc())
        .limit(8)
        .all()
    )

    results = [
        {
            'id': product.id,
            'nome': product.nome,
            'preco': float(product.preco),
            'estoque': product.estoque,
            'categoria': product.categoria.nome if product.categoria else '',
        }
        for product in products
    ]

    return jsonify(results)