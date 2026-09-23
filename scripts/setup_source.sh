#!/usr/bin/env bash
# Baixa e instala o AdventureWorks (OLTP) no PostgreSQL e cria o banco do DW.
# Requer: psql no PATH, ruby, curl, unzip.
set -euo pipefail
mkdir -p data/source && cd data/source
curl -L -o aw.zip https://github.com/Microsoft/sql-server-samples/releases/download/adventureworks/AdventureWorks-oltp-install-script.zip
curl -L -o install.sql https://raw.githubusercontent.com/lorint/AdventureWorks-for-Postgres/master/install.sql
curl -L -o update_csvs.rb https://raw.githubusercontent.com/lorint/AdventureWorks-for-Postgres/master/update_csvs.rb
unzip -oq aw.zip
ruby update_csvs.rb
psql -d postgres -c 'CREATE DATABASE "Adventureworks";'
psql -d Adventureworks -q < install.sql
psql -d postgres -c 'CREATE DATABASE adventureworks_dw;'
echo "Origem carregada. Rode: python run_etl.py"
