#!/bin/bash

BASE_DIR="/home/ai/ai-stack/agents/agent5_security"

APP_PID_FILE="$BASE_DIR/logs/app.pid"
UI_PID_FILE="$BASE_DIR/logs/ui.pid"

echo "🛑 Zatrzymuję Agent 5..."

# --- STOP APP ---
if [ -f "$APP_PID_FILE" ]; then
    APP_PID=$(cat "$APP_PID_FILE")
    echo "⏹️ Zatrzymuję app.py (PID $APP_PID)..."
    kill $APP_PID && rm "$APP_PID_FILE"
else
    echo "⚠️ app.py nie działa (brak PID)"
fi

# --- STOP UI ---
if [ -f "$UI_PID_FILE" ]; then
    UI_PID=$(cat "$UI_PID_FILE")
    echo "⏹️ Zatrzymuję ui.py (PID $UI_PID)..."
    kill $UI_PID && rm "$UI_PID_FILE"
else
    echo "⚠️ ui.py nie działa (brak PID)"
fi

echo "✅ Agent 5 zatrzymany."

