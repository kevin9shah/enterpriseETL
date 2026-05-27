import pandas as pd
import os
import pyarrow.parquet as pq
import pyarrow as pa
from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent


def silver_parquet(df,output_path):
    df.to_parquet(output_path, index = False)
    print(f"Data sucessfully ingested in silver layer at {output_path}")


def silver_parquet_api(json_path, output_path):
    with open(json_path,"r") as f:
        data = json.load(f)
   
    rates = data['conversion_rates']

    df = pd.DataFrame(
        list(rates.items()),
        columns = ["currency","rate"]
    )    
    df.to_parquet(output_path, index = False)
    print(f"Data sucessfully ingested in silver layer at {output_path}")
    return df
