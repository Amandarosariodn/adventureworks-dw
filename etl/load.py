from datetime import datetime
from pathlib import Path

from sqlalchemy import text

PASTA_SQL = Path(__file__).parent.parent / "sql"


def executar_sql(engine, arquivo):
    conexao = engine.raw_connection()
    cursor = conexao.cursor()
    cursor.execute((PASTA_SQL / arquivo).read_text(encoding="utf-8"))
    conexao.commit()
    conexao.close()


def carregar(engine, tabelas):
    executar_sql(engine, "01_create_dw.sql")

    for nome, df in tabelas.items():
        inicio = datetime.now()
        df.to_sql(nome, engine, schema="dw", if_exists="append", index=False, method="multi", chunksize=2000)
        with engine.begin() as conexao:
            conexao.execute(
                text("INSERT INTO dw.etl_execucao (tabela, linhas, inicio, fim, status) "
                     "VALUES (:tabela, :linhas, :inicio, :fim, 'OK')"),
                {"tabela": nome, "linhas": len(df), "inicio": inicio, "fim": datetime.now()},
            )
        print(f"carregado {nome}: {len(df)} linhas")

    executar_sql(engine, "02_kpis_views.sql")
