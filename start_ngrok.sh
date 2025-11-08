#!/usr/bin/env bash
set -e

echo "🚀 Starting FastAPI server (with venv)..."

# ✅ Activate your virtual environment
source venv/bin/activate

# ✅ Kill anything on port 8000 just in case
kill -9 $(lsof -t -i:8000) 2>/dev/null || true

# ✅ Start FastAPI
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!

sleep 3

echo "🌐 Starting ngrok HTTPS tunnel (WebSocket supported, free plan)..."
ngrok http 8000 \
  --request-header-add="Connection: Upgrade" \
  --request-header-add="Upgrade: websocket" \
  --response-header-add="Access-Control-Allow-Origin: *"

# ✅ Stop uvicorn when ngrok closes
kill $UVICORN_PID 2>/dev/null || true
