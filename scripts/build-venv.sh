#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# directories
WHEELDIR="$ROOT_DIR/wheelhouse"
BUILD_VENV="$ROOT_DIR/build-venv"
DEST_VENV="$ROOT_DIR/desktop-app/resources/venv"
DEST_APP_CODE="$ROOT_DIR/desktop-app/resources/app_code"

rm -rf "$WHEELDIR" "$BUILD_VENV" "$DEST_VENV" "$DEST_APP_CODE"
mkdir -p "$WHEELDIR"

echo "[build-venv] Building wheelhouse from requirements.txt"
python3 -m venv "$ROOT_DIR/.venv-builder"
source "$ROOT_DIR/.venv-builder/bin/activate"
pip install --upgrade pip wheel setuptools
pip wheel -w "$WHEELDIR" -r requirements.txt

echo "[build-venv] Creating runtime venv and installing from wheelhouse"
python3 -m venv "$BUILD_VENV"
source "$BUILD_VENV/bin/activate"
pip install --upgrade pip
pip install --no-index --find-links "$WHEELDIR" -r requirements.txt

echo "[build-venv] Copying built venv into desktop-app/resources/venv"
mkdir -p "$(dirname "$DEST_VENV")"
rsync -a --delete "$BUILD_VENV/" "$DEST_VENV/"

echo "[build-venv] Copying minimal Python app code into desktop-app/resources/app_code"
mkdir -p "$DEST_APP_CODE"
# Adjust the list of files/folders to include the Python server and required modules
rsync -a --delete run_inference.py models/ data_pipeline/ config/ weights/ "$DEST_APP_CODE/" || true

deactivate || true
rm -rf "$ROOT_DIR/.venv-builder"

echo "Vendored venv created at $DEST_VENV and app code at $DEST_APP_CODE"
