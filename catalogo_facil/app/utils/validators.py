import re

EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
INSTAGRAM_HANDLE_REGEX = re.compile(r"^[a-zA-Z0-9._]+$")
FACEBOOK_URL_REGEX = re.compile(r"^https?://(www\.)?(facebook\.com|fb\.com)/.+$",re.IGNORECASE)

# -- CPF --
def cpf_valido(cpf):

    # Remove tudo que não for número
    cpf = ''.join(filter(str.isdigit, cpf or ''))

    # Precisa ter 11 dígitos
    if len(cpf) != 11:
        return False

    # Rejeita CPFs com todos os dígitos iguais
    if cpf == cpf[0] * 11:
        return False

    # Validação do 1º dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digito_1 = (soma * 10) % 11
    digito_1 = 0 if digito_1 == 10 else digito_1

    if digito_1 != int(cpf[9]):
        return False

    # Validação do 2º dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digito_2 = (soma * 10) % 11
    digito_2 = 0 if digito_2 == 10 else digito_2

    if digito_2 != int(cpf[10]):
        return False

    return True

# -- Email --
def validar_email(valor: str | None) -> None:
    if not valor:
        return

    valor = valor.strip()

    if not EMAIL_REGEX.match(valor):
        raise ValueError("E-mail inválido. Informe um endereço de e-mail válido.")

# -- Facebook --
def validar_link_facebook(valor: str | None) -> str | None:
    if not valor:
        return

    if not FACEBOOK_URL_REGEX.match(valor):
        raise ValueError(
            "Link do Facebook inválido. Informe a URL completa do perfil ou página."
        )

# -- Instagram --
def validar_instagram(valor: str | None) -> None:
    if not valor:
        return

    if not INSTAGRAM_HANDLE_REGEX.match(valor):
        raise ValueError(
            "Instagram inválido. Use apenas letras, números, pontos e underscores."
        )

