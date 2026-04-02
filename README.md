# CycleSafe Studio

A desktop application for multimodal sensor fusion and bicycle video labeling, built with Electron.

## Installation Guide

### Prerequisites
Before you begin, ensure you have the following installed on your system:
- [Node.js](https://nodejs.org/) (which includes `npm`)
- Python 3.9+ (if you are running the ML pipeline components)

### Mac Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/abdullah-binmadhi/Bicycle_video_labeling.git
   cd Bicycle_video_labeling/desktop-app
   ```

2. Install the necessary dependencies:
   ```bash
   npm install
   ```

3. To run the app in development mode:
   ```bash
   npm run start
   ```

4. To build the application for macOS (Apple Silicon):
   ```bash
   npm run build
   ```
   *Note: This will generate a `CycleSafe Studio.app` file in your `desktop-app` directory. You can move this to your `/Applications` folder.*

---

### Windows Installation

1. Clone the repository:
   ```cmd
   git clone https://github.com/abdullah-binmadhi/Bicycle_video_labeling.git
   cd Bicycle_video_labeling\desktop-app
   ```

2. Install the necessary dependencies:
   ```cmd
   npm install
   ```

3. To run the app in development mode:
   ```cmd
   npm run start
   ```

4. To package the application for Windows (requires electron-packager):
   First, build the CSS:
   ```cmd
   npm run build:css
   ```
   Then package the app for your architecture (e.g., x64):
   ```cmd
   npx electron-packager . "CycleSafe Studio" --platform=win32 --arch=x64 --out=./build --overwrite
   ```
   *Note: This will create an executable (`.exe`) inside the newly created `build` folder.*