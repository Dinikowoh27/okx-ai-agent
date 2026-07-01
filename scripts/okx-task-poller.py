#!/usr/bin/env python3
"""
OKX.AI Task Poller
==================
Poll OKX.AI marketplace for recommended tasks matching KARA Intelligence (#2754).
Sends Telegram notification when new public tasks appear.

Usage:
    export OKX_AGENT_ID=2754
    export TELEGRAM_BOT_TOKEN=...
    export TELEGRAM_CHAT_ID=1492210461
    python3 okx-task-poller.py
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

AGENT_ID = os.environ.get("OKX_AGENT_ID", "2754")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "1492210461")
STATE_FILE = Path(os.environ.get("OKX_POLLER_STATE", "/home/ubuntu/.local/state/okx-task-poller.json"))
ONCHAINOS = os.environ.get("ONCHAINOS_BIN", "/home/ubuntu/.local/bin/onchainos")


def load_dotenv_poller() -> None:
    """Load optional .env.poller from okx-ai-agent directory."""
    poller_env = Path("/home/ubuntu/okx-ai-agent/.env.poller")
    if poller_env.exists():
        for line in poller_env.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key not in os.environ:
                os.environ[key] = value.strip()


def log(msg: str) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[{ts}] {msg}")


def run(cmd: list[str]) -> tuple[int, str, str]:
    env = os.environ.copy()
    env["PATH"] = "/home/ubuntu/.local/bin:" + env.get("PATH", "")
    res = subprocess.run(cmd, capture_output=True, text=True, env=env, check=False)
    return res.returncode, res.stdout, res.stderr


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"seen_jobs": [], "last_run": None}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def parse_recommend_output(text: str) -> list[dict]:
    jobs = []
    pattern = re.compile(
        r"jobId:\s*([0-9a-fx]+)\s*\n"
        r"\s*Title:\s*(.*?)\s*\n"
        r"\s*Description:\s*(.*?)\s*\n"
        r"\s*Budget:\s*([\d.]+)\s*\(token:\s*([0-9a-fx]+)\)\s*\n"
        r"\s*Min credit:\s*([\d.]+)\s*\n"
        r"\s*Created:\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)",
        re.IGNORECASE,
    )
    for m in pattern.finditer(text):
        jobs.append(
            {
                "job_id": m.group(1),
                "title": m.group(2).strip(),
                "description": m.group(3).strip(),
                "budget": m.group(4),
                "token": m.group(5),
                "min_credit": m.group(6),
                "created": m.group(7),
            }
        )
    return jobs


def send_telegram(message: str) -> bool:
    if not BOT_TOKEN:
        log("WARNING: TELEGRAM_BOT_TOKEN not set, skipping notification")
        return False
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    try:
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
        return data.get("ok", False)
    except Exception as exc:
        log(f"Telegram send failed: {exc}")
        return False


def main() -> int:
    load_dotenv_poller()
    log(f"Polling OKX.AI tasks for agent {AGENT_ID}")

    # Try to load token from Hermes default .env if not provided
    if not BOT_TOKEN:
        hermes_env = Path.home() / ".hermes" / ".env"
        if hermes_env.exists():
            for line in hermes_env.read_text().splitlines():
                if line.startswith("TELEGRAM_BOT_TOKEN="):
                    os.environ["TELEGRAM_BOT_TOKEN"] = line.split("=", 1)[1].strip()
                    break

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        log("ERROR: Could not find TELEGRAM_BOT_TOKEN")
        return 1

    code, stdout, stderr = run([ONCHAINOS, "agent", "recommend-task", "--agent-id", AGENT_ID])
    if code != 0:
        log(f"onchainos failed: {stderr}")
        return 1

    jobs = parse_recommend_output(stdout)
    log(f"Found {len(jobs)} recommended task(s)")

    state = load_state()
    seen = set(state.get("seen_jobs", []))
    new_jobs = [j for j in jobs if j["job_id"] not in seen]

    if new_jobs:
        log(f"{len(new_jobs)} new task(s) detected")
        lines = ["🎯 *OKX.AI New Tasks for KARA Intelligence*", ""]
        for j in new_jobs[:5]:
            desc = j["description"][:120] + "..." if len(j["description"]) > 120 else j["description"]
            lines.append(
                f"*{j['title']}*\n"
                f"💰 Budget: {j['budget']} USDT\n"
                f"📝 {desc}\n"
                f"🔗 `{j['job_id'][:20]}...`"
            )
            lines.append("")
        lines.append(f"Total matched: {len(jobs)} tasks")
        send_telegram("\n".join(lines))
    else:
        log("No new tasks")

    # Update state
    state["seen_jobs"] = [j["job_id"] for j in jobs]
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    save_state(state)

    return 0


if __name__ == "__main__":
    sys.exit(main())
