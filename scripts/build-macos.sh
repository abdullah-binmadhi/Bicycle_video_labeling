#!/usr/bin/env bash
# Build macOS production .app using the repo's npm build script
set -euo pipefail
ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT_DIR"

# Ensure Python deps installed (optional; only needed if build runs python tools)
if [ -f requirements.txt ]; then
  if [ ! -d ".venv" ]; then
    python3 -m venv .venv
  fi
  source .venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
fi

# Build the Electron app
cd desktop-app
npm ci
npm run build

# The build script should output "CycleSafe Studio.app" in desktop-app
if [ -d "CycleSafe Studio.app" ]; then
  echo "Build success: CycleSafe Studio.app created in desktop-app/"
  echo "You can zip it for distribution:"
  echo "  cd desktop-app && zip -r CycleSafe_Studio_macos.zip 'CycleSafe Studio.app'"
else
  echo "Build did not produce CycleSafe Studio.app — check the desktop-app build logs"
  exit 2
fi
