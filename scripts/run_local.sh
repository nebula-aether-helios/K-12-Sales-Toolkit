#!/usr/bin/env bash
set -euo pipefail

echo "Building and starting local stack with docker-compose..."
docker compose up --build
