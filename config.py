"""Configurações do DogWorld. Os valores vêm do arquivo .env (veja .env.example)."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _url_do_banco() -> str:
    url = os.getenv("DATABASE_URL") or f"sqlite:///{BASE_DIR / 'dogworld.db'}"
    # Render e Heroku entregam "postgres://", mas o SQLAlchemy exige "postgresql://"
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "troque-esta-chave-antes-de-publicar")
    SQLALCHEMY_DATABASE_URI = _url_do_banco()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Endereço do front-end autorizado a chamar esta API (CORS)
    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://127.0.0.1:5500")

    DOG_API_URL = os.getenv("DOG_API_URL", "https://api.thedogapi.com/v1").rstrip("/")
    DOG_API_KEY = os.getenv("DOG_API_KEY", "")
    DOG_API_TIMEOUT = float(os.getenv("DOG_API_TIMEOUT", "5"))