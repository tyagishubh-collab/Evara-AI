#!/usr/bin/env bash
set -e

echo "🚀 Starting FastAPI server with Cloudflare Tunnel..."

# Activate Python virtual environment
source venv/bin/activate

# Kill any previous FastAPI process on port 8000
kill -9 $(lsof -t -i:8000) 2>/dev/null || true

# Start FastAPI in background
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!

# Give uvicorn a few seconds to start
sleep 3

# Start Cloudflare Tunnel (new syntax, WebSocket-compatible)
cloudflared tunnel run --url http://localhost:8000 || cloudflared tunnel --url http://localhost:8000

# Stop FastAPI when Cloudflare tunnel stops
kill $UVICORN_PID 2>/dev/null || true
