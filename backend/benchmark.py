import time
import asyncio
from src.shared import old_controller as controller

async def main():
    # Force initialization first to separate DB read/build time from the logic we want to optimize
    controller._ensure_graph_built()

    start_time = time.time()

    # Run the get_topology multiple times to measure the impact
    iterations = 50
    for _ in range(iterations):
        res = await controller.get_topology()

    end_time = time.time()

    print(f"Baseline for {iterations} iterations: {end_time - start_time:.4f} seconds")
    print(f"Per iteration: {(end_time - start_time) / iterations:.4f} seconds")

if __name__ == "__main__":
    asyncio.run(main())
