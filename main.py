import sys
from pathlib import Path
import logging

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Ensure logs directory exists
(BASE_DIR / "logs").mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(BASE_DIR / "logs/pipeline.log")
    ]
)
logger = logging.getLogger(__name__)

from ingestion.csv_ingest import main as run_csv_pipeline
from ingestion.api_ingest import main as run_api_pipeline

def main():
    logger.info("=== Starting ETL Data Pipeline ===")
    try:
        # 1. Run CSV Ingestion (Bronze -> Silver -> Gold)
        run_csv_pipeline()
        
        # 2. Run API Ingestion (Bronze -> Silver)
        run_api_pipeline()
        
        logger.info("=== ETL Data Pipeline Finished Successfully ===")
    except Exception as e:
        logger.error(f"Pipeline failed with exception: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
