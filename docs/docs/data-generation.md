# Data Generation

Griddy provides a dedicated data generation utility to ingest power system models and create synthetic interval readings.

## Overview

The **Generator** is a specialized Docker service that runs a data pipeline:
1. **CIM Ingestion**: Parses the `IEEE8500.xml` (or custom) model into a DuckDB database.
2. **Weather Ingestion**: Loads historical weather data (EPW format) to inform load profiles.
3. **Reading Generation**: Simulates 15-minute interval readings (Voltage, Current, kWh) for every node in the grid.

## Triggering Data Generation

### Option A — Docker (recommended for CI / production)

The generator is configured as a Docker Compose service with the `tools` profile. It does **not** run automatically during a standard `docker compose up`.

To execute a full data refresh, run:

```bash
docker compose --profile tools run --rm generator
```

### Option B — Local (recommended for development)

If you're running the backend outside Docker, you can run the same pipeline directly with Python:

```bash
cd backend

# Activate your virtual environment
# .venv\Scripts\activate   (Windows)
# source .venv/bin/activate (macOS / Linux)

# Set environment variables
export DB_PATH=./data/grid_data_cim.duckdb
export PARQUET_DIR=./data/cim_readings
export CIM_MODEL_PATH=./sample_data/IEEE8500.xml
export WEATHER_DATA_PATH=./sample_data/weather.epw
export PYTHONPATH=.

mkdir -p data
python scripts/ingest_cim_graph.py
python scripts/ingest_weather.py
python scripts/generate_cim_readings.py
```

You only need to run this once — the database and Parquet files persist in `backend/data/`.

### Why run the generator manually?
- **Remote Environments**: If the automatic bootstrap fails on a remote server.
- **Model Updates**: After replacing the `IEEE8500.xml` or custom CIM model.
- **Data Refresh**: To regenerate synthetic data with new random seeds or different time windows.

## Technical Details

- **Scripts**: Located in `backend/scripts/`.
- **Database**: The generated DuckDB file is saved at `/data/grid_data_cim.duckdb`.
- **Readings**: Interval data is saved as chunked Parquet files in `/data/cim_readings/`.
- **Volume**: Both the database and parquet files persist in the `grid_data` Docker volume.

:::warning[Database Locks]
DuckDB is a single-writer database. Ensure the `backend` service is stopped before running the `generator` to avoid lock contention.
:::

## Configuration

You can customize the generation via environment variables in `docker-compose.yml`:

| Variable | Description |
| :--- | :--- |
| `CIM_MODEL_PATH` | Path to the XML model file. |
| `WEATHER_DATA_PATH` | Path to the EPW weather file. |
| `DB_PATH` | Destination path for the DuckDB file. |
| `PARQUET_DIR` | Destination directory for Parquet readings. |
