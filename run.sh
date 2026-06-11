#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="beat-it"
CONTAINER_NAME="beat-it"

# Build the image
echo "Building image..."
podman build -t "$IMAGE_NAME" .

# Stop any existing container with the same name
podman rm -f "$CONTAINER_NAME" 2>/dev/null || true

# Run the container, passing through all env vars from a .env file if present
ENV_FILE_ARG=""
if [ -f .env ]; then
  ENV_FILE_ARG="--env-file .env"
fi

echo "Starting container..."
podman run --rm -d \
  --name "$CONTAINER_NAME" \
  $ENV_FILE_ARG \
  -p "${PORT:-8080}:${PORT:-8080}" \
  "$IMAGE_NAME"

echo "Container running: $CONTAINER_NAME"
echo "Healthcheck: http://localhost:${PORT:-8080}/healthcheck"
