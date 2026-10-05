import asyncio, os, subprocess, sys
from google.adk import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.agent_tool import AgentTool
from google.genai import types
from monitoring_agent import monitoring_agent  # reuse agent #1

if "GEMINI_API_KEY" in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

MODEL = "gemini-3.5-flash-lite"

# ---- CONFIG AGENT TOOLS (read-only) ----
ALLOWED_FILES = ["/etc/ssh/sshd_config", "/etc/hosts", "/etc/resolv.conf",
                 "/etc/nginx/nginx.conf"]

def read_config_file(path: str) -> dict:
    """Reads the first 60 lines of an allowed config file (read-only)."""
    if path not in ALLOWED_FILES:
        return {"error": f"Not allowed. Allowed files: {ALLOWED_FILES}"}
    try:
        with open(path) as f:
            return {"path": path, "content": "".join(f.readlines()[:60])}
    except Exception as e:
        return {"error": str(e)}

def list_listening_ports() -> dict:
    """Lists TCP ports this server is listening on."""
    r = subprocess.run(["ss", "-tln"], capture_output=True, text=True)
    return {"output": r.stdout[:1500]}

def check_package_installed(package: str) -> dict:
    """Checks whether an apt package (e.g. nginx) is installed."""
    r = subprocess.run(["dpkg", "-s", package], capture_output=True, text=True)
    return {"package": package, "installed": r.returncode == 0}

config_agent = Agent(
    name="config_agent",
    model=MODEL,
    instruction=("You are a configuration auditor. Use your tools to inspect "
                 "packages, ports and config files. You can only read, never "
                 "change anything. Explain findings and SUGGEST fixes as "
                 "commands for a human to run."),
    tools=[read_config_file, list_listening_ports, check_package_installed],
)

# ---- COORDINATOR: calls both agents as tools and combines answers ----
coordinator = Agent(
    name="coordinator",
    model=MODEL,
    instruction=("You are an IT operations coordinator. Use monitoring_agent "
                 "for live health and service status. Use config_agent for "
                 "packages, ports and config files. For problems, call both, "
                 "then give one clear summary with next steps."),
    tools=[AgentTool(agent=monitoring_agent), AgentTool(agent=config_agent)],
)

async def main():
    q = " ".join(sys.argv[1:]) or ("Check server health. Is nginx running? "
        "If not, find out why (installed? which ports are open?) and suggest fixes.")
    svc = InMemorySessionService()
    s = await svc.create_session(app_name="multi_app", user_id="student", session_id="m1")
    runner = Runner(agent=coordinator, app_name="multi_app", session_service=svc)
    msg = types.Content(role="user", parts=[types.Part(text=q)])
    async for ev in runner.run_async(user_id=s.user_id, session_id=s.id, new_message=msg):
        if ev.content and ev.content.parts:
            for p in ev.content.parts:
                if p.function_call:
                    print(f"[{ev.author}] calling -> {p.function_call.name}")
                elif p.text:
                    print(f"\n[{ev.author}] {p.text}")

if __name__ == "__main__":
    asyncio.run(main())
