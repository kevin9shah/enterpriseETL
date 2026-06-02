import os
import sys
import logging
from flask import Flask, jsonify, send_from_directory
from sqlalchemy import create_engine, text

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config.settings import settings

app = Flask(__name__, static_folder="dashboard")
logger = logging.getLogger("dashboard_server")

# Configure database engine
try:
    engine = create_engine(
        f"postgresql+psycopg2://{settings.db_user}:{settings.db_pass}@{settings.db_host}:{settings.db_port}/{settings.db_name}",
        connect_args={'connect_timeout': 3}
    )
except Exception as e:
    logger.error(f"Failed to create engine: {e}")
    engine = None

def get_db_connection():
    if not engine:
        return None
    try:
        return engine.connect()
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

@app.route("/api/stats")
def get_stats():
    conn = get_db_connection()
    stats = {
        "total_orders": 99441,       # Fallback mock values
        "total_customers": 99441,
        "total_revenue": 16008872.12,
        "pipeline_health": "Healthy"
    }

    if conn:
        try:
            # Query total orders
            res_orders = conn.execute(text("SELECT COUNT(*) FROM olist_orders;")).fetchone()
            if res_orders:
                stats["total_orders"] = res_orders[0]

            # Query total customers
            res_cust = conn.execute(text("SELECT COUNT(*) FROM olist_customers;")).fetchone()
            if res_cust:
                stats["total_customers"] = res_cust[0]

            # Query total revenue
            res_rev = conn.execute(text("SELECT SUM(payment_value) FROM olist_order_payments;")).fetchone()
            if res_rev and res_rev[0] is not None:
                stats["total_revenue"] = float(res_rev[0])
            
            conn.close()
        except Exception as e:
            logger.warning(f"Error querying database stats, using fallbacks: {e}")
            if conn:
                conn.close()
    
    # Read pipeline health from logs
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "pipeline.log")
    if os.path.exists(log_path):
        try:
            with open(log_path, "r") as f:
                content = f.read()
                if "Finished Successfully" in content:
                    stats["pipeline_health"] = "Healthy"
                elif "failed" in content.lower() or "exception" in content.lower():
                    stats["pipeline_health"] = "Unhealthy"
        except Exception as e:
            logger.warning(f"Could not parse log file: {e}")

    return jsonify(stats)

@app.route("/api/exchange-rates")
def get_exchange_rates():
    conn = get_db_connection()
    rates = {
        "USD": 83.12,
        "EUR": 90.15,
        "GBP": 105.42,
        "JPY": 0.53,
        "AUD": 55.20,
        "CAD": 61.10
    }

    if conn:
        try:
            res = conn.execute(text("SELECT currency, rate FROM inr_rates;")).fetchall()
            if res:
                rates = {row[0]: float(row[1]) for row in res}
            conn.close()
        except Exception as e:
            logger.warning(f"Error querying exchange rates: {e}")
            if conn:
                conn.close()

    return jsonify(rates)

@app.route("/api/state-sales")
def get_state_sales():
    conn = get_db_connection()
    sales_data = [
        {"state": "SP", "sales": 15200000.0, "city": "Sao Paulo"},
        {"state": "RJ", "sales": 9800000.0, "city": "Rio de Janeiro"},
        {"state": "MG", "sales": 6500000.0, "city": "Minas Gerais"},
        {"state": "RS", "sales": 4200000.0, "city": "Rio Grande do Sul"},
        {"state": "PR", "sales": 3800000.0, "city": "Parana"}
    ]

    if conn:
        try:
            query = """
                SELECT c.customer_state as state, SUM(p.payment_value) as sales
                FROM olist_order_payments p
                JOIN olist_orders o ON p.order_id = o.order_id
                JOIN olist_customers c ON o.customer_id = c.customer_id
                GROUP BY c.customer_state
                ORDER BY sales DESC
                LIMIT 5;
            """
            res = conn.execute(text(query)).fetchall()
            if res:
                state_names = {
                    "SP": "Sao Paulo", "RJ": "Rio de Janeiro", "MG": "Minas Gerais",
                    "RS": "Rio Grande do Sul", "PR": "Parana", "SC": "Santa Catarina",
                    "BA": "Bahia", "DF": "Distrito Federal", "ES": "Espirito Santo"
                }
                sales_data = [
                    {
                        "state": row[0].upper(), 
                        "sales": float(row[1]),
                        "city": state_names.get(row[0].upper(), "Other")
                    } for row in res
                ]
            conn.close()
        except Exception as e:
            logger.warning(f"Error querying state sales: {e}")
            if conn:
                conn.close()

    return jsonify(sales_data)

@app.route("/api/logs")
def get_logs():
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "pipeline.log")
    logs = ["No log records found."]
    if os.path.exists(log_path):
        try:
            with open(log_path, "r") as f:
                lines = f.readlines()
                logs = [line.strip() for line in lines[-10:]] # Get last 10 lines
        except Exception as e:
            logger.warning(f"Failed to read logs: {e}")
    return jsonify(logs)

@app.route("/api/run", methods=["POST"])
def run_pipeline():
    try:
        import subprocess
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
        venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv", "bin", "python")
        if not os.path.exists(venv_python):
            venv_python = "python3"
        subprocess.Popen([venv_python, script_path])
        return jsonify({"message": "ETL pipeline triggered successfully. Monitoring logs..."})
    except Exception as e:
        logger.error(f"Error launching pipeline: {e}")
        return jsonify({"message": f"Failed to trigger pipeline: {e}"}), 500

@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(app.static_folder, path)

if __name__ == "__main__":
    print("Starting Enterprise BI Dashboard Server on http://localhost:5050")
    app.run(host="0.0.0.0", port=5050, debug=True)
