from decimal import Decimal, InvalidOperation
from urllib.parse import quote
from io import BytesIO
from flask import Blueprint, flash, redirect, render_template, request,send_file, url_for
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from datetime import datetime, time

from app.extensions import db
from ..models import Client, Product, Sale, SaleItem, Shop, Category
from ..utils import (
    calcular_melhor_categoria,
    calcular_melhor_dia,
    calcular_melhor_dia_semana,
    calcular_categorias,
    parse_sort,
    toggle_sort,
    dados_semana_atual_vs_anterior,
    gerar_grafico_pizza_categorias,
    gerar_grafico_colunas_semana,
    mensagem_cobranca,
    preparar_vendas_filtradas_por_categoria, )

bp = Blueprint("sales", __name__, url_prefix="/vendas")

# -- LIST --
@bp.route("/")
def list_sales():
    search = request.args.get("search", "").strip()
    sort = request.args.get("sort", "").strip()
    page = request.args.get("page", 1, type=int)

    sort_items, sort_map = parse_sort(sort)
    query = Sale.query

    if search:
        query = query.outerjoin(Client, Sale.client_id == Client.id).filter(
            or_(
                Client.nome.ilike(f"%{search}%"),
                Client.numero.ilike(f"%{search}%"),
                Sale.status.ilike(f"%{search}%"),
            )
        )

    join_cliente = any(campo == "nome_cliente" for campo, _ in sort_items)
    if join_cliente and not search:
        query = query.outerjoin(Client, Sale.client_id == Client.id)

    ordem_colunas = []

    for campo, direcao in sort_items:
        if campo == "nome_cliente":
            ordem_colunas.append(
                Client.nome.asc() if direcao == "asc" else Client.nome.desc()
            )
        elif campo == "data":
            ordem_colunas.append(
                Sale.data.asc() if direcao == "asc" else Sale.data.desc()
            )
        elif campo == "status":
            ordem_colunas.append(
                Sale.status.asc() if direcao == "asc" else Sale.status.desc()
            )
        elif campo == "total":
            ordem_colunas.append(
                Sale.total.asc() if direcao == "asc" else Sale.total.desc()
            )
        elif campo == "lucro":
            ordem_colunas.append(
                Sale.lucro.asc() if direcao == "asc" else Sale.lucro.desc()
            )

    if not ordem_colunas:
        ordem_colunas = [Sale.id.desc()]

    pagination = query.order_by(*ordem_colunas).paginate(
        page=page,
        per_page=10,
        error_out=False,
    )

    build_sort_url = lambda campo: toggle_sort(sort, campo)

    return render_template(
        "sales/list.html",
        sales=pagination.items,
        pagination=pagination,
        search=search,
        sort=sort,
        sort_map=sort_map,
        build_sort_url=build_sort_url,
    )

# -- DETAIL --
@bp.route("/<int:sale_id>")
def detail_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    return render_template("sales/detail.html", sale=sale)

# -- CREATE --
@bp.route("/nova", methods=["GET", "POST"])
def create_sale():
    products = Product.query.filter_by(ativo=True).order_by(Product.nome.asc()).all()

    if request.method == "POST":
        client_id = request.form.get("client_id", "").strip()
        status = request.form.get("status", "pendente").strip().lower()

        product_ids = request.form.getlist("product_id[]")
        quantidades = request.form.getlist("quantidade[]")
        precos_unitarios = request.form.getlist("preco_unitario[]")

        if status not in ["pago", "pendente"]:
            status = "pendente"

        if client_id:
            try:
                client_id = int(client_id)
            except ValueError:
                flash("Cliente inválido.", "error")
                return render_template("sales/form.html", products=products)

            client = Client.query.get(client_id)
            if not client:
                flash("Cliente não encontrado.", "error")
                return render_template("sales/form.html", products=products)
        else:
            client_id = None

        if not product_ids:
            flash("Adicione ao menos um item à venda.", "error")
            return render_template("sales/form.html", products=products)

        sale = Sale(
            client_id=client_id,
            total=Decimal("0.00"),
            lucro=Decimal("0.00"),
            status=status,
        )
        db.session.add(sale)
        db.session.flush()

        total = Decimal("0.00")
        lucro_total = Decimal("0.00")
        added_items = 0

        for product_id, quantidade, preco_unitario in zip(
            product_ids, quantidades, precos_unitarios
        ):
            product_id = (product_id or "").strip()
            quantidade = (quantidade or "").strip()
            preco_unitario = (preco_unitario or "").strip().replace(",", ".")

            if not product_id:
                continue

            try:
                product_id = int(product_id)
            except ValueError:
                db.session.rollback()
                flash("Produto inválido.", "error")
                return render_template("sales/form.html", products=products)

            try:
                quantidade = int(quantidade or 0)
            except ValueError:
                db.session.rollback()
                flash("Quantidade inválida.", "error")
                return render_template("sales/form.html", products=products)

            try:
                preco_unitario = Decimal(preco_unitario or "0")
            except (InvalidOperation, ValueError):
                db.session.rollback()
                flash("Preço unitário inválido.", "error")
                return render_template("sales/form.html", products=products)

            if quantidade <= 0:
                continue

            product = Product.query.get(product_id)

            if not product or not product.ativo:
                db.session.rollback()
                flash("Um dos produtos selecionados é inválido ou está inativo.", "error")
                return render_template("sales/form.html", products=products)

            if quantidade > product.estoque:
                db.session.rollback()
                flash(f'Estoque insuficiente para o produto "{product.nome}".', "error")
                return render_template("sales/form.html", products=products)

            custo_unitario = Decimal(str(product.p_custo))
            subtotal = Decimal(quantidade) * preco_unitario
            lucro_item = subtotal - (Decimal(quantidade) * custo_unitario)

            product.estoque -= quantidade

            item = SaleItem(
                sale_id=sale.id,
                product_id=product.id,
                quantidade=quantidade,
                nome_produto=product.nome,
                preco_unitario=preco_unitario,
                custo_unitario=custo_unitario,
                categoria_produto=product.categoria.nome if product.categoria else "Sem categoria",
                subtotal=subtotal,
            )

            db.session.add(item)
            total += subtotal
            lucro_total += lucro_item
            added_items += 1

        if added_items == 0:
            db.session.rollback()
            flash("Selecione ao menos um item válido para a venda.", "error")
            return render_template("sales/form.html", products=products)

        sale.total = total
        sale.lucro = lucro_total
        db.session.commit()

        flash("Venda registrada com sucesso.", "success")
        return redirect(url_for("sales.list_sales"))

    return render_template("sales/form.html", products=products)

# -- MARK AS PAID --
@bp.route("/<int:sale_id>/marcar-pago", methods=["POST"])
def mark_sale_as_paid(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    sale.status = "pago"
    db.session.commit()

    flash("Venda marcada como paga.", "success")
    return redirect(url_for("sales.list_sales"))

# -- WHATSAPP CHARGE --
@bp.route("/<int:sale_id>/cobranca-whatsapp")
def send_whatsapp_charge(sale_id):
    sale = Sale.query.get_or_404(sale_id)

    if not sale.client:
        flash("Essa venda não possui cliente vinculado.", "error")
        return redirect(url_for("sales.list_sales"))

    numero = sale.client.numero or ""

    if not numero:
        flash("Cliente sem número válido para cobrança.", "error")
        return redirect(url_for("sales.list_sales"))

    mensagem = mensagem_cobranca(sale)
    link = f"https://wa.me/{numero}?text={quote(mensagem)}"

    return redirect(link)

# -- DELETE --
@bp.route("/<int:sale_id>/excluir", methods=["POST"])
def delete_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)

    for item in sale.items:
        if item.product:
            item.product.estoque += item.quantidade

    db.session.delete(sale)
    db.session.commit()

    flash("Venda cancelada com sucesso.", "success")
    return redirect(url_for("sales.list_sales"))

# -- CONSULT --
@bp.route("/consulta", methods=["GET"])
def consult_sales():
    hoje = datetime.today()
    primeiro_dia_mes = hoje.replace(day=1).date()

    data_inicial = request.args.get(
        "data_inicial", primeiro_dia_mes.strftime("%Y-%m-%d")
    ).strip()

    data_final = request.args.get(
        "data_final", hoje.date().strftime("%Y-%m-%d")
    ).strip()

    categoria = request.args.get("categoria", "").strip()
    categorias = Category.query.order_by(Category.nome.asc()).all()

    sales = []
    searched = True
    total_periodo = Decimal("0.00")
    lucro_periodo = Decimal("0.00")
    quantidade_vendas = 0
    data_geracao = datetime.now()

    melhor_categoria_fat = None
    melhor_categoria_qtd = None
    melhor_dia = None
    melhor_dia_semana = None

    try:
        query = Sale.query.options(
            joinedload(Sale.items),
            joinedload(Sale.client),
        )

        if data_inicial:
            data_inicial_dt = datetime.combine(
                datetime.strptime(data_inicial, "%Y-%m-%d").date(),
                time.min,
            )
            query = query.filter(Sale.data >= data_inicial_dt)

        if data_final:
            data_final_dt = datetime.combine(
                datetime.strptime(data_final, "%Y-%m-%d").date(),
                time.max,
            )
            query = query.filter(Sale.data <= data_final_dt)

        sales = query.order_by(Sale.data.desc()).all()

        sales, total_periodo, lucro_periodo = preparar_vendas_filtradas_por_categoria(
            sales,
            categoria if categoria else None
        )

        quantidade_vendas = len(sales)

        melhor_categoria_qtd = calcular_melhor_categoria(sales, "quantidade")
        melhor_categoria_fat = calcular_melhor_categoria(sales, "faturamento")
        melhor_dia = calcular_melhor_dia(sales)

        loja = Shop.query.first()
        dias_funcionamento = (
            loja.atividade if loja and loja.atividade else [0, 1, 2, 3, 4, 5, 6]
        )

        melhor_dia_semana = calcular_melhor_dia_semana(sales, dias_funcionamento)

    except ValueError:
        flash("Informe datas válidas para a consulta.", "error")
        sales = []
        quantidade_vendas = 0
        total_periodo = Decimal("0.00")
        lucro_periodo = Decimal("0.00")
        melhor_categoria_qtd = None
        melhor_categoria_fat = None
        melhor_dia = None
        melhor_dia_semana = None

    return render_template(
        "sales/search.html",
        sales=sales,
        data_inicial=data_inicial,
        data_final=data_final,
        categoria=categoria,
        categorias=categorias,
        searched=searched,
        total_periodo=total_periodo,
        lucro_periodo=lucro_periodo,
        quantidade_vendas=quantidade_vendas,
        data_geracao=data_geracao,
        melhor_categoria_fat=melhor_categoria_fat,
        melhor_categoria_qtd=melhor_categoria_qtd,
        melhor_dia=melhor_dia,
        melhor_dia_semana=melhor_dia_semana,
    )

# -- PDF CONSULT -- 
@bp.route("/report/pdf")
def export_sales_report_pdf():
    hoje = datetime.today()
    primeiro_dia_mes = hoje.replace(day=1).date()

    data_inicial = request.args.get(
        "data_inicial", primeiro_dia_mes.strftime("%Y-%m-%d")
    ).strip()

    data_final = request.args.get(
        "data_final", hoje.date().strftime("%Y-%m-%d")
    ).strip()

    try:
        query = Sale.query.options(joinedload(Sale.items))

        if data_inicial:
            data_inicial_dt = datetime.combine(
                datetime.strptime(data_inicial, "%Y-%m-%d").date(),
                time.min,
            )
            query = query.filter(Sale.data >= data_inicial_dt)

        if data_final:
            data_final_dt = datetime.combine(
                datetime.strptime(data_final, "%Y-%m-%d").date(),
                time.max,
            )
            query = query.filter(Sale.data <= data_final_dt)

        sales = query.order_by(Sale.data.desc()).all()

        total_periodo = sum((sale.total for sale in sales), Decimal("0.00"))
        lucro_periodo = sum((sale.lucro for sale in sales), Decimal("0.00"))
        quantidade_vendas = len(sales)

        loja = Shop.query.first()
        dias_funcionamento = (
            loja.atividade if loja and loja.atividade else [0, 1, 2, 3, 4, 5, 6]
        )

        categorias_fat = calcular_categorias(sales, criterio="faturamento")
        categorias_qtd = calcular_categorias(sales, criterio="quantidade")
        dados_semana = dados_semana_atual_vs_anterior(
            sales,
            dias_funcionamento=dias_funcionamento
        )

        grafico_pizza = gerar_grafico_pizza_categorias(
            categorias_fat,
            titulo="Categorias por faturamento"
        )

        grafico_pizza_qtd = gerar_grafico_pizza_categorias(
            categorias_qtd,
            titulo="Categorias por quantidade"
        )

        grafico_colunas = gerar_grafico_colunas_semana(
            dados_semana,
            titulo="Semana atual x Semana anterior"
        )

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)

        largura, altura = A4
        y = altura - 50

        def nova_pagina_se_precisar(y_atual, espaco=80):
            if y_atual < espaco:
                pdf.showPage()
                pdf.setFont("Helvetica", 11)
                return altura - 50
            return y_atual

        def limitar_texto(texto, max_chars=35):
            texto = str(texto or "")
            if len(texto) <= max_chars:
                return texto
            return texto[:max_chars - 3] + "..."

        pdf.setTitle("Relatório de Vendas")

        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(40, y, "Relatório de Vendas")
        y -= 28

        pdf.setFont("Helvetica", 11)
        pdf.drawString(40, y, f"Período: {data_inicial} até {data_final}")
        y -= 18
        pdf.drawString(40, y, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        y -= 18

        if loja and getattr(loja, "nome", None):
            pdf.drawString(40, y, f"Loja: {loja.nome}")
            y -= 18

        y -= 10

        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(40, y, "Resumo")
        y -= 18

        pdf.setFont("Helvetica", 11)
        pdf.drawString(40, y, f"Quantidade de vendas: {quantidade_vendas}")
        y -= 16
        pdf.drawString(40, y, f"Faturamento do período: R$ {total_periodo}")
        y -= 16
        pdf.drawString(40, y, f"Lucro do período: R$ {lucro_periodo}")
        y -= 24

        if categorias_fat:
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(40, y, "Top 10 categorias por faturamento")
            y -= 18

            pdf.setFont("Helvetica", 11)
            for i, categoria in enumerate(categorias_fat[:10], start=1):
                y = nova_pagina_se_precisar(y)

                linha = (
                    f'{i}º - {limitar_texto(categoria["nome"])} | '
                    f'Qtd: {categoria["quantidade"]} | '
                    f'Fat: R$ {categoria["faturamento"]}'
                )
                pdf.drawString(40, y, linha)
                y -= 16

            y -= 14

        if categorias_qtd:
            y = nova_pagina_se_precisar(y, espaco=120)

            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(40, y, "Top 10 categorias por quantidade vendida")
            y -= 18

            pdf.setFont("Helvetica", 11)
            for i, categoria in enumerate(categorias_qtd[:10], start=1):
                y = nova_pagina_se_precisar(y)

                linha = (
                    f'{i}º - {limitar_texto(categoria["nome"])} | '
                    f'Qtd: {categoria["quantidade"]} | '
                    f'Fat: R$ {categoria["faturamento"]}'
                )
                pdf.drawString(40, y, linha)
                y -= 16
        
            if grafico_pizza or grafico_pizza_qtd or grafico_colunas:
                pdf.showPage()

                def draw_centered_text(texto, y, font_name="Helvetica-Bold", font_size=15):
                    pdf.setFont(font_name, font_size)
                    text_width = pdf.stringWidth(texto, font_name, font_size)
                    x = (largura - text_width) / 2
                    pdf.drawString(x, y, texto)

                draw_centered_text("Gráficos do Relatório", altura - 45, "Helvetica-Bold", 15)

                faixa = (
                    f'{dados_semana["inicio_semana_anterior"].strftime("%d/%m/%Y")} a '
                    f'{dados_semana["fim_semana_atual"].strftime("%d/%m/%Y")}'
                )
                draw_centered_text(f"Faixa analisada: {faixa}", altura - 62, "Helvetica", 10)

                y_topo = altura - 95

                if grafico_pizza:
                    pdf.setFont("Helvetica-Bold", 11)
                    pdf.drawString(55, y_topo, "Categorias por faturamento")
                    pdf.drawImage(
                        ImageReader(grafico_pizza),
                        30,
                        y_topo - 210,
                        width=240,
                        height=190,
                        preserveAspectRatio=True,
                        mask="auto",
                    )

                if grafico_pizza_qtd:
                    pdf.setFont("Helvetica-Bold", 11)
                    pdf.drawString(315, y_topo, "Categorias por quantidade")
                    pdf.drawImage(
                        ImageReader(grafico_pizza_qtd),
                        300,
                        y_topo - 210,
                        width=240,
                        height=190,
                        preserveAspectRatio=True,
                        mask="auto",
                    )

                if grafico_colunas:
                    pdf.setFont("Helvetica-Bold", 11)
                    pdf.drawString(55, y_topo - 235, "Semana atual x Semana anterior")
                    pdf.drawImage(
                        ImageReader(grafico_colunas),
                        45,
                        y_topo - 470,
                        width=500,
                        height=210,
                        preserveAspectRatio=True,
                        mask="auto",
                    )

            pdf.save()
            buffer.seek(0)

            return send_file(
                buffer,
                mimetype="application/pdf",
                as_attachment=True,
                download_name=f"relatorio_vendas-{datetime.today().strftime('%d-%m-%Y')}.pdf",
            )

    except ValueError:
        flash("Informe datas válidas para a consulta.", "error")
        return redirect(url_for("sales.consult_sales"))

    except Exception as e:
        flash(f"Erro ao gerar PDF: {e}", "error")
        return redirect(url_for("sales.consult_sales"))