#!/usr/bin/env python3
"""Full audit of OKX.AI KARA Intelligence agent before resubmission."""
import json
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path("/home/ubuntu/okx-ai-agent")
SERVICES_FILE = ROOT / "services.json"
AGENT_ID = "2754"
BASE = "https://okx-ai.eida.web.id"
ONCHAINOS = Path.home() / ".local/bin/onchainos"


def run(args: list[str], timeout: int = 60) -> dict:
    env = {"PATH": f"{Path.home()}/.npm-global/bin:{Path.home()}/.local/bin:/usr/bin:/bin"}
    res = subprocess.run([str(ONCHAINOS)] + args, capture_output=True, text=True, env=env, timeout=timeout)
    try:
        return json.loads(res.stdout)
    except Exception:
        return {"ok": res.returncode == 0, "stdout": res.stdout, "stderr": res.stderr, "rc": res.returncode}


def http(method: str, path: str, payload: dict | None = None) -> tuple[int, dict | str]:
    url = f"{BASE}{path}"
    data = json.dumps(payload).encode() if payload else None
    headers = {"User-Agent": "OKX-AI-KARA-Audit/1.0"}
    if payload:
        headers["Content-Type"] = "application/json"
    try:
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode()
            try:
                return r.getcode(), json.loads(body)
            except Exception:
                return r.getcode(), body[:200]
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:200]
        return e.code, body
    except Exception as e:
        return 0, str(e)


def main():
    cfg = json.loads(SERVICES_FILE.read_text())
    services = cfg["services"]
    findings = []

    print("=" * 60)
    print("OKX.AI KARA Intelligence Full Audit")
    print("=" * 60)

    # 1. Service catalog validation
    print("\n[1] Service catalog validation")
    val = run([
        "agent", "validate-listing",
        "--role", "asp",
        "--name", cfg["agent"]["name"],
        "--description", cfg["agent"]["description"],
        "--service", json.dumps(services),
    ])
    print(json.dumps(val, indent=2)[:500])
    if not val.get("pass"):
        findings.append("validate-listing failed")

    # 2. Service name lengths and forbidden markers
    print("\n[2] Service name / description checks")
    forbidden = ["test", "[test]", "(pre)", "-dev", "(dev)", "draft"]
    for s in services:
        name = s["serviceName"]
        desc = s["serviceDescription"]
        if not (5 <= len(name) <= 30):
            findings.append(f"service name length out of range: {name} ({len(name)})")
        for f in forbidden:
            # use word-boundary-style check: standalone token, bracketed, or hyphenated
            patterns = [f" {f} ", f"[{f}]", f"({f})", f"-{f}", f"{f}-"]
            text = (name + " " + desc).lower()
            if any(p in text for p in patterns):
                findings.append(f"forbidden marker '{f}' in service: {name}")
        print(f"  ✅ {name} ({len(name)} chars)")

    # 3. Gate-check
    print("\n[3] Gate-check")
    gate = run(["agent", "gate-check", "--role", "asp"])
    print(json.dumps(gate, indent=2)[:800])
    if not gate.get("data", {}).get("ready"):
        findings.append("gate-check not ready")
    if not gate.get("data", {}).get("communication", {}).get("ok"):
        findings.append("communication channel not ready")

    # 4. Endpoint probe
    print("\n[4] A2MCP endpoint probes")
    endpoints = [
        ("token-report", {"chain": "base", "address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"}),
        ("wallet-analysis", {"address": "0x28C6c06298d514Db089934071355E5743bf21d60"}),
        ("smart-money", {"chain": "base", "limit": 2}),
        ("security-scan", {"chain": "base", "address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"}),
        ("social-brief", {"symbol": "BTC"}),
        ("rugpull-score", {"chain": "base", "address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"}),
        ("kara-intel-pack", {"chain": "base", "token_address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", "wallet_address": "0x28C6c06298d514Db089934071355E5743bf21d60"}),
        ("launch-dd", {"chain": "base", "address": "0x940181a94a35a4569e4529a3cdfb74e38fd98631"}),
        ("contract-audit", {"chain": "base", "address": "0x940181a94a35a4569e4529a3cdfb74e38fd98631"}),
        ("xlayer-smart-money", {"time_frame": "7D", "limit": 2}),
        ("wallet-cleanup", {"chain": "base", "address": "0x38Baf554CbD3df737F49545170BeCE990D6233Ed"}),
        ("wallet-pnl", {"chain": "base", "addresses": "0x38Baf554CbD3df737F49545170BeCE990D6233Ed"}),
        ("whale-alert", {"chain": "base", "min_volume": 5000}),
        ("bridge-route", {"from": "USDC", "from_chain": "base", "to": "USDC", "to_chain": "arbitrum", "amount": "10"}),
        ("news-alpha", {"symbol": "BTC"}),
        ("meme-pump", {"chain": "base"}),
    ]
    for path, payload in endpoints:
        get_code, _ = http("GET", f"/a2mcp/{path}")
        post_code, post_body = http("POST", f"/a2mcp/{path}", payload)
        post_ok = "-"
        if isinstance(post_body, dict):
            post_ok = str(post_body.get("ok"))
        ok = get_code == 200 and post_code == 200
        status = "✅" if ok else "❌"
        print(f"  {status} {path:<30} GET={get_code} POST={post_code} ok={post_ok}")
        if not ok:
            findings.append(f"endpoint unhealthy: {path} GET={get_code} POST={post_code}")

    # 5. Agent profile
    print("\n[5] Agent profile status")
    prof = run(["agent", "profile", AGENT_ID])
    data = prof.get("data", {})
    print(f"  approvalDisplayStatus: {data.get('approvalDisplayStatus')}")
    print(f"  approvalLabel: {data.get('approvalLabel')}")
    print(f"  statusLabel: {data.get('statusLabel')}")
    print(f"  onlineStatus: {data.get('onlineStatus')}")
    print(f"  serviceList count: {len(data.get('serviceList', []))}")

    # 6. Summary
    print("\n" + "=" * 60)
    if findings:
        print(f"❌ AUDIT FAILED ({len(findings)} findings):")
        for f in findings:
            print(f"  - {f}")
    else:
        print("✅ AUDIT PASSED — no blockers found for resubmission.")
    print("=" * 60)


if __name__ == "__main__":
    main()
