import re

# -- Email --
def normalizar_email(valor: str | None) -> str | None:
    if not valor:
        return None

    valor = valor.strip().lower()

    return valor or None

# -- Facebook --
def normalizar_link_facebook(valor: str | None) -> str | None:
    if not valor:
        return None

    valor = valor.strip()

    if not valor:
        return None

    return valor.rstrip("/")

# -- Instagram --
def link_instagram(handle: str | None) -> str | None:
    if not handle:
        return None
    return f"https://www.instagram.com/{handle}"

def normalizar_instagram(valor: str | None) -> str | None:
    if not valor:
        return None

    valor = valor.strip()

    if not valor:
        return None

    if valor.startswith("@"):
        valor = valor[1:]

    valor = valor.rstrip("/")

    valor = re.sub(
        r"^https?://(www\.)?instagram\.com/",
        "",
        valor,
        flags=re.IGNORECASE
    )

    if "/" in valor:
        valor = valor.split("/")[0].strip()

    return valor

def texto_exibicao_instagram(handle: str | None) -> str | None:
    if not handle:
        return None
    return f"@{handle}"

# -- Telefone --
def formatar_telefone_visual(numero):
    numero_limpo = re.sub(r'\D', '', numero or '')

    # Se vier com 55 na frente, remove para exibir ao usuário
    if len(numero_limpo) == 13 and numero_limpo.startswith('55'):
        numero_limpo = numero_limpo[2:]

    if len(numero_limpo) == 11:
        return f'({numero_limpo[:2]}) {numero_limpo[2:7]}-{numero_limpo[7:]}'

    return numero or ''

def gerar_link_whatsapp(numero: str | None) -> str | None:
    if not numero:
        return None

    numero_limpo = "".join(char for char in numero if char.isdigit())

    if not numero_limpo:
        return None

    if not numero_limpo.startswith("55"):
        numero_limpo = f"55{numero_limpo}"

    return f"https://wa.me/{numero_limpo}"

def normalizar_numero(numero):
    numero = "".join(filter(str.isdigit, str(numero or "")))

    if not numero:
        return ""

    while numero.startswith("0"):
        numero = numero[1:]

    if len(numero) in (12, 13) and numero.startswith("55"):
        return numero

    if len(numero) in (10, 11):
        return "55" + numero
    
    return numero

# -- Outros --

def formatar_valor_brl(valor):
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def valor_atividade(atividade):
    dias = {
        0: "Segunda",
        1: "Terça",
        2: "Quarta",
        3: "Quinta",
        4: "Sexta",
        5: "Sábado",
        6: "Domingo",
    }

    return [dias[dia] for dia in atividade if dia in dias]