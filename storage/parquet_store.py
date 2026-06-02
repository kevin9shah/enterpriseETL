import json
import logging
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

logger = logging.getLogger(__name__)

def silver_parquet(df,output_path):
    df.to_parquet(output_path, index = False)
    logger.info(f"Data successfully ingested in silver layer at {output_path}")


def silver_parquet_api(json_path, output_path):
    with open(json_path,"r") as f:
        data = json.load(f)

    rates = data['conversion_rates']

    df = pd.DataFrame(
        list(rates.items()),
        columns = ["currency","rate"]
    )
    df.to_parquet(output_path, index = False)
    logger.info(f"Data successfully ingested in silver layer at {output_path}")
    return df
