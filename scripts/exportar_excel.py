"""Exporta as views de KPI do DW para um Excel (uma aba por indicador).

Útil para usar o Power BI no navegador (app.powerbi.com), que não acessa o PostgreSQL local.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from etl.config import dw_engine  # noqa: E402

SAIDA = Path(__file__).resolve().parent.parent / "docs" / "dashboard" / "kpis_adventureworks.xlsx"
VIEWS = {
    "resumo": "vw_kpi_resumo",
    "kpi01_receita": "vw_kpi01_receita_liquida",
    "kpi02_pedidos": "vw_kpi02_volume_pedidos",
    "kpi03_ticket_medio": "vw_kpi03_ticket_medio",
    "kpi04_margem": "vw_kpi04_margem_bruta",
    "kpi05_crescimento_yoy": "vw_kpi05_crescimento_yoy",
    "kpi06_territorio": "vw_kpi06_receita_territorio",
    "kpi07_categoria": "vw_kpi07_receita_categoria",
    "kpi08_desconto": "vw_kpi08_desconto",
    "kpi09_recompra": "vw_kpi09_taxa_recompra",
    "kpi10_cota": "vw_kpi10_atingimento_cota",
}


def main():
    eng = dw_engine()
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(SAIDA, engine="openpyxl") as xls:
        for aba, view in VIEWS.items():
            df = pd.read_sql(f"SELECT * FROM dw.{view}", eng)
            for col in df.select_dtypes("object"):
                if df[col].map(lambda v: hasattr(v, "year")).all():
                    df[col] = pd.to_datetime(df[col])
            df.to_excel(xls, sheet_name=aba, index=False)
            print(f"  {aba:<22} {len(df):>4} linhas")
    print("  gerado:", SAIDA.relative_to(SAIDA.parents[2]))


if __name__ == "__main__":
    main()
