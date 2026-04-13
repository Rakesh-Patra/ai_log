import asyncio
import sys
import os
import json

# Ensure app is importable
sys.path.append(os.getcwd())

async def test_live():
    log_file = "tests/e2e_debug_log.txt"
    with open(log_file, "w", encoding='utf-8') as f:
        f.write(f"CWD: {os.getcwd()}\n")
        try:
            from app.utils.insforge import get_insforge_client
            client = get_insforge_client()
            session_id = "e2e_verified_session_v2"
            
            f.write(f"Testing session: {session_id}\n")
            f.write(f"Base URL: {client.base_url}\n")
            
            # Test 1: Save User Message
            f.write("Saving user message...\n")
            res = await client.save_message(session_id, "user", "Hello from E2E Debug!")
            f.write(f"Response: {res}\n")
            
            # Test 2: Fetch History
            f.write("Fetching history...\n")
            history = await client.get_history(session_id)
            f.write(f"History count: {len(history)}\n")
            f.write(f"History details: {json.dumps(history, indent=2)}\n")
            
            if len(history) > 0:
                f.write("✅ SUCCESS\n")
            else:
                f.write("❌ FAILED: History empty\n")
                
        except Exception as e:
            f.write(f"💥 CRASH: {str(e)}\n")
            import traceback
            f.write(traceback.format_exc())

if __name__ == "__main__":
    # Placeholder only — use a real key in your local .env for live calls; never commit keys.
    os.environ.setdefault("GOOGLE_API_KEY", "test-placeholder-not-a-real-google-api-key")
    asyncio.run(test_live())
