#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true
export $(grep -v '^#' .env | xargs)

BASE="http://localhost:8000"

echo "==> health"
curl -s "$BASE/health" | python3 -m json.tool

echo "==> smart-money (base, limit 3)"
curl -s -X POST "$BASE/a2mcp/smart-money" \
  -H "Content-Type: application/json" \
  -d '{"chain":"base","limit":3}' | python3 -m json.tool | head -80

echo "==> security-scan (sample token)"
curl -s -X POST "$BASE/a2mcp/security-scan" \
  -H "Content-Type: application/json" \
  -d '{"chain":"base","address":"0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"}' | python3 -m json.tool | head -80

echo "==> social-brief (BTC)"
curl -s -X POST "$BASE/a2mcp/social-brief" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTC"}' | python3 -m json.tool | head -80
