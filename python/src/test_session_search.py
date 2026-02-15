import asyncio
import json
from src.server.services.session_service import SessionService
from src.server.utils import get_supabase_client

async def test_session_lifecycle():
    service = SessionService()
    
    # 1. Create session
    print("1. Creating session...")
    try:
        session = await service.create_session(
            agent="gemini-test",
            context={"goal": "Test semantic search across sessions"},
            metadata={"version": "1.0"}
        )
        session_id = session["id"]
        print(f"Created session: {session_id}")

        # 2. Add event
        print("2. Adding event...")
        await service.add_event(
            session_id=session_id,
            event_type="decision_made",
            event_data={"decision": "Use vite-plugin-pwa for offline support", "reason": "Better integration with Vite and easier configuration"}
        )
        print("Added event.")

        # 3. End session with summary
        print("3. Ending session with summary...")
        summary = "Successfully implemented PWA scaffolding for offline use in the HVAC technician specialist project. Used vite-plugin-pwa and added connectivity detection."
        await service.end_session(
            session_id=session_id,
            summary=summary
        )
        print("Ended session.")

        # 4. Search sessions semantically
        print("4. Searching sessions semantically...")
        query = "How was the offline support for the HVAC app implemented?"
        results = await service.search_sessions(
            query=query,
            threshold=0.3 # Lowered threshold to ensure we get results if embeddings are slightly different
        )
        
        print(f"Found {len(results)} results.")
        found_test = False
        for res in results:
            sim = res.get('similarity', 0)
            summ = res.get('summary', 'No summary')
            print(f"- [{sim:.2f}] {summ}")
            if res['id'] == session_id:
                print("✅ Found our test session!")
                found_test = True
        
        if not found_test:
            print("❌ Did not find our test session in search results.")

    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_session_lifecycle())
