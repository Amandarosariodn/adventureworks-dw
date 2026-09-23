-- =============================================================================
-- Data Warehouse AdventureWorks - Modelo multidimensional (esquema estrela)
-- Banco: adventureworks_dw | Schema: dw
-- Fatos: fato_vendas (grão: item de pedido de venda)
--        fato_cota_vendedor (grão: vendedor x trimestre)
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS dw;
SET search_path TO dw;

DROP TABLE IF EXISTS fato_vendas, fato_cota_vendedor CASCADE;
DROP TABLE IF EXISTS dim_tempo, dim_produto, dim_cliente, dim_territorio,
                     dim_vendedor, dim_promocao, dim_metodo_envio CASCADE;

-- -----------------------------------------------------------------------------
-- Dimensões
-- -----------------------------------------------------------------------------
CREATE TABLE dim_tempo (
    sk_tempo         INTEGER PRIMARY KEY,          -- AAAAMMDD
    data             DATE        NOT NULL UNIQUE,
    ano              SMALLINT    NOT NULL,
    semestre         SMALLINT    NOT NULL,
    trimestre        SMALLINT    NOT NULL,
    mes              SMALLINT    NOT NULL,
    nome_mes         VARCHAR(15) NOT NULL,
    ano_mes          CHAR(7)     NOT NULL,         -- AAAA-MM
    dia              SMALLINT    NOT NULL,
    dia_semana       SMALLINT    NOT NULL,         -- 1=segunda ... 7=domingo
    nome_dia_semana  VARCHAR(15) NOT NULL,
    fim_de_semana    BOOLEAN     NOT NULL
);

CREATE TABLE dim_produto (
    sk_produto        SERIAL PRIMARY KEY,
    produto_id        INTEGER      NOT NULL UNIQUE,
    nome_produto      VARCHAR(60)  NOT NULL,
    numero_produto    VARCHAR(25)  NOT NULL,
    cor               VARCHAR(20)  NOT NULL,
    tamanho           VARCHAR(20)  NOT NULL,
    linha_produto     VARCHAR(20)  NOT NULL,
    classe            VARCHAR(20)  NOT NULL,
    estilo            VARCHAR(20)  NOT NULL,
    modelo            VARCHAR(60)  NOT NULL,
    subcategoria      VARCHAR(60)  NOT NULL,
    categoria         VARCHAR(60)  NOT NULL,
    custo_padrao      NUMERIC(12,4) NOT NULL,
    preco_lista       NUMERIC(12,4) NOT NULL,
    fabricado_interno BOOLEAN      NOT NULL,
    data_inicio_venda DATE,
    data_fim_venda    DATE
);

CREATE TABLE dim_territorio (
    sk_territorio  SERIAL PRIMARY KEY,
    territorio_id  INTEGER     NOT NULL UNIQUE,
    nome_territorio VARCHAR(50) NOT NULL,
    codigo_pais    VARCHAR(3)  NOT NULL,
    pais           VARCHAR(50) NOT NULL,
    grupo          VARCHAR(50) NOT NULL          -- North America, Europe, Pacific
);

CREATE TABLE dim_cliente (
    sk_cliente    SERIAL PRIMARY KEY,
    cliente_id    INTEGER      NOT NULL UNIQUE,
    nome_cliente  VARCHAR(150) NOT NULL,
    tipo_cliente  VARCHAR(20)  NOT NULL,          -- Pessoa física | Loja (revenda)
    cidade        VARCHAR(50)  NOT NULL,
    estado        VARCHAR(50)  NOT NULL,
    pais          VARCHAR(50)  NOT NULL
);

CREATE TABLE dim_vendedor (
    sk_vendedor     SERIAL PRIMARY KEY,
    vendedor_id     INTEGER      NOT NULL UNIQUE, -- 0 = venda online (sem vendedor)
    nome_vendedor   VARCHAR(150) NOT NULL,
    cargo           VARCHAR(60)  NOT NULL,
    territorio      VARCHAR(50)  NOT NULL,
    cota_anual      NUMERIC(14,2),
    bonus           NUMERIC(14,2),
    pct_comissao    NUMERIC(6,4),
    data_contratacao DATE
);

CREATE TABLE dim_promocao (
    sk_promocao   SERIAL PRIMARY KEY,
    promocao_id   INTEGER      NOT NULL UNIQUE,
    descricao     VARCHAR(255) NOT NULL,
    tipo          VARCHAR(50)  NOT NULL,
    categoria     VARCHAR(50)  NOT NULL,
    pct_desconto  NUMERIC(6,4) NOT NULL,
    data_inicio   DATE         NOT NULL,
    data_fim      DATE         NOT NULL
);

CREATE TABLE dim_metodo_envio (
    sk_metodo_envio SERIAL PRIMARY KEY,
    metodo_envio_id INTEGER      NOT NULL UNIQUE,
    nome_metodo     VARCHAR(50)  NOT NULL,
    taxa_base       NUMERIC(12,4) NOT NULL,
    taxa_por_kg     NUMERIC(12,4) NOT NULL
);

-- -----------------------------------------------------------------------------
-- Fatos
-- -----------------------------------------------------------------------------
CREATE TABLE fato_vendas (
    sk_data_pedido    INTEGER NOT NULL REFERENCES dim_tempo(sk_tempo),
    sk_data_envio     INTEGER     REFERENCES dim_tempo(sk_tempo),
    sk_produto        INTEGER NOT NULL REFERENCES dim_produto(sk_produto),
    sk_cliente        INTEGER NOT NULL REFERENCES dim_cliente(sk_cliente),
    sk_territorio     INTEGER NOT NULL REFERENCES dim_territorio(sk_territorio),
    sk_vendedor       INTEGER NOT NULL REFERENCES dim_vendedor(sk_vendedor),
    sk_promocao       INTEGER NOT NULL REFERENCES dim_promocao(sk_promocao),
    sk_metodo_envio   INTEGER NOT NULL REFERENCES dim_metodo_envio(sk_metodo_envio),
    numero_pedido     INTEGER NOT NULL,           -- dimensão degenerada
    item_pedido_id    INTEGER NOT NULL,
    canal_venda       VARCHAR(10) NOT NULL,       -- Online | Revenda
    quantidade        INTEGER       NOT NULL,
    preco_unitario    NUMERIC(14,4) NOT NULL,
    valor_bruto       NUMERIC(14,4) NOT NULL,     -- quantidade * preço unitário
    valor_desconto    NUMERIC(14,4) NOT NULL,
    valor_liquido     NUMERIC(14,4) NOT NULL,     -- receita da linha
    custo_total       NUMERIC(14,4) NOT NULL,
    lucro_bruto       NUMERIC(14,4) NOT NULL,
    frete_rateado     NUMERIC(14,4) NOT NULL,
    imposto_rateado   NUMERIC(14,4) NOT NULL,
    dias_para_envio   SMALLINT,
    PRIMARY KEY (numero_pedido, item_pedido_id)
);

CREATE TABLE fato_cota_vendedor (
    sk_vendedor   INTEGER NOT NULL REFERENCES dim_vendedor(sk_vendedor),
    sk_tempo_inicio INTEGER NOT NULL REFERENCES dim_tempo(sk_tempo), -- início do período da cota
    sk_tempo_fim    INTEGER NOT NULL REFERENCES dim_tempo(sk_tempo), -- fim do período da cota
    valor_cota      NUMERIC(14,2) NOT NULL,
    PRIMARY KEY (sk_vendedor, sk_tempo_inicio)
);

CREATE INDEX ix_fv_data      ON fato_vendas (sk_data_pedido);
CREATE INDEX ix_fv_produto   ON fato_vendas (sk_produto);
CREATE INDEX ix_fv_cliente   ON fato_vendas (sk_cliente);
CREATE INDEX ix_fv_territorio ON fato_vendas (sk_territorio);
CREATE INDEX ix_fv_vendedor  ON fato_vendas (sk_vendedor);

-- -----------------------------------------------------------------------------
-- Controle de execução da ETL
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS etl_execucao (
    id           SERIAL PRIMARY KEY,
    tabela       VARCHAR(50) NOT NULL,
    linhas       INTEGER     NOT NULL,
    inicio       TIMESTAMP   NOT NULL,
    fim          TIMESTAMP   NOT NULL,
    status       VARCHAR(10) NOT NULL
);

-- -----------------------------------------------------------------------------
-- Dicionário de dados (comentários no catálogo do PostgreSQL)
-- -----------------------------------------------------------------------------
COMMENT ON TABLE dim_tempo IS 'Calendário diário cobrindo todo o período de pedidos e envios';
COMMENT ON COLUMN dim_tempo.sk_tempo IS 'Chave substituta no formato AAAAMMDD';
COMMENT ON COLUMN dim_tempo.data IS 'Data do calendário';
COMMENT ON COLUMN dim_tempo.ano IS 'Ano da data';
COMMENT ON COLUMN dim_tempo.semestre IS 'Semestre do ano (1 ou 2)';
COMMENT ON COLUMN dim_tempo.trimestre IS 'Trimestre do ano (1 a 4)';
COMMENT ON COLUMN dim_tempo.mes IS 'Mês do ano (1 a 12)';
COMMENT ON COLUMN dim_tempo.nome_mes IS 'Nome do mês em português';
COMMENT ON COLUMN dim_tempo.ano_mes IS 'Ano e mês no formato AAAA-MM';
COMMENT ON COLUMN dim_tempo.dia IS 'Dia do mês';
COMMENT ON COLUMN dim_tempo.dia_semana IS 'Dia da semana ISO (1=segunda, 7=domingo)';
COMMENT ON COLUMN dim_tempo.nome_dia_semana IS 'Nome do dia da semana em português';
COMMENT ON COLUMN dim_tempo.fim_de_semana IS 'Verdadeiro para sábado e domingo';

COMMENT ON TABLE dim_produto IS 'Produtos com hierarquia categoria > subcategoria > produto';
COMMENT ON COLUMN dim_produto.sk_produto IS 'Chave substituta do produto';
COMMENT ON COLUMN dim_produto.produto_id IS 'Chave natural (production.product.productid)';
COMMENT ON COLUMN dim_produto.nome_produto IS 'Nome do produto';
COMMENT ON COLUMN dim_produto.numero_produto IS 'Código comercial do produto';
COMMENT ON COLUMN dim_produto.cor IS 'Cor do produto (Não informado quando nulo)';
COMMENT ON COLUMN dim_produto.tamanho IS 'Tamanho do produto';
COMMENT ON COLUMN dim_produto.linha_produto IS 'Linha: Estrada, Montanha, Touring ou Padrão';
COMMENT ON COLUMN dim_produto.classe IS 'Classe: Alta, Média ou Baixa';
COMMENT ON COLUMN dim_produto.estilo IS 'Estilo: Feminino, Masculino ou Unissex';
COMMENT ON COLUMN dim_produto.modelo IS 'Nome do modelo do produto';
COMMENT ON COLUMN dim_produto.subcategoria IS 'Subcategoria do produto';
COMMENT ON COLUMN dim_produto.categoria IS 'Categoria do produto (Bikes, Components, Clothing, Accessories)';
COMMENT ON COLUMN dim_produto.custo_padrao IS 'Custo padrão atual do produto';
COMMENT ON COLUMN dim_produto.preco_lista IS 'Preço de tabela atual do produto';
COMMENT ON COLUMN dim_produto.fabricado_interno IS 'Verdadeiro se fabricado pela empresa';
COMMENT ON COLUMN dim_produto.data_inicio_venda IS 'Data de início de comercialização';
COMMENT ON COLUMN dim_produto.data_fim_venda IS 'Data de fim de comercialização (nulo = ativo)';

COMMENT ON TABLE dim_territorio IS 'Territórios de venda';
COMMENT ON COLUMN dim_territorio.sk_territorio IS 'Chave substituta do território';
COMMENT ON COLUMN dim_territorio.territorio_id IS 'Chave natural (sales.salesterritory.territoryid)';
COMMENT ON COLUMN dim_territorio.nome_territorio IS 'Nome do território';
COMMENT ON COLUMN dim_territorio.codigo_pais IS 'Código ISO do país';
COMMENT ON COLUMN dim_territorio.pais IS 'Nome do país';
COMMENT ON COLUMN dim_territorio.grupo IS 'Grupo geográfico (North America, Europe, Pacific)';

COMMENT ON TABLE dim_cliente IS 'Clientes pessoa física (online) e lojas (revenda)';
COMMENT ON COLUMN dim_cliente.sk_cliente IS 'Chave substituta do cliente';
COMMENT ON COLUMN dim_cliente.cliente_id IS 'Chave natural (sales.customer.customerid)';
COMMENT ON COLUMN dim_cliente.nome_cliente IS 'Nome da pessoa ou razão da loja';
COMMENT ON COLUMN dim_cliente.tipo_cliente IS 'Pessoa física ou Loja';
COMMENT ON COLUMN dim_cliente.cidade IS 'Cidade do endereço principal';
COMMENT ON COLUMN dim_cliente.estado IS 'Estado/província do endereço principal';
COMMENT ON COLUMN dim_cliente.pais IS 'País do endereço principal';

COMMENT ON TABLE dim_vendedor IS 'Vendedores; membro 0 representa vendas online sem vendedor';
COMMENT ON COLUMN dim_vendedor.sk_vendedor IS 'Chave substituta do vendedor';
COMMENT ON COLUMN dim_vendedor.vendedor_id IS 'Chave natural (sales.salesperson.businessentityid); 0 = online';
COMMENT ON COLUMN dim_vendedor.nome_vendedor IS 'Nome completo do vendedor';
COMMENT ON COLUMN dim_vendedor.cargo IS 'Cargo do funcionário';
COMMENT ON COLUMN dim_vendedor.territorio IS 'Território atribuído ao vendedor';
COMMENT ON COLUMN dim_vendedor.cota_anual IS 'Cota de vendas atual';
COMMENT ON COLUMN dim_vendedor.bonus IS 'Bônus do vendedor';
COMMENT ON COLUMN dim_vendedor.pct_comissao IS 'Percentual de comissão';
COMMENT ON COLUMN dim_vendedor.data_contratacao IS 'Data de contratação';

COMMENT ON TABLE dim_promocao IS 'Ofertas especiais e descontos';
COMMENT ON COLUMN dim_promocao.sk_promocao IS 'Chave substituta da promoção';
COMMENT ON COLUMN dim_promocao.promocao_id IS 'Chave natural (sales.specialoffer.specialofferid)';
COMMENT ON COLUMN dim_promocao.descricao IS 'Descrição da promoção';
COMMENT ON COLUMN dim_promocao.tipo IS 'Tipo de desconto';
COMMENT ON COLUMN dim_promocao.categoria IS 'Público-alvo (Reseller, Customer, No Discount)';
COMMENT ON COLUMN dim_promocao.pct_desconto IS 'Percentual de desconto (0 a 1)';
COMMENT ON COLUMN dim_promocao.data_inicio IS 'Início da vigência';
COMMENT ON COLUMN dim_promocao.data_fim IS 'Fim da vigência';

COMMENT ON TABLE dim_metodo_envio IS 'Transportadoras e métodos de envio';
COMMENT ON COLUMN dim_metodo_envio.sk_metodo_envio IS 'Chave substituta do método de envio';
COMMENT ON COLUMN dim_metodo_envio.metodo_envio_id IS 'Chave natural (purchasing.shipmethod.shipmethodid)';
COMMENT ON COLUMN dim_metodo_envio.nome_metodo IS 'Nome do método de envio';
COMMENT ON COLUMN dim_metodo_envio.taxa_base IS 'Taxa mínima de envio';
COMMENT ON COLUMN dim_metodo_envio.taxa_por_kg IS 'Taxa de envio por quilo';

COMMENT ON TABLE fato_vendas IS 'Vendas no grão de item de pedido';
COMMENT ON COLUMN fato_vendas.sk_data_pedido IS 'FK dim_tempo: data do pedido';
COMMENT ON COLUMN fato_vendas.sk_data_envio IS 'FK dim_tempo: data de envio';
COMMENT ON COLUMN fato_vendas.sk_produto IS 'FK dim_produto';
COMMENT ON COLUMN fato_vendas.sk_cliente IS 'FK dim_cliente';
COMMENT ON COLUMN fato_vendas.sk_territorio IS 'FK dim_territorio';
COMMENT ON COLUMN fato_vendas.sk_vendedor IS 'FK dim_vendedor';
COMMENT ON COLUMN fato_vendas.sk_promocao IS 'FK dim_promocao';
COMMENT ON COLUMN fato_vendas.sk_metodo_envio IS 'FK dim_metodo_envio';
COMMENT ON COLUMN fato_vendas.numero_pedido IS 'Dimensão degenerada: número do pedido (salesorderid)';
COMMENT ON COLUMN fato_vendas.item_pedido_id IS 'Identificador do item (salesorderdetailid)';
COMMENT ON COLUMN fato_vendas.canal_venda IS 'Online (site) ou Revenda (lojas via vendedor)';
COMMENT ON COLUMN fato_vendas.quantidade IS 'Quantidade vendida';
COMMENT ON COLUMN fato_vendas.preco_unitario IS 'Preço unitário praticado';
COMMENT ON COLUMN fato_vendas.valor_bruto IS 'Quantidade x preço unitário, antes do desconto';
COMMENT ON COLUMN fato_vendas.valor_desconto IS 'Valor total de desconto concedido no item';
COMMENT ON COLUMN fato_vendas.valor_liquido IS 'Receita líquida do item (valor bruto - desconto)';
COMMENT ON COLUMN fato_vendas.custo_total IS 'Quantidade x custo padrão vigente na data do pedido';
COMMENT ON COLUMN fato_vendas.lucro_bruto IS 'Valor líquido - custo total';
COMMENT ON COLUMN fato_vendas.frete_rateado IS 'Frete do pedido rateado proporcionalmente ao item';
COMMENT ON COLUMN fato_vendas.imposto_rateado IS 'Imposto do pedido rateado proporcionalmente ao item';
COMMENT ON COLUMN fato_vendas.dias_para_envio IS 'Dias entre pedido e envio';

COMMENT ON TABLE fato_cota_vendedor IS 'Cota trimestral de vendas por vendedor';
COMMENT ON COLUMN fato_cota_vendedor.sk_vendedor IS 'FK dim_vendedor';
COMMENT ON COLUMN fato_cota_vendedor.sk_tempo_inicio IS 'FK dim_tempo: data de início do período da cota';
COMMENT ON COLUMN fato_cota_vendedor.sk_tempo_fim IS 'FK dim_tempo: data de fim do período da cota (3 meses)';
COMMENT ON COLUMN fato_cota_vendedor.valor_cota IS 'Valor da cota de vendas no trimestre';
