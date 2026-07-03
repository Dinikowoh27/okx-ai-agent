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


# ---------------------------------------------------------------------------
# Demo responses for OKX QA / empty-payload probes
# QA sometimes calls endpoints without params; never return 400.
# ---------------------------------------------------------------------------

DEMO_TOKEN = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"  # USDC on Base
DEMO_WALLET = "0x28C6c06298d514Db089934071355E5743bf21d60"   # known Binance hot wallet


def _demo_token_audit(service: str) -> dict[str, Any]:
    return {
        "ok": True,
        "demo": True,
        "service": service,
        "verdict": "SAFE",
        "score": 5,
        "reasons": ["stablecoin contract", "low tax", "ownership renounced"],
        "token_address": DEMO_TOKEN,
        "chain": "base",
        "note": "Replace the demo response by providing a real token address in the request body.",
    }


def _demo_wallet_scan(service: str) -> dict[str, Any]:
    return {
        "ok": True,
        "demo": True,
        "service": service,
        "wallet": DEMO_WALLET,
        "chain": "base",
        "risk_summary": {
            "high_risk_approvals": 0,
            "suspicious_holdings": 0,
            "trusted_tokens": ["USDC", "USDT", "WETH"],
        },
        "note": "Replace the demo response by providing a wallet address in the request body.",
    }


def _demo_wallet_pnl() -> dict[str, Any]:
    return {
        "ok": True,
        "demo": True,
        "service": "wallet-pnl",
        "chain": "base",
        "wallet_count": 1,
        "aggregate": {
            "realizedPnlUsd": 1240.5,
            "unrealizedPnlUsd": -80.25,
            "buyTxVolume": 15000.0,
            "sellTxVolume": 16240.5,
            "txs": 42,
        },
        "note": "Replace the demo response by providing wallet addresses in the 'addresses' field.",
    }


def _demo_bridge_route() -> dict[str, Any]:
    return {
        "ok": True,
        "demo": True,
        "service": "bridge-route",
        "route": {
            "from": "USDC",
            "from_chain": "base",
            "to": "USDC",
            "to_chain": "arbitrum",
            "amount": "100",
            "best_provider": "Across",
            "estimated_fee_usd": "0.35",
            "estimated_time": "~2 min",
        },
        "note": "Replace the demo response by providing from, from_chain, to, to_chain, and amount.",
    }


def _demo_kara_intel_pack() -> dict[str, Any]:
    return {
        "ok": True,
        "demo": True,
        "service": "kara-intel-pack",
        "token_report": _demo_token_audit("token-report"),
        "wallet_analysis": _demo_wallet_scan("wallet-analysis"),
        "security_scan": _demo_token_audit("security-scan"),
        "note": "Replace the demo response by providing token_address and wallet_address.",
    }


async def _safe_json(req: Request) -> dict[str, Any]:
    """Return empty dict if body is missing or not JSON."""
    try:
        return await req.json()
    except Exception:  # noqa: BLE001
        return {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="KARA Intelligence OKX.AI A2MCP", lifespan=lifespan)


@app.get("/health")
def health():
    return {"ok": True, "agent": "kara-intelligence"}


# ---------------------------------------------------------------------------
# Legacy / general services
# ---------------------------------------------------------------------------


@app.post("/a2mcp/token-report")
async def token_report(req: Request):
    body = await _safe_json(req)
    chain = body.get("chain", "base")
    address = body.get("address", "")
    if not address:
        return _demo_token_audit("token-report")
    return run(["token", "report", "--address", address, "--chain", chain])


@app.post("/a2mcp/wallet-analysis")
async def wallet_analysis(req: Request):
    body = await _safe_json(req)
    address = body.get("address", "")
    if not address:
        return _demo_wallet_scan("wallet-analysis")
    return run(["workflow", "wallet-analysis", "--address", address])


@app.post("/a2mcp/smart-money")
async def smart_money(req: Request):
    body = await _safe_json(req)
    chain = body.get("chain", "base")
    limit = str(body.get("limit", "5"))
    return run(["signal", "list", "--chain", chain, "--limit", limit])


@app.post("/a2mcp/security-scan")
async def security_scan(req: Request):
    body = await _safe_json(req)
    chain = body.get("chain", "base")
    address = body.get("address", "")
    if not address:
        return _demo_token_audit("security-scan")
    token = f"{chain}:{address}"
    return run(["security", "token-scan", "--tokens", token])


@app.post("/a2mcp/social-brief")
async def social_brief(req: Request):
    body = await _safe_json(req)
    symbol = body.get("symbol", "BTC")
    return run(["social", "news-by-symbol", "--token-symbols", symbol])


@app.post("/a2mcp/rugpull-score")
async def rugpull_score(req: Request):
    """Combined rugpull risk score from token scan + token report."""
    body = await _safe_json(req)
    chain = body.get("chain", "base")
    address = body.get("address", "")
    if not address:
        return _demo_token_audit("rugpull-score")

    security = run(["security", "token-scan", "--tokens", f"{chain}:{address}"])
    report = run(["token", "report", "--address", address, "--chain", chain])

    score = 0
    reasons = []
    sec_data = None
    if security.get("ok") and isinstance(security.get("data"), list) and security["data"]:
        sec_data = security["data"][0]
    elif security.get("ok") and isinstance(security.get("data"), dict):
        sec_data = security["data"]

    if not sec_data:
        score += 30
        reasons.append("security scan unavailable")
    else:
        if sec_data.get("isHoneypot"):
            score += 50
            reasons.append("honeypot detected")
        try:
            buy_tax = float(sec_data.get("buyTaxes", "0") or "0")
            sell_tax = float(sec_data.get("sellTaxes", "0") or "0")
            if buy_tax > 5 or sell_tax > 5:
                score += 25
                reasons.append("high tax")
        except (ValueError, TypeError):
            pass
        if sec_data.get("isMintable"):
            score += 20
            reasons.append("mintable supply")
        if sec_data.get("isNotRenounced"):
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
    body = await _safe_json(req)
    chain = body.get("chain", "base")
    token_address = body.get("token_address", "")
    wallet_address = body.get("wallet_address", "")
    if not token_address or not wallet_address:
        return _demo_kara_intel_pack()
    return {
        "ok": True,
        "token_report": run(["token", "report", "--address", token_address, "--chain", chain]),
        "wallet_analysis": run(["workflow", "wallet-analysis", "--address", wallet_address]),
        "security_scan": run(["security", "token-scan", "--tokens", f"{chain}:{token_address}"]),
    }


# ---------------------------------------------------------------------------
# New KARA Intelligence v2 services
# ---------------------------------------------------------------------------


def _audit_token(chain: str, address: str) -> dict[str, Any]:
    """Shared token audit logic for launch-dd and contract-audit."""
    report = run(["token", "report", "--address", address, "--chain", chain])
    security = run(["security", "token-scan", "--tokens", f"{chain}:{address}"])

    score = 0
    reasons = []
    verdict = "SAFE"
    sec_data = None
    if security.get("ok") and isinstance(security.get("data"), list) and security["data"]:
        sec_data = security["data"][0]
    elif security.get("ok") and isinstance(security.get("data"), dict):
        sec_data = security["data"]

    if not sec_data:
        score += 30
        reasons.append("security scan unavailable")
    else:
        if sec_data.get("isHoneypot"):
            score += 50
            reasons.append("honeypot detected")
        try:
            buy_tax = float(sec_data.get("buyTaxes", "0") or "0")
            sell_tax = float(sec_data.get("sellTaxes", "0") or "0")
            if buy_tax > 5 or sell_tax > 5:
                score += 25
                reasons.append("high tax")
        except (ValueError, TypeError):
            pass
        if sec_data.get("isMintable"):
            score += 20
            reasons.append("mintable supply")
        if sec_data.get("isNotRenounced"):
            score += 15
            reasons.append("ownership not renounced")

    if not report.get("ok"):
        score += 10
        reasons.append("token report incomplete")

    if score >= 70:
        verdict = "SCAM"
    elif score >= 40:
        verdict = "RISKY"
    elif score >= 15:
        verdict = "CAUTION"
    else:
        verdict = "SAFE"

    return {
        "ok": True,
        "verdict": verdict,
        "score": min(score, 100),
        "reasons": reasons,
        "token_report": report,
        "security_scan": security,
    }


@app.post("/a2mcp/launch-dd")
async def launch_dd(req: Request):
    """Token launch due diligence: security + token report + verdict."""
    body = await _safe_json(req)
    chain = body.get("chain", "base")
    address = body.get("address", "")
    if not address:
        return _demo_token_audit("launch-dd")
    return _audit_token(chain, address)


@app.post("/a2mcp/contract-audit")
async def contract_audit(req: Request):
    """Quick contract audit: same deep check as launch-dd."""
    body = await _safe_json(req)
    chain = body.get("chain", "base")
    address = body.get("address", "")
    if not address:
        return _demo_token_audit("contract-audit")
    return _audit_token(chain, address)


@app.post("/a2mcp/xlayer-smart-money")
async def xlayer_smart_money(req: Request):
    """Top profitable wallets on X Layer."""
    body = await _safe_json(req)
    time_frame = body.get("time_frame", "7D")
    sort_by = body.get("sort_by", "PnL")
    limit = int(body.get("limit", "20"))

    tf_map = {"1D": "1", "3D": "2", "7D": "3", "1M": "4", "3M": "5"}
    sort_map = {"PnL": "1", "WinRate": "2", "Txs": "3", "Volume": "4", "ROI": "5"}

    tf = tf_map.get(time_frame, "3")
    sb = sort_map.get(sort_by, "1")

    result = run(
        ["leaderboard", "list", "--chain", "xlayer", "--time-frame", tf, "--sort-by", sb],
        timeout=120,
    )
    if result.get("ok") and isinstance(result.get("data"), list):
        result["data"] = result["data"][:limit]
    return result


@app.post("/a2mcp/wallet-cleanup")
async def wallet_cleanup(req: Request):
    """Scan wallet for dangerous approvals and risky holdings."""
    body = await _safe_json(req)
    chain = body.get("chain", "base")
    address = body.get("address", "")
    if not address:
        return _demo_wallet_scan("wallet-cleanup")

    approvals = run(["security", "approvals", "--address", address, "--chain", chain])
    holdings = run(["security", "token-scan", "--address", address, "--chain", chain])
    return {
        "ok": True,
        "wallet": address,
        "chain": chain,
        "approvals": approvals,
        "holdings_risk_scan": holdings,
    }


@app.post("/a2mcp/wallet-pnl")
async def wallet_pnl(req: Request):
    """Aggregate PnL across multiple wallets."""
    body = await _safe_json(req)
    chain = body.get("chain", "base")
    addresses = body.get("addresses", "")
    if not addresses:
        return _demo_wallet_pnl()

    addrs = [a.strip() for a in str(addresses).split(",") if a.strip()]
    summaries = []
    totals = {
        "realizedPnlUsd": 0.0,
        "unrealizedPnlUsd": 0.0,
        "buyTxVolume": 0.0,
        "sellTxVolume": 0.0,
        "txs": 0,
    }
    for addr in addrs:
        overview = run(["market", "portfolio-overview", "--chain", chain, "--address", addr])
        summaries.append({"address": addr, "overview": overview})
        if overview.get("ok") and isinstance(overview.get("data"), dict):
            d = overview["data"]
            for key in totals:
                try:
                    totals[key] += float(d.get(key, "0") or "0")
                except (ValueError, TypeError):
                    pass

    return {
        "ok": True,
        "chain": chain,
        "wallet_count": len(addrs),
        "aggregate": totals,
        "wallets": summaries,
    }


@app.post("/a2mcp/whale-alert")
async def whale_alert(req: Request):
    """Latest smart-money / KOL DEX trades on a chain."""
    body = await _safe_json(req)
    chain = body.get("chain", "base")
    min_volume = str(body.get("min_volume", "1000"))
    tracker_type = body.get("tracker_type", "smart_money")
    trade_type = str(body.get("trade_type", "0"))

    tracker_map = {"smart_money": "1", "kol": "2"}
    tt = tracker_map.get(tracker_type, "1")

    result = run(
        [
            "tracker",
            "activities",
            "--tracker-type",
            tt,
            "--chain",
            chain,
            "--min-volume",
            min_volume,
            "--trade-type",
            trade_type,
        ],
        timeout=120,
    )
    return result


@app.post("/a2mcp/bridge-route")
async def bridge_route(req: Request):
    """Find cheapest/fastest cross-chain bridge route."""
    body = await _safe_json(req)
    from_token = body.get("from", "")
    from_chain = body.get("from_chain", "")
    to_token = body.get("to", "")
    to_chain = body.get("to_chain", "")
    amount = str(body.get("amount", ""))
    sort = str(body.get("sort", "0"))

    missing = [k for k, v in {
        "from": from_token,
        "from_chain": from_chain,
        "to": to_token,
        "to_chain": to_chain,
        "amount": amount,
    }.items() if not v]
    if missing:
        return _demo_bridge_route()

    return run(
        [
            "cross-chain",
            "quote",
            "--from",
            from_token,
            "--from-chain",
            from_chain,
            "--to",
            to_token,
            "--to-chain",
            to_chain,
            "--readable-amount",
            amount,
            "--sort",
            sort,
        ],
        timeout=120,
    )


@app.post("/a2mcp/news-alpha")
async def news_alpha(req: Request):
    """Crypto news + sentiment for a symbol or topic."""
    body = await _safe_json(req)
    symbol = body.get("symbol", "BTC")
    sentiment = run(["social", "sentiment-symbol", "--token-symbols", symbol])
    news = run(["social", "news-by-symbol", "--token-symbols", symbol])
    return {
        "ok": True,
        "symbol": symbol,
        "sentiment": sentiment,
        "news": news,
    }


@app.post("/a2mcp/meme-pump")
async def meme_pump(req: Request):
    """Scan newly launched meme tokens with risk filters."""
    body = await _safe_json(req)
    chain = body.get("chain", "base")
    stage = body.get("stage", "NEW")
    result = run(["memepump", "tokens", "--chain", chain, "--stage", stage], timeout=120)
    if result.get("ok") and isinstance(result.get("data"), list):
        result["data"] = result["data"][:20]
    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT)
