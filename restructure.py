import os
import shutil

# Dest dirs
os.makedirs("backend/src/analytics", exist_ok=True)
os.makedirs("backend/src/discovery", exist_ok=True)
os.makedirs("backend/src/agent", exist_ok=True)
os.makedirs("backend/src/grid", exist_ok=True)
os.makedirs("backend/src/shared", exist_ok=True)

def safe_move(src, dest):
    if os.path.exists(src):
        shutil.move(src, dest)
    else:
        print(f"Warning: {src} not found.")

safe_move("use_cases/analytics/calculate_consumption.py", "backend/src/analytics/")
safe_move("use_cases/analytics/calculate_voltage.py", "backend/src/analytics/")
safe_move("use_cases/analytics/phase_balancing.py", "backend/src/analytics/")
safe_move("use_cases/discovery/discover_downstream.py", "backend/src/discovery/")
safe_move("use_cases/discovery/trace_upstream.py", "backend/src/discovery/")
safe_move("use_cases/agent/translate_nl_to_sql.py", "backend/src/agent/")

safe_move("core/entities/asset.py", "backend/src/grid/")
safe_move("core/entities/graph_node.py", "backend/src/grid/")
safe_move("core/entities/meter.py", "backend/src/grid/")
safe_move("core/entities/reading.py", "backend/src/grid/")
safe_move("interface_adapters/graph/networkx_engine.py", "backend/src/grid/")

safe_move("core/interfaces/graph_engine.py", "backend/src/shared/")
safe_move("core/interfaces/repository.py", "backend/src/shared/")
safe_move("interface_adapters/storage/duckdb_repository.py", "backend/src/shared/")
safe_move("frameworks_drivers/database/setup.py", "backend/src/shared/database_setup.py")

safe_move("frameworks_drivers/web/app.py", "backend/main.py")
safe_move("interface_adapters/api/agent_controller.py", "backend/src/shared/old_controller.py")

safe_move("tests", "backend/tests")
safe_move("scripts", "backend/scripts")

for d in ["core", "use_cases", "interface_adapters", "frameworks_drivers"]:
    shutil.rmtree(d, ignore_errors=True)

print("Restructuring complete.")
