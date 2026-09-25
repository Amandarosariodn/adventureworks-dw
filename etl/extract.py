import pandas as pd

CONSULTAS = {
    "produtos": """
        SELECT p.productid, p.name, p.productnumber, p.color, p.size, p.productline,
               p.class, p.style, p.standardcost, p.listprice, p.makeflag,
               p.sellstartdate, p.sellenddate,
               pm.name AS modelo, ps.name AS subcategoria, pc.name AS categoria
        FROM production.product p
        LEFT JOIN production.productmodel pm ON pm.productmodelid = p.productmodelid
        LEFT JOIN production.productsubcategory ps ON ps.productsubcategoryid = p.productsubcategoryid
        LEFT JOIN production.productcategory pc ON pc.productcategoryid = ps.productcategoryid
    """,
    "territorios": """
        SELECT t.territoryid, t.name, t.countryregioncode, cr.name AS pais, t."group" AS grupo
        FROM sales.salesterritory t
        JOIN person.countryregion cr ON cr.countryregioncode = t.countryregioncode
    """,
    "clientes": """
        SELECT c.customerid, c.personid, c.storeid, p.firstname, p.lastname, s.name AS loja
        FROM sales.customer c
        LEFT JOIN person.person p ON p.businessentityid = c.personid
        LEFT JOIN sales.store s ON s.businessentityid = c.storeid
    """,
    "enderecos": """
        SELECT bea.businessentityid, bea.addresstypeid, a.city, sp.name AS estado, cr.name AS pais
        FROM person.businessentityaddress bea
        JOIN person.address a ON a.addressid = bea.addressid
        JOIN person.stateprovince sp ON sp.stateprovinceid = a.stateprovinceid
        JOIN person.countryregion cr ON cr.countryregioncode = sp.countryregioncode
    """,
    "vendedores": """
        SELECT sp.businessentityid, p.firstname, p.lastname, e.jobtitle, e.hiredate,
               t.name AS territorio, sp.salesquota, sp.bonus, sp.commissionpct
        FROM sales.salesperson sp
        JOIN person.person p ON p.businessentityid = sp.businessentityid
        JOIN humanresources.employee e ON e.businessentityid = sp.businessentityid
        LEFT JOIN sales.salesterritory t ON t.territoryid = sp.territoryid
    """,
    "promocoes": """
        SELECT specialofferid, description, type, category, discountpct, startdate, enddate
        FROM sales.specialoffer
    """,
    "metodos_envio": """
        SELECT shipmethodid, name, shipbase, shiprate FROM purchasing.shipmethod
    """,
    "cotas": """
        SELECT businessentityid, quotadate, salesquota FROM sales.salespersonquotahistory
    """,
    "vendas": """
        SELECT d.salesorderid, d.salesorderdetailid, d.orderqty, d.productid, d.specialofferid,
               d.unitprice, d.unitpricediscount, h.orderdate, h.shipdate, h.onlineorderflag,
               h.customerid, h.salespersonid, h.territoryid, h.shipmethodid,
               h.subtotal, h.taxamt, h.freight,
               COALESCE(ch.standardcost, p.standardcost) AS custo_unitario
        FROM sales.salesorderdetail d
        JOIN sales.salesorderheader h ON h.salesorderid = d.salesorderid
        JOIN production.product p ON p.productid = d.productid
        LEFT JOIN production.productcosthistory ch
               ON ch.productid = d.productid
              AND h.orderdate >= ch.startdate
              AND (ch.enddate IS NULL OR h.orderdate <= ch.enddate)
    """,
}


def extrair(engine):
    dados = {}
    for nome, sql in CONSULTAS.items():
        dados[nome] = pd.read_sql(sql, engine)
        print(f"extraído {nome}: {len(dados[nome])} linhas")
    return dados
