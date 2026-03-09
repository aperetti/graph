# Docker Installation

This guide covers how to set up and run the Grid Analytical Agent using Docker.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running.
- [Docker Compose](https://docs.docker.com/compose/install/) (included with Docker Desktop).

## Quick Start

To build and start the entire application stack, run the following command from the project root:

```bash
docker compose up --build
```

This will:
1. Build the **Frontend** container (using Nginx).
2. Build the **Backend** container (FastAPI/Uvicorn).
3. Initialize the **grid_data** persistent volume.
4. Auto-ingest the `IEEE8500.xml` model and generate synthetic data (if `BOOTSTRAP_DATA` is true).

## Environment Variables

You can customize the deployment using the following variables in the `docker-compose.yml` or an `.env` file:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `BOOTSTRAP_DATA` | `true` | Set to `true` to automatically ingest the model and generate readings on startup. |
| `DB_PATH` | `/data/grid_data_cim.duckdb` | Path to the persistent DuckDB file. |
| `PARQUET_DIR` | `/data/cim_readings` | Directory for synthetic reading storage. |
| `CIM_MODEL_PATH` | `/app/IEEE8500.xml` | Path to the CIM source model file. |

## Accessing the Application

Once the containers are running, you can access the system at:

- **Web Dashboard**: [http://localhost:8080](http://localhost:8080)
- **API Documentation (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)

## Persistence

All grid data and readings are stored in the `grid_data` Docker volume. This ensures your analysis results and generated data persist even if you stop or remove the containers.
