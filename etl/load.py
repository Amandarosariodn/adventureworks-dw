"""Carga: recria o schema do DW e carrega as tabelas via COPY (carga completa)."""
import io
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from etl.config import DW_SCHEMA

DDL = Path(__file__).resolve().parent.parent / "sql" / "01_create_dw.sql"
ORDEM_CARGA = ["dim_tempo", "dim_produto", "dim_territorio", "dim_cliente",
               "dim_vendedor", "dim_promocao", "dim_metodo_envio",
               "fato_vendas", "fato_cota_vendedor"]


def executar_arquivo_sql(engine, caminho: Path) -> None:
    """Executa um script SQL inteiro direto no driver (sem interpretar '%' como parâmetro)."""
    with engine.begin() as conn:
        with conn.connection.dbapi_connection.cursor() as cur:
            cur.execute(caminho.read_text(encoding="utf-8"))


def criar_schema(engine) -> None:
    executar_arquivo_sql(engine, DDL)
    print("  [load] schema dw recriado")


def _copy(conn, tabela: str, df: pd.DataFrame) -> None:
    buffer = io.StringIO()
    df.to_csv(buffer, index=False, header=False, na_rep="\\N")
    buffer.seek(0)
    cols = ", ".join(df.columns)
    with conn.connection.dbapi_connection.cursor() as cur:
        cur.copy_expert(
            f"COPY {DW_SCHEMA}.{tabela} ({cols}) FROM STDIN WITH (FORMAT csv, NULL '\\N')",
            buffer,
        )


def carregar(engine, tabelas: dict) -> None:
    with engine.begin() as conn:
        for nome in ORDEM_CARGA:
            df = tabelas[nome]
            inicio = datetime.now()
            _copy(conn, nome, df)
            # Mantém as sequences SERIAL alinhadas às chaves geradas na transformação
            sk = df.columns[0]
            if sk.startswith("sk_") and not nome.startswith("fato") and nome != "dim_tempo":
                conn.execute(text(
                    f"SELECT setval(pg_get_serial_sequence('{DW_SCHEMA}.{nome}', '{sk}'), "
                    f"(SELECT MAX({sk}) FROM {DW_SCHEMA}.{nome}))"))
            conn.execute(
                text(f"INSERT INTO {DW_SCHEMA}.etl_execucao (tabela, linhas, inicio, fim, status) "
                     "VALUES (:t, :l, :i, :f, 'OK')"),
                {"t": nome, "l": len(df), "i": inicio, "f": datetime.now()},
            )
            print(f"  [load] {nome:<20} {len(df):>7} linhas")
