import os

replacements = {
    "core.interfaces.graph_engine": "src.shared.graph_engine",
    "core.entities.graph_node": "src.grid.graph_node",
    "core.interfaces.repository": "src.shared.repository",
    "core.entities.asset": "src.grid.asset",
    "core.entities.meter": "src.grid.meter",
    "core.entities.reading": "src.grid.reading",
    "interface_adapters.storage.duckdb_repository": "src.shared.duckdb_repository",
    "interface_adapters.graph.networkx_engine": "src.grid.networkx_engine",
    "interface_adapters.api import agent_controller": "src.shared import old_controller as agent_controller",
    "interface_adapters.api.agent_controller": "src.shared.old_controller",
    "frameworks_drivers.database.setup": "src.shared.database_setup",
    "use_cases.discovery.discover_downstream": "src.discovery.discover_downstream",
    "use_cases.discovery.trace_upstream": "src.discovery.trace_upstream",
    "use_cases.analytics.calculate_voltage": "src.analytics.calculate_voltage",
    "use_cases.analytics.phase_balancing": "src.analytics.phase_balancing",
    "use_cases.analytics.calculate_consumption": "src.analytics.calculate_consumption",
    "use_cases.agent.translate_nl_to_sql": "src.agent.translate_nl_to_sql",
    "frameworks_drivers.web.app:app": "main:app",
}

for root, _, files in os.walk("backend"):
    for file in files:
        if file.endswith(".py"):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = content
            for old, new in replacements.items():
                new_content = new_content.replace(old, new)
                
            if new_content != content:
                print(f"Updated {filepath}")
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
