import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()


def conectar(prefixo, banco_padrao):
    usuario = os.getenv(prefixo + "_USER", os.getenv("USER"))
    senha = os.getenv(prefixo + "_PASSWORD", "")
    host = os.getenv(prefixo + "_HOST", "localhost")
    porta = os.getenv(prefixo + "_PORT", "5432")
    banco = os.getenv(prefixo + "_DB", banco_padrao)
    return create_engine(f"postgresql+psycopg2://{usuario}:{senha}@{host}:{porta}/{banco}")


def engine_origem():
    return conectar("SRC", "Adventureworks")


def engine_dw():
    return conectar("DW", "adventureworks_dw")
