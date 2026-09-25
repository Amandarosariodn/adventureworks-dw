import pandas as pd

NAO_INFORMADO = "Não informado"
MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho",
         "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
DIAS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
LINHAS = {"R": "Estrada", "M": "Montanha", "T": "Touring", "S": "Padrão"}
CLASSES = {"H": "Alta", "M": "Média", "L": "Baixa"}
ESTILOS = {"W": "Feminino", "M": "Masculino", "U": "Unissex"}


def criar_chave(df, coluna):
    df = df.reset_index(drop=True)
    df.insert(0, coluna, range(1, len(df) + 1))
    return df


def buscar_chave(valores, dimensao, chave_natural, chave):
    mapa = dict(zip(dimensao[chave_natural], dimensao[chave]))
    return valores.map(mapa).astype(int)


def data_para_chave(datas):
    return datas.dt.strftime("%Y%m%d").astype(int)


def dim_tempo(vendas):
    inicio = vendas["orderdate"].min().year
    fim = vendas["shipdate"].max().year
    datas = pd.date_range(f"{inicio}-01-01", f"{fim}-12-31")
    return pd.DataFrame({
        "sk_tempo": datas.strftime("%Y%m%d").astype(int),
        "data": datas.date,
        "ano": datas.year,
        "semestre": (datas.month > 6) + 1,
        "trimestre": datas.quarter,
        "mes": datas.month,
        "nome_mes": [MESES[m - 1] for m in datas.month],
        "ano_mes": datas.strftime("%Y-%m"),
        "dia": datas.day,
        "dia_semana": datas.dayofweek + 1,
        "nome_dia_semana": [DIAS[d] for d in datas.dayofweek],
        "fim_de_semana": datas.dayofweek >= 5,
    })


def dim_produto(p):
    df = pd.DataFrame({
        "produto_id": p["productid"],
        "nome_produto": p["name"],
        "numero_produto": p["productnumber"],
        "cor": p["color"],
        "tamanho": p["size"],
        "linha_produto": p["productline"].str.strip().map(LINHAS),
        "classe": p["class"].str.strip().map(CLASSES),
        "estilo": p["style"].str.strip().map(ESTILOS),
        "modelo": p["modelo"],
        "subcategoria": p["subcategoria"],
        "categoria": p["categoria"],
        "custo_padrao": p["standardcost"],
        "preco_lista": p["listprice"],
        "fabricado_interno": p["makeflag"],
        "data_inicio_venda": p["sellstartdate"].dt.date,
        "data_fim_venda": p["sellenddate"].dt.date,
    })
    textos = ["cor", "tamanho", "linha_produto", "classe", "estilo", "modelo", "subcategoria", "categoria"]
    df[textos] = df[textos].fillna(NAO_INFORMADO)
    return criar_chave(df.sort_values("produto_id"), "sk_produto")


def dim_territorio(t):
    df = pd.DataFrame({
        "territorio_id": t["territoryid"],
        "nome_territorio": t["name"],
        "codigo_pais": t["countryregioncode"],
        "pais": t["pais"],
        "grupo": t["grupo"],
    })
    return criar_chave(df.sort_values("territorio_id"), "sk_territorio")


def dim_cliente(c, enderecos):
    enderecos = enderecos.sort_values(["businessentityid", "addresstypeid"]).drop_duplicates("businessentityid")
    c = c.copy()
    c["entidade"] = c["personid"].fillna(c["storeid"])
    c = c.merge(enderecos, how="left", left_on="entidade", right_on="businessentityid")
    loja = c["storeid"].notna()
    pessoa = c["firstname"] + " " + c["lastname"]
    df = pd.DataFrame({
        "cliente_id": c["customerid"],
        "nome_cliente": c["loja"].where(loja, pessoa).str.strip(),
        "tipo_cliente": loja.map({True: "Loja", False: "Pessoa física"}),
        "cidade": c["city"],
        "estado": c["estado"],
        "pais": c["pais"],
    }).fillna(NAO_INFORMADO)
    return criar_chave(df.sort_values("cliente_id"), "sk_cliente")


def dim_vendedor(v):
    df = pd.DataFrame({
        "vendedor_id": v["businessentityid"],
        "nome_vendedor": v["firstname"] + " " + v["lastname"],
        "cargo": v["jobtitle"],
        "territorio": v["territorio"].fillna(NAO_INFORMADO),
        "cota_anual": v["salesquota"],
        "bonus": v["bonus"],
        "pct_comissao": v["commissionpct"],
        "data_contratacao": v["hiredate"],
    })
    online = pd.DataFrame([{"vendedor_id": 0, "nome_vendedor": "Venda online",
                            "cargo": "Não se aplica", "territorio": "Não se aplica"}])
    df = pd.concat([online, df.sort_values("vendedor_id")])
    return criar_chave(df, "sk_vendedor")


def dim_promocao(p):
    df = pd.DataFrame({
        "promocao_id": p["specialofferid"],
        "descricao": p["description"],
        "tipo": p["type"],
        "categoria": p["category"],
        "pct_desconto": p["discountpct"],
        "data_inicio": p["startdate"].dt.date,
        "data_fim": p["enddate"].dt.date,
    })
    return criar_chave(df.sort_values("promocao_id"), "sk_promocao")


def dim_metodo_envio(m):
    df = pd.DataFrame({
        "metodo_envio_id": m["shipmethodid"],
        "nome_metodo": m["name"],
        "taxa_base": m["shipbase"],
        "taxa_por_kg": m["shiprate"],
    })
    return criar_chave(df.sort_values("metodo_envio_id"), "sk_metodo_envio")


def fato_vendas(v, dims):
    valores = ["orderqty", "unitprice", "unitpricediscount", "subtotal", "taxamt", "freight", "custo_unitario"]
    v = v.copy()
    v[valores] = v[valores].astype(float)
    v["salespersonid"] = v["salespersonid"].fillna(0)

    bruto = v["orderqty"] * v["unitprice"]
    desconto = bruto * v["unitpricediscount"]
    liquido = bruto - desconto
    custo = v["orderqty"] * v["custo_unitario"]
    proporcao = liquido / v["subtotal"]

    return pd.DataFrame({
        "sk_data_pedido": data_para_chave(v["orderdate"]),
        "sk_data_envio": data_para_chave(v["shipdate"]),
        "sk_produto": buscar_chave(v["productid"], dims["dim_produto"], "produto_id", "sk_produto"),
        "sk_cliente": buscar_chave(v["customerid"], dims["dim_cliente"], "cliente_id", "sk_cliente"),
        "sk_territorio": buscar_chave(v["territoryid"], dims["dim_territorio"], "territorio_id", "sk_territorio"),
        "sk_vendedor": buscar_chave(v["salespersonid"], dims["dim_vendedor"], "vendedor_id", "sk_vendedor"),
        "sk_promocao": buscar_chave(v["specialofferid"], dims["dim_promocao"], "promocao_id", "sk_promocao"),
        "sk_metodo_envio": buscar_chave(v["shipmethodid"], dims["dim_metodo_envio"], "metodo_envio_id", "sk_metodo_envio"),
        "numero_pedido": v["salesorderid"],
        "item_pedido_id": v["salesorderdetailid"],
        "canal_venda": v["onlineorderflag"].map({True: "Online", False: "Revenda"}),
        "quantidade": v["orderqty"].astype(int),
        "preco_unitario": v["unitprice"],
        "valor_bruto": bruto,
        "valor_desconto": desconto,
        "valor_liquido": liquido,
        "custo_total": custo,
        "lucro_bruto": liquido - custo,
        "frete_rateado": v["freight"] * proporcao,
        "imposto_rateado": v["taxamt"] * proporcao,
        "dias_para_envio": (v["shipdate"] - v["orderdate"]).dt.days,
    }).round(4)


def fato_cota_vendedor(c, dim_vend):
    inicio = c["quotadate"]
    fim = inicio + pd.DateOffset(months=3) - pd.Timedelta(days=1)
    return pd.DataFrame({
        "sk_vendedor": buscar_chave(c["businessentityid"], dim_vend, "vendedor_id", "sk_vendedor"),
        "sk_tempo_inicio": data_para_chave(inicio),
        "sk_tempo_fim": data_para_chave(fim),
        "valor_cota": c["salesquota"],
    })


def transformar(dados):
    tabelas = {
        "dim_tempo": dim_tempo(dados["vendas"]),
        "dim_produto": dim_produto(dados["produtos"]),
        "dim_territorio": dim_territorio(dados["territorios"]),
        "dim_cliente": dim_cliente(dados["clientes"], dados["enderecos"]),
        "dim_vendedor": dim_vendedor(dados["vendedores"]),
        "dim_promocao": dim_promocao(dados["promocoes"]),
        "dim_metodo_envio": dim_metodo_envio(dados["metodos_envio"]),
    }
    tabelas["fato_vendas"] = fato_vendas(dados["vendas"], tabelas)
    tabelas["fato_cota_vendedor"] = fato_cota_vendedor(dados["cotas"], tabelas["dim_vendedor"])
    return tabelas
