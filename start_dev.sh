#!/bin/bash

# Hermes Quick Start Script
# Runs Backend (8000) and Frontend (5173/5175) in parallel.

echo "🚀 Starting Hermes Engine..."

# Function to kill background processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    kill $(jobs -p) 2>/dev/null
    exit
}

# Trap SIGINT (Ctrl+C)
trap cleanup SIGINT

# 1. Start Backend
echo "📈 Starting Backend (Port 8000)..."
if [ -d "hermes-backend/venv" ]; then
    source hermes-backend/venv/bin/activate
    uvicorn hermes-backend.main:app --port 8000 --reload &
    BACKEND_PID=$!
else
    echo "❌ Error: Backend venv not found. Run 'python3 -m venv hermes-backend/venv' first."
    exit 1
fi

# 2. Start Frontend
echo "✨ Starting Frontend..."
cd hermes-frontend
npm run dev -- --clearScreen false &
FRONTEND_PID=$!

# Wait for both
wait $BACKEND_PID $FRONTEND_PID
