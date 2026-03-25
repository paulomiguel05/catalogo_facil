from app.utils.formatters import (
    normalizar_numero,
    formatar_telefone_visual,
    texto_exibicao_instagram,
    link_instagram,
    normalizar_instagram,
    normalizar_link_facebook,
    normalizar_email,
    gerar_link_whatsapp,
    formatar_valor_brl,
    valor_atividade
)

from app.utils.images import (
    imagem_para_base64,
    logo_para_base64,
    produto_para_base64,
    salvar_logo_catalogo,
    remover_logo_catalogo,
    salvar_imagem_produto,
    remover_imagem_produto
)

from app.utils.sorting import (
    parse_sort,
    toggle_sort
)

from app.utils.validators import (
    cpf_valido,
    validar_link_facebook,
    validar_instagram,
    validar_email
)

from app.utils.whatsapp import (
    mensagem_cobranca,
    renderizar_template_mensagem,
)

# -- Sales -- 

from app.utils.sales.sales_metrics import (
    calcular_melhor_categoria,
    calcular_melhor_dia,
    calcular_melhor_dia_semana,
    preparar_vendas_filtradas_por_categoria,
)

from app.utils.sales.sales_report import (
    calcular_categorias,
    dados_semana_atual_vs_anterior,
)

from app.utils.sales.sales_charts import (
    gerar_grafico_pizza_categorias,
    gerar_grafico_colunas_semana,
)

# -- Catalogo -- 

from app.utils.catalog_schemas import (
    COLOR_DEFAULTS,
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
)