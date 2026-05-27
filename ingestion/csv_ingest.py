from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

import pandas as pd
import os
from sqlalchemy import create_engine, text
source_path = BASE_DIR / "data/source/olist_customers_dataset.csv"
# bronze_path = BASE_DIR / "data/bronze/csv_store/olist_customers_dataset.csv"
bronze_path_csv = BASE_DIR / "data/brone/api_store/"
# silver_path = BASE_DIR / "data/silver/csv_store/olist_customers_dataset.parquet"
silver_path_csv = BASE_DIR / "data/silver/api_store/"
gold_path = BASE_DIR / "data/gold/olist_customers_dataset.parquet"

df = pd.read_csv(source_path)

if not df.empty:
    print("Data got for bronze layer")    
else:
    print("Data ingestion failed")

df.to_csv(bronze_path, index = False)
print("Data sucessfully ingested in bronze layer")


df.columns = df.columns.str.lower()

df = df.drop_duplicates()

from storage.parquet_store import silver_parquet
silver_parquet(df,silver_path)


from storage.postgre_store import put_in_postgre
df = pd.read_parquet(silver_path)
put_in_postgre(df,"olist_customers")
