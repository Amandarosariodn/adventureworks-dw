"""Configuração de conexões lida de variáveis de ambiente (.env)."""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()


def _url(prefix: str, default_db: str) -> str:
    user = os.getenv(f"{prefix}_USER", os.getenv("USER", "postgres"))
    password = os.getenv(f"{prefix}_PASSWORD", "")
    host = os.getenv(f"{prefix}_HOST", "localhost")
    port = os.getenv(f"{prefix}_PORT", "5432")
    db = os.getenv(f"{prefix}_DB", default_db)
    auth = f"{user}:{password}" if password else user
    return f"postgresql+psycopg2://{auth}@{host}:{port}/{db}"


SOURCE_URL = _url("SRC", "Adventureworks")
DW_URL = _url("DW", "adventureworks_dw")
DW_SCHEMA = "dw"


def source_engine():
    return create_engine(SOURCE_URL)


def dw_engine():
    return create_engine(DW_URL)
