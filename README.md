# Enterprise ETL & Data Engineering Pipeline

## Overview
This project is an end-to-end ETL pipeline that ingests data from APIs and CSV files, processes it through a layered architecture (Bronze → Silver → Gold), and prepares it for analytics use cases.

## Architecture
External Data Sources (API + CSV)
→ Bronze Layer (Raw JSON/CSV storage)
→ Silver Layer (Cleaned + Parquet format)
→ Gold Layer (PostgreSQL analytics-ready data)

## Tech Stack
Python, Pandas, Requests, PostgreSQL, SQLAlchemy, PyArrow, dotenv

## Features
- Multi-source data ingestion (API + CSV)
- ETL layered architecture (Bronze/Silver/Gold)
- JSON normalization and transformation
- Parquet-based storage optimization
- PostgreSQL integration for analytics

## Project Structure
ingestion/ (API + CSV pipelines)  
storage/ (Parquet + PostgreSQL handlers)  
data/bronze/ (raw data)  
data/silver/ (processed data)  
main.py (pipeline runner)

## Use Cases
- Currency rate analysis
- E-commerce analytics
- Cross-source data integration
- Business KPI generation

## Future Improvements
- Airflow orchestration
- AWS cloud migration (S3 + RDS)
- Kafka streaming ingestion
- Data quality validation layer
- Star schema modeling (fact & dimension tables)
- BI dashboard integration

## Key Learnings
ETL design, data modeling, API ingestion, data transformation, parquet storage, and PostgreSQL analytics layer design.

## Author
Kevin Shah