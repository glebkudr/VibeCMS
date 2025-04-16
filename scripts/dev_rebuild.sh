#!/bin/bash
# Dev-mode launcher: frontend watcher + backend (docker-compose with env.dev)
set -e

FRONTEND_DIR="admin_app/frontend"
PROJECT_ROOT="$(pwd)"

cd "$FRONTEND_DIR"

echo "[INFO] Starting Vite build watcher (npm run watch)..."
npm install
npm run watch &

cd "$PROJECT_ROOT"

echo "[INFO] Running docker-compose with .env.dev..."
docker-compose --env-file .env.dev up

echo "[SUCCESS] Dev environment is running!" 