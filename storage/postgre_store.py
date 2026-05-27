import psycopg2
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
load_dotenv()
engine = create_engine(
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
def get_connection():
    try:
        return psycopg2.connect(
            database=os.getenv("DB_NAME"),
            user = os.getenv("DB_USER"),
            password= os.getenv("DB_PASSWORD"),
            host = os.getenv("DB_HOST"),
            port = os.getenv("DB_PORT"),
        )
    except:
        return False
def connect():
    conn = get_connection()
    if conn:
        print("Connected to database successfully")
    else:
        print("Failed to connect to database")

def put_in_postgre(df,table_name):
    df.to_sql(table_name,
    engine,
        if_exists = "replace",
        index = False
    )
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT 5;"))
        for row in result:
            print(row)
    print("Data sucessfully ingested in postgre")
   
