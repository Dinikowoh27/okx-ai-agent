# OKX.AI Agent Service — Eida

Hermes-powered ASP (Agent Service Provider) for OKX.AI marketplace.

## What it sells

A2MCP pay-per-call services built on top of `onchainos` skills:

| Service | OnchainOS command | Path | Fee |
|---|---|---|---|
| Token Intel Report | `token report` | `/a2mcp/token-report` | 0.5 USDT |
| Wallet Analysis | `workflow wallet-analysis` | `/a2mcp/wallet-analysis` | 0.5 USDT |
| Smart Money Signals | `signal list` | `/a2mcp/smart-money` | 1 USDT |
| Security Scan | `security token-scan` | `/a2mcp/security-scan` | 0.5 USDT |
| Crypto News Brief | `social news` | `/a2mcp/social-brief` | 0.5 USDT |

## Project layout

```
okx-ai-agent/
├── .env                 # credentials (gitignored)
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── server.py            # FastAPI A2MCP server
├── services.json        # service catalog for ASP registration
├── scripts/
│   ├── register-asp.sh  # register/update ASP identity
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

3. Run local server:
   ```bash
   python server.py
   ```

4. Smoke test:
   ```bash
   bash scripts/test-local.sh
   ```

5. Expose publicly (Cloudflare Tunnel / 9Router) and update `services.json` endpoints.

## Register ASP

```bash
bash scripts/register-asp.sh
```

This calls `onchainos agent create --role asp` using `services.json` and a local avatar image.

## Notes

- Keep `.env` out of git.
- Fund the X Layer wallet with a small amount of OKB for gas before activating services.
- A2MCP endpoint must be publicly reachable over `https://`.
