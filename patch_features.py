import sys
import re

new_content = """<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
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
                </div>"""

def patch_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Regex to capture everything between <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"> and its matching closing div
    # In these files, it ends right before <!-- Legacy Pipeline Steps --> or similar.
    # Let's use a simpler pattern
    pattern = r'<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">[\s\S]*?</div>\s*</div>'
    match = re.search(pattern, content)
    if match:
        new_text = new_content + "\n            </div>"
        patched = content[:match.start()] + new_text + content[match.end():]
        with open(filepath, 'w') as f:
            f.write(patched)
        print(f"Patched {filepath}")
    else:
        print(f"Could not find target in {filepath}")

patch_file('desktop-app/update_docs.py')
patch_file('desktop-app/update_docs_force.py')
