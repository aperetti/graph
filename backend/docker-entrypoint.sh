#!/bin/bash
set -e

# Data directory
mkdir -p /data

# Bootstrapping logic
if [ "$BOOTSTRAP_DATA" = "true" ]; then
    echo "Starting data bootstrapping..."
    
    # Check if CIM model exists
    if [ -f "$CIM_MODEL_PATH" ]; then
        echo "Ingesting CIM model from $CIM_MODEL_PATH..."
        # We need to set PYTHONPATH so ingest_cim.py can find src
        export PYTHONPATH=$PYTHONPATH:/app
        python scripts/ingest_cim.py
        
        echo "Generating synthetic readings..."
        python scripts/generate_cim_readings.py
        
        echo "Bootstrapping complete."
    else
        echo "WARNING: CIM model not found at $CIM_MODEL_PATH. Skipping ingestion."
    fi
fi

# Start the application
echo "Starting FastAPI server..."
exec uvicorn main:app --host "$HOST" --port "$PORT"
