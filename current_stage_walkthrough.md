# Project Walkthrough: Current Stage Technical Explanation

This document explains the technical details, design patterns, and code implementations completed during the current stage of the project.

---

## 1. Pipeline Orchestration & Entry Points

### The Initial Problem
Previously, when files like [api_ingest.py](file:///Users/kevinshah/Desktop/project/ingestion/api_ingest.py) were imported, all the code inside them (e.g. sending network requests to the exchange API and writing JSON files) ran immediately. Additionally, [main.py](file:///Users/kevinshah/Desktop/project/main.py) was only an import statement, meaning running the main file did not execute the full pipeline.

### The Technical Solution
We wrapped the ETL steps inside independent `main()` functions:
- **`ingestion/api_ingest.py`**: The API call and file storage logic are now placed inside a `def main():` block. It will only run when directly executed or when its `main()` function is explicitly called.
- **`main.py`**: Acts as a central orchestrator. It imports both pipelines and executes them in sequence:
  ```python
  from ingestion.csv_ingest import main as run_csv_pipeline
  from ingestion.api_ingest import main as run_api_pipeline

  def main():
      run_csv_pipeline()
      run_api_pipeline()
  ```

---

## 2. High-Performance SQL Staging & Upserts

### The Initial Problem
Originally, your database loader in [storage/postgre_store.py](file:///Users/kevinshah/Desktop/project/storage/postgre_store.py) was configured with `if_exists="replace"`.
Every time the pipeline ran:
1. PostgreSQL dropped the target tables.
2. PostgreSQL recreated the tables from scratch.
3. This destroyed all table indexes, primary key constraints, foreign key relationships, database views, and historical records.

### The Technical Solution (Staging Table Strategy)
To keep the code clean and easy to read while maintaining production performance, we implemented a **Staging Table Upsert Strategy** inside [storage/postgre_store.py](file:///Users/kevinshah/Desktop/project/storage/postgre_store.py):

```mermaid
graph TD
    DF["Pandas DataFrame"] -->|1. Write Bulk| TempTable["temp_stage_<table> (Overwritten)"]
    TempTable -->|2. SQL INSERT...SELECT ON CONFLICT| TargetTable["target_<table> (Primary Key Guarded)"]
    TargetTable -->|3. Clean Up| DropTemp["DROP TABLE temp_stage_<table>"]
```

#### Step-by-Step Breakdown of the Database Load Logic:

1. **Staging Bulk Load**:
   First, we save the DataFrame into a temporary staging table named `temp_stage_<table_name>` using Pandas' standard bulk writer.
   ```python
   staging_table = f"temp_stage_{table_name}"
   df.to_sql(staging_table, engine, if_exists="replace", index=False)
   ```
   *Why*: This is extremely fast because it is a direct bulk load into a temp table rather than writing row-by-row.

2. **Schema Protection**:
   If the target table does not exist yet (e.g. on the first run), we create it with correct database types and set its **Primary Key** constraint so that PostgreSQL knows how to identify duplicates.
   ```sql
   CREATE TABLE IF NOT EXISTS olist_customers (
       customer_id VARCHAR PRIMARY KEY,
       customer_unique_id VARCHAR,
       customer_zip_code_prefix INT,
       customer_city VARCHAR,
       customer_state VARCHAR
   );
   ```

3. **Atomic SQL Upsert**:
   We execute a database-side merge (`ON CONFLICT`). It inserts new records, but if a primary key conflict occurs, it updates the existing row with the incoming staging table data.
   ```sql
   INSERT INTO olist_customers (customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state)
   SELECT customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state 
   FROM temp_stage_olist_customers
   ON CONFLICT (customer_id) 
   DO UPDATE SET 
       customer_unique_id = EXCLUDED.customer_unique_id,
       customer_zip_code_prefix = EXCLUDED.customer_zip_code_prefix,
       customer_city = EXCLUDED.customer_city,
       customer_state = EXCLUDED.customer_state;
   ```
   *Why*: Doing this directly inside PostgreSQL is hundreds of times faster than doing it in Python.

4. **Cleanup**:
   Finally, we drop the temporary staging table so we do not leave garbage behind in the database:
   ```sql
   DROP TABLE IF EXISTS temp_stage_<table_name>;
   ```

---

## 3. How to Run and Verify

1. **Verify your database credentials** are correct inside your [.env](file:///Users/kevinshah/Desktop/project/.env) file.
2. **Execute the pipeline** from your workspace terminal:
   ```bash
   python3 main.py
   ```
3. **Verify the outputs**:
   - The CSV ingestion pipeline will read, clean, and write Olist datasets to Silver Parquet, and upsert them to PostgreSQL.
   - The Exchange Rate API pipeline will pull exchange rates, save the Bronze JSON, convert the output to Silver Parquet, **and load it into the `inr_rates` Gold table in PostgreSQL**.

---

## 4. API Gold Layer — `inr_rates` PostgreSQL Load

### The Problem
Previously the exchange-rate pipeline stopped at the Silver layer. While `olist_*` tables were being written to PostgreSQL via the staging upsert strategy, `inr_rates` data lived only in `data/silver/api_store/inr_rates.parquet` and was never promoted to the Gold warehouse. This broke the symmetry of the Medallion Architecture for the API source.

### The Solution

#### Step 1 — `postgre_store.py`: Add the `inr_rates` upsert block

Added an `elif table_name == "inr_rates":` branch to `put_in_postgre` with:
```sql
CREATE TABLE IF NOT EXISTS inr_rates (
    currency VARCHAR PRIMARY KEY,
    rate NUMERIC
);

INSERT INTO inr_rates (currency, rate)
SELECT currency, rate
FROM temp_stage_inr_rates
ON CONFLICT (currency)
DO UPDATE SET
    rate = EXCLUDED.rate;
```
*Why*: The `currency` column (e.g. `"USD"`, `"EUR"`) is a natural primary key. On repeat runs the rate simply gets overwritten — exactly what you want for exchange rate data.

#### Step 2 — `api_ingest.py`: Wire Gold layer after Silver write

```python
from storage.postgre_store import put_in_postgre

# Capture the DataFrame returned by silver_parquet_api
df_silver = silver_parquet_api(bronze_path_api, silver_path_api)

# Load into PostgreSQL Gold layer
put_in_postgre(df_silver, "inr_rates")
```
*Why*: `silver_parquet_api` already returned the DataFrame; we just needed to capture it and pass it downstream. No changes to `parquet_store.py` were required.

#### Result
Running `python -m ingestion.api_ingest` now completes the **full Bronze → Silver → Gold** flow for exchange rates. The `inr_rates` table in PostgreSQL is idempotent — re-running the pipeline updates rates in-place without creating duplicates.

```mermaid
graph LR
    API["Exchange Rate API"] -->|HTTP GET| Bronze["Bronze: inr_rates.json"]
    Bronze -->|silver_parquet_api| Silver["Silver: inr_rates.parquet"]
    Silver -->|put_in_postgre| Staging["temp_stage_inr_rates"]
    Staging -->|ON CONFLICT currency DO UPDATE| Gold["Gold: inr_rates (PostgreSQL)"]
    Staging -->|DROP TABLE| Cleanup["Staging Cleaned Up"]
```
