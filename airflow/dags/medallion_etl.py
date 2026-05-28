import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator

# Import granular ingestion functions
from ingestion.csv_ingest import ingest_bronze, ingest_silver, ingest_gold
from ingestion.api_ingest import main as run_api_pipeline

default_args = {
    'owner': 'Kevin Shah',
    'depends_on_past': False,
    'start_date': datetime(2026, 5, 28),
    'email_on_failure': False,
    'email_on_retry': False,
}

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

with DAG(
    'medallion_etl_pipeline',
    default_args=default_args,
    description='Orchestrates decoupled parallel Medallion ETL steps (Bronze -> Silver -> Gold)',
    schedule_interval=None,  # Run manually
    catchup=False,
    tags=['medallion', 'etl'],
) as dag:

    start = EmptyOperator(
        task_id='start',
    )

    end = EmptyOperator(
        task_id='end',
    )

    # API Ingestion task remains standard and runs in parallel
    api_ingestion = PythonOperator(
        task_id='api_ingestion',
        python_callable=run_api_pipeline,
        retries=3,
        retry_delay=timedelta(minutes=1),
        retry_exponential_backoff=True,
    )

    start >> api_ingestion >> end

    # Loop dynamically to create parallel pipelines for each CSV table
    for dataset in DATASETS:
        t_name = dataset["table_name"]
        f_name = dataset["file_name"]

        # Bronze Layer (Raw Extraction)
        bronze_task = PythonOperator(
            task_id=f"bronze_{t_name}",
            python_callable=ingest_bronze,
            op_kwargs={"table_name": t_name, "file_name": f_name},
        )

        # Silver Layer (Cleaning & Quality Gate validations)
        silver_task = PythonOperator(
            task_id=f"silver_{t_name}",
            python_callable=ingest_silver,
            op_kwargs={"table_name": t_name, "file_name": f_name},
            retries=1,
            retry_delay=timedelta(seconds=30),
        )

        # Gold Layer (PostgreSQL native load and upserts)
        gold_task = PythonOperator(
            task_id=f"gold_{t_name}",
            python_callable=ingest_gold,
            op_kwargs={"table_name": t_name, "file_name": f_name},
            retries=1,
            retry_delay=timedelta(seconds=30),
        )

        # Configure linear dependencies for the dataset: Start -> Bronze -> Silver -> Gold -> End
        start >> bronze_task >> silver_task >> gold_task >> end
