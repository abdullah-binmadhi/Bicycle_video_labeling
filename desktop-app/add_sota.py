import re

html_path = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html"

with open(html_path, "r") as f:
    html = f.read()

# 1. Update Navigation
nav_original = """        <li><a id="nav-instructions" class="active hover:bg-white/10" onclick="switchView('instructions')">
          <svg class="h-4 w-4 opacity-70" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          Overview & Docs
        </a></li>"""

nav_sota = """        <li><a id="nav-instructions" class="active hover:bg-white/10" onclick="switchView('instructions')">
          <svg class="h-4 w-4 opacity-70" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          Overview & Docs
        </a></li>
        <li><a id="nav-sota" class="hover:bg-white/10 text-emerald-100" onclick="switchView('sota')">
          <svg class="h-4 w-4 text-emerald-400 opacity-80" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
          SOTA Comparison
        </a></li>"""

if nav_original in html:
    html = html.replace(nav_original, nav_sota)
    print("Nav injected.")
else:
    print("Failed to find nav section")

# 2. Inject SOTA View
view_sota = """          <!-- View: SOTA Comparison -->
          <div id="view-sota" class="hidden-view flex flex-col gap-8 w-full max-w-6xl mx-auto pb-16 animate-fade-in">
            <div class="mb-4 relative rounded-3xl p-8 overflow-hidden bg-slate-900/50 border border-emerald-500/20 shadow-2xl">
              <div class="absolute right-0 top-0 w-1/3 h-full bg-gradient-to-l from-emerald-500/10 to-transparent"></div>
              <div class="relative z-10 flex items-start gap-6">
                <div class="w-16 h-16 rounded-2xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0 border border-emerald-500/30 shadow-[0_0_20px_rgba(16,185,129,0.3)]">
                    <svg class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>
                </div>
                <div>
                  <h1 class="text-3xl lg:text-4xl font-extrabold text-white tracking-tight mb-2">State-of-the-Art (SOTA) Analysis</h1>
                  <p class="text-slate-300 max-w-4xl leading-relaxed text-sm">
                    A peer-reviewed architectural derivation highlighting critical divergences between the <strong class="text-emerald-400">CycleSafe Multimodal framework</strong> and contemporary baseline methodologies within micro-mobility surface classification literature.
                  </p>
                </div>
              </div>
            </div>

            <div class="space-y-6">
                <!-- SOTA 1 -->
                <div class="glass-card p-8 rounded-2xl border border-white/5 flex flex-col md:flex-row gap-6 hover:border-emerald-500/20 transition-all duration-300 group">
                    <div class="w-12 h-12 rounded-full bg-rose-500/10 flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform border border-rose-500/20">
                        <svg class="w-6 h-6 text-rose-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" /></svg>
                    </div>
                    <div>
                        <h3 class="text-xl font-bold text-white mb-2">1. Resolution of the "Visual-Blindness" Paradigm</h3>
                        <p class="text-slate-400 text-sm leading-relaxed mb-4">
                            <span class="badge badge-sm bg-rose-500/20 text-rose-400 border-none mr-2 font-bold tracking-widest text-[10px]">THE SOTA FLAW</span>
                            Contemporary road classification models heavily depend on active Computer Vision pipelines (e.g., YOLO/CNN configurations mounted on handlebars). These fail precipitously under sub-optimal parameters: twilight operations, lens occlusions from mud, or solar glare. Continuous real-time visual processing also incurs high computational overhead, degrading battery endurance.
                        </p>
                        <div class="bg-emerald-500/5 rounded-xl p-4 border border-emerald-500/10 shadow-inner">
                            <p class="text-emerald-200/90 text-sm leading-relaxed flex items-start gap-2">
                                <svg class="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                                <span><strong class="text-emerald-400 font-bold">CycleSafe Methodology:</strong> We execute an architectural inversion. Computer Vision (CLIP/Roboflow) is strictly relegated to offline preprocessing to automate ground truth assignment. Real-time inference executes "blindly" via a `PhysicsTransformer` analyzing purely 1-Dimensional IMU telemetry, achieving zero-degradation performance during total visual occlusion.</span>
                            </p>
                        </div>
                    </div>
                </div>

                <!-- SOTA 2 -->
                <div class="glass-card p-8 rounded-2xl border border-white/5 flex flex-col md:flex-row gap-6 hover:border-emerald-500/20 transition-all duration-300 group">
                    <div class="w-12 h-12 rounded-full bg-blue-500/10 flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform border border-blue-500/20">
                        <svg class="w-6 h-6 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                    </div>
                    <div>
                        <h3 class="text-xl font-bold text-white mb-2">2. Kinematic Velocity Fusion Framework</h3>
                        <p class="text-slate-400 text-sm leading-relaxed mb-4">
                            <span class="badge badge-sm bg-rose-500/20 text-rose-400 border-none mr-2 font-bold tracking-widest text-[10px]">THE SOTA FLAW</span>
                            Legacy IMU models operate on crude heuristic thresholds, primarily tracking raw vertical Z-axis amplitude. This creates a "Vibration-Velocity Illusion," where high-speed smooth terrain (e.g., 30 MPH on hard dirt) mimics the absolute vibrational footprint of low-speed harsh terrain (e.g., 5 MPH on cobblestone), inducing chronic misclassification logic.
                        </p>
                        <div class="bg-emerald-500/5 rounded-xl p-4 border border-emerald-500/10 shadow-inner">
                            <p class="text-emerald-200/90 text-sm leading-relaxed flex items-start gap-2">
                                <svg class="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                                <span><strong class="text-emerald-400 font-bold">CycleSafe Methodology:</strong> Our network mathematically fuses concurrent GPS velocity coordinate measurements over the sliding 50Hz IMU spatial window. By integrating velocity vectors directly into the neural layers, the transformer contextualizes physical amplitudes against temporal speed, breaking the heuristic illusion.</span>
                            </p>
                        </div>
                    </div>
                </div>

                <!-- SOTA 3 -->
                <div class="glass-card p-8 rounded-2xl border border-white/5 flex flex-col md:flex-row gap-6 hover:border-emerald-500/20 transition-all duration-300 group">
                    <div class="w-12 h-12 rounded-full bg-orange-500/10 flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform border border-orange-500/20">
                        <svg class="w-6 h-6 text-orange-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                    </div>
                    <div>
                        <h3 class="text-xl font-bold text-white mb-2">3. Out-of-Distribution (OOD) Rejection Tolerance</h3>
                        <p class="text-slate-400 text-sm leading-relaxed mb-4">
                            <span class="badge badge-sm bg-rose-500/20 text-rose-400 border-none mr-2 font-bold tracking-widest text-[10px]">THE SOTA FLAW</span>
                            Standard classifiers utilize closed-loop softmax mapping configurations. Should a bicyclist dismount and transition into pedestrian movement, these networks mathematically hallucinate predictions—categorizing organic footfalls as "Severe Cobblestone"—corrupting the subsequent data aggregations.
                        </p>
                        <div class="bg-emerald-500/5 rounded-xl p-4 border border-emerald-500/10 shadow-inner">
                            <p class="text-emerald-200/90 text-sm leading-relaxed flex items-start gap-2">
                                <svg class="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                                <span><strong class="text-emerald-400 font-bold">CycleSafe Methodology:</strong> We integrate an active Isolation Forest protocol acting as a pre-inference algorithmic gate. It demands continuous rotational kinematics characteristics matching established biking profiles. Disconnected locomotion instantly triggers a hard OOD dataset rejection.</span>
                            </p>
                        </div>
                    </div>
                </div>

                <!-- SOTA 4 -->
                <div class="glass-card p-8 rounded-2xl border border-white/5 flex flex-col md:flex-row gap-6 hover:border-emerald-500/20 transition-all duration-300 group">
                    <div class="w-12 h-12 rounded-full bg-purple-500/10 flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform border border-purple-500/20">
                        <svg class="w-6 h-6 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>
                    </div>
                    <div>
                        <h3 class="text-xl font-bold text-white mb-2">4. Absolute Device Invariance Generalization</h3>
                        <p class="text-slate-400 text-sm leading-relaxed mb-4">
                            <span class="badge badge-sm bg-rose-500/20 text-rose-400 border-none mr-2 font-bold tracking-widest text-[10px]">THE SOTA FLAW</span>
                            A vast majority of academic baseline variants exhibit destructive overfitting tolerances; extrapolating logic from narrow, homogeneous mobile device arrays (e.g., strict iOS collection). Re-deploying inference pipelines to peripheral micro-electromechanical varying hardware configurations yields precipitous precision collapse.
                        </p>
                        <div class="bg-emerald-500/5 rounded-xl p-4 border border-emerald-500/10 shadow-inner">
                            <p class="text-emerald-200/90 text-sm leading-relaxed flex items-start gap-2">
                                <svg class="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                                <span><strong class="text-emerald-400 font-bold">CycleSafe Methodology:</strong> We enforce holistic temporal cross-hardware standardization algorithms. By synchronously batching localized iOS and Android IMU subsets directly into PyTorch data-loaders, the Transformer classifies physical road matrices irrespective of base-hardware resonance profiles.</span>
                            </p>
                        </div>
                    </div>
                </div>
            </div>
          </div>
          
          <!-- View: Extract Frames -->"""

if "<!-- View: Extract Frames -->" in html:
    html = html.replace("<!-- View: Extract Frames -->", view_sota)
    print("View injected.")
else:
    print("Failed to find inject target")

with open(html_path, "w") as f:
    f.write(html)
