import asyncio, os, shutil, socket, subprocess, sys, time
import psutil
from google.adk import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

if "GEMINI_API_KEY" in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

# ---- TOOLS: plain Python functions the agent can call ----
def get_system_health() -> dict:
    """Returns this server's current CPU, memory, disk usage and uptime."""
    mem = psutil.virtual_memory()
    disk = shutil.disk_usage("/")
    return {
        "hostname": socket.gethostname(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": mem.percent,
        "memory_used_gb": round(mem.used / 1e9, 2),
        "memory_total_gb": round(mem.total / 1e9, 2),
        "disk_percent": round(disk.used / disk.total * 100, 1),
        "uptime_hours": round((time.time() - psutil.boot_time()) / 3600, 1),
    }

def check_service(service_name: str) -> dict:
    """Checks if a systemd service (e.g. ssh, docker) is active. Read-only."""
    result = subprocess.run(
        ["systemctl", "is-active", service_name],
        capture_output=True, text=True,
    )
    return {"service": service_name, "status": result.stdout.strip()}

# ---- AGENT ----
monitoring_agent = Agent(
    name="monitoring_agent",
    model="gemini-3.5-flash-lite",
    instruction=(
        "You are a server monitoring assistant. Use your tools to get real "
        "data, never guess. Report in plain English and flag anything "
        "concerning: CPU >80%, memory >85%, disk >90%, or a service not active."
    ),
    tools=[get_system_health, check_service],
)

# ---- RUNNER (same pattern as test_agent.py) ----
async def main():
    question = " ".join(sys.argv[1:]) or "Give me a health report and check ssh and docker."
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name="monitor_app", user_id="student", session_id="s1"
    )
    runner = Runner(agent=monitoring_agent, app_name="monitor_app",
                    session_service=session_service)
    content = types.Content(role="user", parts=[types.Part(text=question)])
    async for event in runner.run_async(
        user_id=session.user_id, session_id=session.id, new_message=content
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text, end="", flush=True)
    print()

if __name__ == "__main__":
    asyncio.run(main())
