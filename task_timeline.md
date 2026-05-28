# Project Task Timeline & Progress Log

This file tracks the modernization tasks completed, in progress, and planned for the ETL/ELT data engineering pipeline. It serves as a living document to guide both the developer and subsequent AI agents.

---

## 📋 Status Overview
- **Project Location**: `/Users/kevinshah/Desktop/project`
- **Completed Phases**: Pipeline Entry Points, SQL Upserts (Medallion Gold Loading)
- **Next Target**: Environment Isolation (Dockerization)

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
*   [x] Restructure Python scripts into distinct pipeline tasks.
*   [x] Define a Directed Acyclic Graph (DAG) with task dependencies.
*   [x] Add task retry logic with exponential backoff, especially for API request operations.

### [/] Phase 6: Observability (Logging, Configuration, Alerting) (IN PROGRESS)
*   [x] Refactor raw print statements to use the Python standard `logging` library with structured format outputs.
*   [x] Centralize configuration variables in a unified settings module using `pydantic-settings`.
*   [ ] Add an alert dispatcher to ping webhooks (e.g. Slack/Discord) upon task failures.

### [/] Phase 7: Testing & CI/CD Pipeline (IN PROGRESS)
*   [x] Write unit tests for cleaning functions in [ingestion/csv_ingest.py](file:///Users/kevinshah/Desktop/project/ingestion/csv_ingest.py) using `pytest`.
*   [ ] Set up database mocks or transaction rollbacks for testing database load operations.
*   [ ] Create a GitHub Actions workflow (`.github/workflows/ci.yml`) to run tests and linters (`ruff`/`flake8`) automatically on every commit.

---

## 📈 Context for Future AI Agents
*   **Database Credentials**: Located in [.env](file:///Users/kevinshah/Desktop/project/.env)
*   **Execution Command**: Run `python3 main.py` in `/Users/kevinshah/Desktop/project` to execute the current pipeline.
*   **Ingestion Logic**: CSV logic resides in [ingestion/csv_ingest.py](file:///Users/kevinshah/Desktop/project/ingestion/csv_ingest.py). API logic resides in [ingestion/api_ingest.py](file:///Users/kevinshah/Desktop/project/ingestion/api_ingest.py).
*   **Storage Logic**: Parquet formatting resides in [storage/parquet_store.py](file:///Users/kevinshah/Desktop/project/storage/parquet_store.py). PostgreSQL connection and staging-table loading resides in [storage/postgre_store.py](file:///Users/kevinshah/Desktop/project/storage/postgre_store.py).
*   **Staging Upsert Pattern**: Instead of dropping tables, data is written to `temp_stage_<table_name>` and upserted using a native SQL merge statement (`ON CONFLICT`). Target schemas are explicitly generated.
