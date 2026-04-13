import asyncio
import os
import sys

# Add the current directory to sys.path to resolve 'app'
sys.path.append(os.getcwd())

async def test_lifespan():
    from app.main import lifespan
    from fastapi import FastAPI
    from app.temporal.client import get_temporal_client
    
    app = FastAPI(lifespan=lifespan)
    
    print("Testing lifespan initialization...")
    try:
        async with lifespan(app):
            print("OK: Lifespan started successfully")
            client = await get_temporal_client()
            print(f"OK: Temporal client available: {client}")
    except Exception as e:
        print(f"FAIL: Lifespan or Temporal connection failed: {e}")

if __name__ == "__main__":
    # Ensure environment variables are set for the test if needed
    # os.environ["GOOGLE_API_KEY"] = "dummy"
    
    # We need a proper event loop
    asyncio.run(test_lifespan())
