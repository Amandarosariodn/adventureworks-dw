import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from etl.config import engine_dw

TABELAS = ["fato_vendas", "fato_cota_vendedor", "dim_tempo", "dim_produto", "dim_cliente",
           "dim_territorio", "dim_vendedor", "dim_promocao", "dim_metodo_envio"]

SQL_COLUNAS = """
SELECT c.table_name AS tabela, c.column_name AS coluna,
       CASE WHEN c.character_maximum_length IS NOT NULL
            THEN c.data_type || '(' || c.character_maximum_length || ')'
            WHEN c.data_type = 'numeric'
            THEN 'numeric(' || c.numeric_precision || ',' || c.numeric_scale || ')'
            ELSE c.data_type END AS tipo,
       CASE WHEN c.is_nullable = 'NO' THEN 'Não' ELSE 'Sim' END AS nulo,
       CASE WHEN pk.column_name IS NOT NULL AND fk.column_name IS NOT NULL THEN 'PK/FK'
            WHEN pk.column_name IS NOT NULL THEN 'PK'
            WHEN fk.column_name IS NOT NULL THEN 'FK' ELSE '' END AS chave,
       col_description(format('dw.%%I', c.table_name)::regclass, c.ordinal_position) AS descricao,
       c.ordinal_position
FROM information_schema.columns c
LEFT JOIN (SELECT kcu.table_name, kcu.column_name FROM information_schema.table_constraints tc
           JOIN information_schema.key_column_usage kcu USING (constraint_schema, constraint_name)
           WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_schema = 'dw') pk
       ON pk.table_name = c.table_name AND pk.column_name = c.column_name
LEFT JOIN (SELECT DISTINCT kcu.table_name, kcu.column_name FROM information_schema.table_constraints tc
           JOIN information_schema.key_column_usage kcu USING (constraint_schema, constraint_name)
           WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'dw') fk
       ON fk.table_name = c.table_name AND fk.column_name = c.column_name
WHERE c.table_schema = 'dw'
ORDER BY c.table_name, c.ordinal_position
"""

SQL_TABELAS = """
SELECT relname AS tabela, obj_description(oid) AS descricao
FROM pg_class WHERE relnamespace = 'dw'::regnamespace AND relkind = 'r'
"""


def carregar_dicionario():
    eng = engine_dw()
    colunas = pd.read_sql(SQL_COLUNAS, eng)
    tabelas = pd.read_sql(SQL_TABELAS, eng).set_index("tabela")["descricao"].to_dict()
    return colunas[colunas.tabela.isin(TABELAS)], tabelas


def main():
    colunas, tabelas = carregar_dicionario()
    linhas = ["# Dicionário de dados - Data Warehouse AdventureWorks", "",
              "Gerado automaticamente a partir do catálogo do PostgreSQL (schema `dw`).", ""]
    for t in TABELAS:
        linhas += [f"## {t}", "", f"{tabelas.get(t, '')}", "",
                   "| Coluna | Tipo | Chave | Nulo | Descrição |", "|---|---|---|---|---|"]
        for _, r in colunas[colunas.tabela == t].iterrows():
            linhas.append(f"| {r.coluna} | {r.tipo} | {r.chave} | {r.nulo} | {r.descricao or ''} |")
        linhas.append("")
    out = Path(__file__).resolve().parent.parent / "docs" / "dicionario_dados.md"
    out.write_text("\n".join(linhas), encoding="utf-8")
    print("  gerado:", out.name)


if __name__ == "__main__":
    main()
