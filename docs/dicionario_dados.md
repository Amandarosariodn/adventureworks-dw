# Dicionário de dados - Data Warehouse AdventureWorks

Gerado automaticamente a partir do catálogo do PostgreSQL (schema `dw`).

## fato_vendas

Vendas no grão de item de pedido

| Coluna | Tipo | Chave | Nulo | Descrição |
|---|---|---|---|---|
| sk_data_pedido | integer | FK | Não | FK dim_tempo: data do pedido |
| sk_data_envio | integer | FK | Sim | FK dim_tempo: data de envio |
| sk_produto | integer | FK | Não | FK dim_produto |
| sk_cliente | integer | FK | Não | FK dim_cliente |
| sk_territorio | integer | FK | Não | FK dim_territorio |
| sk_vendedor | integer | FK | Não | FK dim_vendedor |
| sk_promocao | integer | FK | Não | FK dim_promocao |
| sk_metodo_envio | integer | FK | Não | FK dim_metodo_envio |
| numero_pedido | integer | PK | Não | Dimensão degenerada: número do pedido (salesorderid) |
| item_pedido_id | integer | PK | Não | Identificador do item (salesorderdetailid) |
| canal_venda | character varying(10) |  | Não | Online (site) ou Revenda (lojas via vendedor) |
| quantidade | integer |  | Não | Quantidade vendida |
| preco_unitario | numeric(14,4) |  | Não | Preço unitário praticado |
| valor_bruto | numeric(14,4) |  | Não | Quantidade x preço unitário, antes do desconto |
| valor_desconto | numeric(14,4) |  | Não | Valor total de desconto concedido no item |
| valor_liquido | numeric(14,4) |  | Não | Receita líquida do item (valor bruto - desconto) |
| custo_total | numeric(14,4) |  | Não | Quantidade x custo padrão vigente na data do pedido |
| lucro_bruto | numeric(14,4) |  | Não | Valor líquido - custo total |
| frete_rateado | numeric(14,4) |  | Não | Frete do pedido rateado proporcionalmente ao item |
| imposto_rateado | numeric(14,4) |  | Não | Imposto do pedido rateado proporcionalmente ao item |
| dias_para_envio | smallint |  | Sim | Dias entre pedido e envio |

## fato_cota_vendedor

Cota trimestral de vendas por vendedor

| Coluna | Tipo | Chave | Nulo | Descrição |
|---|---|---|---|---|
| sk_vendedor | integer | PK/FK | Não | FK dim_vendedor |
| sk_tempo_inicio | integer | PK/FK | Não | FK dim_tempo: data de início do período da cota |
| sk_tempo_fim | integer | FK | Não | FK dim_tempo: data de fim do período da cota (3 meses) |
| valor_cota | numeric(14,2) |  | Não | Valor da cota de vendas no trimestre |

## dim_tempo

Calendário diário cobrindo todo o período de pedidos e envios

| Coluna | Tipo | Chave | Nulo | Descrição |
|---|---|---|---|---|
| sk_tempo | integer | PK | Não | Chave substituta no formato AAAAMMDD |
| data | date |  | Não | Data do calendário |
| ano | smallint |  | Não | Ano da data |
| semestre | smallint |  | Não | Semestre do ano (1 ou 2) |
| trimestre | smallint |  | Não | Trimestre do ano (1 a 4) |
| mes | smallint |  | Não | Mês do ano (1 a 12) |
| nome_mes | character varying(15) |  | Não | Nome do mês em português |
| ano_mes | character(7) |  | Não | Ano e mês no formato AAAA-MM |
| dia | smallint |  | Não | Dia do mês |
| dia_semana | smallint |  | Não | Dia da semana ISO (1=segunda, 7=domingo) |
| nome_dia_semana | character varying(15) |  | Não | Nome do dia da semana em português |
| fim_de_semana | boolean |  | Não | Verdadeiro para sábado e domingo |

## dim_produto

Produtos com hierarquia categoria > subcategoria > produto

| Coluna | Tipo | Chave | Nulo | Descrição |
|---|---|---|---|---|
| sk_produto | integer | PK | Não | Chave substituta do produto |
| produto_id | integer |  | Não | Chave natural (production.product.productid) |
| nome_produto | character varying(60) |  | Não | Nome do produto |
| numero_produto | character varying(25) |  | Não | Código comercial do produto |
| cor | character varying(20) |  | Não | Cor do produto (Não informado quando nulo) |
| tamanho | character varying(20) |  | Não | Tamanho do produto |
| linha_produto | character varying(20) |  | Não | Linha: Estrada, Montanha, Touring ou Padrão |
| classe | character varying(20) |  | Não | Classe: Alta, Média ou Baixa |
| estilo | character varying(20) |  | Não | Estilo: Feminino, Masculino ou Unissex |
| modelo | character varying(60) |  | Não | Nome do modelo do produto |
| subcategoria | character varying(60) |  | Não | Subcategoria do produto |
| categoria | character varying(60) |  | Não | Categoria do produto (Bikes, Components, Clothing, Accessories) |
| custo_padrao | numeric(12,4) |  | Não | Custo padrão atual do produto |
| preco_lista | numeric(12,4) |  | Não | Preço de tabela atual do produto |
| fabricado_interno | boolean |  | Não | Verdadeiro se fabricado pela empresa |
| data_inicio_venda | date |  | Sim | Data de início de comercialização |
| data_fim_venda | date |  | Sim | Data de fim de comercialização (nulo = ativo) |

## dim_cliente

Clientes pessoa física (online) e lojas (revenda)

| Coluna | Tipo | Chave | Nulo | Descrição |
|---|---|---|---|---|
| sk_cliente | integer | PK | Não | Chave substituta do cliente |
| cliente_id | integer |  | Não | Chave natural (sales.customer.customerid) |
| nome_cliente | character varying(150) |  | Não | Nome da pessoa ou razão da loja |
| tipo_cliente | character varying(20) |  | Não | Pessoa física ou Loja |
| cidade | character varying(50) |  | Não | Cidade do endereço principal |
| estado | character varying(50) |  | Não | Estado/província do endereço principal |
| pais | character varying(50) |  | Não | País do endereço principal |

## dim_territorio

Territórios de venda

| Coluna | Tipo | Chave | Nulo | Descrição |
|---|---|---|---|---|
| sk_territorio | integer | PK | Não | Chave substituta do território |
| territorio_id | integer |  | Não | Chave natural (sales.salesterritory.territoryid) |
| nome_territorio | character varying(50) |  | Não | Nome do território |
| codigo_pais | character varying(3) |  | Não | Código ISO do país |
| pais | character varying(50) |  | Não | Nome do país |
| grupo | character varying(50) |  | Não | Grupo geográfico (North America, Europe, Pacific) |

## dim_vendedor

Vendedores; membro 0 representa vendas online sem vendedor

| Coluna | Tipo | Chave | Nulo | Descrição |
|---|---|---|---|---|
| sk_vendedor | integer | PK | Não | Chave substituta do vendedor |
| vendedor_id | integer |  | Não | Chave natural (sales.salesperson.businessentityid); 0 = online |
| nome_vendedor | character varying(150) |  | Não | Nome completo do vendedor |
| cargo | character varying(60) |  | Não | Cargo do funcionário |
| territorio | character varying(50) |  | Não | Território atribuído ao vendedor |
| cota_anual | numeric(14,2) |  | Sim | Cota de vendas atual |
| bonus | numeric(14,2) |  | Sim | Bônus do vendedor |
| pct_comissao | numeric(6,4) |  | Sim | Percentual de comissão |
| data_contratacao | date |  | Sim | Data de contratação |

## dim_promocao

Ofertas especiais e descontos

| Coluna | Tipo | Chave | Nulo | Descrição |
|---|---|---|---|---|
| sk_promocao | integer | PK | Não | Chave substituta da promoção |
| promocao_id | integer |  | Não | Chave natural (sales.specialoffer.specialofferid) |
| descricao | character varying(255) |  | Não | Descrição da promoção |
| tipo | character varying(50) |  | Não | Tipo de desconto |
| categoria | character varying(50) |  | Não | Público-alvo (Reseller, Customer, No Discount) |
| pct_desconto | numeric(6,4) |  | Não | Percentual de desconto (0 a 1) |
| data_inicio | date |  | Não | Início da vigência |
| data_fim | date |  | Não | Fim da vigência |

## dim_metodo_envio

Transportadoras e métodos de envio

| Coluna | Tipo | Chave | Nulo | Descrição |
|---|---|---|---|---|
| sk_metodo_envio | integer | PK | Não | Chave substituta do método de envio |
| metodo_envio_id | integer |  | Não | Chave natural (purchasing.shipmethod.shipmethodid) |
| nome_metodo | character varying(50) |  | Não | Nome do método de envio |
| taxa_base | numeric(12,4) |  | Não | Taxa mínima de envio |
| taxa_por_kg | numeric(12,4) |  | Não | Taxa de envio por quilo |
