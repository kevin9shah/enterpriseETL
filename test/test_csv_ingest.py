import pandas as pd

from ingestion.csv_ingest import clean_customers, clean_orders, clean_payments


def test_clean_customers():
    # Arrange: Create a mock input DataFrame with duplicate, mixed-case states, and messy cities
    raw_data = {
        "CUSTOMER_ID": ["1", "1", "2"],
        "customer_unique_id": ["u1", "u1", "u2"],
        "customer_zip_code_prefix": [123, 123, 456],
        "customer_city": [" SAO PAULO ", " SAO PAULO ", "Franca"],
        "customer_state": ["sp", "sp", "sp"]
    }
    df = pd.DataFrame(raw_data)

    # Act: Run clean customers transformation
    cleaned_df = clean_customers(df)

    # Assert:
    # 1. Row count should be 2 (duplicates removed)
    assert len(cleaned_df) == 2
    # 2. Column names should be lowercase
    assert list(cleaned_df.columns) == ["customer_id", "customer_unique_id", "customer_zip_code_prefix", "customer_city", "customer_state"]
    # 3. State must be uppercase
    assert cleaned_df.loc[cleaned_df["customer_id"] == "2", "customer_state"].values[0] == "SP"
    # 4. City names must be lowercase and stripped
    assert cleaned_df.loc[cleaned_df["customer_id"] == "1", "customer_city"].values[0] == "sao paulo"


def test_clean_orders():
    # Arrange: Mock order with strings that should convert to timestamps
    raw_data = {
        "ORDER_ID": ["o1"],
        "customer_id": ["c1"],
        "order_status": ["delivered"],
        "order_purchase_timestamp": ["2017-10-02 10:56:33"],
        "order_approved_at": ["2017-10-02 11:07:15"],
        "order_delivered_carrier_date": ["2017-10-04 19:55:00"],
        "order_delivered_customer_date": ["2017-10-10 21:25:13"],
        "order_estimated_delivery_date": ["2017-10-18 00:00:00"]
    }
    df = pd.DataFrame(raw_data)

    # Act
    cleaned_df = clean_orders(df)

    # Assert
    # 1. order_date column is created and matches purchase date
    assert "order_date" in cleaned_df.columns
    assert str(cleaned_df["order_date"].values[0]) == "2017-10-02"
    # 2. String timestamps are casted to pandas Timestamp object
    assert isinstance(cleaned_df["order_purchase_timestamp"].iloc[0], pd.Timestamp)


def test_clean_payments():
    # Arrange: Mock payments having multiple values for the same order_id
    raw_data = {
        "ORDER_ID": ["o1", "o1", "o2"],
        "payment_value": [50.0, 25.5, 100.0]
    }
    df = pd.DataFrame(raw_data)

    # Act
    cleaned_df = clean_payments(df)

    # Assert
    # 1. Dataset must be aggregated by order_id
    assert len(cleaned_df) == 2
    # 2. Total payment values must be summed correctly
    assert cleaned_df.loc[cleaned_df["order_id"] == "o1", "payment_value"].values[0] == 75.5
