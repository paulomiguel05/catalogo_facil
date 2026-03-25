from typing import Iterable

def mensagem_cobranca(sale):
    cliente_nome = sale.client.nome if sale.client else 'cliente'
    valor = f'{sale.total:.2f}'.replace('.', ',')
    data_venda = sale.data.strftime('%d/%m/%Y %H:%M')

    mensagem = (
        f'Olá, {cliente_nome}! '
        f'Estou entrando em contato sobre a venda registrada em {data_venda}. '
        f'O valor pendente é de R$ {valor}. '
        f'Quando possível, me confirme o pagamento. Aguardo!'
    )

    return mensagem

def renderizar_template_mensagem(mensagem_base: str, cliente) -> str:
    """
    Substitui placeholders simples no texto.
    Depois você pode expandir isso com mais campos.
    """
    mensagem = mensagem_base or ""

    substituicoes = {
        "{nome}": getattr(cliente, "nome", "") or "cliente",
    }

    for chave, valor in substituicoes.items():
        mensagem = mensagem.replace(chave, str(valor))

    return mensagem.strip()
