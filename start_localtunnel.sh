#!/usr/bin/env bash
set -e

# Start uvicorn server in background
echo "Starting FastAPI (uvicorn) on :8000 ..."
uvicorn app:app --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!

# Ensure npx/localtunnel is available
if ! command -v npx >/dev/null 2>&1; then
  echo "npx not found. Please install Node.js and npm. Then run: npm install -g localtunnel"
  wait $UVICORN_PID
  exit 1
fi

echo "Starting localtunnel on :8000 ... (Ctrl+C to stop)"
npx localtunnel --port 8000
kill $UVICORN_PID 2>/dev/null || true
