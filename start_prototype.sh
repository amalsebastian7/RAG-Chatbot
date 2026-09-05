#!/bin/bash

# ==============================================================================
# Enterprise Local RAG Chatbot - Prototype Launch Script
# ==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_VENV="$PROJECT_ROOT/python-ai-engine/venv/bin"
LOG_DIR="$PROJECT_ROOT/.logs"

mkdir -p "$LOG_DIR"

echo "=========================================================="
echo "🛡️ Starting Enterprise Local RAG Chatbot Prototype"
echo "=========================================================="

# 1. Check Ollama
echo "[1/4] Checking local Ollama service..."
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "⚠️ Ollama is not running on port 11434. Starting ollama..."
    ollama serve > "$LOG_DIR/ollama.log" 2>&1 &
    sleep 3
fi
echo "✓ Ollama is online."

# 2. Start Python FastAPI AI Engine
echo "[2/4] Starting Python FastAPI AI Engine on port 8000..."
cd "$PROJECT_ROOT/python-ai-engine"
"$PYTHON_VENV/uvicorn" main:app --host 0.0.0.0 --port 8000 > "$LOG_DIR/python-fastapi.log" 2>&1 &
PYTHON_PID=$!
echo "$PYTHON_PID" > "$LOG_DIR/python.pid"
sleep 3

if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "✓ Python FastAPI is online (PID $PYTHON_PID)."
else
    echo "⚠️ Python FastAPI starting up... logs: $LOG_DIR/python-fastapi.log"
fi

# 3. Start Java Spring Boot Orchestrator
echo "[3/4] Starting Java Spring Boot Orchestrator on port 8080..."
cd "$PROJECT_ROOT/java-orchestrator"
./mvnw spring-boot:run > "$LOG_DIR/java-orchestrator.log" 2>&1 &
JAVA_PID=$!
echo "$JAVA_PID" > "$LOG_DIR/java.pid"

# 4. Start Streamlit Front-End
echo "[4/4] Starting Streamlit Chat UI on port 8501..."
cd "$PROJECT_ROOT/python-ai-engine"
"$PYTHON_VENV/streamlit" run app_ui.py --server.port 8501 --server.headless true > "$LOG_DIR/streamlit.log" 2>&1 &
STREAMLIT_PID=$!
echo "$STREAMLIT_PID" > "$LOG_DIR/streamlit.pid"

echo "=========================================================="
echo "🎉 Prototype Services Launched Successfully!"
echo ""
echo "  💬 Streamlit Chat UI:      http://localhost:8501"
echo "  🐍 Python FastAPI Docs:    http://localhost:8000/docs"
echo "  ☕ Java Spring Boot:       http://localhost:8080/api/scan/status"
echo ""
echo "  Credentials (US-01):"
echo "    - Username: admin   | Password: sopsecure2026"
echo "    - Username: analyst | Password: enterprise2026"
echo ""
echo "  To stop all services: ./stop_prototype.sh"
echo "=========================================================="
