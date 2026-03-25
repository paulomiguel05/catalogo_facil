import os
from pathlib import Path

# Otimização de Rotas para dados e APP.

def get_app_home() -> Path:
    program_data = Path(os.environ.get("PROGRAMDATA", Path.home()))
    return Path(os.environ.get("CATALOGO_FACIL_HOME", program_data / "CatalogoFacil"))

APP_HOME = get_app_home()
DATA_DIR = APP_HOME / "data"
UPLOAD_DIR = APP_HOME / "uploads"
LOG_DIR = APP_HOME / "logs"

PRODUCT_UPLOAD_DIR = UPLOAD_DIR / "produtos"
CATALOG_UPLOAD_DIR = UPLOAD_DIR / "catalogos"
DB_PATH = DATA_DIR / "catalogo.db"

for path in [DATA_DIR, PRODUCT_UPLOAD_DIR, CATALOG_UPLOAD_DIR, LOG_DIR]:
    path.mkdir(parents=True, exist_ok=True)

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH.as_posix()}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    APP_HOME = str(APP_HOME)
    DATA_DIR = str(DATA_DIR)
    LOG_DIR = str(LOG_DIR)
    PRODUCT_UPLOAD_DIR = str(PRODUCT_UPLOAD_DIR)
    CATALOG_UPLOAD_DIR = str(CATALOG_UPLOAD_DIR)