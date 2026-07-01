#!/usr/bin/env python3
"""
A2MCP server for OKX.AI.
Receives paid API calls from OKX.AI users, runs the matching onchainos CLI skill,
and returns JSON results.

TODO: verify x402 / MPP payment proof when OKX.AI sends it in headers/body.
"""
import json
import os
import subprocess
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

load_dotenv()

ONCHAINOS = os.path.expanduser(os.getenv("ONCHAINOS_BIN", "~/.local/bin/onchainos"))
HOST = os.getenv("OKX_AI_HOST", "0.0.0.0")
PORT = int(os.getenv("OKX_AI_PORT", "8000"))


def run(cmd: list[str], timeout: int = 60) -> dict[str, Any]:
    """Run an onchainos command and return its JSON output."""
    env = os.environ.copy()
    env["PATH"] = os.path.expanduser(os.getenv("ONCHAINOS_DIR", "~/.local/bin")) + ":" + env.get("PATH", "")
    try:
        result = subprocess.run(
            [ONCHAINOS] + cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            check=False,
        )
        if result.returncode != 0:
            return {"ok": False, "error": result.stderr or result.stdout}
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"ok": True, "raw": result.stdout}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout"}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Eida OKX.AI A2MCP", lifespan=lifespan)


@app.get("/health")
def health():
    return {"ok": True, "agent": "eida-okx-ai"}


@app.post("/a2mcp/token-report")
async def token_report(req: Request):
    body = await req.json()
    chain = body.get("chain", "base")
    address = body.get("address", "")
    if not address:
        return JSONResponse({"ok": False, "error": "address required"}, status_code=400)
    return run(["token", "report", "--address", address, "--chain", chain])


@app.post("/a2mcp/wallet-analysis")
async def wallet_analysis(req: Request):
    body = await req.json()
    address = body.get("address", "")
    if not address:
        return JSONResponse({"ok": False, "error": "address required"}, status_code=400)
    return run(["workflow", "wallet-analysis", "--address", address])


@app.post("/a2mcp/smart-money")
async def smart_money(req: Request):
    body = await req.json()
    chain = body.get("chain", "base")
    limit = str(body.get("limit", "5"))
    return run(["signal", "list", "--chain", chain, "--limit", limit])


@app.post("/a2mcp/security-scan")
async def security_scan(req: Request):
    body = await req.json()
    chain = body.get("chain", "base")
    address = body.get("address", "")
    if not address:
        return JSONResponse({"ok": False, "error": "address required"}, status_code=400)
    token = f"{chain}:{address}"
    return run(["security", "token-scan", "--tokens", token])


@app.post("/a2mcp/social-brief")
async def social_brief(req: Request):
    body = await req.json()
    symbol = body.get("symbol", "BTC")
    return run(["social", "news-by-symbol", "--token-symbols", symbol])


@app.post("/a2mcp/rugpull-score")
async def rugpull_score(req: Request):
    """Combined rugpull risk score from token scan + token report."""
    body = await req.json()
    chain = body.get("chain", "base")
    address = body.get("address", "")
    if not address:
        return JSONResponse({"ok": False, "error": "address required"}, status_code=400)

    security = run(["security", "token-scan", "--tokens", f"{chain}:{address}"])
    report = run(["token", "report", "--address", address, "--chain", chain])

    # Simple heuristic score 0-100 (lower = safer)
    score = 0
    reasons = []
    if not security.get("ok"):
        score += 30
        reasons.append("security scan unavailable")
    else:
        data = security.get("data", {})
        if data.get("is_honeypot"):
            score += 50
            reasons.append("honeypot detected")
        if data.get("buy_tax", 0) > 5 or data.get("sell_tax", 0) > 5:
            score += 25
            reasons.append("high tax")
        if data.get("is_mintable"):
            score += 20
            reasons.append("mintable supply")
        if data.get("is_ownership_renounced") is False:
            score += 15
            reasons.append("ownership not renounced")

    if not report.get("ok"):
        score += 10
        reasons.append("token report incomplete")

    verdict = "BUY" if score <= 20 else "SKIP" if score <= 50 else "BLOCK"
    return {
        "ok": True,
        "score": min(score, 100),
        "verdict": verdict,
        "reasons": reasons,
        "security": security,
        "report": report,
    }


@app.post("/a2mcp/kara-intel-pack")
async def kara_intel_pack(req: Request):
    """Bundle: token report + wallet analysis + security scan."""
    body = await req.json()
    chain = body.get("chain", "base")
    token_address = body.get("token_address", "")
    wallet_address = body.get("wallet_address", "")
    if not token_address or not wallet_address:
        return JSONResponse(
            {"ok": False, "error": "token_address and wallet_address required"},
            status_code=400,
        )
    return {
        "ok": True,
        "token_report": run(["token", "report", "--address", token_address, "--chain", chain]),
        "wallet_analysis": run(["workflow", "wallet-analysis", "--address", wallet_address]),
        "security_scan": run(["security", "token-scan", "--tokens", f"{chain}:{token_address}"]),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT)
