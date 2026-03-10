#!/bin/bash
set -e

# Data directory
mkdir -p /data

echo "Starting dedicated data generation..."

# Ensure PYTHONPATH is set so scripts can find src if needed
export PYTHONPATH=$PYTHONPATH:/app

echo "1. Ingesting CIM model from $CIM_MODEL_PATH..."
python /app/scripts/ingest_cim.py

echo "2. Ingesting weather data from $WEATHER_DATA_PATH..."
python /app/scripts/ingest_weather.py

echo "3. Generating synthetic readings (weather-aware)..."
python /app/scripts/generate_cim_readings.py

echo "Data generation complete."
