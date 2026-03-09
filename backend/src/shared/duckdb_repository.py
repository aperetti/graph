"""DuckDB repository implementation."""
import duckdb
from typing import List, Optional, Any
from src.shared.repository import AssetRepository
from src.grid.asset import Asset, Edge
from src.shared.database_setup import DB_PATH

class DuckDBRepository(AssetRepository):
    """DuckDB implementation of the Asset Repository."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def get_asset(self, asset_id: str) -> Optional[Asset]:
        with duckdb.connect(self.db_path, read_only=True) as conn:
            result = conn.execute(
                "SELECT node_id, node_type, name, phases_present FROM grid_nodes WHERE node_id = ?", 
                (asset_id,)
            ).fetchone()
            
            if result:
                return Asset(
                    id=result[0],
                    asset_type=result[1],
                    name=result[2],
                    phases_present=result[3]
                )
        return None

    def save_asset(self, asset: Asset) -> None:
        with duckdb.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO grid_nodes (node_id, node_type, name, phases_present) 
                VALUES (?, ?, ?, ?)
                ON CONFLICT (node_id) DO UPDATE SET 
                    node_type = excluded.node_type,
                    name = excluded.name,
                    phases_present = excluded.phases_present
                """,
                (asset.id, asset.asset_type, asset.name, asset.phases_present)
            )

    def save_edge(self, edge: Edge) -> None:
        with duckdb.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO grid_edges (edge_id, from_node_id, to_node_id, conductor_type, phases) 
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (edge_id) DO UPDATE SET 
                    from_node_id = excluded.from_node_id,
                    to_node_id = excluded.to_node_id,
                    conductor_type = excluded.conductor_type,
                    phases = excluded.phases
                """,
                (edge.id, edge.from_node_id, edge.to_node_id, edge.conductor_type, edge.phases)
            )

    def get_all_edges(self) -> List[dict]:
        with duckdb.connect(self.db_path, read_only=True) as conn:
            results = conn.execute("SELECT edge_id, from_node_id, to_node_id, phases FROM grid_edges").fetchall()
            return [
                {
                    "edge_id": row[0],
                    "from_node_id": row[1],
                    "to_node_id": row[2],
                    "phases": row[3]
                }
                for row in results
            ]

    def get_all_nodes_with_coordinates(self) -> List[dict]:
        with duckdb.connect(self.db_path, read_only=True) as conn:
            results = conn.execute("SELECT node_id, node_type, name, latitude, longitude, is_open, phases_present FROM grid_nodes").fetchall()
            return [
                {
                    "node_id": row[0],
                    "node_type": row[1],
                    "name": row[2],
                    "latitude": row[3],
                    "longitude": row[4],
                    "is_open": row[5],
                    "phases_present": row[6]
                }
                for row in results
            ]
