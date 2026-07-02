#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true
export $(grep -v '^#' .env | xargs)

BASE="http://localhost:8000"

echo "==> health"
curl -s "$BASE/health" | python3 -m json.tool

echo "==> launch-dd"
curl -s -X POST "$BASE/a2mcp/launch-dd" \
  -H "Content-Type: application/json" \
  -d '{"chain":"base","address":"0x940181a94a35a4569e4529a3cdfb74e38fd98631"}' | python3 -m json.tool | head -40

echo "==> xlayer-smart-money"
curl -s -X POST "$BASE/a2mcp/xlayer-smart-money" \
  -H "Content-Type: application/json" \
  -d '{"time_frame":"7D","limit":3}' | python3 -m json.tool | head -40

echo "==> wallet-cleanup"
curl -s -X POST "$BASE/a2mcp/wallet-cleanup" \
  -H "Content-Type: application/json" \
  -d '{"chain":"base","address":"0x38Baf554CbD3df737F49545170BeCE990D6233Ed"}' | python3 -m json.tool | head -40

echo "==> wallet-pnl"
curl -s -X POST "$BASE/a2mcp/wallet-pnl" \
  -H "Content-Type: application/json" \
  -d '{"chain":"base","addresses":"0x38Baf554CbD3df737F49545170BeCE990D6233Ed"}' | python3 -m json.tool | head -40

echo "==> whale-alert"
curl -s -X POST "$BASE/a2mcp/whale-alert" \
  -H "Content-Type: application/json" \
  -d '{"chain":"base","min_volume":5000}' | python3 -m json.tool | head -40

echo "==> bridge-route"
curl -s -X POST "$BASE/a2mcp/bridge-route" \
  -H "Content-Type: application/json" \
  -d '{"from":"USDC","from_chain":"base","to":"USDC","to_chain":"arbitrum","amount":"10"}' | python3 -m json.tool | head -40

echo "==> news-alpha"
curl -s -X POST "$BASE/a2mcp/news-alpha" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTC"}' | python3 -m json.tool | head -40

echo "==> meme-pump"
curl -s -X POST "$BASE/a2mcp/meme-pump" \
  -H "Content-Type: application/json" \
  -d '{"chain":"base"}' | python3 -m json.tool | head -40
