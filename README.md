# CycleSafe Studio

A desktop application for multimodal sensor fusion and bicycle video labeling, built with Electron.

## Installation & Setup Guide

Follow these steps to install and run the app on any new device. 

### Phase 1: System Prerequisites (Manual Steps)
Before downloading the app, you **must** install these foundational programs on your computer. *(Note: If you are using an AI IDE agent, it cannot do this part for you—you have to download these manually).*

1. **Install Node.js:** Download and install from the [Node.js Official Website](https://nodejs.org/). This includes `npm`, which is required to run the desktop app.
2. **Install Python:** Download and install Python 3.9 or newer from the [Python Official Website](https://www.python.org/downloads/). 
   * **Important for Windows:** Ensure you check the box that says "Add Python to PATH" during the installation process.

---

### Phase 2: App Setup & Dependencies
Once Node.js and Python are installed, you (or your AI agent) can run the following terminal commands to set up the project.

#### 1. Clone the Repository
Download the project to your computer:
```bash
git clone https://github.com/abdullah-binmadhi/Bicycle_video_labeling.git
```

#### 2. Install Machine Learning Dependencies
```bash
pip install transformers torch torchvision opencv-python Pillow pandas
```

#### 3. Install App Dependencies
Navigate into the desktop app folder and install the required Node modules:
```bash
cd Bicycle_video_labeling/desktop-app
npm install
```

---

### Phase 3: Running & Building the App

#### Running in Development Mode
To launch the app for testing or development (works on both Mac and Windows):
```bash
npm run start
```

#### Building for Mac (Apple Silicon)
To package the app into an application file:
```bash
npm run build
```
*Note: This will generate a `CycleSafe Studio.app` file in your `desktop-app` directory. You can drag and drop this directly into your Mac's `/Applications` folder.*

#### Building for Windows
To package the app into a `.exe` executable file:

1. First, build the CSS:
   ```cmd
   npm run build:css
   ```
2. Then package the application (example for x64 architecture):
   ```cmd
   npx electron-packager . "CycleSafe Studio" --platform=win32 --arch=x64 --out=./build --overwrite
   ```
*Note: This will create an executable (`.exe`) inside a newly created `build` folder.*
