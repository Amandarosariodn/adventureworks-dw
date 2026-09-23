"""Executa o pipeline ETL completo: OLTP AdventureWorks -> Data Warehouse (PostgreSQL)."""
import time
from pathlib import Path

from sqlalchemy import text

from etl.config import dw_engine, source_engine
from etl.extract import extract_all
from etl.load import carregar, criar_schema, executar_arquivo_sql
from etl.transform import transform_all

KPIS_SQL = Path(__file__).resolve().parent / "sql" / "02_kpis_views.sql"


def main() -> None:
    inicio = time.time()
    print("1/4 Extraindo dados do OLTP...")
    raw = extract_all(source_engine())

    print("2/4 Transformando...")
    tabelas = transform_all(raw)

    dw = dw_engine()
    print("3/4 Carregando no Data Warehouse...")
    criar_schema(dw)
    carregar(dw, tabelas)

    print("4/4 Criando views de indicadores...")
    executar_arquivo_sql(dw, KPIS_SQL)
    with dw.connect() as conn:
        receita = conn.execute(text("SELECT SUM(valor_liquido) FROM dw.fato_vendas")).scalar()

    print(f"ETL concluída em {time.time() - inicio:.1f}s | receita total carregada: {receita:,.2f}")


if __name__ == "__main__":
    main()
