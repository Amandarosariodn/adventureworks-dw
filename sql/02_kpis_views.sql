-- =============================================================================
-- Indicadores (KPIs) do Data Warehouse AdventureWorks
-- Cada indicador é exposto como view no schema dw para consumo no dashboard
-- (Power BI / Metabase). Todas as consultas usam apenas o modelo estrela.
-- =============================================================================
SET search_path TO dw;

-- KPI 01 - Receita líquida (mensal, por canal)
CREATE OR REPLACE VIEW vw_kpi01_receita_liquida AS
SELECT t.ano, t.mes, t.ano_mes, f.canal_venda,
       ROUND(SUM(f.valor_liquido), 2) AS receita_liquida
FROM fato_vendas f
JOIN dim_tempo t ON t.sk_tempo = f.sk_data_pedido
GROUP BY t.ano, t.mes, t.ano_mes, f.canal_venda;

-- KPI 02 - Quantidade de pedidos e unidades vendidas (mensal)
CREATE OR REPLACE VIEW vw_kpi02_volume_pedidos AS
SELECT t.ano, t.mes, t.ano_mes,
       COUNT(DISTINCT f.numero_pedido) AS qtd_pedidos,
       SUM(f.quantidade)               AS unidades_vendidas
FROM fato_vendas f
JOIN dim_tempo t ON t.sk_tempo = f.sk_data_pedido
GROUP BY t.ano, t.mes, t.ano_mes;

-- KPI 03 - Ticket médio (receita líquida / nº de pedidos) por ano e canal
CREATE OR REPLACE VIEW vw_kpi03_ticket_medio AS
SELECT t.ano, f.canal_venda,
       COUNT(DISTINCT f.numero_pedido) AS qtd_pedidos,
       ROUND(SUM(f.valor_liquido), 2)  AS receita_liquida,
       ROUND(SUM(f.valor_liquido) / COUNT(DISTINCT f.numero_pedido), 2) AS ticket_medio
FROM fato_vendas f
JOIN dim_tempo t ON t.sk_tempo = f.sk_data_pedido
GROUP BY t.ano, f.canal_venda;

-- KPI 04 - Margem bruta % ((receita - custo) / receita) por ano e canal
CREATE OR REPLACE VIEW vw_kpi04_margem_bruta AS
SELECT t.ano, f.canal_venda,
       ROUND(SUM(f.valor_liquido), 2) AS receita_liquida,
       ROUND(SUM(f.custo_total), 2)   AS custo_total,
       ROUND(SUM(f.lucro_bruto), 2)   AS lucro_bruto,
       ROUND(100 * SUM(f.lucro_bruto) / NULLIF(SUM(f.valor_liquido), 0), 2) AS margem_bruta_pct
FROM fato_vendas f
JOIN dim_tempo t ON t.sk_tempo = f.sk_data_pedido
GROUP BY t.ano, f.canal_venda;

-- KPI 05 - Crescimento da receita em relação ao mesmo mês do ano anterior (YoY %)
CREATE OR REPLACE VIEW vw_kpi05_crescimento_yoy AS
WITH mensal AS (
    SELECT t.ano, t.mes, t.ano_mes, SUM(f.valor_liquido) AS receita
    FROM fato_vendas f
    JOIN dim_tempo t ON t.sk_tempo = f.sk_data_pedido
    GROUP BY t.ano, t.mes, t.ano_mes
)
SELECT a.ano, a.mes, a.ano_mes,
       ROUND(a.receita, 2) AS receita,
       ROUND(b.receita, 2) AS receita_ano_anterior,
       ROUND(100 * (a.receita - b.receita) / NULLIF(b.receita, 0), 2) AS crescimento_yoy_pct
FROM mensal a
LEFT JOIN mensal b ON b.ano = a.ano - 1 AND b.mes = a.mes;

-- KPI 06 - Receita e participação (%) por território de venda
CREATE OR REPLACE VIEW vw_kpi06_receita_territorio AS
SELECT tr.grupo, tr.pais, tr.nome_territorio,
       ROUND(SUM(f.valor_liquido), 2) AS receita_liquida,
       ROUND(100 * SUM(f.valor_liquido) / SUM(SUM(f.valor_liquido)) OVER (), 2) AS participacao_pct
FROM fato_vendas f
JOIN dim_territorio tr ON tr.sk_territorio = f.sk_territorio
GROUP BY tr.grupo, tr.pais, tr.nome_territorio;

-- KPI 07 - Receita, participação (%) e margem por categoria de produto
CREATE OR REPLACE VIEW vw_kpi07_receita_categoria AS
SELECT p.categoria,
       SUM(f.quantidade)               AS unidades_vendidas,
       ROUND(SUM(f.valor_liquido), 2)  AS receita_liquida,
       ROUND(100 * SUM(f.valor_liquido) / SUM(SUM(f.valor_liquido)) OVER (), 2) AS participacao_pct,
       ROUND(100 * SUM(f.lucro_bruto) / NULLIF(SUM(f.valor_liquido), 0), 2)    AS margem_bruta_pct
FROM fato_vendas f
JOIN dim_produto p ON p.sk_produto = f.sk_produto
GROUP BY p.categoria;

-- KPI 08 - Percentual de desconto concedido e penetração de promoções
CREATE OR REPLACE VIEW vw_kpi08_desconto AS
SELECT t.ano, f.canal_venda,
       ROUND(SUM(f.valor_desconto), 2) AS valor_desconto,
       ROUND(100 * SUM(f.valor_desconto) / NULLIF(SUM(f.valor_bruto), 0), 2) AS desconto_medio_pct,
       ROUND(100.0 * COUNT(*) FILTER (WHERE pr.pct_desconto > 0) / COUNT(*), 2) AS itens_com_promocao_pct
FROM fato_vendas f
JOIN dim_tempo t     ON t.sk_tempo = f.sk_data_pedido
JOIN dim_promocao pr ON pr.sk_promocao = f.sk_promocao
GROUP BY t.ano, f.canal_venda;

-- KPI 09 - Taxa de recompra: % de clientes com mais de um pedido
CREATE OR REPLACE VIEW vw_kpi09_taxa_recompra AS
WITH pedidos_cliente AS (
    SELECT c.tipo_cliente, f.sk_cliente, COUNT(DISTINCT f.numero_pedido) AS pedidos
    FROM fato_vendas f
    JOIN dim_cliente c ON c.sk_cliente = f.sk_cliente
    GROUP BY c.tipo_cliente, f.sk_cliente
)
SELECT tipo_cliente,
       COUNT(*)                                  AS clientes_ativos,
       COUNT(*) FILTER (WHERE pedidos > 1)       AS clientes_recorrentes,
       ROUND(100.0 * COUNT(*) FILTER (WHERE pedidos > 1) / COUNT(*), 2) AS taxa_recompra_pct,
       ROUND(AVG(pedidos), 2)                    AS media_pedidos_por_cliente
FROM pedidos_cliente
GROUP BY tipo_cliente;

-- KPI 10 - Atingimento de cota dos vendedores (realizado / cota) por trimestre
CREATE OR REPLACE VIEW vw_kpi10_atingimento_cota AS
SELECT v.nome_vendedor, v.territorio,
       ti.data AS inicio_periodo, tf.data AS fim_periodo, ti.ano,
       c.valor_cota,
       ROUND(COALESCE(SUM(f.valor_liquido), 0), 2) AS valor_realizado,
       ROUND(100 * COALESCE(SUM(f.valor_liquido), 0) / NULLIF(c.valor_cota, 0), 2) AS atingimento_pct
FROM fato_cota_vendedor c
JOIN dim_vendedor v ON v.sk_vendedor = c.sk_vendedor
JOIN dim_tempo ti   ON ti.sk_tempo = c.sk_tempo_inicio
JOIN dim_tempo tf   ON tf.sk_tempo = c.sk_tempo_fim
LEFT JOIN fato_vendas f
       ON f.sk_vendedor = c.sk_vendedor
      AND f.sk_data_pedido BETWEEN c.sk_tempo_inicio AND c.sk_tempo_fim
GROUP BY v.nome_vendedor, v.territorio, ti.data, tf.data, ti.ano, c.valor_cota;

-- Visão-resumo para os cartões do dashboard
CREATE OR REPLACE VIEW vw_kpi_resumo AS
SELECT ROUND(SUM(valor_liquido), 2)                                  AS receita_liquida,
       COUNT(DISTINCT numero_pedido)                                 AS qtd_pedidos,
       ROUND(SUM(valor_liquido) / COUNT(DISTINCT numero_pedido), 2)  AS ticket_medio,
       ROUND(100 * SUM(lucro_bruto) / SUM(valor_liquido), 2)         AS margem_bruta_pct,
       ROUND(100 * SUM(valor_desconto) / SUM(valor_bruto), 2)        AS desconto_medio_pct,
       COUNT(DISTINCT sk_cliente)                                    AS clientes_ativos
FROM fato_vendas;
