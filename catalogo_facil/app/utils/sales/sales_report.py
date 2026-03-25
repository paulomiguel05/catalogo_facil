from collections import defaultdict
from decimal import Decimal
from datetime import datetime, timedelta


DIAS_SEMANA = {
    0: "Seg",
    1: "Ter",
    2: "Qua",
    3: "Qui",
    4: "Sex",
    5: "Sáb",
    6: "Dom",
}

# Calculo de faturamento de categorias para gerar rankin e grafico.
def calcular_categorias(sales, criterio="faturamento"):
    categorias = defaultdict(lambda: {
        "quantidade": 0,
        "faturamento": Decimal("0.00"),
    })

    for sale in sales:
        for item in sale.items:
            categoria = (item.categoria_produto or "Sem categoria").strip()
            categorias[categoria]["quantidade"] += int(item.quantidade or 0)
            categorias[categoria]["faturamento"] += Decimal(item.subtotal or 0)

    if not categorias:
        return []

    resultado = []
    for nome, dados in categorias.items():
        resultado.append({
            "nome": nome,
            "quantidade": dados["quantidade"],
            "faturamento": dados["faturamento"],
            "valor": dados[criterio],
        })

    resultado.sort(key=lambda x: x["valor"], reverse=True)
    return resultado

# Calculo de comparação com semana passa para gerar grafico.
def dados_semana_atual_vs_anterior(sales, dias_funcionamento=None, referencia=None):
    if dias_funcionamento is None:
        dias_funcionamento = [0, 1, 2, 3, 4, 5, 6]

    if referencia is None:
        referencia = datetime.today().date()

    inicio_semana_atual = referencia - timedelta(days=referencia.weekday())
    fim_semana_atual = inicio_semana_atual + timedelta(days=6)

    inicio_semana_anterior = inicio_semana_atual - timedelta(days=7)
    fim_semana_anterior = inicio_semana_atual - timedelta(days=1)

    atual = {dia: Decimal("0.00") for dia in dias_funcionamento}
    anterior = {dia: Decimal("0.00") for dia in dias_funcionamento}

    for sale in sales:
        data = sale.data.date()
        dia_semana = data.weekday()

        if dia_semana not in dias_funcionamento:
            continue

        if inicio_semana_atual <= data <= fim_semana_atual:
            atual[dia_semana] += Decimal(sale.total or 0)
        elif inicio_semana_anterior <= data <= fim_semana_anterior:
            anterior[dia_semana] += Decimal(sale.total or 0)

    labels = [DIAS_SEMANA[d] for d in dias_funcionamento]
    valores_atual = [float(atual[d]) for d in dias_funcionamento]
    valores_anterior = [float(anterior[d]) for d in dias_funcionamento]

    return {
        "labels": labels,
        "semana_atual": valores_atual,
        "semana_anterior": valores_anterior,
        "inicio_semana_atual": inicio_semana_atual,
        "fim_semana_atual": fim_semana_atual,
        "inicio_semana_anterior": inicio_semana_anterior,
        "fim_semana_anterior": fim_semana_anterior,
    }