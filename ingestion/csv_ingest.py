from pathlib import Path
import sys
from ingestion.schemas import SCHEMA_MAP
import pandera as pa
import logging
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

import pandas as pd
from storage.parquet_store import silver_parquet
from storage.postgre_store import put_in_postgre


logger = logging.getLogger(__name__)

# Configuration for datasets to ingest
DATASETS = [
    {
        "table_name": "olist_customers",
        "file_name": "olist_customers_dataset",
    },
    {
        "table_name": "olist_orders",
        "file_name": "olist_orders_dataset",
    },
    {
        "table_name": "olist_order_payments",
        "file_name": "olist_order_payments_dataset",
    }
]

def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.lower()
    df = df.drop_duplicates()
    df["customer_state"] = df["customer_state"].str.upper()
    df["customer_city"] = df["customer_city"].str.lower().str.strip()
    return df

def clean_orders(df : pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.lower()
    df = df.drop_duplicates()
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
    df["order_date"] = df["order_purchase_timestamp"].dt.date
    df["order_approved_at"] = pd.to_datetime(df["order_approved_at"])
    df["order_delivered_carrier_date"] = pd.to_datetime(df["order_delivered_carrier_date"])
    df["order_delivered_customer_date"] = pd.to_datetime(df["order_delivered_customer_date"])
    df["order_estimated_delivery_date"] = pd.to_datetime(df["order_estimated_delivery_date"])
    return df

def clean_payments(df : pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.lower()
    df = df.drop_duplicates()
    df = df.groupby("order_id", as_index=False)["payment_value"].sum()
    return df

def main():
    for dataset in DATASETS:
        table_name = dataset["table_name"]
        file_name = dataset["file_name"]
        
        source_path = BASE_DIR / f"dataset/{file_name}.csv"
        bronze_path = BASE_DIR / f"data/bronze/csv_store/{file_name}.csv"
        silver_path = BASE_DIR / f"data/silver/csv_store/{file_name}.parquet"
        
        # Check if source file exists
        if not source_path.exists():
            logger.warning(f"Skipping {file_name}: Source file not found at {source_path}")
            continue
            
        logger.info(f"--- Starting CSV ingestion for {table_name} ---")
        
        # 1. Bronze Layer (Raw Ingestion)
        df = pd.read_csv(source_path)
        if df.empty:
            logger.warning(f"{file_name}.csv is empty, skipping ingestion.")
            continue
            
        logger.info(f"Successfully read data from source ({len(df)} rows)")
        bronze_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(bronze_path, index=False)
        logger.info(f"Data successfully ingested in bronze layer at {bronze_path}")
        
        # 2. Silver Layer (Cleaning & Parquet Format)
        df.columns = df.columns.str.lower()
        df = df.drop_duplicates()
        if table_name == "olist_customers":
            df = clean_customers(df)
        elif table_name == "olist_order_payments":
            df = clean_payments(df)
        elif table_name == "olist_orders":
            df = clean_orders(df)
        else:
            df.columns = df.columns.str.lower()
            df = df.drop_duplicates()
            
        # --- DATA QUALITY GATE ---
        schema = SCHEMA_MAP.get(table_name)
        if schema:
            try:
                # Validate the cleaned DataFrame
                df = schema.validate(df, lazy=True)
                logger.info(f"Data validation passed for {table_name}")
            except pa.errors.SchemaErrors as err:
                logger.warning(f"Data validation failed for {table_name}!")
                # Get the rows that failed checks
                failure_cases = err.failure_cases
                logger.warning(f"Found {len(failure_cases)} validation errors.")
                
                # Create quarantine folder and write failures
                quarantine_path = BASE_DIR / f"data/quarantine/{file_name}_failures.csv"
                quarantine_path.parent.mkdir(parents=True, exist_ok=True)
                failure_cases.to_csv(quarantine_path, index=False)
                logger.info(f"Quarantined validation errors saved to {quarantine_path}")
                
                # Drop rows that failed validation to let clean data proceed
                failed_indices = failure_cases["index"].dropna().astype(int).unique()
                df = df.drop(index=failed_indices, errors="ignore")
                logger.info(f"Proceeding with {len(df)} valid records.")
        # -------------------------
      
        silver_path.parent.mkdir(parents=True, exist_ok=True)
        silver_parquet(df, silver_path)

        # 3. Gold Layer (PostgreSQL)
        df_silver = pd.read_parquet(silver_path)
        put_in_postgre(df_silver, table_name)

if __name__ == "__main__":
    main()
