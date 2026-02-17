#!/bin/bash

# Default values
LOG_LEVEL="INFO"
COMPOSE_FILE="podman-compose.yml"

# Help message
usage() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -l, --level LEVEL   Set log level (DEBUG, INFO, WARNING, ERROR). Default: INFO"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 --level DEBUG"
    exit 1
}

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -l|--level) LOG_LEVEL="$2"; shift ;;
        -h|--help) usage ;;
        *) echo "Unknown parameter passed: $1"; usage ;;
    esac
    shift
done

echo "🚀 Starting Hermes with LOG_LEVEL=${LOG_LEVEL}..."

# Export for docker-compose to pick up (if supported in .env or compose file interpolation)
export LOG_LEVEL=${LOG_LEVEL}

# Rebuild and start containers
# We use --build to ensure code changes in hermes-data are picked up
echo "🔨 Building and starting services..."
docker-compose -f "${COMPOSE_FILE}" up -d --build

# Check if startup was successful
if [ $? -ne 0 ]; then
    echo "❌ Failed to start services."
    exit 1
fi

echo "✅ Services started!"
echo "📜 Tailing live logs (Ctrl+C to stop following logs, services will keep running)..."
echo "--------------------------------------------------------------------------------"

# Follow logs
docker-compose -f "${COMPOSE_FILE}" logs -f
