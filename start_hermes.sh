#!/bin/bash

# Default values
LOG_LEVEL="INFO"
MODE="container"
COMPOSE_FILE="podman-compose.yml"

# Help message
usage() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -m, --mode MODE     Run mode: 'container' (default) or 'local'"
    echo "  -l, --level LEVEL   Set log level (DEBUG, INFO, WARNING, ERROR). Default: INFO"
    echo "  -b, --build         Rebuild containers (container mode only)"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 --level DEBUG --mode local"
    exit 1
}

# Parse arguments
BUILD_FLAG=""
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -m|--mode) MODE="$2"; shift ;;
        -l|--level) LOG_LEVEL="$2"; shift ;;
        -b|--build) BUILD_FLAG="--build" ;;
        -h|--help) usage ;;
        *) echo "Unknown parameter passed: $1"; usage ;;
    esac
    shift
done

echo "🚀 Starting Hermes in ${MODE^^} mode with LOG_LEVEL=${LOG_LEVEL}..."

# Export LOG_LEVEL for both modes
export LOG_LEVEL=${LOG_LEVEL}

# Clean up function for local process mode
cleanup_local() {
    echo ""
    echo "🛑 Shutting down local processes..."
    # Kill background jobs spawned by this shell
    kill $(jobs -p) 2>/dev/null
    exit
}

if [ "$MODE" == "container" ]; then
    # --- CONTAINER MODE ---
    echo "🔨 Managing containers..."
    
    # Check if docker-compose is available
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Error: docker-compose not found. Please install Docker or Podman."
        exit 1
    fi

    # Start services
    docker-compose -f "${COMPOSE_FILE}" up -d ${BUILD_FLAG}

    # Check status
    if [ $? -ne 0 ]; then
        echo "❌ Failed to start containers."
        exit 1
    fi

    echo "✅ Containers started!"
    echo "📜 Tailing live logs (Ctrl+C to stop following logs, services will keep running)..."
    echo "--------------------------------------------------------------------------------"
    
    # Tail logs
    docker-compose -f "${COMPOSE_FILE}" logs -f

elif [ "$MODE" == "local" ]; then
    # --- LOCAL MODE ---
    
    # Trap SIGINT to kill processes
    trap cleanup_local SIGINT

    # 1. Start Backend
    echo "📈 Starting Backend (Port 8000)..."
    if [ -d "hermes-backend/venv" ]; then
        source hermes-backend/venv/bin/activate
        # Run uvicorn in background
        uvicorn hermes-backend.main:app --port 8000 --reload --log-level ${LOG_LEVEL,,} &
        BACKEND_PID=$!
    else
        echo "❌ Error: Backend venv not found at hermes-backend/venv."
        echo "   Please run: cd hermes-backend && python3 -m venv venv && pip install -r requirements.txt"
        exit 1
    fi

    # 2. Start Frontend
    echo "✨ Starting Frontend..."
    if [ -d "hermes-frontend" ]; then
        cd hermes-frontend
        # Run npm in background. Clear screen false to see logs mixed with backend.
        npm run dev -- --clearScreen false &
        FRONTEND_PID=$!
        cd ..
    else
        echo "❌ Error: hermes-frontend directory not found."
        exit 1
    fi

    echo "✅ Local services started!"
    echo "📜 Press Ctrl+C to stop all services."
    echo "--------------------------------------------------------------------------------"

    # Wait for both processes
    wait $BACKEND_PID $FRONTEND_PID

else
    echo "❌ Unknown mode: $MODE. Use 'container' or 'local'."
    exit 1
fi
