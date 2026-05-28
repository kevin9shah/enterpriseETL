import pandera as pa
import pandas as pd

# 1. Customer Schema Rules
customer_schema = pa.DataFrameSchema(
    columns={
        "customer_id": pa.Column(str, nullable=False, unique=True),
        "customer_unique_id": pa.Column(str, nullable=False),
        "customer_zip_code_prefix": pa.Column(int, nullable=False),
        "customer_city": pa.Column(str, nullable=False),
        "customer_state": pa.Column(str, checks=pa.Check.str_length(2, 2), nullable=False) # Must be exactly 2 characters (e.g. SP)
    },
    coerce=True, # Automatically cast types if possible (e.g. convert string numbers to float/int)
    strict=True  # Ensure no extra columns that are not defined here exist
)

# 2. Orders Schema Rules
order_schema = pa.DataFrameSchema(
    columns={
        "order_id": pa.Column(str, nullable=False, unique=True),
        "customer_id": pa.Column(str, nullable=False),
        "order_status": pa.Column(str, nullable=False),
        "order_purchase_timestamp": pa.Column(pd.Timestamp, nullable=False),
        "order_approved_at": pa.Column(pd.Timestamp, nullable=True),
        "order_delivered_carrier_date": pa.Column(pd.Timestamp, nullable=True),
        "order_delivered_customer_date": pa.Column(pd.Timestamp, nullable=True),
        "order_estimated_delivery_date": pa.Column(pd.Timestamp, nullable=True),
        "order_date": pa.Column(pa.Date, nullable=False)
    },
    coerce=True,
    strict=True
)

# 3. Payments Schema Rules (Post-aggregation check)
payment_schema = pa.DataFrameSchema(
    columns={
        "order_id": pa.Column(str, nullable=False, unique=True), # Unique after groupby aggregation
        "payment_value": pa.Column(float, checks=pa.Check.greater_than_or_equal_to(0), nullable=False) # No negative payments
    },
    coerce=True,
    strict=True
)

# Map dataset table names to their validation schemas
SCHEMA_MAP = {
    "olist_customers": customer_schema,
    "olist_orders": order_schema,
    "olist_order_payments": payment_schema
}
