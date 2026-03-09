
import duckdb

DB_PATH = "grid_data_cim.duckdb"

def check_schema():
    with duckdb.connect(DB_PATH) as conn:
        print("--- grid_nodes schema ---")
        res = conn.execute("PRAGMA table_info('grid_nodes')").fetchall()
        for row in res:
            print(row)
            
if __name__ == "__main__":
    check_schema()
