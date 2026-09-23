"""Gera as figuras do artigo (modelo estrela e gráficos dos KPIs) a partir do DW."""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyBboxPatch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from etl.config import dw_engine  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "docs" / "figuras"
OUT.mkdir(parents=True, exist_ok=True)

AZUL, LARANJA, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
TEXTO, TEXTO2, GRADE = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({
    "font.family": "Arial", "font.size": 10, "axes.edgecolor": GRADE,
    "axes.labelcolor": TEXTO2, "xtick.color": TEXTO2, "ytick.color": TEXTO2,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRADE, "grid.linewidth": 0.6,
    "axes.axisbelow": True, "figure.dpi": 200,
})


def milhoes(x, _=None):
    return f"{x / 1e6:.0f} mi" if x >= 1e6 or x == 0 else f"{x / 1e3:.0f} mil"


def salvar(fig, nome):
    fig.tight_layout()
    fig.savefig(OUT / nome, facecolor="white")
    plt.close(fig)
    print("  figura:", nome)


def modelo_estrela():
    fig, ax = plt.subplots(figsize=(10, 7.2))
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")

    def tabela(x, y, w, titulo, cols, cor):
        h = 3.2 * (len(cols) + 1) + 1
        ax.add_patch(FancyBboxPatch((x, y - h), w, h, boxstyle="round,pad=0.3,rounding_size=1",
                                    fc="white", ec=cor, lw=1.4))
        ax.add_patch(FancyBboxPatch((x, y - 3.6), w, 3.6, boxstyle="round,pad=0.3,rounding_size=1",
                                    fc=cor, ec=cor, lw=1.4))
        ax.text(x + w / 2, y - 1.8, titulo, ha="center", va="center", color="white",
                fontsize=8.5, fontweight="bold")
        for i, c in enumerate(cols):
            ax.text(x + 1, y - 6 - 3.2 * i, c, fontsize=7, va="center", color=TEXTO)
        return (x + w / 2, y - h / 2)

    dims = {
        "dim_tempo": ((2, 99), ["PK sk_tempo", "data", "ano / semestre", "trimestre / mês", "dia_semana"]),
        "dim_produto": ((37, 99), ["PK sk_produto", "produto_id (NK)", "nome_produto", "categoria", "subcategoria / modelo", "custo_padrao / preco_lista"]),
        "dim_cliente": ((72, 99), ["PK sk_cliente", "cliente_id (NK)", "nome_cliente", "tipo_cliente", "cidade / estado / país"]),
        "dim_territorio": ((2, 56), ["PK sk_territorio", "territorio_id (NK)", "nome_territorio", "país / grupo"]),
        "dim_vendedor": ((72, 56), ["PK sk_vendedor", "vendedor_id (NK)", "nome_vendedor", "território / cota"]),
        "dim_promocao": ((2, 25), ["PK sk_promocao", "promocao_id (NK)", "descrição / tipo", "pct_desconto"]),
        "dim_metodo_envio": ((72, 25), ["PK sk_metodo_envio", "metodo_envio_id (NK)", "nome_metodo", "taxa_base / taxa_por_kg"]),
    }
    centros = {n: tabela(x, y, 26, n, c, AZUL) for n, ((x, y), c) in dims.items()}
    fv = tabela(35, 70, 30, "fato_vendas", [
        "FK sk_data_pedido / sk_data_envio", "FK sk_produto, sk_cliente", "FK sk_territorio, sk_vendedor",
        "FK sk_promocao, sk_metodo_envio", "DD numero_pedido, canal_venda", "quantidade, preco_unitario",
        "valor_bruto, valor_desconto", "valor_liquido, custo_total", "lucro_bruto, frete/imposto rateado",
        "dias_para_envio"], LARANJA)
    fc = tabela(35, 25, 30, "fato_cota_vendedor", [
        "FK sk_vendedor", "FK sk_tempo_inicio / sk_tempo_fim", "valor_cota"], LARANJA)
    for n in dims:
        ax.annotate("", xy=fv, xytext=centros[n],
                    arrowprops=dict(arrowstyle="-", color="#9a9994", lw=0.9), zorder=0)
    for n in ("dim_vendedor", "dim_tempo"):
        ax.annotate("", xy=fc, xytext=centros[n],
                    arrowprops=dict(arrowstyle="-", color="#9a9994", lw=0.9, ls="--"), zorder=0)
    salvar(fig, "fig1_modelo_estrela.png")


def receita_mensal(eng):
    df = pd.read_sql("SELECT ano_mes, canal_venda, receita_liquida FROM dw.vw_kpi01_receita_liquida", eng)
    df = df.pivot(index="ano_mes", columns="canal_venda", values="receita_liquida").fillna(0)
    df = df.loc[df.index < "2025-06"]  # junho/2025 tem apenas dias parciais
    x = pd.to_datetime(df.index + "-01")
    fig, ax = plt.subplots(figsize=(8, 3.6))
    for canal, cor in (("Revenda", AZUL), ("Online", LARANJA)):
        ax.plot(x, df[canal], color=cor, lw=2, label=canal)
    ax.yaxis.set_major_formatter(milhoes)
    ax.set_ylabel("Receita líquida (US$)")
    ax.legend(frameon=False, loc="upper left")
    ax.grid(axis="x", visible=False)
    salvar(fig, "fig2_receita_mensal_canal.png")


def margem_canal(eng):
    df = pd.read_sql("SELECT ano, canal_venda, margem_bruta_pct FROM dw.vw_kpi04_margem_bruta ORDER BY ano", eng)
    df = df.pivot(index="ano", columns="canal_venda", values="margem_bruta_pct")
    fig, ax = plt.subplots(figsize=(8, 3.4))
    w = 0.38
    xs = range(len(df))
    for i, (canal, cor) in enumerate((("Online", LARANJA), ("Revenda", AZUL))):
        pos = [p + (i - 0.5) * (w + 0.02) for p in xs]
        bars = ax.bar(pos, df[canal], width=w, color=cor, label=canal)
        for b, v in zip(bars, df[canal]):
            ax.text(b.get_x() + b.get_width() / 2, max(v, 0) + 0.8, f"{v:.1f}%".replace(".", ","),
                    ha="center", fontsize=8, color=TEXTO2)
    ax.axhline(0, color=TEXTO2, lw=0.8)
    ax.set_xticks(list(xs), df.index.astype(str))
    ax.set_ylabel("Margem bruta (%)")
    ax.set_ylim(-3, 52)
    ax.legend(frameon=False, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.02))
    ax.grid(axis="x", visible=False)
    salvar(fig, "fig3_margem_canal.png")


def barras_h(eng, sql, rotulo, valor, nome, pct_col):
    df = pd.read_sql(sql, eng).sort_values(valor)
    fig, ax = plt.subplots(figsize=(8, 0.42 * len(df) + 0.9))
    ax.barh(df[rotulo], df[valor], color=AZUL, height=0.62)
    for y, (v, p) in enumerate(zip(df[valor], df[pct_col])):
        ax.text(v, y, f"  {v / 1e6:.1f} mi ({p:.1f}%)".replace(".", ","), va="center", fontsize=8, color=TEXTO2)
    ax.xaxis.set_major_formatter(milhoes)
    ax.set_xlim(0, df[valor].max() * 1.25)
    ax.set_xlabel("Receita líquida (US$)")
    ax.grid(axis="y", visible=False)
    salvar(fig, nome)


def ticket_medio(eng):
    df = pd.read_sql("SELECT ano, canal_venda, ticket_medio FROM dw.vw_kpi03_ticket_medio", eng)
    df = df[df.canal_venda == "Online"].sort_values("ano")
    fig, ax = plt.subplots(figsize=(8, 3.0))
    bars = ax.bar(df["ano"].astype(str), df["ticket_medio"], color=LARANJA, width=0.55)
    for b, v in zip(bars, df["ticket_medio"]):
        ax.text(b.get_x() + b.get_width() / 2, v + 40, f"US$ {v:,.0f}".replace(",", "."),
                ha="center", fontsize=8, color=TEXTO2)
    ax.set_ylabel("Ticket médio online (US$)")
    ax.grid(axis="x", visible=False)
    salvar(fig, "fig6_ticket_medio_online.png")


def main():
    eng = dw_engine()
    modelo_estrela()
    receita_mensal(eng)
    margem_canal(eng)
    barras_h(eng, "SELECT categoria, receita_liquida, participacao_pct FROM dw.vw_kpi07_receita_categoria",
             "categoria", "receita_liquida", "fig4_receita_categoria.png", "participacao_pct")
    barras_h(eng, "SELECT nome_territorio, receita_liquida, participacao_pct FROM dw.vw_kpi06_receita_territorio",
             "nome_territorio", "receita_liquida", "fig5_receita_territorio.png", "participacao_pct")
    ticket_medio(eng)


if __name__ == "__main__":
    main()
