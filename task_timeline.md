# Project Task Timeline & Progress Log

This file tracks the modernization tasks completed, in progress, and planned for the ETL/ELT data engineering pipeline. It serves as a living document to guide both the developer and subsequent AI agents.

---

## 📋 Status Overview
- **Project Location**: `/Users/kevinshah/Desktop/project`
- **Completed Phases**: 1 (Entry Points), 2 (SQL Upserts), 3 (Docker), 4 (Data Quality), 5 (Airflow), 5b (API Gold Layer)
- **In Progress**: Phase 6 (Alerting), Phase 7 (CI/CD + Tests)
- **Industry Upgrade Queue**: Phase 8 (GitHub Actions CI/CD) → Phase 9 (Metabase Dashboard) → Phase 10 (Incremental Loading) → Phase 11 (dbt) → Phase 12 (S3/LocalStack) → Phase 13 (Full Docker Stack)

---

## 🛠️ Detailed Task Checklist

### [x] Phase 1: Entry Point Standardization & Integration (COMPLETED)
*   [x] Wrap [ingestion/api_ingest.py](file:///Users/kevinshah/Desktop/project/ingestion/api_ingest.py) script execution logic in a `main()` function to prevent automatic execution when imported.
*   [x] Update [main.py](file:///Users/kevinshah/Desktop/project/main.py) to import and orchestrate both the CSV and API pipelines sequentially.
*   [x] Verify sequential execution of the CSV and API pipelines.

### [x] Phase 2: Relational Schema Modeling & SQL Upserts (COMPLETED)
*   [x] Replace destructive `if_exists="replace"` in [storage/postgre_store.py](file:///Users/kevinshah/Desktop/project/storage/postgre_store.py) to preserve database schemas, keys, constraints, and historical records.
*   [x] Implement a staging-table-based `UPSERT` (`INSERT ... ON CONFLICT DO UPDATE`) strategy inside [storage/postgre_store.py](file:///Users/kevinshah/Desktop/project/storage/postgre_store.py) with explicit column mapping and type definitions for each table.
*   [x] Validate table schema creation (`CREATE TABLE IF NOT EXISTS`) and primary key constraint additions.
*   [x] Run the pipeline to confirm successful database loads.

### [x] Phase 3: Infrastructure Containerization (COMPLETED)
*   [x] Create a `Dockerfile` for the Python pipeline to make the application runtime environment portable.
*   [x] Create a `docker-compose.yml` to orchestrate containerized services:
    *   PostgreSQL (Data Warehouse)
    *   LocalStack (Optional: to mock AWS S3 for cloud-like storage)
    *   Orchestration agent (Prefect / Airflow)
*   [x] Update connection configuration in [.env](file:///Users/kevinshah/Desktop/project/.env) to leverage Docker network hostname resolution (`postgres` instead of `127.0.0.1`).

### [x] Phase 4: Data Quality & Schema Validation (COMPLETED)
*   [x] Install `pandera` for runtime schema enforcement.
*   [x] Define schemas for e-commerce datasets (customers, orders, payments) describing data types, check thresholds, unique keys, and nullable parameters.
*   [x] Integrate Pandera validation checks into [ingestion/csv_ingest.py](file:///Users/kevinshah/Desktop/project/ingestion/csv_ingest.py) to validate data boundaries before copying to Bronze and Silver layers.
*   [x] Establish a "quarantine" zone to save rows that fail validation rather than crashing the pipeline.

### [x] Phase 5: Production-Grade Orchestration (COMPLETED)
*   [x] Pick an orchestrator (Apache Airflow).
*   [x] Restructure Python scripts into distinct pipeline tasks (`ingest_bronze`, `ingest_silver`, `ingest_gold`).
*   [x] Define a Directed Acyclic Graph (DAG) with task dependencies in [airflow/dags/medallion_etl.py](file:///Users/kevinshah/Desktop/project/airflow/dags/medallion_etl.py).
*   [x] Add task retry logic with exponential backoff, especially for API request operations.
*   [x] Decouple monolithic pipeline into granular per-layer tasks for independent retries.

### [x] Phase 5b: API Gold Layer — `inr_rates` PostgreSQL Load (COMPLETED — 2026-05-28)
*   [x] Add `inr_rates` upsert block to [storage/postgre_store.py](file:///Users/kevinshah/Desktop/project/storage/postgre_store.py):
    *   Schema: `currency VARCHAR PRIMARY KEY, rate NUMERIC`
    *   Strategy: `INSERT ... SELECT FROM staging ON CONFLICT (currency) DO UPDATE SET rate = EXCLUDED.rate`
*   [x] Update [storage/parquet_store.py](file:///Users/kevinshah/Desktop/project/storage/parquet_store.py) — `silver_parquet_api` already returns the DataFrame (no change needed).
*   [x] Update [ingestion/api_ingest.py](file:///Users/kevinshah/Desktop/project/ingestion/api_ingest.py) to capture `df_silver` and call `put_in_postgre(df_silver, "inr_rates")` after the Parquet write.
*   [x] Run `python -m ingestion.api_ingest` — completed successfully with no errors.
*   [x] Exchange rate data now flows through the full Bronze → Silver → Gold pipeline.

### [/] Phase 6: Observability (Logging, Configuration, Alerting) (IN PROGRESS)
*   [x] Refactor raw print statements to use the Python standard `logging` library with structured format outputs.
*   [x] Centralize configuration variables in a unified settings module using `pydantic-settings`.
*   [ ] Add an alert dispatcher to ping webhooks (e.g. Slack/Discord) upon task failures via Airflow `on_failure_callback`.

### [/] Phase 7: Testing & CI/CD Pipeline (IN PROGRESS)
*   [x] Write unit tests for cleaning functions in [ingestion/csv_ingest.py](file:///Users/kevinshah/Desktop/project/ingestion/csv_ingest.py) using `pytest`.
*   [ ] Set up database mocks or transaction rollbacks for testing database load operations.
*   [ ] Create a GitHub Actions workflow (`.github/workflows/ci.yml`) to run `pytest` and `ruff` linter automatically on every commit.

---

## 🚀 Industry-Level Upgrade Roadmap

### [ ] Phase 8: CI/CD — GitHub Actions (HIGH PRIORITY — 1 day)
*   [ ] Create `.github/workflows/ci.yml` workflow file.
*   [ ] Add job to install dependencies from `requirements.txt` and run `pytest`.
*   [ ] Add `ruff` linting step to enforce code style on every push.
*   [ ] Add secrets scanning step to prevent credentials being committed.
*   [ ] Badge the README with build status.
*   *Why*: Every company uses CI/CD. This is the single highest-signal addition for a portfolio project.

### [ ] Phase 9: BI Dashboard — Metabase (HIGH PRIORITY — 2 hours)
*   [ ] Add `metabase` service to `docker-compose.yml` (official Docker image: `metabase/metabase`).
*   [ ] Connect Metabase to the local PostgreSQL Gold layer.
*   [ ] Build dashboards:
    *   Orders by status (bar chart).
    *   Revenue by customer state (map/bar).
    *   INR exchange rates table (live from `inr_rates`).
*   [ ] Screenshot dashboards and embed in `README.md`.
*   *Why*: Recruiters are not engineers — a visual dashboard makes the project tangible and memorable.

### [ ] Phase 10: Incremental Loading with Watermarks (HIGH PRIORITY — 2 days)
*   [ ] Add a `pipeline_state` table in PostgreSQL to track `last_loaded_at` timestamps per dataset.
*   [ ] Modify `ingest_bronze` to filter source records using the stored watermark (`WHERE updated_at > last_loaded_at`).
*   [ ] Update the watermark atomically after a successful Gold load.
*   [ ] Update the Airflow DAG to pass the watermark value between tasks via XCom.
*   *Why*: Loading all data on every run doesn't scale. Watermark-based incremental loading is how every real pipeline works.

### [ ] Phase 11: dbt Gold Layer Transformations (HIGH IMPACT — 1 week)
*   [ ] Install `dbt-postgres` and initialise a dbt project (`dbt init`).
*   [ ] Move raw SQL upsert logic out of `postgre_store.py` into dbt models.
*   [ ] Build dimensional models (Kimball star schema):
    *   `dim_customers.sql` — customer dimension.
    *   `dim_dates.sql` — date dimension derived from order timestamps.
    *   `fct_orders.sql` — fact table joining orders + payments + customers.
    *   `fct_revenue_by_state.sql` — pre-aggregated metric for dashboards.
*   [ ] Add dbt schema tests (`not_null`, `unique`, `accepted_values`) to replace Pandera checks at the warehouse layer.
*   [ ] Generate and host dbt docs (`dbt docs generate && dbt docs serve`).
*   [ ] Integrate `dbt run` as an Airflow task after the Gold load tasks.
*   *Why*: dbt is THE industry standard for warehouse transformations. Listed in almost every Data Engineer / Analytics Engineer JD.

### [ ] Phase 12: Cloud Storage — S3 via LocalStack (MEDIUM — 2 days)
*   [ ] Enable and configure the `localstack` service in `docker-compose.yml` with S3 enabled.
*   [ ] Install `boto3` and create an S3 client helper in `storage/s3_store.py`.
*   [ ] Replace local filesystem writes in `ingest_bronze` and `ingest_silver` with S3 uploads:
    *   Bronze: `s3://bronze-bucket/csv_store/` and `s3://bronze-bucket/api_store/`
    *   Silver: `s3://silver-bucket/csv_store/` and `s3://silver-bucket/api_store/`
*   [ ] Update readers to read Parquet from S3 using `pandas.read_parquet("s3://...")`.
*   [ ] Document LocalStack setup in `README.md`.
*   *Why*: Production pipelines never write to local disk. S3/GCS is the standard Bronze/Silver store. LocalStack lets you simulate it for free.

### [ ] Phase 13: Full Portable Docker Compose Stack (MEDIUM — 1 day)
*   [ ] Complete `docker-compose.yml` to include all services:
    *   `postgres` — Gold layer data warehouse.
    *   `airflow-webserver` + `airflow-scheduler` — orchestration.
    *   `localstack` — mock S3 for Bronze/Silver.
    *   `metabase` — BI dashboard.
*   [ ] Add a `Makefile` with convenience commands:
    *   `make up` → `docker-compose up -d`
    *   `make pipeline` → trigger the Airflow DAG via REST API
    *   `make test` → run `pytest` in container
    *   `make down` → `docker-compose down -v`
*   [ ] Verify a clean `make up && make pipeline` works end-to-end from scratch.
*   *Why*: A recruiter or hiring manager should be able to clone the repo and run the entire stack in one command.

---

## 📈 Context for Future AI Agents
*   **Database Credentials**: Located in [.env](file:///Users/kevinshah/Desktop/project/.env)
*   **Execution Command**: Run `python3 main.py` in `/Users/kevinshah/Desktop/project` to execute the full pipeline (CSV + API, all three layers).
*   **API Execution**: Run `python -m ingestion.api_ingest` to run only the exchange-rate pipeline (Bronze → Silver → Gold for `inr_rates`).
*   **Ingestion Logic**: CSV logic resides in [ingestion/csv_ingest.py](file:///Users/kevinshah/Desktop/project/ingestion/csv_ingest.py). API logic resides in [ingestion/api_ingest.py](file:///Users/kevinshah/Desktop/project/ingestion/api_ingest.py).
*   **Storage Logic**: Parquet formatting resides in [storage/parquet_store.py](file:///Users/kevinshah/Desktop/project/storage/parquet_store.py). PostgreSQL connection and staging-table loading resides in [storage/postgre_store.py](file:///Users/kevinshah/Desktop/project/storage/postgre_store.py).
*   **Staging Upsert Pattern**: All four tables (`olist_customers`, `olist_orders`, `olist_order_payments`, `inr_rates`) write to `temp_stage_<table_name>` and upsert using `ON CONFLICT`. Staging table is dropped atomically within the same transaction.
*   **Gold Tables in PostgreSQL**: `olist_customers`, `olist_orders`, `olist_order_payments`, `inr_rates`.
*   **Next Industry Upgrades**: See Phases 8–13 above. Recommended order: Phase 8 (CI/CD) → Phase 9 (Metabase) → Phase 10 (Incremental) → Phase 11 (dbt) → Phase 12 (S3) → Phase 13 (Full Docker).

