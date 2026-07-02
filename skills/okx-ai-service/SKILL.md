---
name: okx-ai-service
description: "Hermes skill wrapper for the OKX.AI A2MCP service server. Routes inbound A2MCP requests to the correct onchainos CLI command via the local FastAPI server and handles ASP registration / service-catalog updates."
license: MIT
metadata:
  author: eida
  version: "0.2.0"
---

# OKX.AI Service Handler

Internal skill untuk menjalankan layanan KARA Intelligence di OKX.AI marketplace.

## When to use

- Menerima request A2MCP dari OKX.AI user.
- Menjalankan onchainos CLI skill sesuai service yang dipanggil.
- Menyiapkan/register ASP identity dan service catalog.
- Mengupdate service yang sudah terdaftar.

## Local server

FastAPI server berjalan di `okx-ai-agent/server.py`.

```bash
cd "$OKX_AI_DIR"
source .venv/bin/activate
python server.py
```

## A2MCP Endpoints

| Path | Service | onchainos command |
|---|---|---|
| `POST /a2mcp/launch-dd` | Token Launch Due Diligence | `token report` + `security token-scan` |
| `POST /a2mcp/contract-audit` | Smart Contract Quick Audit | `token report` + `security token-scan` |
| `POST /a2mcp/xlayer-smart-money` | X Layer Smart Money Hunter | `leaderboard list --chain xlayer` |
| `POST /a2mcp/wallet-cleanup` | Wallet Security Cleanup | `security approvals` + `security token-scan --address` |
| `POST /a2mcp/wallet-pnl` | Multi-Wallet PnL Dashboard | `market portfolio-overview` per wallet |
| `POST /a2mcp/whale-alert` | Whale Alert Feed | `tracker activities --tracker-type smart_money/kol` |
| `POST /a2mcp/bridge-route` | Bridge Route Optimizer | `cross-chain quote` |
| `POST /a2mcp/news-alpha` | AI Crypto News Sentiment Alpha | `social sentiment-symbol` + `social news-by-symbol` |
| `POST /a2mcp/meme-pump` | Meme Pump Scanner | `memepump tokens --chain` |

## A2A Service

- **Custom On-Chain Automation** — user deskripsikan workflow, KARA membangun dan men-deploy automation.

## Register ASP identity

1. Isi `services.json` dengan nama, deskripsi, avatar, dan daftar service.
2. Ganti endpoint URL di `services.json` ke public HTTPS yang sebenarnya.
3. Pastikan file avatar ada di `assets/avatar.png`.
4. Jalankan:

```bash
cd "$OKX_AI_DIR"
source .venv/bin/activate
python scripts/register-asp.py
```

Script akan upload avatar, validate listing, lalu `onchainos agent create`.

## Update existing ASP

Gunakan `onchainos agent update --agent-id <id> --service <delta-json>`. Delta berisi operation `create`, `update`, atau `delete` untuk setiap service.

## Service design rules

- Service name: 5–30 karakter, noun phrase, tidak sama dengan agent name.
- Description: 2 bagian — (1) apa yang dilakukan, (2) apa yang user harus sediakan.
- Type: `A2MCP` untuk pay-per-call API, `A2A` untuk custom task.
- Fee: angka murni dalam USDT, maksimal 6 desimal.
- Endpoint: harus `https://`, publicly reachable, ≤512 karakter (kosong untuk A2A).

## Quality gate

Sebelum mengirim hasil ke user:
1. Verifikasi CLI output punya field `ok: true`.
2. Kalau error, jangan buat data palsu — kembalikan error message.
3. Untuk A2MCP, response harus JSON.

## Safety

- Jangan commit `.env`.
- Jangan expose `OKX_SECRET_KEY` atau `OKX_PASSPHRASE` di log/chat.
- Wallet hot — jangan simpan banyak dana.
