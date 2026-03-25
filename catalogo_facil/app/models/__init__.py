from flask_sqlalchemy import SQLAlchemy

from app.models.product import Product
from app.models.sale import Sale, SaleItem
from app.models.client import Client
from app.models.category import Category
from app.models.catalog import Catalog, CatalogItem
from app.models.shop import Shop