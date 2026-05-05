# CycleSafe Studio

CycleSafe Studio is a desktop application for multimodal sensor fusion and bicycle video labeling (Electron frontend + Python ML pipeline).

**This README focuses on reproducible installation and packaging so the app can be installed on another device.**

---

**Requirements summary**
- Node.js (v18+ recommended) and `npm` or `pnpm`
- Python 3.9+ with a virtual environment
- Xcode command line tools on macOS (for building native wheels if needed)

Files added to help reproducible installs:
- `requirements.txt` — Python packages used by the ML pipeline.

---

## Quick setup (macOS / Linux)

1. Clone the repo:

```bash
git clone https://github.com/abdullah-binmadhi/Bicycle_video_labeling.git
cd "Bicycle Video ML Model"
```

2. Create and activate a Python virtual environment, then install Python deps:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

3. Install Node dependencies and build the Electron app UI:

```bash
cd desktop-app
npm install
# Development run
npm run start

# To build the production macOS app (Apple Silicon):
npm run build
# The build script packages the app and places "CycleSafe Studio.app" in the desktop-app directory
```

4. Copy the application bundle to Applications (macOS):

```bash
mv "CycleSafe Studio.app" /Applications/ || sudo mv "CycleSafe Studio.app" /Applications/
```

---

## Quick setup (Windows)

1. Clone the repo and open a PowerShell terminal in the repository root.

2. Create and activate a Python virtual environment and install Python packages:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

3. From `desktop-app` install Node dependencies and package the app (example for x64):

```powershell
cd desktop-app
npm install
npm run build:css
npx electron-packager . "CycleSafe Studio" --platform=win32 --arch=x64 --out=./build --overwrite
```

---

## Notes & best practices to avoid installation problems on other devices

- Use a Python virtual environment for each machine to avoid dependency conflicts.
- Prefer `pip install -r requirements.txt` rather than ad-hoc installs; `requirements.txt` contains the core ML deps used by the project.
- If `torch` wheels fail to install via `pip` on a target machine, follow the official PyTorch install instructions for the target platform (CUDA vs CPU, macOS/ARM wheels).
- For macOS Apple Silicon (M1/M2), install Python via Homebrew or an Apple Silicon installer, and use the `arch`-appropriate wheels for `torch` if required.
- If you encounter macOS Gatekeeper (unsigned app) warnings after copying the `.app`, right-click the app and choose Open and then Approve; or sign & notarize the app for distribution.

### Packaging & Distribution

- The `desktop-app/package.json` includes a `build` script that runs `tailwindcss` and `electron-packager`. This should produce `CycleSafe Studio.app` for macOS when run on a matching host architecture. If you want cross-platform builds from one host, consider using CI (GitHub Actions) that runs per-target builds (macOS runner for macOS .app, Windows runner for .exe).
- For production distribution on macOS consider signing and notarizing the `.app`. For Windows consider code-signing to avoid SmartScreen warnings.

### Verifications I performed

- Confirmed `desktop-app/main.js` is the Electron entrypoint and `desktop-app/package.json` exists.
- Added `requirements.txt` with the main Python packages used by the ML scripts.

---

## Troubleshooting

- If the app fails to start in dev: check the dev console (the app opens DevTools by default).
- If Python ML scripts fail due to missing packages, activate `./.venv` and run `pip install -r requirements.txt`.
- If `electron-packager` is missing, install its dev dependency or run: `npm i -D electron-packager`.

---

If you want, I can:
- add a small `scripts/start-dev.sh` and `scripts/build-macos.sh` to automate these steps,
- create a `setup.md` with platform-specific wheel links for `torch`, or
- add a GitHub Actions workflow to produce release artifacts for macOS and Windows.

Tell me which of these you'd like next.