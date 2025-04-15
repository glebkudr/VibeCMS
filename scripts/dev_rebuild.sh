#!/bin/bash
# Bash script to automate frontend build/dev and docker-compose restart
set -e

FRONTEND_DIR="admin_app/frontend"
PROJECT_ROOT="$(pwd)"

cd "$FRONTEND_DIR"

echo "[INFO] Killing old 'npm run dev' or 'vite' processes..."
pkill -f "npm run dev" || true
pkill -f "vite" || true

echo "[INFO] Building frontend..."
npm run build

echo "[INFO] Starting 'npm run dev' in background..."
nohup npm run dev > dev.log 2>&1 &

cd "$PROJECT_ROOT"

echo "[INFO] Running docker-compose..."
docker-compose --env-file .env.dev up --build -d

echo "[SUCCESS] All done!" 