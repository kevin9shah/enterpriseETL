#!/bin/bash

PROJECT_DIR="/Users/kevinshah/Desktop/project"
export AIRFLOW_HOME="$PROJECT_DIR/airflow"
VENV_BIN="$PROJECT_DIR/venv/bin"
export PATH="$VENV_BIN:$PATH"

LOG_DIR="$AIRFLOW_HOME/logs/services"
mkdir -p "$LOG_DIR"

WEBSERVER_LOG="$LOG_DIR/webserver.log"
SCHEDULER_LOG="$LOG_DIR/scheduler.log"

WEBSERVER_PID_FILE="$AIRFLOW_HOME/webserver.pid"
SCHEDULER_PID_FILE="$AIRFLOW_HOME/scheduler.pid"

start() {
    echo "Starting Apache Airflow services..."
    
    # Start webserver
    if [ -f "$WEBSERVER_PID_FILE" ] && kill -0 $(cat "$WEBSERVER_PID_FILE") 2>/dev/null; then
        echo "Airflow Webserver is already running."
    else
        echo "Launching Webserver..."
        "$VENV_BIN/airflow" webserver --port 8080 > "$WEBSERVER_LOG" 2>&1 &
        echo $! > "$WEBSERVER_PID_FILE"
        echo "Webserver started (PID: $(cat $WEBSERVER_PID_FILE)). Logs: $WEBSERVER_LOG"
    fi
    
    # Start scheduler
    if [ -f "$SCHEDULER_PID_FILE" ] && kill -0 $(cat "$SCHEDULER_PID_FILE") 2>/dev/null; then
        echo "Airflow Scheduler is already running."
    else
        echo "Launching Scheduler..."
        "$VENV_BIN/airflow" scheduler > "$SCHEDULER_LOG" 2>&1 &
        echo $! > "$SCHEDULER_PID_FILE"
        echo "Scheduler started (PID: $(cat $SCHEDULER_PID_FILE)). Logs: $SCHEDULER_LOG"
    fi
    
    echo "Airflow services started. Access Web UI at http://localhost:8080 (credentials: admin / admin)"
}

stop() {
    echo "Stopping Apache Airflow services..."
    
    if [ -f "$WEBSERVER_PID_FILE" ]; then
        PID=$(cat "$WEBSERVER_PID_FILE")
        if kill -0 $PID 2>/dev/null; then
            echo "Stopping Webserver (PID: $PID)..."
            kill $PID
        fi
        rm -f "$WEBSERVER_PID_FILE"
    fi
    
    if [ -f "$SCHEDULER_PID_FILE" ]; then
        PID=$(cat "$SCHEDULER_PID_FILE")
        if kill -0 $PID 2>/dev/null; then
            echo "Stopping Scheduler (PID: $PID)..."
            kill $PID
        fi
        rm -f "$SCHEDULER_PID_FILE"
    fi
    
    # Clean up gunicorn master and worker processes just in case
    pkill -f "airflow-webserver" 2>/dev/null
    
    echo "Airflow services stopped."
}

status() {
    if [ -f "$WEBSERVER_PID_FILE" ] && kill -0 $(cat "$WEBSERVER_PID_FILE") 2>/dev/null; then
        echo "Webserver: RUNNING (PID: $(cat $WEBSERVER_PID_FILE))"
    else
        echo "Webserver: STOPPED"
    fi
    
    if [ -f "$SCHEDULER_PID_FILE" ] && kill -0 $(cat "$SCHEDULER_PID_FILE") 2>/dev/null; then
        echo "Scheduler: RUNNING (PID: $(cat $SCHEDULER_PID_FILE))"
    else
        echo "Scheduler: STOPPED"
    fi
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        sleep 2
        start
        ;;
    status)
        status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
