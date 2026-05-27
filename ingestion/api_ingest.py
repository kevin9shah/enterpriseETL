import requests
import os
from dotenv import load_dotenv
from pathlib import Path
import sys
import json
import pandas as pd
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

load_dotenv()

bronze_path_api = BASE_DIR / "data/bronze/api_store/inr_rates.json"
silver_path_api = BASE_DIR / "data/silver/api_store/inr_rates.parquet"
API = os.getenv("Exchange_Rate_API_KEY")
url = f"https://v6.exchangerate-api.com/v6/{API}/latest/INR"
response = requests.get(url)
data = response.json()

with open(bronze_path_api, "w") as file:
    json.dump(data, file, indent=4)

df = pd.read_json(bronze_path_api)
#print(df)

from storage.parquet_store import silver_parquet_api

silver_parquet_api(bronze_path_api,silver_path_api)