"""Transformação: limpeza, tradução, enriquecimento e geração de chaves substitutas."""
from __future__ import annotations

import numpy as np
import pandas as pd

NA = "Não informado"
MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho",
         "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
DIAS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
LINHAS = {"R": "Estrada", "M": "Montanha", "T": "Touring", "S": "Padrão"}
CLASSES = {"H": "Alta", "M": "Média", "L": "Baixa"}
ESTILOS = {"W": "Feminino", "M": "Masculino", "U": "Unissex"}


def _add_sk(df: pd.DataFrame, sk: str) -> pd.DataFrame:
    df = df.reset_index(drop=True)
    df.insert(0, sk, np.arange(1, len(df) + 1))
    return df


def _strip(series: pd.Series, mapping: dict | None = None) -> pd.Series:
    s = series.astype("string").str.strip()
    if mapping:
        s = s.map(mapping)
    return s.fillna(NA).replace("", NA)


def dim_tempo(vendas: pd.DataFrame, cotas: pd.DataFrame) -> pd.DataFrame:
    inicio = min(vendas["orderdate"].min(), cotas["quotadate"].min())
    fim = max(vendas["shipdate"].max(), cotas["quotadate"].max() + pd.DateOffset(months=3))
    datas = pd.date_range(inicio.normalize().replace(month=1, day=1),
                          fim.normalize().replace(month=12, day=31), freq="D")
    return pd.DataFrame({
        "sk_tempo": datas.strftime("%Y%m%d").astype(int),
        "data": datas.date,
        "ano": datas.year,
        "semestre": np.where(datas.month <= 6, 1, 2),
        "trimestre": datas.quarter,
        "mes": datas.month,
        "nome_mes": [MESES[m - 1] for m in datas.month],
        "ano_mes": datas.strftime("%Y-%m"),
        "dia": datas.day,
        "dia_semana": datas.dayofweek + 1,
        "nome_dia_semana": [DIAS[d] for d in datas.dayofweek],
        "fim_de_semana": datas.dayofweek >= 5,
    })


def dim_produto(p: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame({
        "produto_id": p["productid"],
        "nome_produto": p["name"].str.strip(),
        "numero_produto": p["productnumber"].str.strip(),
        "cor": _strip(p["color"]),
        "tamanho": _strip(p["size"]),
        "linha_produto": _strip(p["productline"], LINHAS),
        "classe": _strip(p["class"], CLASSES),
        "estilo": _strip(p["style"], ESTILOS),
        "modelo": _strip(p["modelo"]),
        "subcategoria": _strip(p["subcategoria"]),
        "categoria": _strip(p["categoria"]),
        "custo_padrao": p["standardcost"],
        "preco_lista": p["listprice"],
        "fabricado_interno": p["makeflag"].astype(bool),
        "data_inicio_venda": pd.to_datetime(p["sellstartdate"]).dt.date,
        "data_fim_venda": pd.to_datetime(p["sellenddate"]).dt.date,
    }).sort_values("produto_id")
    return _add_sk(df, "sk_produto")


def dim_territorio(t: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame({
        "territorio_id": t["territoryid"],
        "nome_territorio": t["name"],
        "codigo_pais": t["countryregioncode"],
        "pais": t["pais"],
        "grupo": t["grupo"],
    }).sort_values("territorio_id")
    return _add_sk(df, "sk_territorio")


def dim_cliente(c: pd.DataFrame, enderecos: pd.DataFrame) -> pd.DataFrame:
    # Um endereço por entidade: prioriza o menor tipo (Faturamento/Casa/Principal)
    end = (enderecos.sort_values(["businessentityid", "addresstypeid"])
                    .drop_duplicates("businessentityid"))
    c = c.copy()
    c["entidade"] = c["personid"].fillna(c["storeid"])
    c = c.merge(end, how="left", left_on="entidade", right_on="businessentityid")
    pessoa = (c["firstname"].fillna("") + " " + c["lastname"].fillna("")).str.strip()
    df = pd.DataFrame({
        "cliente_id": c["customerid"],
        "nome_cliente": np.where(c["storeid"].notna(), c["loja"], pessoa),
        "tipo_cliente": np.where(c["storeid"].notna(), "Loja", "Pessoa física"),
        "cidade": _strip(c["city"]),
        "estado": _strip(c["estado"]),
        "pais": _strip(c["pais"]),
    })
    df["nome_cliente"] = _strip(df["nome_cliente"])
    return _add_sk(df.sort_values("cliente_id"), "sk_cliente")


def dim_vendedor(v: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame({
        "vendedor_id": v["businessentityid"],
        "nome_vendedor": v["firstname"] + " " + v["lastname"],
        "cargo": v["jobtitle"],
        "territorio": _strip(v["territorio"]),
        "cota_anual": v["salesquota"],
        "bonus": v["bonus"],
        "pct_comissao": v["commissionpct"],
        "data_contratacao": pd.to_datetime(v["hiredate"]).dt.date,
    })
    # Membro especial para pedidos online (sem vendedor associado)
    online = pd.DataFrame([{"vendedor_id": 0, "nome_vendedor": "Venda online",
                            "cargo": "Não se aplica", "territorio": "Não se aplica"}])
    df = pd.concat([online, df.sort_values("vendedor_id")], ignore_index=True)
    return _add_sk(df, "sk_vendedor")


def dim_promocao(p: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame({
        "promocao_id": p["specialofferid"],
        "descricao": p["description"],
        "tipo": p["type"],
        "categoria": p["category"],
        "pct_desconto": p["discountpct"],
        "data_inicio": pd.to_datetime(p["startdate"]).dt.date,
        "data_fim": pd.to_datetime(p["enddate"]).dt.date,
    }).sort_values("promocao_id")
    return _add_sk(df, "sk_promocao")


def dim_metodo_envio(m: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame({
        "metodo_envio_id": m["shipmethodid"],
        "nome_metodo": m["name"],
        "taxa_base": m["shipbase"],
        "taxa_por_kg": m["shiprate"],
    }).sort_values("metodo_envio_id")
    return _add_sk(df, "sk_metodo_envio")


def _sk_data(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s).dt.strftime("%Y%m%d").astype("Int64")


def _lookup(df: pd.DataFrame, dim: pd.DataFrame, fk: str, nk: str, sk: str) -> pd.Series:
    mapa = dict(zip(dim[nk], dim[sk]))
    result = df[fk].map(mapa)
    faltantes = result.isna().sum()
    if faltantes:
        raise ValueError(f"{faltantes} linhas sem correspondência em {sk}")
    return result.astype(int)


def _custo_vigente(v: pd.DataFrame, custos: pd.DataFrame, produtos: pd.DataFrame) -> pd.Series:
    """Custo padrão vigente na data do pedido (productcosthistory), com fallback no custo atual."""
    base = v[["productid", "orderdate"]].reset_index()
    hist = base.merge(custos, on="productid", how="left")
    vigente = hist[(hist["orderdate"] >= hist["startdate"]) &
                   (hist["enddate"].isna() | (hist["orderdate"] <= hist["enddate"]))]
    vigente = vigente.sort_values("startdate").drop_duplicates("index", keep="last")
    custo = base["index"].map(dict(zip(vigente["index"], vigente["standardcost"])))
    atual = base["productid"].map(dict(zip(produtos["produto_id"], produtos["custo_padrao"])))
    return pd.Series(custo.fillna(atual).values, index=v.index)


def fato_vendas(v: pd.DataFrame, custos: pd.DataFrame, dims: dict) -> pd.DataFrame:
    v = v.copy()
    v["salespersonid"] = v["salespersonid"].fillna(0).astype(int)
    qtd = v["orderqty"].astype(float)
    preco = v["unitprice"].astype(float)
    bruto = qtd * preco
    desconto = bruto * v["unitpricediscount"].astype(float)
    liquido = bruto - desconto
    custo = qtd * _custo_vigente(v, custos, dims["dim_produto"]).astype(float)
    proporcao = liquido / v["subtotal"].astype(float).replace(0, np.nan)

    return pd.DataFrame({
        "sk_data_pedido": _sk_data(v["orderdate"]),
        "sk_data_envio": _sk_data(v["shipdate"]),
        "sk_produto": _lookup(v, dims["dim_produto"], "productid", "produto_id", "sk_produto"),
        "sk_cliente": _lookup(v, dims["dim_cliente"], "customerid", "cliente_id", "sk_cliente"),
        "sk_territorio": _lookup(v, dims["dim_territorio"], "territoryid", "territorio_id", "sk_territorio"),
        "sk_vendedor": _lookup(v, dims["dim_vendedor"], "salespersonid", "vendedor_id", "sk_vendedor"),
        "sk_promocao": _lookup(v, dims["dim_promocao"], "specialofferid", "promocao_id", "sk_promocao"),
        "sk_metodo_envio": _lookup(v, dims["dim_metodo_envio"], "shipmethodid", "metodo_envio_id", "sk_metodo_envio"),
        "numero_pedido": v["salesorderid"],
        "item_pedido_id": v["salesorderdetailid"],
        "canal_venda": np.where(v["onlineorderflag"], "Online", "Revenda"),
        "quantidade": v["orderqty"],
        "preco_unitario": preco.round(4),
        "valor_bruto": bruto.round(4),
        "valor_desconto": desconto.round(4),
        "valor_liquido": liquido.round(4),
        "custo_total": custo.round(4),
        "lucro_bruto": (liquido - custo).round(4),
        "frete_rateado": (v["freight"].astype(float) * proporcao).fillna(0).round(4),
        "imposto_rateado": (v["taxamt"].astype(float) * proporcao).fillna(0).round(4),
        "dias_para_envio": (pd.to_datetime(v["shipdate"]) - pd.to_datetime(v["orderdate"])).dt.days.astype("Int64"),
    })


def fato_cota_vendedor(c: pd.DataFrame, dim_vend: pd.DataFrame) -> pd.DataFrame:
    c = c.sort_values(["businessentityid", "quotadate"]).copy()
    inicio = pd.to_datetime(c["quotadate"])
    fim = inicio + pd.DateOffset(months=3) - pd.Timedelta(days=1)
    return pd.DataFrame({
        "sk_vendedor": _lookup(c, dim_vend, "businessentityid", "vendedor_id", "sk_vendedor"),
        "sk_tempo_inicio": _sk_data(inicio),
        "sk_tempo_fim": _sk_data(fim),
        "valor_cota": c["salesquota"].astype(float).round(2),
    })


def transform_all(raw: dict) -> dict[str, pd.DataFrame]:
    dims = {
        "dim_tempo": dim_tempo(raw["vendas"], raw["cotas"]),
        "dim_produto": dim_produto(raw["produtos"]),
        "dim_territorio": dim_territorio(raw["territorios"]),
        "dim_cliente": dim_cliente(raw["clientes"], raw["enderecos"]),
        "dim_vendedor": dim_vendedor(raw["vendedores"]),
        "dim_promocao": dim_promocao(raw["promocoes"]),
        "dim_metodo_envio": dim_metodo_envio(raw["metodos_envio"]),
    }
    facts = {
        "fato_vendas": fato_vendas(raw["vendas"], raw["custos"], dims),
        "fato_cota_vendedor": fato_cota_vendedor(raw["cotas"], dims["dim_vendedor"]),
    }
    for name, df in {**dims, **facts}.items():
        print(f"  [transform] {name:<20} {len(df):>7} linhas")
    return {**dims, **facts}
