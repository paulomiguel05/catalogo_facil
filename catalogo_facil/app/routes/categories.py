from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from sqlalchemy import func
from app.extensions import db
from ..models.category import Category
from ..utils import parse_sort, toggle_sort

bp = Blueprint('categories', __name__, url_prefix='/categorias')

# -- LIST --
@bp.route("/")
def list_categories():
    search = request.args.get("search", "").strip()
    sort = request.args.get("sort", "").strip()
    page = request.args.get("page", 1, type=int)

    sort_items, sort_map = parse_sort(sort)
    query = Category.query

    if search:
        query = query.filter(Category.nome.ilike(f"%{search}%"))

    ordem_colunas = []

    for campo, direcao in sort_items:
        if campo == "nome":
            ordem_colunas.append(
                Category.nome.asc() if direcao == "asc" else Category.nome.desc()
            )

    if not ordem_colunas:
        ordem_colunas = [Category.id.desc()]

    pagination = query.order_by(*ordem_colunas).paginate(
        page=page,
        per_page=10,
        error_out=False
    )

    build_sort_url = lambda campo: toggle_sort(sort, campo)

    return render_template(
        "categories/list.html",
        categories=pagination.items,
        pagination=pagination,
        search=search,
        sort=sort,
        sort_map=sort_map,
        build_sort_url=build_sort_url,
    )


# -- CREATE --
@bp.route('/nova', methods=['GET', 'POST'])
def create_category():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()

        if not nome:
            flash('O nome da categoria é obrigatório.', 'error')
            return render_template('categories/form.html', category=None)

        categoria_existente = Category.query.filter(
            func.lower(Category.nome) == nome.lower()
        ).first()

        if categoria_existente:
            flash('Essa categoria já existe.', 'error')
            return render_template('categories/form.html', category=None)

        category = Category(nome=nome)
        db.session.add(category)
        
        try:
            db.session.commit()
            flash('Categoria cadastrada com sucesso.', 'success')
        except Exception:
            db.session.rollback()
            flash('Erro ao cadastrar categoria. ⚠️', 'error')

        return redirect(url_for('categories.list_categories'))

    return render_template('categories/form.html', category=None)

# -- DETAIL --
@bp.route('/<int:category_id>')
def detail_category(category_id):
    category = Category.query.get_or_404(category_id)
    return render_template('categories/detail.html', category=category)

# -- UPDATE --
@bp.route('/<int:category_id>/editar', methods=['GET', 'POST'])
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()

        if not nome:
            flash('O nome da categoria é obrigatório.', 'error')
            return render_template('categories/form.html', category=category)

        categoria_existente = Category.query.filter(
            func.lower(Category.nome) == nome.lower(),
            Category.id != category.id
        ).first()

        if categoria_existente:
            flash('Já existe outra categoria com esse nome.', 'error')
            return render_template('categories/form.html', category=category)

        category.nome = nome

        try:
            db.session.commit()
            flash('Categoria atualizada com sucesso.', 'success')
        except Exception:
            db.session.rollback()
            flash('Erro ao atualizar categoria. ⚠️', 'error')

        return redirect(url_for('categories.list_categories'))

    return render_template('categories/form.html', category=category)

# -- REMOVE PRODUCTS FROM CATEGORY --
@bp.route('/<int:category_id>/remover-produtos', methods=['POST'])
def remove_products_from_category(category_id):
    
    category = Category.query.get_or_404(category_id)

    product_ids = request.form.getlist('product_ids')

    if not product_ids:
        flash('Selecione ao menos um produto para remover da categoria.', 'error')
        return redirect(url_for('categories.detail_category', category_id=category.id))

    produtos_removidos = 0

    for product_id in product_ids:
        try:
            product_id = int(product_id)
        except ValueError:
            continue

        product = next((p for p in category.produtos if p.id == product_id), None)

        if product:
            product.category_id = None
            produtos_removidos += 1

    db.session.commit()

    if produtos_removidos:
        flash('Produto(s) removido(s) da categoria com sucesso.', 'success')
    else:
        flash('Nenhum produto válido foi removido. ⚠️', 'error')

    return redirect(url_for('categories.detail_category', category_id=category.id))

# -- DELETE --
@bp.route('/<int:category_id>/excluir', methods=['POST'])
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)

    try:
        for product in list(category.produtos):
            product.category_id = None

        db.session.delete(category)
        db.session.commit()

        flash('Categoria deletada com sucesso. ⚠️ Os produtos que estavam nela ficaram sem categoria. ⚠️', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir categoria: {e} ⚠️', 'danger')

    return redirect(url_for('categories.list_categories'))

# -- SEARCH CATEGORIES --
@bp.route('/busca')
def search_categories():
    q = request.args.get('q', '').strip()

    if not q:
        return jsonify([])

    categories = (
        Category.query
        .filter(Category.nome.ilike(f'%{q}%'))
        .order_by(Category.nome.asc())
        .limit(8)
        .all()
    )

    results = [
        {
            'id': category.id,
            'nome': category.nome,
        }
        for category in categories
    ]

    return jsonify(results)
