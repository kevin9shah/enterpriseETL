# Enterprise ETL Data Engineering Pipeline

## Overview
This project is a multi-source ETL (Extract, Transform, Load) pipeline that processes data from APIs and CSV files, applies data cleaning and transformation, and stores it in structured formats using a layered architecture (Bronze → Silver → Gold).

The goal is to simulate a real-world data engineering system used in industry for analytics and reporting.

---

## Architecture

The pipeline follows a layered data engineering approach:

API Data (Exchange Rates) + CSV Data (E-commerce Dataset)
                ↓
        Bronze Layer (Raw Data Storage - JSON/CSV)
                ↓
        Silver Layer (Cleaned & Transformed Data - Parquet)
                ↓
        Gold Layer (PostgreSQL - Analytics Ready Data)

---

## Tech Stack

- Python
- Pandas
- Requests (API calls)
- PostgreSQL
- SQLAlchemy
- PyArrow (Parquet storage)
- dotenv (environment variables)

---

## Features

- Multi-source data ingestion (API + CSV)
- Bronze-Silver data pipeline architecture
- JSON normalization and transformation
- Parquet-based columnar storage optimization
- PostgreSQL integration setup
- Modular and scalable ETL design

---

## Project Structure

ingestion/
│   api_ingest.py
│   csv_ingest.py
│   db_ingest.py

storage/
│   parquet_store.py
│   postgre_store.py

data/
│   bronze/
│   silver/

main.py
requirements.txt
README.md

---

## How to Run

### 1. Install dependencies
pip install -r requirements.txt

### 2. Run CSV ingestion pipeline
python ingestion/csv_ingest.py

### 3. Run API ingestion pipeline
python ingestion/api_ingest.py

---

## Key Learning Outcomes

- Built a real-world ETL pipeline
- Understood data lake architecture (Bronze/Silver/Gold)
- Learned API ingestion and JSON normalization
- Worked with Parquet for efficient storage
- Integrated PostgreSQL for structured analytics storage

---

## Future Improvements

- Add orchestration using Airflow
- Implement logging and monitoring
- Add Docker support for deployment
- Build dashboard using Streamlit or React
- Add real-time streaming ingestion

---

## Author
Kevin Shah