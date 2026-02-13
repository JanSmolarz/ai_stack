#!/bin/bash

BASE_DIR="/home/ai/ai-stack/agents/agent5_security"
VENV_PY="/home/ai/ai-stack/venv/bin/python"

APP_PID_FILE="$BASE_DIR/logs/app.pid"
UI_PID_FILE="$BASE_DIR/logs/ui.pid"

echo "🚀 Uruchamiam Agent 5..."

cd "$BASE_DIR" || exit 1

# --- START APP.PY ---
echo "▶️ Startuję app.py (FastAPI)..."
nohup $VENV_PY app.py > logs/app.log 2>&1 &
echo $! > "$APP_PID_FILE"

sleep 2

# --- START UI.PY ---
echo "▶️ Startuję ui.py (Streamlit)..."
nohup /home/ai/ai-stack/venv/bin/streamlit run ui.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    > logs/ui.log 2>&1 &
echo $! > "$UI_PID_FILE"

echo "✅ Agent 5 uruchomiony!"
echo "🔹 API: http://localhost:8015/docs"
echo "🔹 UI : http://localhost:8501"

