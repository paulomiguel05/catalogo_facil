import os
import base64
from io import BytesIO
from uuid import uuid4

from PIL import Image
from werkzeug.utils import secure_filename

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

# Tratamentos de imagem, update e delete.

def _salvar_imagem(file, upload_folder, prefixo):
    if not file or not file.filename:
        return ""

    filename = secure_filename(file.filename)

    if "." not in filename:
        raise ValueError("Arquivo inválido.")

    ext = filename.rsplit(".", 1)[1].lower()

    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError("Formato de imagem inválido. Use PNG, JPG, JPEG ou WEBP.")

    os.makedirs(upload_folder, exist_ok=True)

    novo_nome = f"{prefixo}_{uuid4().hex}.{ext}"
    caminho_arquivo = os.path.join(upload_folder, novo_nome)

    file.save(caminho_arquivo)

    return novo_nome

def _remover_imagem(nome_arquivo, upload_folder):
    if not nome_arquivo:
        return

    caminho_arquivo = os.path.join(upload_folder, nome_arquivo)

    if os.path.exists(caminho_arquivo) and os.path.isfile(caminho_arquivo):
        os.remove(caminho_arquivo)

def salvar_logo_catalogo(file, upload_folder):
    return _salvar_imagem(file, upload_folder, "catalog_logo")

def remover_logo_catalogo(nome_arquivo, upload_folder):
    _remover_imagem(nome_arquivo, upload_folder)

def salvar_imagem_produto(file, upload_folder):
    return _salvar_imagem(file, upload_folder, "produto")

def remover_imagem_produto(nome_arquivo, upload_folder):
    _remover_imagem(nome_arquivo, upload_folder)

def logo_para_base64(caminho_arquivo, largura_maxima=600):
    with Image.open(caminho_arquivo) as img:
        if img.width > largura_maxima:
            proporcao = largura_maxima / img.width
            nova_altura = int(img.height * proporcao)
            img = img.resize((largura_maxima, nova_altura), Image.LANCZOS)

        possui_transparencia = (
            img.mode in ("RGBA", "LA")
            or "transparency" in img.info
        )

        buffer = BytesIO()

        if possui_transparencia:
            if img.mode not in ("RGBA", "LA"):
                img = img.convert("RGBA")
        else:
            if img.mode != "RGBA":
                img = img.convert("RGBA")

        img.save(buffer, format="PNG", optimize=True)

        imagem_bytes = buffer.getvalue()
        imagem_base64 = base64.b64encode(imagem_bytes).decode("utf-8")

        return f"data:image/png;base64,{imagem_base64}"

def produto_para_base64(caminho_arquivo, largura_maxima=1400, qualidade=90):
    with Image.open(caminho_arquivo) as img:
        if img.mode != "RGB":
            img = img.convert("RGB")

        if img.width > largura_maxima:
            proporcao = largura_maxima / img.width
            nova_altura = int(img.height * proporcao)
            img = img.resize((largura_maxima, nova_altura), Image.LANCZOS)

        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=qualidade, optimize=True)

        imagem_bytes = buffer.getvalue()
        imagem_base64 = base64.b64encode(imagem_bytes).decode("utf-8")

        return f"data:image/jpeg;base64,{imagem_base64}"

def imagem_para_base64(caminho_arquivo, largura_maxima=1000, qualidade=80):
    return produto_para_base64(
        caminho_arquivo,
        largura_maxima=largura_maxima,
        qualidade=qualidade,
    )