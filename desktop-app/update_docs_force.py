import os
import re

html_path = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html"

with open(html_path, "r") as f:
    html = f.read()

# Try to find target via regex
regex_pattern = r'(\s*<div id="view-instructions".*?<!-- View: Extract Frames -->)'

new_instructions = """
          <div id="view-instructions" class="flex flex-col gap-8 w-full max-w-6xl mx-auto pb-16 animate-fade-in">
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
                    <!-- Feature: Smart Video Tagging -->
                    <div class="glass-card p-6 rounded-2xl border border-white/5 hover:border-indigo-500/30 transition-all duration-300 group">
                        <div class="w-10 h-10 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path></svg>
                        </div>
                        <h3 class="text-lg font-bold text-white mb-2">Smart Video Tagging</h3>
                        <p class="text-sm text-slate-400 leading-relaxed">
                            Automatically finds objects in your video (like cars and pedestrians) and identifies the road surface you're riding on (like smooth asphalt or gravel) without manual effort.
                        </p>
                    </div>

                    <!-- Feature: Visual Context -->
                    <div class="glass-card p-6 rounded-2xl border border-white/5 hover:border-purple-500/30 transition-all duration-300 group">
                        <div class="w-10 h-10 rounded-lg bg-purple-500/10 text-purple-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform border border-purple-500/20">
                            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path></svg>
                        </div>
                        <h3 class="text-lg font-bold text-white mb-2">Visual Context</h3>
                        <p class="text-sm text-slate-400 leading-relaxed">
                            Connects what the camera sees (like approaching potholes) with what the bike feels, helping the AI understand the complete environment naturally.
                        </p>
                    </div>

                    <!-- Feature: Vibration Analysis -->
                    <div class="glass-card p-6 rounded-2xl border border-white/5 hover:border-teal-500/30 transition-all duration-300 group">
                        <div class="w-10 h-10 rounded-lg bg-teal-500/10 text-teal-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform border border-teal-500/20">
                            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
                        </div>
                        <h3 class="text-lg font-bold text-white mb-2">Vibration Analysis</h3>
                        <p class="text-sm text-slate-400 leading-relaxed">
                            Listens to the bike's bumps and shakes using sensors. Includes built-in filters to cut out background noise and focus only on true road impacts.
                        </p>
                    </div>

                    <!-- Feature: Live Progress Tracking -->
                    <div class="glass-card p-6 rounded-2xl border border-white/5 hover:border-rose-500/30 transition-all duration-300 group">
                        <div class="w-10 h-10 rounded-lg bg-rose-500/10 text-rose-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform border border-rose-500/20">
                            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg>
                        </div>
                        <h3 class="text-lg font-bold text-white mb-2">Live Progress Tracking</h3>
                        <p class="text-sm text-slate-400 leading-relaxed">
                            Watch your AI get smarter in real-time. As the system learns, it draws beautiful, interactive charts to show you its progress and accuracy.
                        </p>
                    </div>

                    <!-- Feature: 3D Bike Simulation -->
                    <div class="glass-card p-6 rounded-2xl border border-white/5 hover:border-purple-500/30 transition-all duration-300 group">
                        <div class="w-10 h-10 rounded-lg bg-purple-500/20 text-purple-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"></path></svg>
                        </div>
                        <h3 class="text-lg font-bold text-white mb-2">3D Bike Simulation</h3>
                        <p class="text-sm text-slate-400 leading-relaxed">
                            See exactly what your bike felt with an interactive 3D model. Watch it tilt, turn, and bounce based on your actual recorded ride data.
                        </p>
                    </div>

                    <!-- Feature: Clear Error Checking -->
                    <div class="glass-card p-6 rounded-2xl border border-white/5 hover:border-emerald-500/30 transition-all duration-300 group">
                        <div class="w-10 h-10 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002-2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
                        </div>
                        <h3 class="text-lg font-bold text-white mb-2">Clear Error Checking</h3>
                        <p class="text-sm text-slate-400 leading-relaxed">
                            Easily spot where the AI got confused or where data went missing. Visual tools help you quickly find and fix issues in your dataset.
                        </p>
                    </div>
                </div>
            </div>
            </div>

            <!-- Legacy Pipeline Steps -->
            <div class="glass-card rounded-2xl p-8 border border-white/10 mt-4 bg-slate-900/30">
              <h2 class="text-xl font-bold border-b border-white/10 pb-3 mb-6 text-white text-sm tracking-widest uppercase">Legacy Training Pipeline Roadmap</h2>
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

match = re.search(regex_pattern, html, flags=re.DOTALL)
if match:
    # Replace the captured group
    html = html.replace(match.group(1), new_instructions)
    with open(html_path, "w") as f:
        f.write(html)
    print("SUCCESS: HTML updated.")
else:
    print("FAILED: Could not find block.")
