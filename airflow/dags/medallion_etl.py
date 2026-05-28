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

# Import main ingestion functions
from ingestion.csv_ingest import main as run_csv_pipeline
from ingestion.api_ingest import main as run_api_pipeline

default_args = {
    'owner': 'Kevin Shah',
    'depends_on_past': False,
    'start_date': datetime(2026, 5, 28),
    'email_on_failure': False,
    'email_on_retry': False,
}

with DAG(
    'medallion_etl_pipeline',
    default_args=default_args,
    description='Orchestrates parallel CSV and API Ingestion pipelines',
    schedule_interval=None,  # Run manually
    catchup=False,
    tags=['medallion', 'etl'],
) as dag:

    start = EmptyOperator(
        task_id='start',
    )

    csv_ingestion = PythonOperator(
        task_id='csv_ingestion',
        python_callable=run_csv_pipeline,
        retries=1,
        retry_delay=timedelta(seconds=30),
    )

    api_ingestion = PythonOperator(
        task_id='api_ingestion',
        python_callable=run_api_pipeline,
        retries=3,
        retry_delay=timedelta(minutes=1),
        retry_exponential_backoff=True,
    )

    end = EmptyOperator(
        task_id='end',
    )

    start >> [csv_ingestion, api_ingestion] >> end
