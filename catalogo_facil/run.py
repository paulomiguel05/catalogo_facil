import os
import sys
import socket
import threading
import webbrowser

from PIL import Image
import pystray
from waitress import serve

from app import create_app
from app.extensions import db
from config import DB_PATH

app = create_app()


def ensure_database():
    if not DB_PATH.exists():
        with app.app_context():
            from app import models
            db.create_all()


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def abrir_navegador(url):
    webbrowser.open_new(url)


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def iniciar_servidor():
    port = int(os.environ.get("PORT", "2005"))

    serve(
        app,
        host="0.0.0.0",
        port=port,
        threads=8,
    )


def criar_icone_bandeja(local_link):
    caminho_icone = resource_path("assets/catalogo_facil.ico")
    imagem = Image.open(caminho_icone)

    def abrir_app(icon, item):
        abrir_navegador(local_link)

    def sair_app(icon, item):
        icon.stop()
        os._exit(0)

    menu = pystray.Menu(
        pystray.MenuItem("Abrir Catálogo Fácil", abrir_app),
        pystray.MenuItem("Sair", sair_app),
    )

    icon = pystray.Icon(
        "CatalogoFacil",
        imagem,
        "Catálogo Fácil",
        menu,
    )
    return icon


if __name__ == "__main__":
    ensure_database()

    port = int(os.environ.get("PORT", "2005"))
    ip = get_local_ip()

    local_link = f"http://localhost:{port}"
    celular_link = f"http://{ip}:{port}"

    app.config["LOCAL_LINK"] = local_link
    app.config["CELULAR_LINK"] = celular_link

    print(f"Local:   {local_link}")
    print(f"Celular: {celular_link}")

    servidor_thread = threading.Thread(target=iniciar_servidor, daemon=True)
    servidor_thread.start()

    threading.Timer(2.0, abrir_navegador, args=[local_link]).start()

    tray_icon = criar_icone_bandeja(local_link)
    tray_icon.run()

    