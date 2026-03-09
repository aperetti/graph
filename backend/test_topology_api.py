
import sys
import os

# Add backend and its dependencies to path
backend_path = os.path.join(os.getcwd(), 'backend')
sys.path.append(backend_path)

# Mock FastAPI app context if needed, but we can just import the controller
from src.shared import old_controller as controller

async def test_topology():
    print("Testing graph initialization and topology fetch...")
    try:
        # This will trigger _ensure_graph_built
        res = await controller.get_topology()
        print(f"Success! Fetched {len(res['nodes'])} nodes and {len(res['edges'])} edges.")
        
        # Check first edge phases
        if res['edges']:
            e = res['edges'][0]
            print(f"Sample edge phases type: {type(e['phases'])} value: {e['phases']}")
            
    except Exception as e:
        print(f"FAILED with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_topology())
