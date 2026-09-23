# Dashboard - Power BI ou Metabase

O dashboard consome diretamente as views `dw.vw_kpi*` criadas pela ETL
(`sql/02_kpis_views.sql`). Toda regra de negócio está no banco, então as duas ferramentas
mostram os mesmos números.

## Conexão

| Parâmetro | Valor |
|---|---|
| Tipo | PostgreSQL |
| Host / Porta | `localhost` / `5432` |
| Banco | `adventureworks_dw` |
| Schema | `dw` |
| Usuário | o mesmo do `.env` (`DW_USER`) |

- **Power BI Desktop**: Obter Dados → Banco de dados PostgreSQL → servidor `localhost`,
  banco `adventureworks_dw` → modo *Import* → selecione as views `dw.vw_kpi*`.
- **Metabase**: Admin → Databases → Add database → PostgreSQL → preencha os dados acima.
  As views aparecem em *Browse data → adventureworks_dw → Dw*.

## Layout sugerido (storytelling em 3 blocos)

**1. Visão geral (linha de cartões)** - fonte `vw_kpi_resumo`
Receita líquida · Nº de pedidos · Ticket médio · Margem bruta % · Desconto médio % · Clientes ativos

**2. Crescimento e canais**
| Visual | View | Configuração |
|---|---|---|
| Linha: receita mensal por canal | `vw_kpi01_receita_liquida` | eixo X `ano_mes`, valor `receita_liquida`, legenda `canal_venda` |
| Colunas: pedidos e unidades | `vw_kpi02_volume_pedidos` | eixo X `ano_mes`, valor `qtd_pedidos` |
| Colunas: ticket médio por ano | `vw_kpi03_ticket_medio` | eixo X `ano`, valor `ticket_medio`, legenda `canal_venda` |
| Colunas: crescimento YoY % | `vw_kpi05_crescimento_yoy` | eixo X `ano_mes`, valor `crescimento_yoy_pct` (filtrar ano ≥ 2023) |

**3. Rentabilidade, mercado e equipe**
| Visual | View | Configuração |
|---|---|---|
| Colunas agrupadas: margem % por canal | `vw_kpi04_margem_bruta` | eixo X `ano`, valor `margem_bruta_pct`, legenda `canal_venda` |
| Barras: receita por território | `vw_kpi06_receita_territorio` | eixo `nome_territorio`, valor `receita_liquida` (rótulo `participacao_pct`) |
| Barras: receita e margem por categoria | `vw_kpi07_receita_categoria` | eixo `categoria`, valor `receita_liquida` |
| Tabela: desconto e promoções | `vw_kpi08_desconto` | `ano`, `canal_venda`, `desconto_medio_pct`, `itens_com_promocao_pct` |
| Cartões: recompra por tipo de cliente | `vw_kpi09_taxa_recompra` | `taxa_recompra_pct` por `tipo_cliente` |
| Tabela/matriz: atingimento de cota | `vw_kpi10_atingimento_cota` | linhas `nome_vendedor`, colunas `inicio_periodo`, valor `atingimento_pct` (formatação condicional ≥ 100%) |

Filtros no topo da página: `ano` (segmentação) e `canal_venda`.
