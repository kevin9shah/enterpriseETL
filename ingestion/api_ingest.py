import requests
import os
from dotenv import load_dotenv
from pathlib import Path
import sys
import json
import pandas as pd
from storage.parquet_store import silver_parquet_api
import logging
from config.settings import settings 

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

logger = logging.getLogger(__name__)

def main():
    

    bronze_path_api = BASE_DIR / "data/bronze/api_store/inr_rates.json"
    silver_path_api = BASE_DIR / "data/silver/api_store/inr_rates.parquet"
    API = settings.exchange_rate_api_key
    url = f"https://v6.exchangerate-api.com/v6/{API}/latest/INR"
    
    logger.info("--- Starting API ingestion for Exchange Rates ---")
    response = requests.get(url)
    if response.status_code != 200:
        logger.error(f"Failed to fetch data from API: Status code {response.status_code}")
        return
        
    data = response.json()

    # Ensure bronze directory exists
    bronze_path_api.parent.mkdir(parents=True, exist_ok=True)
    with open(bronze_path_api, "w") as file:
        json.dump(data, file, indent=4)
    logger.info(f"Data successfully ingested in bronze layer at {bronze_path_api}")

    # Ensure silver directory exists
    silver_path_api.parent.mkdir(parents=True, exist_ok=True)
    silver_parquet_api(bronze_path_api, silver_path_api)

if __name__ == "__main__":
    main()