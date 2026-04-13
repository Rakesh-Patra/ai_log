import asyncio
import sys
import os

# Ensure app is importable
sys.path.append(os.getcwd())

from app.utils.insforge import get_insforge_client

async def verify():
    output = []
    output.append("Testing InsForgeClient...")
    client = get_insforge_client()
    session_id = f"test_session_{int(asyncio.get_event_loop().time())}"
    
    # 1. Save a message
    output.append(f"Saving message for session {session_id}...")
    res = await client.save_message(session_id, "user", "Hello InsForge!")
    if res:
        output.append("✅ Message saved successfully.")
    else:
        output.append("❌ Failed to save message.")
        with open("tests/verify_results.txt", "w", encoding='utf-8') as f:
            f.write("\n".join(output))
        return

    # 2. Get history
    output.append("Fetching history...")
    history = await client.get_history(session_id)
    if history and len(history) > 0:
        output.append(f"✅ History fetched: {len(history)} messages found.")
        for msg in history:
            output.append(f"  [{msg['role']}]: {msg['content']}")
    else:
        output.append("❌ History empty or fetch failed.")

    with open("tests/verify_results.txt", "w", encoding='utf-8') as f:
        f.write("\n".join(output))

if __name__ == "__main__":
    asyncio.run(verify())
