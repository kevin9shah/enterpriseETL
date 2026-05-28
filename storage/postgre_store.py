from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import logging
from config.settings import settings

engine = create_engine(
    f"postgresql+psycopg2://{settings.db_user}:{settings.db_pass}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
)

logger = logging.getLogger(__name__)

def get_connection():
    try:
        return engine.connect()
    except Exception as e:
        logger.error(f"Connection error: {e}")
        return False

def connect():
    conn = get_connection()
    if conn:
        logger.info("Connected to database successfully")
        conn.close()
    else:
        logger.error("Failed to connect to database")

def put_in_postgre(df, table_name):
    # Define temporary staging table name
    staging_table = f"temp_stage_{table_name}"
    
    # 2. Use simple if/else blocks to execute explicit SQL queries for each table
    query = ""
    
    if table_name == "olist_customers":
        query = f"""
        -- Step A: Create target table if it does not exist
        CREATE TABLE IF NOT EXISTS olist_customers (
            customer_id VARCHAR PRIMARY KEY,
            customer_unique_id VARCHAR,
            customer_zip_code_prefix INT,
            customer_city VARCHAR,
            customer_state VARCHAR
        );
        
        -- Step B: Insert data from staging, updating existing rows on conflict
        INSERT INTO olist_customers (customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state)
        SELECT customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state 
        FROM {staging_table}
        ON CONFLICT (customer_id) 
        DO UPDATE SET 
            customer_unique_id = EXCLUDED.customer_unique_id,
            customer_zip_code_prefix = EXCLUDED.customer_zip_code_prefix,
            customer_city = EXCLUDED.customer_city,
            customer_state = EXCLUDED.customer_state;
        """
        
    elif table_name == "olist_orders":
        query = f"""
        -- Step A: Create target table if it does not exist
        CREATE TABLE IF NOT EXISTS olist_orders (
            order_id VARCHAR PRIMARY KEY,
            customer_id VARCHAR,
            order_status VARCHAR,
            order_purchase_timestamp TIMESTAMP,
            order_approved_at TIMESTAMP,
            order_delivered_carrier_date TIMESTAMP,
            order_delivered_customer_date TIMESTAMP,
            order_estimated_delivery_date TIMESTAMP,
            order_date DATE
        );
        
        -- Step B: Insert data from staging, updating existing rows on conflict
        INSERT INTO olist_orders (order_id, customer_id, order_status, order_purchase_timestamp, order_approved_at, order_delivered_carrier_date, order_delivered_customer_date, order_estimated_delivery_date, order_date)
        SELECT order_id, customer_id, order_status, order_purchase_timestamp, order_approved_at, order_delivered_carrier_date, order_delivered_customer_date, order_estimated_delivery_date, order_date
        FROM {staging_table}
        ON CONFLICT (order_id)
        DO UPDATE SET
            customer_id = EXCLUDED.customer_id,
            order_status = EXCLUDED.order_status,
            order_purchase_timestamp = EXCLUDED.order_purchase_timestamp,
            order_approved_at = EXCLUDED.order_approved_at,
            order_delivered_carrier_date = EXCLUDED.order_delivered_carrier_date,
            order_delivered_customer_date = EXCLUDED.order_delivered_customer_date,
            order_estimated_delivery_date = EXCLUDED.order_estimated_delivery_date,
            order_date = EXCLUDED.order_date;
        """
        
    elif table_name == "olist_order_payments":
        query = f"""
        -- Step A: Create target table if it does not exist
        CREATE TABLE IF NOT EXISTS olist_order_payments (
            order_id VARCHAR PRIMARY KEY,
            payment_value NUMERIC
        );
        
        -- Step B: Insert data from staging, updating existing rows on conflict
        INSERT INTO olist_order_payments (order_id, payment_value)
        SELECT order_id, payment_value
        FROM {staging_table}
        ON CONFLICT (order_id)
        DO UPDATE SET
            payment_value = EXCLUDED.payment_value;
        """
        
    else:
        # Fallback for tables we didn't explicitly model yet
        with engine.begin() as conn:
            df.to_sql(table_name, conn, if_exists="append", index=False)
        logger.info(f"Appended data to {table_name}")
        return

    # 3. Execute staging write, SQL query and drop the staging table inside a single transaction
    with engine.begin() as conn:
        df.to_sql(staging_table, conn, if_exists="replace", index=False)
        conn.execute(text(query))
        conn.execute(text(f"DROP TABLE IF EXISTS {staging_table};"))
        
    logger.info(f"Data successfully upserted into database table: {table_name}")


