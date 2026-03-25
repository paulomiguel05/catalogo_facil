import re
from datetime import datetime, timedelta
from urllib.parse import quote

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from sqlalchemy import func, or_

from app.extensions import db
from app.models import Client, Sale
from app.utils import (
    cpf_valido,
    formatar_telefone_visual,
    formatar_valor_brl,
    normalizar_numero,
    parse_sort,
    toggle_sort,
)

bp = Blueprint("clients", __name__, url_prefix="/clientes")


# -- LIST --
@bp.route("/")
def list_clients():
    search = request.args.get("search", "").strip()
    sort = request.args.get("sort", "").strip()
    page = request.args.get("page", 1, type=int)

    sort_items, sort_map = parse_sort(sort)

    pending_subquery = (
        db.session.query(
            Sale.client_id.label("client_id"),
            func.count(Sale.id).label("pending_count"),
        )
        .filter(Sale.status != "pago")
        .group_by(Sale.client_id)
        .subquery()
    )

    pending_count_col = func.coalesce(pending_subquery.c.pending_count, 0)

    query = (
        Client.query
        .outerjoin(pending_subquery, pending_subquery.c.client_id == Client.id)
        .add_columns(pending_count_col.label("pending_count"))
    )

    if search:
        query = query.filter(
            or_(
                Client.nome.ilike(f"%{search}%"),
                Client.numero.ilike(f"%{search}%"),
                Client.cpf.ilike(f"%{search}%"),
            )
        )

    ordem_colunas = []

    for campo, direcao in sort_items:
        if campo == "nome":
            coluna = Client.nome
        elif campo == "pagamentos":
            coluna = pending_count_col
        else:
            continue

        ordem_colunas.append(
            coluna.asc() if direcao == "asc" else coluna.desc()
        )

    if not ordem_colunas:
        ordem_colunas = [Client.id.desc()]

    pagination = query.order_by(*ordem_colunas).paginate(
        page=page,
        per_page=10,
        error_out=False,
    )

    build_sort_url = lambda campo: toggle_sort(sort, campo)

    return render_template(
        "clients/list.html",
        clients=pagination.items,
        pagination=pagination,
        search=search,
        sort=sort,
        sort_map=sort_map,
        build_sort_url=build_sort_url,
        formatar_telefone_visual=formatar_telefone_visual,
    )

# -- CREATE --
@bp.route("/novo", methods=["GET", "POST"])
def create_client():
    if request.method == "POST":
        try:
            nome = request.form.get("nome", "").strip()
            numero = request.form.get("numero", "").strip()
            cpf = request.form.get("cpf", "").strip()
            endereco = request.form.get("endereco", "").strip()

            if not nome:
                flash("O nome do cliente é obrigatório.", "error")
                return render_template(
                    "clients/form.html",
                    client=None,
                    formatar_telefone_visual=formatar_telefone_visual,
                )

            if not numero:
                flash("O número do cliente é obrigatório.", "error")
                return render_template(
                    "clients/form.html",
                    client=None,
                    formatar_telefone_visual=formatar_telefone_visual,
                )

            numero_normalizado = normalizar_numero(numero)
            if not numero_normalizado:
                flash("Telefone inválido. Digite DDD + número. Ex.: 11912345678", "error")
                return render_template(
                    "clients/form.html",
                    client=None,
                    formatar_telefone_visual=formatar_telefone_visual,
                )

            if cpf and not cpf_valido(cpf):
                flash("CPF inválido.", "error")
                return render_template(
                    "clients/form.html",
                    client=None,
                    formatar_telefone_visual=formatar_telefone_visual,
                )

            client = Client(
                nome=nome,
                numero=numero_normalizado,
                cpf="".join(filter(str.isdigit, cpf)) if cpf else None,
                endereco=endereco,
            )

            db.session.add(client)
            db.session.commit()

            flash("Cliente cadastrado com sucesso.", "success")
            return redirect(url_for("clients.list_clients"))

        except Exception:
            db.session.rollback()
            flash("Erro ao cadastrar cliente.", "error")

    return render_template(
        "clients/form.html",
        client=None,
        formatar_telefone_visual=formatar_telefone_visual,
    )

# -- UPDATE --
@bp.route("/<int:client_id>/editar", methods=["GET", "POST"])
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)

    if request.method == "POST":
        try:
            nome = request.form.get("nome", "").strip()
            numero = request.form.get("numero", "").strip()
            cpf = request.form.get("cpf", "").strip()
            endereco = request.form.get("endereco", "").strip()

            if not nome:
                flash("O nome do cliente é obrigatório.", "error")
                return render_template(
                    "clients/form.html",
                    client=client,
                    formatar_telefone_visual=formatar_telefone_visual,
                )

            if not numero:
                flash("O número do cliente é obrigatório.", "error")
                return render_template(
                    "clients/form.html",
                    client=client,
                    formatar_telefone_visual=formatar_telefone_visual,
                )

            numero_normalizado = normalizar_numero(numero)
            if not numero_normalizado:
                flash("Telefone inválido. Digite DDD + número. Ex.: 11912345678", "error")
                return render_template(
                    "clients/form.html",
                    client=client,
                    formatar_telefone_visual=formatar_telefone_visual,
                )

            if cpf and not cpf_valido(cpf):
                flash("CPF inválido.", "error")
                return render_template(
                    "clients/form.html",
                    client=client,
                    formatar_telefone_visual=formatar_telefone_visual,
                )

            client.nome = nome
            client.numero = numero_normalizado
            client.cpf = "".join(filter(str.isdigit, cpf)) if cpf else None
            client.endereco = endereco

            db.session.commit()

            flash("Cliente atualizado com sucesso.", "success")
            return redirect(url_for("clients.list_clients"))

        except Exception:
            db.session.rollback()
            flash("Erro ao atualizar cliente.", "error")

    return render_template(
        "clients/form.html",
        client=client,
        formatar_telefone_visual=formatar_telefone_visual,
    )

# -- DELETE --
@bp.route("/<int:client_id>/excluir", methods=["POST"])
def delete_client(client_id):
    client = Client.query.get_or_404(client_id)

    limite_data = datetime.now() - timedelta(days=90)
    possui_vendas_recentes = any(sale.data >= limite_data for sale in client.sales)

    if possui_vendas_recentes:
        flash(
            "Não é possível excluir um cliente que possui vendas registradas nos últimos 3 meses.",
            "error",
        )
        return redirect(url_for("clients.list_clients"))

    try:
        db.session.delete(client)
        db.session.commit()
        flash("Cliente excluído com sucesso.", "success")

    except Exception:
        db.session.rollback()
        flash("Erro ao excluir cliente.", "error")

    return redirect(url_for("clients.list_clients"))

# -- DETAIL / PURCHASE HISTORY --
@bp.route("/<int:client_id>")
def client_detail(client_id):
    client = Client.query.get_or_404(client_id)
    sales = sorted(client.sales, key=lambda sale: sale.data, reverse=True)

    return render_template(
        "clients/detail.html",
        client=client,
        sales=sales,
        formatar_telefone_visual=formatar_telefone_visual,
    )


# -- SEARCH CLIENTS --
@bp.route("/busca")
def search_clients():
    q = request.args.get("q", "").strip()

    if not q:
        return jsonify([])

    q_numeros = re.sub(r"\D", "", q)

    filtros = [Client.nome.ilike(f"%{q}%")]

    if q_numeros:
        filtros.append(Client.numero.ilike(f"%55{q_numeros}%"))
        filtros.append(Client.numero.ilike(f"%{q_numeros}%"))

    clients = (
        Client.query
        .filter(or_(*filtros))
        .order_by(Client.nome.asc())
        .limit(8)
        .all()
    )

    results = [
        {
            "id": client.id,
            "nome": client.nome,
            "numero": formatar_telefone_visual(client.numero),
            "cpf": client.cpf or "",
        }
        for client in clients
    ]

    return jsonify(results)


# -- WHATSAPP CHARGE --
@bp.route("/<int:client_id>/cobrar-total")
def send_whatsapp_total_charge(client_id):
    client = Client.query.get_or_404(client_id)

    pending_sales = [sale for sale in client.sales if sale.status != "pago"]
    total_pendente = sum(sale.total for sale in pending_sales)

    if not pending_sales:
        flash("Este cliente não possui pendências.", "info")
        return redirect(url_for("clients.client_detail", client_id=client.id))

    numero = re.sub(r"\D", "", client.numero or "")
    if not numero:
        flash("O cliente não possui número cadastrado.", "danger")
        return redirect(url_for("clients.client_detail", client_id=client.id))

    if not numero.startswith("55"):
        numero = f"55{numero}"

    linhas = "\n".join(
        [f"- Venda #{sale.id}: R$ {formatar_valor_brl(sale.total)}" for sale in pending_sales]
    )

    mensagem = (
        f"Olá, {client.nome}! Tudo bem?\n\n"
        f"Identificamos os seguintes valores em aberto:\n"
        f"{linhas}\n\n"
        f"Total pendente: R$ {formatar_valor_brl(total_pendente)}\n\n"
        f"Fico à disposição."
    )

    return redirect(f"https://wa.me/{numero}?text={quote(mensagem)}")