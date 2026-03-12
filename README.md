# Griddy — Grid-Scale Analytical Agent

An interactive, full-stack application for analyzing electrical distribution grids. Griddy ingests a CIM-based grid model, generates synthetic AMI time-series data, and exposes a rich geospatial dashboard for voltage analysis, phase balancing, load-flow tracing, and alarm correlation.

---

## Features

- **Interactive Grid Map** — Navigate a 12,000+ node IEEE 8500 distribution model with zoom, pan, node selection, and a right-click context menu.
- **Graph Traversal** — Trace upstream to the source substation or downstream to every affected meter from any selected device.
- **Voltage Distribution** — Statistical breakdown (mean, median, std dev) of voltage readings across any downstream sub-tree over a user-defined time range.
- **Phase Balance Analysis** — Aggregate kWh and instantaneous current across phases A, B, and C to identify neutral loading or phase imbalance.
- **Consumption Time-Series** — Side-by-side kWh (delivered/received) and voltage charts with 1W / 1M / 1Y / custom range filters.
- **Voltage Heatmap** — System-wide geospatial heatmap of voltage health.
- **Alarm Correlation** — Spatially cluster active alarms to identify transformer or feeder outages.
- **Natural Language Queries** — Translate plain-English questions (e.g., *"What was peak load on Phase B last Tuesday?"*) into SQL via a built-in agent.

---

## Technology Stack

| Layer | Technology |
| :--- | :--- |
| Backend | Python · FastAPI · Uvicorn |
| Graph Engine | NetworkX (directed multigraph) |
| Database | DuckDB (relational) · Parquet (time-series) |
| Frontend | React 19 · TypeScript · Vite |
| Visualization | Deck.gl · MapLibre GL · ECharts |
| UI Components | Mantine |
| Containerization | Docker · Docker Compose |
| Documentation | Docusaurus |

---

## Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop) (includes Docker Compose)

### Run with Docker Compose

```bash
docker compose up --build
```

This command will:

1. Build the **frontend** container (React → Nginx).
2. Build the **backend** container (FastAPI/Uvicorn).
3. Initialize the `grid_data` persistent volume.
4. Auto-ingest the bundled `IEEE8500.xml` CIM model and generate synthetic AMI readings (controlled by `BOOTSTRAP_DATA`).

Once running, open your browser:

| Service | URL |
| :--- | :--- |
| Web Dashboard | <http://localhost:8080> |
| API (Swagger) | <http://localhost:8000/docs> |
| Documentation | <http://localhost:3000> |

---

## Environment Variables

Customize the deployment using a `.env` file in the project root or by overriding values directly in `docker-compose.yml`:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `BOOTSTRAP_DATA` | `true` | Ingest the CIM model and generate synthetic readings on startup. |
| `DB_PATH` | `/data/grid_data_cim.duckdb` | Path to the persistent DuckDB file inside the container. |
| `PARQUET_DIR` | `/data/cim_readings` | Directory for Parquet time-series storage. |
| `CIM_MODEL_PATH` | `/app/sample_data/IEEE8500.xml` | Path to the CIM source model file. |
| `WEATHER_DATA_PATH` | `/app/sample_data/weather.epw` | Path to the EPW weather data file. |
| `BACKEND_PORT` | `8000` | Host port for the backend service. |
| `FRONTEND_PORT` | `8080` | Host port for the frontend dashboard. |
| `WEBSITE_PORT` | `3000` | Host port for the documentation site. |

### Manual Data Refresh

To re-run the data ingestion pipeline without rebuilding the entire stack:

```bash
docker compose --profile tools run generator
```

---

## Grid Analysis

### Interacting with the Map

- **Zoom & Pan** — Use your mouse or trackpad to navigate the map.
- **Node Selection** — Click any node (Substation, Transformer, Switch, or Meter) to open the details panel.
- **Context Menu** — Right-click a node to access analysis shortcuts:
  - **Trace Downstream** — Highlight all assets logically below the selected node.
  - **Trace Upstream** — Trace the path back to the source substation.
  - **Run Voltage Analysis** — Open the voltage distribution panel.
  - **Run Phase Balance** — Analyze current and energy imbalance across phases.

### Degrees of Separation

Most analyses let you configure **Degrees of Separation**, which controls the depth of the downstream traversal:

| Value | Behavior |
| :--- | :--- |
| `0` | Analyze only the selected node. |
| `5` (default) | Analyze the node and all neighbors up to 5 hops away. |
| Full trace | Traverse the entire downstream tree. |

---

## Project Structure

```
graph/
├── backend/              # FastAPI service, graph engine, analytics
│   ├── src/
│   │   ├── agent/        # Natural language → SQL translation
│   │   ├── analytics/    # Voltage, phase balance, consumption use cases
│   │   ├── discovery/    # Upstream/downstream graph traversal
│   │   ├── grid/         # Grid model and data structures
│   │   └── shared/       # DuckDB repository, NetworkX engine
│   ├── scripts/          # Data ingestion and generation scripts
│   ├── sample_data/      # IEEE 8500 CIM model and weather data
│   └── tests/            # Unit and functional tests
├── frontend/             # React + TypeScript + Vite dashboard
│   └── src/
│       ├── features/     # Grid map and analytics panel components
│       ├── services/     # API client
│       └── shared/       # Types and utilities
├── docs/                 # Docusaurus documentation website
├── docker-compose.yml
├── functional-requirements.md
└── technical-requirements.md
```

---

## Documentation

Full documentation is available at <http://localhost:3000> after starting the stack, and covers:

- [Grid Analysis Guide](docs/docs/analysis-guide/index.md)
- [Voltage Analysis](docs/docs/analysis-guide/voltage-analysis.md)
- [Phase Balance / Load Flow](docs/docs/analysis-guide/load-flow.md)
- [Voltage Map (Heatmap)](docs/docs/analysis-guide/voltage-map.md)
- [Data Generation](docs/docs/data-generation.md)
- [Docker Installation](docs/docs/docker-installation.md)

---

## License

This project is licensed under the [MIT License](LICENSE).
