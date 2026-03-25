import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# -- Transforma figuras do matplotlib em img --
def _fig_to_buffer(fig):
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight", dpi=180)
    buffer.seek(0)
    plt.close(fig)
    return buffer

# Geradores de graficos para PDF 
def gerar_grafico_pizza_categorias(categorias, titulo="Categorias"):
    if not categorias:
        return None

    categorias = categorias[:7]
    labels = [c["nome"] for c in categorias]
    values = [float(c["valor"]) for c in categorias]

    if not any(values):
        return None

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.set_title(titulo)
    ax.axis("equal")

    return _fig_to_buffer(fig)


def gerar_grafico_colunas_semana(dados_semana, titulo="Semana atual vs anterior"):
    labels = dados_semana.get("labels", [])
    semana_atual = dados_semana.get("semana_atual", [])
    semana_anterior = dados_semana.get("semana_anterior", [])

    if not labels:
        return None

    x = list(range(len(labels)))
    largura = 0.35

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar([i - largura / 2 for i in x], semana_anterior, largura, label="Semana anterior")
    ax.bar([i + largura / 2 for i in x], semana_atual, largura, label="Semana atual")

    ax.set_title(titulo)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Faturamento")
    ax.legend()

    return _fig_to_buffer(fig)