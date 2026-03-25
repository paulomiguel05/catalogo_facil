from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import inspect

from app.extensions import db
from app.models import Shop
from app.utils import (
    formatar_telefone_visual,
    normalizar_email,
    normalizar_instagram,
    normalizar_link_facebook,
    normalizar_numero,
    validar_email,
    validar_instagram,
    validar_link_facebook,
) 

bp = Blueprint("shops", __name__, url_prefix="/loja")

def tabela_shop_existe():
    return inspect(db.engine).has_table("shop")

# -- CREATE / UPDATE -- 
@bp.route("/", methods=["GET", "POST"])
def manage_shop():
    shop = Shop.query.first() if tabela_shop_existe() else None

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        numero = normalizar_numero(request.form.get("numero", ""))
        atividade = request.form.getlist("atividade[]")
        instagram = normalizar_instagram(request.form.get("instagram", ""))
        facebook = normalizar_link_facebook(request.form.get("facebook", ""))
        email = normalizar_email(request.form.get("email", ""))

        if not nome:
            flash("Informe o nome da loja.", "error")
            return render_template(
                "shops/form.html",
                shop=shop,
                formatar_telefone_visual=formatar_telefone_visual,
            )

        if not numero:
            flash("Informe o número da loja.", "error")
            return render_template(
                "shops/form.html",
                shop=shop,
                formatar_telefone_visual=formatar_telefone_visual,
            )

        if not atividade:
            flash("Selecione pelo menos um dia de funcionamento.", "error")
            return render_template(
                "shops/form.html",
                shop=shop,
                formatar_telefone_visual=formatar_telefone_visual,
            )

        try:
            atividade = sorted(set(int(dia) for dia in atividade))
        except ValueError:
            flash("Dias de atividade inválidos.", "error")
            return render_template(
                "shops/form.html",
                shop=shop,
                formatar_telefone_visual=formatar_telefone_visual,
            )

        try:
            validar_instagram(instagram)
            validar_link_facebook(facebook)
            validar_email(email)
        except ValueError as e:
            flash(str(e), "error")
            return render_template(
                "shops/form.html",
                shop=shop,
                formatar_telefone_visual=formatar_telefone_visual,
            )

        try:
            if shop:
                shop.nome = nome
                shop.numero = numero
                shop.instagram = instagram
                shop.facebook = facebook
                shop.email = email
                shop.atividade = atividade
                flash("Loja atualizada com sucesso.", "success")
            else:
                shop = Shop(
                    nome=nome,
                    numero=numero,
                    instagram=instagram,
                    facebook=facebook,
                    email=email,
                    atividade=atividade,
                )
                db.session.add(shop)
                flash("Loja cadastrada com sucesso.", "success")

            db.session.commit()
            return redirect(url_for("main.home"))

        except Exception as e:
            db.session.rollback()
            print(e)
            flash("Erro ao salvar os dados da loja.", "error")

    return render_template(
        "shops/form.html",
        shop=shop,
        formatar_telefone_visual=formatar_telefone_visual,
    )

# -- JOIN EFECTS --
@bp.before_app_request
def exigir_loja_cadastrada():
    if not request.endpoint:
        return

    rotas_liberadas = {
        "shops.manage_shop",
        "static",
    }

    if request.endpoint in rotas_liberadas:
        return
    
    if not tabela_shop_existe():
        return

    shop = Shop.query.first()
    if not shop:
        flash("Cadastre os dados da sua loja antes de continuar.", "warning")
        return redirect(url_for("shops.manage_shop"))