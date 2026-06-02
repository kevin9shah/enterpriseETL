"""
Tests for storage/postgre_store.py

Uses unittest.mock to patch SQLAlchemy's engine so no live database connection
is required.  The tests verify:
  1. The staging table is written with df.to_sql()
  2. The correct upsert SQL is executed (CREATE TABLE IF NOT EXISTS + INSERT ... ON CONFLICT)
  3. The staging table is dropped at the end of the transaction
  4. The operation runs inside a single transaction (engine.begin() used once)
"""
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch, call


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_conn():
    """Return a mock connection that supports context-manager usage."""
    conn = MagicMock()
    conn.__enter__ = MagicMock(return_value=conn)
    conn.__exit__ = MagicMock(return_value=False)
    return conn


def _mock_engine(mock_conn):
    """Return a mock engine whose begin() yields mock_conn."""
    engine = MagicMock()
    engine.begin.return_value = mock_conn
    return engine


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_customers_df():
    return pd.DataFrame({
        "customer_id": ["c1", "c2"],
        "customer_unique_id": ["u1", "u2"],
        "customer_zip_code_prefix": [12345, 67890],
        "customer_city": ["sao paulo", "franca"],
        "customer_state": ["SP", "SP"],
    })


@pytest.fixture()
def sample_orders_df():
    return pd.DataFrame({
        "order_id": ["o1"],
        "customer_id": ["c1"],
        "order_status": ["delivered"],
        "order_purchase_timestamp": [pd.Timestamp("2017-10-02 10:56:33")],
        "order_approved_at": [pd.Timestamp("2017-10-02 11:07:15")],
        "order_delivered_carrier_date": [pd.Timestamp("2017-10-04 19:55:00")],
        "order_delivered_customer_date": [pd.Timestamp("2017-10-10 21:25:13")],
        "order_estimated_delivery_date": [pd.Timestamp("2017-10-18 00:00:00")],
        "order_date": [pd.Timestamp("2017-10-02").date()],
    })


@pytest.fixture()
def sample_payments_df():
    return pd.DataFrame({
        "order_id": ["o1", "o2"],
        "payment_value": [75.5, 100.0],
    })


@pytest.fixture()
def sample_inr_rates_df():
    return pd.DataFrame({
        "currency": ["USD", "EUR"],
        "rate": [83.5, 90.2],
    })


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPutInPostgre:
    """Verify put_in_postgre() without a live database."""

    def _run_put_in_postgre(self, df, table_name):
        """
        Import put_in_postgre with the engine patched to a mock.
        Returns (mock_conn, execute_calls) for assertions.
        """
        mock_conn = _make_mock_conn()
        mock_engine = _mock_engine(mock_conn)

        with patch("storage.postgre_store.engine", mock_engine):
            from storage.postgre_store import put_in_postgre
            put_in_postgre(df, table_name)

        return mock_conn, mock_engine

    # ------------------------------------------------------------------
    # olist_customers
    # ------------------------------------------------------------------
    def test_customers_uses_single_transaction(self, sample_customers_df):
        """engine.begin() must be called exactly once — atomicity."""
        _, mock_engine = self._run_put_in_postgre(sample_customers_df, "olist_customers")
        assert mock_engine.begin.call_count == 1

    def test_customers_staging_table_written(self, sample_customers_df):
        """df.to_sql() must write to temp_stage_olist_customers.

        pandas calls df.to_sql(table_name, conn, ...) — 'to_sql' is a method on
        the DataFrame, not on the connection.  We patch pd.DataFrame.to_sql so we
        can inspect the positional arguments regardless of how the mock conn is used.
        """
        mock_conn = _make_mock_conn()
        mock_engine = _mock_engine(mock_conn)

        with patch("storage.postgre_store.engine", mock_engine), \
             patch("pandas.DataFrame.to_sql") as mock_to_sql:
            from storage.postgre_store import put_in_postgre
            put_in_postgre(sample_customers_df, "olist_customers")

        # First positional argument to to_sql is the table name
        written_tables = [c.args[0] for c in mock_to_sql.call_args_list]
        assert "temp_stage_olist_customers" in written_tables, (
            f"Staging table not written. Calls: {written_tables}"
        )

    def test_customers_upsert_sql_executed(self, sample_customers_df):
        """execute() must be called with SQL containing the correct table name."""
        mock_conn, _ = self._run_put_in_postgre(sample_customers_df, "olist_customers")
        executed_sql = " ".join(
            str(c.args[0]) for c in mock_conn.execute.call_args_list
        )
        assert "olist_customers" in executed_sql
        assert "ON CONFLICT" in executed_sql

    def test_customers_staging_table_dropped(self, sample_customers_df):
        """The staging table must be DROPped in the same transaction."""
        mock_conn, _ = self._run_put_in_postgre(sample_customers_df, "olist_customers")
        executed_sql = " ".join(
            str(c.args[0]) for c in mock_conn.execute.call_args_list
        )
        assert "DROP TABLE IF EXISTS temp_stage_olist_customers" in executed_sql

    # ------------------------------------------------------------------
    # olist_orders
    # ------------------------------------------------------------------
    def test_orders_upsert_sql_executed(self, sample_orders_df):
        mock_conn, _ = self._run_put_in_postgre(sample_orders_df, "olist_orders")
        executed_sql = " ".join(
            str(c.args[0]) for c in mock_conn.execute.call_args_list
        )
        assert "olist_orders" in executed_sql
        assert "ON CONFLICT" in executed_sql

    def test_orders_staging_table_dropped(self, sample_orders_df):
        mock_conn, _ = self._run_put_in_postgre(sample_orders_df, "olist_orders")
        executed_sql = " ".join(
            str(c.args[0]) for c in mock_conn.execute.call_args_list
        )
        assert "DROP TABLE IF EXISTS temp_stage_olist_orders" in executed_sql

    # ------------------------------------------------------------------
    # olist_order_payments
    # ------------------------------------------------------------------
    def test_payments_upsert_sql_executed(self, sample_payments_df):
        mock_conn, _ = self._run_put_in_postgre(sample_payments_df, "olist_order_payments")
        executed_sql = " ".join(
            str(c.args[0]) for c in mock_conn.execute.call_args_list
        )
        assert "olist_order_payments" in executed_sql
        assert "ON CONFLICT" in executed_sql

    def test_payments_staging_table_dropped(self, sample_payments_df):
        mock_conn, _ = self._run_put_in_postgre(sample_payments_df, "olist_order_payments")
        executed_sql = " ".join(
            str(c.args[0]) for c in mock_conn.execute.call_args_list
        )
        assert "DROP TABLE IF EXISTS temp_stage_olist_order_payments" in executed_sql

    # ------------------------------------------------------------------
    # inr_rates
    # ------------------------------------------------------------------
    def test_inr_rates_upsert_sql_executed(self, sample_inr_rates_df):
        mock_conn, _ = self._run_put_in_postgre(sample_inr_rates_df, "inr_rates")
        executed_sql = " ".join(
            str(c.args[0]) for c in mock_conn.execute.call_args_list
        )
        assert "inr_rates" in executed_sql
        assert "ON CONFLICT" in executed_sql

    def test_inr_rates_staging_table_dropped(self, sample_inr_rates_df):
        mock_conn, _ = self._run_put_in_postgre(sample_inr_rates_df, "inr_rates")
        executed_sql = " ".join(
            str(c.args[0]) for c in mock_conn.execute.call_args_list
        )
        assert "DROP TABLE IF EXISTS temp_stage_inr_rates" in executed_sql

    # ------------------------------------------------------------------
    # Fallback / unknown table
    # ------------------------------------------------------------------
    def test_unknown_table_falls_back_to_append(self):
        """Unknown tables should fall back to df.to_sql(if_exists='append')."""
        df = pd.DataFrame({"col": [1, 2]})
        mock_conn = _make_mock_conn()
        mock_engine = _mock_engine(mock_conn)

        with patch("storage.postgre_store.engine", mock_engine):
            from storage.postgre_store import put_in_postgre
            put_in_postgre(df, "unknown_table")

        # engine.begin() used for the fallback path too
        assert mock_engine.begin.call_count == 1
