# OKX.AI Agent Service — KARA Intelligence

Hermes-powered ASP (Agent Service Provider) for the OKX.AI marketplace.

## What it sells

A2MCP pay-per-call services and one A2A custom-automation service, built on top of `onchainos` skills and exposed through a public FastAPI server.

| Service | Path | Fee | Category |
|---|---|---|---|
| Token Launch Due Diligence | `/a2mcp/launch-dd` | 0.5 USDT | Finance Copilot |
| X Layer Smart Money Hunter | `/a2mcp/xlayer-smart-money` | 0.2 USDT | Finance Copilot |
| Wallet Security Cleanup | `/a2mcp/wallet-cleanup` | 0.2 USDT | Finance Copilot |
| Custom On-Chain Automation | *(A2A task)* | 1.0 USDT | Software Utility |
| Smart Contract Quick Audit | `/a2mcp/contract-audit` | 0.5 USDT | Software Utility |
| Multi-Wallet PnL Dashboard | `/a2mcp/wallet-pnl` | 0.3 USDT | Software Utility |
| Whale Alert Feed | `/a2mcp/whale-alert` | 0.2 USDT | Social Buzz |
| Bridge Route Optimizer | `/a2mcp/bridge-route` | 0.2 USDT | Software Utility |
| AI Crypto News Sentiment Alpha | `/a2mcp/news-alpha` | 0.2 USDT | Finance Copilot |
| Meme Pump Scanner | `/a2mcp/meme-pump` | 0.2 USDT | Finance Copilot |

## Project layout

```
okx-ai-agent/
├── .env                 # credentials (gitignored)
├── .env.example
├── .gitignore
├── README.md
├── PROMO.md
├── requirements.txt
├── server.py            # FastAPI A2MCP server
├── services.json        # service catalog for ASP registration
├── scripts/
│   ├── register-asp.py  # register/update ASP identity
│   └── test-local.sh    # curl smoke tests
└── skills/
    └── okx-ai-service/
        └── SKILL.md     # Hermes skill wrapper
```

## Quick start

1. Install deps:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Make sure `.env` has `OKX_API_KEY`, `OKX_SECRET_KEY`, `OKX_PASSPHRASE`.
   Optional: set `ONCHAINOS_BIN` if `onchainos` is not in `~/.local/bin`.

3. Run local server:
   ```bash
   python server.py
   ```

4. Smoke test:
   ```bash
   bash scripts/test-local.sh
   ```

5. Expose publicly (Cloudflare Tunnel / 9Router) and update `services.json` endpoints.

## Register / update ASP

```bash
python scripts/register-asp.py
```

This calls `onchainos agent create --role asp` using `services.json` and a local avatar image.

To update an existing agent (e.g., #2754), use the `onchainos agent update` flow with a service delta.

## Notes

- Keep `.env` out of git.
- Fund the X Layer wallet with a small amount of OKB for gas before activating services.
- A2MCP endpoints must be publicly reachable over `https://`.
