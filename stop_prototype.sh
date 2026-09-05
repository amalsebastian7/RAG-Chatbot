#!/bin/bash

# ==============================================================================
# Enterprise Local RAG Chatbot - Prototype Stop Script
# ==============================================================================

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$PROJECT_ROOT/.logs"

echo "Stopping prototype services..."

if [ -f "$LOG_DIR/streamlit.pid" ]; then
    kill $(cat "$LOG_DIR/streamlit.pid") 2>/dev/null || true
    rm -f "$LOG_DIR/streamlit.pid"
fi

if [ -f "$LOG_DIR/python.pid" ]; then
    kill $(cat "$LOG_DIR/python.pid") 2>/dev/null || true
    rm -f "$LOG_DIR/python.pid"
fi

if [ -f "$LOG_DIR/java.pid" ]; then
    kill $(cat "$LOG_DIR/java.pid") 2>/dev/null || true
    rm -f "$LOG_DIR/java.pid"
fi

# Fallback cleanup for ports 8000, 8080, 8501
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:8080 | xargs kill -9 2>/dev/null || true
lsof -ti:8501 | xargs kill -9 2>/dev/null || true

echo "✓ All prototype services stopped."
