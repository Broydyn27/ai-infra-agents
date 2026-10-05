
import asyncio import os from google.adk import Agent from google.adk.runners import Runner 
from google.adk.sessions import InMemorySessionService from google.genai import types

# Ensure the Gemini API key is recognized by the SDK backend
if "GEMINI_API_KEY" in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

async def main():
    # 1. Initialize the session service in RAM
    session_service = InMemorySessionService()
    
    # 2. Create a test session
    session = await session_service.create_session(
        app_name="test_app",
        user_id="student",
        session_id="test_session_1"
    )

    # 3. Define the core agent
    root_agent = Agent(
        name="test_agent",
        model="gemini-3.5-flash-lite",
        instruction="You are a helpful IT assistant. Confirm the ADK is active in one short sentence.",
    )

    # 4. Initialize the runner with required session dependencies
    runner = Runner(
        agent=root_agent,
        app_name="test_app",
        session_service=session_service,
    )

    print("Testing API connection...\nResponse:")
    
    # 5. Package the message using official types
    content = types.Content(
        role="user",
        parts=[types.Part(text="Is the ADK online?")]
    )
    
    # 6. Execute and stream back events
    events = runner.run_async(
        user_id=session.user_id,
        session_id=session.id,
        new_message=content
    )

    async for event in events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text, end="", flush=True)
    print("\n")

if __name__ == "__main__":
    asyncio.run(main())
