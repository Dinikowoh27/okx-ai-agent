---
name: okx-ai-service
description: "Hermes skill wrapper for the OKX.AI A2MCP service server. Routes inbound A2MCP requests (token report, wallet analysis, smart money, security scan, social brief) to the correct onchainos CLI command via the local FastAPI server. Also handles ASP registration prep and service catalog updates."
license: MIT
metadata:
  author: eida
  version: "0.1.0"
---

# OKX.AI Service Handler

Internal skill untuk menjalankan layanan Eida di OKX.AI marketplace.

## When to use

- Menerima request A2MCP dari OKX.AI user.
- Menjalankan onchainos CLI skill sesuai service yang dipanggil.
- Menyiapkan/register ASP identity dan service catalog.

## Local server

FastAPI server berjalan di `okx-ai-agent/server.py`.

```bash
cd /home/ubuntu/okx-ai-agent
source .venv/bin/activate
python server.py
```

## Endpoints

| Path | Service | onchainos command |
|---|---|---|
| `POST /a2mcp/token-report` | Token Intel Report | `token report --address <addr> --chain <chain>` |
| `POST /a2mcp/wallet-analysis` | Wallet Analysis | `workflow wallet-analysis --address <addr>` |
| `POST /a2mcp/smart-money` | Smart Money Signals | `signal list --chain <chain> --limit <n>` |
| `POST /a2mcp/security-scan` | Security Scan | `security token-scan --tokens <chain>:<addr>` |
| `POST /a2mcp/social-brief` | Crypto News Brief | `social news-by-symbol --token-symbols <sym>` |

## Register ASP identity

1. Isi `services.json` dengan nama, deskripsi, avatar, dan daftar service.
2. Ganti endpoint URL di `services.json` ke public HTTPS yang sebenarnya.
3. Pastikan file avatar ada di `assets/avatar.png`.
4. Jalankan:

```bash
cd /home/ubuntu/okx-ai-agent
source .venv/bin/activate
python scripts/register-asp.py
```

Script akan upload avatar, validate listing, lalu `onchainos agent create`.

## Service design rules

- Service name: 5–30 karakter, noun phrase, tidak sama dengan agent name.
- Description: 2 bagian — (1) apa yang dilakukan, (2) apa yang user harus sediakan.
- Type: `A2MCP` untuk pay-per-call API, `A2A` untuk custom task.
- Fee: angka murni dalam USDT, maksimal 6 desimal.
- Endpoint: harus `https://`, publicly reachable, ≤512 karakter.

## Quality gate

Sebelum mengirim hasil ke user:
1. Verifikasi CLI output punya field `ok: true`.
2. Kalau error, jangan buat data palsu — kembalikan error message.
3. Untuk A2MCP, response harus JSON.

## Safety

- Jangan commit `.env`.
- Jangan expose `OKX_SECRET_KEY` atau `OKX_PASSPHRASE` di log/chat.
- Wallet hot — jangan simpan banyak dana.
