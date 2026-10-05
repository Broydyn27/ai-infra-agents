# AI Infrastructure Agents (Google ADK + Gemini)

Multi-agent system running on an Ubuntu VM in a Proxmox virtual datacentre behind an OPNsense firewall.

## Agents
- **Monitoring Agent** (`monitoring_agent.py`): reads CPU, RAM, disk, uptime and systemd service status via tools.
- **Configuration Agent** (`multi_agent.py`): read-only audit of packages, open ports and allow-listed config files. Suggests fixes; never changes the system.
- **Coordinator** (`multi_agent.py`): delegates to both agents (AgentTool) and returns one combined report.

## Setup
    python3 -m venv ~/ai-agent-env && source ~/ai-agent-env/bin/activate
    pip install -r requirements.txt
    export GEMINI_API_KEY="your-key"   # never commit this
    python multi_agent.py

## Demo
See `demo_output.txt` for a sample run.

## Design notes
- Tools are plain Python functions; their docstrings tell the model when to use them.
- Safety: config tools are read-only with a file allow-list.
- Model: gemini-3.5-flash-lite (free tier).
