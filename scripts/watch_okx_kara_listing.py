#!/usr/bin/env python3
"""Watch OKX.AI agent #2754 listing status and notify when it goes live."""
import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path("/home/ubuntu/okx-ai-agent")
ENV_FILE = PROJECT_DIR / ".env"
ONCHAINOS = Path.home() / ".local/bin/onchainos"
AGENT_ID = "2754"
MARKETPLACE_URL = "https://www.okx.ai/agents/2754"


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, val = line.split("=", 1)
            os.environ.setdefault(key, val)


def main() -> int:
    load_env(ENV_FILE)
    env = os.environ.copy()
    env["PATH"] = str(Path.home() / ".local/bin") + ":" + env.get("PATH", "")

    # Use service-list to fetch both agent status and services.
    proc = subprocess.run(
        [str(ONCHAINOS), "agent", "service-list", "--agent-id", AGENT_ID],
        capture_output=True,
        text=True,
        env=env,
    )
    if proc.returncode != 0:
        # Agent not active yet; stay silent.
        return 0

    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return 0

    if not data.get("ok") or not data.get("data"):
        return 0

    agent_info = data["data"][0].get("agentInfo", {})
    approval_status = agent_info.get("approvalStatus")
    online_status = agent_info.get("onlineStatus")
    sales = agent_info.get("salesCount", 0)
    services = data["data"][0].get("list", [])

    # Status code 1 generally means listed / active.
    if approval_status == 1 and online_status == 1:
        print(
            "🎉 *KARA Intelligence sudah listed di OKX.AI!*\n\n"
            f"🔗 {MARKETPLACE_URL}\n"
            f"📦 Service: {len(services)}\n"
            f"💰 Sales: {sales}\n\n"
            "Sekarang kita bisa post demo + submit Google Form."
        )
        return 0

    # Stay silent while still under review.
    return 0


if __name__ == "__main__":
    sys.exit(main())
