#!/usr/bin/env bash
# Start development environment (Linux / macOS)
set -euo pipefail
ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT_DIR"

# 1) Python environment
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 2) Start Electron app (UI) in development
cd desktop-app
npm install
npm run start
