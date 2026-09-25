import time

from etl.config import engine_dw, engine_origem
from etl.extract import extrair
from etl.load import carregar
from etl.transform import transformar

inicio = time.time()

dados = extrair(engine_origem())
tabelas = transformar(dados)
carregar(engine_dw(), tabelas)

print(f"ETL concluída em {time.time() - inicio:.1f}s")
