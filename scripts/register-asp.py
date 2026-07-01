#!/usr/bin/env python3
"""Register the OKX.AI ASP identity from services.json."""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT / ".env"
SERVICES = ROOT / "services.json"
ONCHAINOS = Path.home() / ".local/bin/onchainos"


def load_env(path: Path) -> dict:
    env = {}
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k] = v
    return env


def run(args: list[str], env: dict | None = None) -> dict:
    base_env = os.environ.copy()
    base_env["PATH"] = str(Path.home() / ".local/bin") + ":" + base_env.get("PATH", "")
    if env:
        base_env.update(env)
    result = subprocess.run(
        [str(ONCHAINOS)] + args,
        capture_output=True,
        text=True,
        env=base_env,
        check=False,
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "ok": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }


def upload_avatar(path: Path, env: dict) -> str:
    res = run(["agent", "upload", "--file", str(path)], env)
    if not res.get("ok"):
        print("Avatar upload failed:", res)
        sys.exit(1)
    return res["data"]["url"]


def main() -> int:
    if not SERVICES.exists():
        print(f"services.json not found at {SERVICES}")
        return 1

    cfg = json.loads(SERVICES.read_text())
    agent_cfg = cfg["agent"]
    services = cfg["services"]

    env = load_env(ENV)
    if not all(k in env for k in ("OKX_API_KEY", "OKX_SECRET_KEY", "OKX_PASSPHRASE")):
        print("Missing OKX credentials in .env")
        return 1

    # Upload avatar
    picture_path = ROOT / agent_cfg["picture"]
    if not picture_path.exists():
        print(f"Avatar not found at {picture_path}. Please add a 1:1 square PNG/JPEG.")
        return 1
    print(f"Uploading avatar {picture_path} ...")
    picture_url = upload_avatar(picture_path, env)
    print(f"Avatar URL: {picture_url}")

    # Validate listing
    print("Validating listing ...")
    validate_res = run(
        [
            "agent",
            "validate-listing",
            "--role",
            "asp",
            "--name",
            agent_cfg["name"],
            "--description",
            agent_cfg["description"],
            "--service",
            json.dumps(services),
        ],
        env,
    )
    print(json.dumps(validate_res, indent=2))
    if validate_res.get("pass") is not True:
        print("Listing validation failed. Fix services.json and retry.")
        return 1

    # Create agent
    print("Creating ASP identity ...")
    create_res = run(
        [
            "agent",
            "create",
            "--role",
            "asp",
            "--name",
            agent_cfg["name"],
            "--description",
            agent_cfg["description"],
            "--picture",
            picture_url,
            "--service",
            json.dumps(services),
        ],
        env,
    )
    print(json.dumps(create_res, indent=2))
    return 0 if create_res.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
