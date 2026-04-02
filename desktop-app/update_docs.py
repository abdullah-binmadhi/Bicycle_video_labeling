import os

html_path = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html"

with open(html_path, "r") as f:
    html = f.read()

# Locate the exact block we want to replace
start_marker = '<div id="view-instructions"'
end_marker = '          <!-- View: Extract Frames -->'

# Extract the part to replace
start_idx = html.find(start_marker)
end_idx = html.find(end_marker)

if start_idx != -1 and end_idx != -1:
    old_block = html[start_idx:end_idx]
    
    new_instructions = """<div id="view-instructions" class="flex flex-col gap-8 w-full max-w-6xl mx-auto pb-16 animate-fade-in">
            <!-- Hero Header -->
            <div class="mb-4 relative rounded-3xl p-8 overflow-hidden bg-gradient-to-br from-slate-900 to-black border border-white/5 shadow-2xl">
              <div class="absolute -right-20 -top-20 w-64 h-64 bg-emerald-500/10 blur-3xl rounded-full"></div>
              <div class="absolute -left-20 -bottom-20 w-64 h-64 bg-purple-500/10 blur-3xl rounded-full"></div>
              <div class="relative z-10">
                <h1 class="text-4xl lg:text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-purple-400 tracking-tight drop-shadow-md mb-2">CycleSafe Studio</h1>
                <p class="text-lg text-slate-300 max-w-3xl leading-relaxed">
                  Your professional workbench for Multi-Dimensional Sensor Fusion. Transform raw telemetry streams and video into deployment-ready PyTorch neural networks.
                </p>
                <div class="flex gap-3 mt-6">
                    <span class="badge bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 py-3 px-4 font-mono font-bold tracking-widest text-xs">v2.0.0 ENGINE UPDATE</span>
                    <span class="badge bg-purple-500/20 text-purple-400 border border-purple-500/30 py-3 px-4 font-mono font-bold tracking-widest text-xs">LIVE TELEMETRY</span>
                </div>
              </div>
            </div>

            <!-- Features Grid -->
            <div>
                <h2 class="text-2xl font-bold border-b border-white/10 pb-3 mb-6 text-white tracking-widest uppercase text-sm">Next-Generation Capabilities</h2>
                
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <!-- Feature: GPS Velocity Fusion -->
                    <div class="glass-card p-6 rounded-2xl border border-white/5 hover:border-blue-500/30 transition-all duration-300 group">
                        <div class="w-10 h-10 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                        </div>
                        <h3 class="text-lg font-bold text-white mb-2">GPS Velocity Fusion</h3>
                        <p class="text-sm text-slate-400 leading-relaxed">
                            Mitigates static oscillation errors by mapping real-time speed over IMU coordinates. Ensures the system easily distinguishes driving fast on dirt from driving slowly on cobblestone.
                        </p>
                    </div>

                    <!-- Feature: OOD Anomaly Gate -->
                    <div class="glass-card p-6 rounded-2xl border border-white/5 hover:border-orange-500/30 transition-all duration-300 group">
                        <div class="w-10 h-10 rounded-lg bg-orange-500/20 text-orange-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
                        </div>
                        <h3 class="text-lg font-bold text-white mb-2">Anomaly Gate (OOD)</h3>
                        <p class="text-sm text-slate-400 leading-relaxed">
                            Actively drops frames lacking rotational biking kinematics. If a rider steps off the bike and walks, the Out-of-Distribution safety net immediately isolates the signal logic to prevent false positives.
                        </p>
                    </div>

                    <!-- Feature: Active Learning Routing -->
                    <div class="glass-card p-6 rounded-2xl border border-white/5 hover:border-rose-500/30 transition-all duration-300 group">
                        <div class="w-10 h-10 rounded-lg bg-rose-500/20 text-rose-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/></svg>
                        </div>
                        <h3 class="text-lg font-bold text-white mb-2">Active Learning Routing</h3>
                        <p class="text-sm text-slate-400 leading-relaxed">
                            Accelerate model refinement. Discover false predictions during inference and click a button to immediately package the 50Hz physics array & camera frame back into your Roboflow staging queue.
                        </p>
                    </div>

                    <!-- Feature: 3D Tracking -->
                    <div class="glass-card p-6 rounded-2xl border border-white/5 hover:border-purple-500/30 transition-all duration-300 group">
                        <div class="w-10 h-10 rounded-lg bg-purple-500/20 text-purple-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/></svg>
                        </div>
                        <h3 class="text-lg font-bold text-white mb-2">WebGL Digital Twin</h3>
                        <p class="text-sm text-slate-400 leading-relaxed">
                            Watch the actual structural vibrations map into a 3D simulation powered by Three.js. Visually diagnose pitch, yaw, and rapid Z-axis jolts during playback.
                        </p>
                    </div>

                    <!-- Feature: Diagnostics -->
                    <div class="glass-card p-6 rounded-2xl border border-white/5 hover:border-emerald-500/30 transition-all duration-300 group">
                        <div class="w-10 h-10 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
                        </div>
                        <h3 class="text-lg font-bold text-white mb-2">Diagnostic Analytics</h3>
                        <p class="text-sm text-slate-400 leading-relaxed">
                            Interactive cross-session Matrix and drift diagnostics directly within the UI, built with Chart.js. Generate rigorous, one-click PDF validation reports of the model's accuracy.
                        </p>
                    </div>

                    <!-- Feature: Sync Scrubber -->
                    <div class="glass-card p-6 rounded-2xl border border-white/5 hover:border-indigo-500/30 transition-all duration-300 group">
                        <div class="w-10 h-10 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"/></svg>
                        </div>
                        <h3 class="text-lg font-bold text-white mb-2">Video/Sensor Scrubber</h3>
                        <p class="text-sm text-slate-400 leading-relaxed">
                            Scrub back and forth through hours of video utilizing a tightly coupled time domain synchronization engine—instantly updating Maps, FFT Spectrograms, and 3D scenes.
                        </p>
                    </div>
                </div>
            </div>

            <!-- Legacy Pipeline Steps -->
            <div class="glass-card rounded-2xl p-8 border border-white/10 mt-4 bg-slate-900/30">
              <h2 class="text-xl font-bold border-b border-white/10 pb-3 mb-6 text-white">Legacy Training Pipeline Roadmap</h2>
              <ul class="steps steps-vertical w-full text-slate-300">
                <li class="step step-primary">
                  <div class="text-left w-full pl-6 py-3">
                    <h4 class="font-bold text-lg text-white">1. Frame Extraction</h4>
                    <p class="text-sm text-slate-400 mt-1 max-w-3xl">Cameras record at 30Hz, while sensors record at 50Hz. Extract precise frames tied to UNIX timestamps.</p>
                  </div>
                </li>
                <li class="step step-info">
                  <div class="text-left w-full pl-6 py-3">
                    <h4 class="font-bold text-lg text-white">2. Ground Truth Parsing (CLIP/Roboflow)</h4>
                    <p class="text-sm text-slate-400 mt-1 max-w-3xl">Automated HuggingFace tagging or manual outlier resolution in the Hub.</p>
                  </div>
                </li>
                <li class="step step-accent">
                  <div class="text-left w-full pl-6 py-3">
                    <h4 class="font-bold text-lg text-white">3. High-Frequency Temporal Sync</h4>
                    <p class="text-sm text-slate-400 mt-1 max-w-3xl">Weave video ground truth against sliding windows of purely 1-D physics telemetry streams.</p>
                  </div>
                </li>
                <li class="step">
                  <div class="text-left w-full pl-6 py-3">
                    <h4 class="font-bold text-lg text-white">4. Core Physics Transformer Model</h4>
                    <p class="text-sm text-slate-400 mt-1 max-w-3xl">PyTorch training utilizing high-batch sizes and validation slicing to yield absolute road classifications.</p>
                  </div>
                </li>
              </ul>
            </div>
          </div>\n\n          <!-- View: Extract Frames -->"""
    
    html = html.replace(old_block, new_instructions)
    with open(html_path, "w") as f:
        f.write(html)
    print("UI Updated")
else:
    print("Failed to find block!")
