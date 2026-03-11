import asyncio
import time
import httpx
from src.shared.old_controller import router
from fastapi import FastAPI
import duckdb
import os

DB_PATH = os.getenv("DB_PATH", "grid_data_cim.duckdb")

app = FastAPI()
app.include_router(router)

async def make_requests(n):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Initial request to populate lazy loading graph and get past setup errors
        res = await client.get("/api/analytics/consumption/NODE1?start_time=2023-01-01T00:00:00&end_time=2023-01-02T00:00:00")

        start_time = time.time()
        tasks = []
        for _ in range(n):
            tasks.append(client.get("/api/analytics/consumption/NODE1?start_time=2023-01-01T00:00:00&end_time=2023-01-02T00:00:00"))

        responses = await asyncio.gather(*tasks)
        end_time = time.time()
        print(f"{n} concurrent requests took {end_time - start_time:.4f} seconds")

if __name__ == "__main__":
    # Add fake delay in execution to simulate slow query
    def fake_execute(*args, **kwargs):
        time.sleep(1) # simulate 1s blocking query
        import src.analytics.calculate_consumption as cc
        return cc.old_execute(*args, **kwargs)

    import src.analytics.calculate_consumption as cc
    cc.old_execute = cc.CalculateAggregateConsumptionUseCase.execute
    cc.CalculateAggregateConsumptionUseCase.execute = fake_execute

    asyncio.run(make_requests(10))
