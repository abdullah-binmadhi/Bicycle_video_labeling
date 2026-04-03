import re

html_path = 'desktop-app/src/index.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

start_marker = '<h2 class="text-xl font-medium border-b border-[#333] pb-3 mb-6 text-white text-sm tracking-widest uppercase">Training Pipeline Roadmap</h2>'
end_marker = '<!-- View: SOTA Comparison -->'

start_idx = html.find(start_marker)
end_idx = html.find(end_marker)

if start_idx != -1 and end_idx != -1:
    old_block = html[start_idx:end_idx]
    
    new_block = """<h2 class="text-xl font-medium border-b border-[#333] pb-3 mb-6 text-white text-sm tracking-widest uppercase">Training Pipeline Roadmap</h2>
              <ul class="steps steps-vertical w-full text-[#888888]">
                <li class="step step-neutral">
                  <div class="text-left w-full pl-6 py-3">
                    <h4 class="font-medium text-lg text-white">1. Frame Extraction</h4>
                    <p class="text-sm text-[#888888] mt-1 max-w-3xl">Cameras record at 30Hz, while IMU sensors record down to 50Hz. Python extracts precise RGB frames strictly tied to hardware UNIX timestamps.</p>
                  </div>
                </li>
                <li class="step step-neutral">
                  <div class="text-left w-full pl-6 py-3">
                    <h4 class="font-medium text-lg text-white">2. Automated Annotation (YOLO + CLIP)</h4>
                    <p class="text-sm text-[#888888] mt-1 max-w-3xl">100% automated offline pipeline. YOLO-World generates spatial bounding boxes from a custom vocabulary, before PIPING crops directly to CLIP for zero-shot text description profiling.</p>
                  </div>
                </li>
                <li class="step step-neutral">
                  <div class="text-left w-full pl-6 py-3">
                    <h4 class="font-medium text-lg text-white">3. Manual Feature Refinement</h4>
                    <p class="text-sm text-[#888888] mt-1 max-w-3xl">Scrub through the video dataset and manually draw bounding boxes through the interactive Canvas UI for the rarest edge-cases or missed items.</p>
                  </div>
                </li>
                <li class="step step-neutral">
                  <div class="text-left w-full pl-6 py-3">
                    <h4 class="font-medium text-lg text-white">4. High-Frequency Synchronization</h4>
                    <p class="text-sm text-[#888888] mt-1 max-w-3xl">The backend matches disparate time-domains (33ms video vs 20ms physics) using Pandas <code>merge_asof</code>, applies SciPy Butterworth DSP filters, and drops anomalous gap data.</p>
                  </div>
                </li>
                <li class="step step-neutral">
                  <div class="text-left w-full pl-6 py-3">
                    <h4 class="font-medium text-lg text-white">5. Core PyTorch Network Training</h4>
                    <p class="text-sm text-[#888888] mt-1 max-w-3xl">Trains the LateFusionNetwork on processed datasets natively inside the application. Live JSON stdout telemetry feeds the real-time Dashboard Chart.js graphs.</p>
                  </div>
                </li>
                <li class="step">
                  <div class="text-left w-full pl-6 py-3">
                    <h4 class="font-medium text-lg text-white">6. Real-Time Inference</h4>
                    <p class="text-sm text-[#888888] mt-1 max-w-3xl">Simulate predictions seamlessly utilizing PyTorch evaluation modes over unseen synchronized sensor feeds.</p>
                  </div>
                </li>
              </ul>
            </div>

            <!-- Features Grid -->
            <div class="mt-8">
                <h2 class="text-2xl font-medium border-b border-[#333] pb-3 mb-6 text-white tracking-widest uppercase text-sm">Next-Generation Capabilities</h2>
                
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

                    <!-- Feature: Two Stage Auto -->
                    <div class="border border-[#222] bg-[#0c0c0c] p-6 rounded-none hover:border-indigo-500/30 transition-all duration-300 group">
                        <div class="w-10 h-10 rounded-none bg-indigo-500/20 text-indigo-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" /></svg>
                        </div>
                        <h3 class="text-lg font-medium text-white mb-2">Automated Annotation Engine</h3>
                        <p class="text-sm text-[#888888] leading-relaxed">
                            Two-stage foundational pipeline. YOLO-World scans the video for bounding boxes using any text, while CLIP analyzes the spatial crops to tag deep semantics like "smooth dry asphalt". 
                        </p>
                    </div>

                    <!-- Feature: Vision Embeddings -->
                    <div class="border border-[#222] bg-[#0c0c0c] p-6 rounded-none hover:border-purple-500/30 transition-all duration-300 group">
                        <div class="w-10 h-10 rounded-none bg-purple-500/10 text-purple-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform border border-purple-500/20">
                            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                        </div>
                        <h3 class="text-lg font-medium text-white mb-2">Vision Embeddings</h3>
                        <p class="text-sm text-[#888888] leading-relaxed">
                            Camera-based latent vectors that can be safely toggled inside the Neural Training dashboard. It encodes road surface obstacles directly into the overarching transformer payload.
                        </p>
                    </div>

                    <!-- Feature: IMU Physics Timeline -->
                    <div class="border border-[#222] bg-[#0c0c0c] p-6 rounded-none hover:border-teal-500/30 transition-all duration-300 group">
                        <div class="w-10 h-10 rounded-none bg-teal-500/10 text-teal-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform border border-teal-500/20">
                            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
                        </div>
                        <h3 class="text-lg font-medium text-white mb-2">IMU Physics Timeline</h3>
                        <p class="text-sm text-[#888888] leading-relaxed">
                            Interweaves 6-DoF Vibration Sequences (accelerometer and gyroscope). Includes interactive DSP Butterworth sliding parameters embedded natively inside the sync algorithms.
                        </p>
                    </div>

                    <!-- Feature: Live Matrix / Charting -->
                    <div class="border border-[#222] bg-[#0c0c0c] p-6 rounded-none hover:border-rose-500/30 transition-all duration-300 group">
                        <div class="w-10 h-10 rounded-none bg-rose-500/10 text-rose-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform border border-rose-500/20">
                            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>
                        </div>
                        <h3 class="text-lg font-medium text-white mb-2">Live Training Trajectories</h3>
                        <p class="text-sm text-[#888888] leading-relaxed">
                            As your PyTorch gradients burn network weights, validation telemetry (e.g. MSE Loss, Epoch metrics) pipes through IPC into Electron to draw real-time interactive mapping lines.
                        </p>
                    </div>

                    <!-- Feature: WebGL Digital Twin -->
                    <div class="border border-[#222] bg-[#0c0c0c] p-6 rounded-none hover:border-purple-500/30 transition-all duration-300 group">
                        <div class="w-10 h-10 rounded-none bg-purple-500/20 text-[#e0e0e0] flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/></svg>
                        </div>
                        <h3 class="text-lg font-medium text-white mb-2">WebGL Digital Twin</h3>
                        <p class="text-sm text-[#888888] leading-relaxed">
                            Watch the actual structural vibrations map into a 3D simulation powered by Three.js. Visually diagnose pitch, yaw, and rapid Z-axis jolts during playback.
                        </p>
                    </div>

                    <!-- Feature: Diagnostics -->
                    <div class="border border-[#222] bg-[#0c0c0c] p-6 rounded-none hover:border-emerald-500/30 transition-all duration-300 group">
                        <div class="w-10 h-10 rounded-none bg-emerald-500/20 text-[#e0e0e0] flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002-2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
                        </div>
                        <h3 class="text-lg font-medium text-white mb-2">Diagnostic Analytics</h3>
                        <p class="text-sm text-[#888888] leading-relaxed">
                            Interactive cross-session Matrix and drift diagnostics directly within the UI. Analyze merged gap penalties, dataframe lengths, and class distributions visually via DOM nodes.
                        </p>
                    </div>

                </div>
            </div>
        </div>

        <!-- View: SOTA Comparison -->"""
    
    html = html.replace(old_block, new_block)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print("HTML UI update successful")
else:
    print("Could not find markers in HTML")

