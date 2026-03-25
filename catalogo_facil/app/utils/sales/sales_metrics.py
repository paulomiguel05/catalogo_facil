from collections import defaultdict
from decimal import Decimal

DIAS_SEMANA = {
    0: "Segunda-feira",
    1: "Terça-feira",
    2: "Quarta-feira",
    3: "Quinta-feira",
    4: "Sexta-feira",
    5: "Sábado",
    6: "Domingo",
}

# Calculos para gerar resultados e graficos para PDF 
def calcular_melhor_categoria(sales, criterio="quantidade"):
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
        return None

    if criterio == "faturamento":
        nome_categoria, dados = max(
            categorias.items(),
            key=lambda x: (x[1]["faturamento"], x[1]["quantidade"])
        )
    else:
        nome_categoria, dados = max(
            categorias.items(),
            key=lambda x: (x[1]["quantidade"], x[1]["faturamento"])
        )

    return {
        "nome": nome_categoria,
        "quantidade": dados["quantidade"],
        "faturamento": dados["faturamento"],
        "criterio": criterio,
    }

def calcular_melhor_dia(sales):
    """
    Retorna o dia (data) com maior faturamento.
    """
    dias = defaultdict(lambda: {
        "faturamento": Decimal("0.00"),
        "lucro": Decimal("0.00"),
        "vendas": 0,
    })

    for sale in sales:
        data_venda = sale.data.date()

        dias[data_venda]["faturamento"] += Decimal(sale.total or 0)
        dias[data_venda]["lucro"] += Decimal(sale.lucro or 0)
        dias[data_venda]["vendas"] += 1

    if not dias:
        return None

    data, dados = max(
        dias.items(),
        key=lambda x: (x[1]["faturamento"], x[1]["vendas"])
    )

    return {
        "data": data,
        "faturamento": dados["faturamento"],
        "lucro": dados["lucro"],
        "vendas": dados["vendas"],
    }

def calcular_melhor_dia_semana(sales, dias_funcionamento=None):
    """
    Retorna o melhor dia da semana considerando apenas os dias em que a loja funciona.
    dias_funcionamento deve ser uma lista de inteiros no padrão weekday():
    0=segunda, 1=terça, ..., 6=domingo
    """
    if dias_funcionamento is None:
        dias_funcionamento = [0, 1, 2, 3, 4, 5, 6]

    dias_validos = set(dias_funcionamento)

    dias_semana = defaultdict(lambda: {
        "faturamento": Decimal("0.00"),
        "lucro": Decimal("0.00"),
        "vendas": 0,
    })

    for sale in sales:
        indice = sale.data.weekday()

        if indice not in dias_validos:
            continue

        dias_semana[indice]["faturamento"] += Decimal(sale.total or 0)
        dias_semana[indice]["lucro"] += Decimal(sale.lucro or 0)
        dias_semana[indice]["vendas"] += 1

    if not dias_semana:
        return None

    indice, dados = max(
        dias_semana.items(),
        key=lambda x: (x[1]["faturamento"], x[1]["vendas"])
    )

    return {
        "indice": indice,
        "nome": DIAS_SEMANA[indice],
        "faturamento": dados["faturamento"],
        "lucro": dados["lucro"],
        "vendas": dados["vendas"],
    }

def preparar_vendas_filtradas_por_categoria(sales, categoria=None):
    vendas_filtradas = []
    total_periodo = Decimal("0.00")
    lucro_periodo = Decimal("0.00")

    for sale in sales:
        if categoria:
            itens_relacionados = [
                item for item in sale.items
                if (item.categoria_produto or "Sem categoria").strip() == categoria
            ]
        else:
            itens_relacionados = list(sale.items)

        if not itens_relacionados:
            continue

        total_filtrado = sum(
            (Decimal(item.subtotal or 0) for item in itens_relacionados),
            Decimal("0.00")
        )

        lucro_filtrado = sum(
            (item.calcular_lucro() for item in itens_relacionados),
            Decimal("0.00")
        )

        # quantidade de linhas de item da categoria
        itens_filtrados = len(itens_relacionados)

        # atributos temporários só para exibição
        sale.total_filtrado = total_filtrado
        sale.lucro_filtrado = lucro_filtrado
        sale.itens_filtrados = itens_filtrados
        sale.itens_relacionados = itens_relacionados

        vendas_filtradas.append(sale)
        total_periodo += total_filtrado
        lucro_periodo += lucro_filtrado

    return vendas_filtradas, total_periodo, lucro_periodo