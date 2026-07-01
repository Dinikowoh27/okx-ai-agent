#!/bin/bash
set -euo pipefail
cd /home/ubuntu/okx-ai-agent
export PATH="/home/ubuntu/.local/bin:$PATH"
if [ -f .env.poller ]; then
  export $(grep -v '^#' .env.poller | xargs)
fi
exec python3 scripts/okx-task-poller.py
