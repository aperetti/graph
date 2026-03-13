---
description: Development server ports and URLs for the Griddy project
---

# Development Server Ports

> **IMPORTANT: Always use these ports when testing or opening the application in a browser.**

| Service         | Port   | URL                      | Config Source                          |
|-----------------|--------|--------------------------|----------------------------------------|
| **Frontend**    | `3001` | http://localhost:3001     | `frontend/vite.config.ts` → `server.port` |
| **Docs**        | `3000` | http://localhost:3000     | Docusaurus default                     |
| **Backend API** | `8000` | http://localhost:8000/api | `backend/main.py` → `uvicorn.run(port=8000)` |

## Proxy Configuration

The Vite dev server (port 3001) proxies API and docs requests:

- `/api/*` → `http://localhost:8000` (backend)
- `/docs/*` → `http://localhost:3000` (docusaurus)

## Start Commands

| Service  | Command        | Working Directory |
|----------|----------------|-------------------|
| Frontend | `npm run dev`  | `frontend/`       |
| Docs     | `npm start`    | `docs/`           |
| Backend  | `python main.py` or launch config | `backend/` |

## Common Mistakes

- **Do NOT use port 5173** — that is Vite's default, but this project overrides it to `3001`.
- **Do NOT confuse ports 3000 (docs) and 3001 (frontend)** — they are separate services.
