"""
Root conftest.py
Patches config.settings.settings before any module that imports it is loaded,
so that tests don't require a live .env or real database.
"""
import os
import sys
from pathlib import Path

# Ensure the project root is on the path for all tests
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Provide dummy env vars so pydantic-settings doesn't fail on import
# ---------------------------------------------------------------------------
os.environ.setdefault("EXCHANGE_RATE_API_KEY", "test-dummy-key")
os.environ.setdefault("DB_NAME", "test_db")
os.environ.setdefault("DB_USER", "test_user")
os.environ.setdefault("DB_PASS", "test_pass")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
