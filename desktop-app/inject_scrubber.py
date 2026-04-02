import re

with open("/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html", "r") as f:
    text = f.read()

# I want to add the Scrubber under the Inference Video block
video_div_end = """               <p id="inf-idle-msg" class="text-slate-500 font-medium text-sm flex gap-2 items-center">
                  <svg class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg>
                  Waiting for dataset...
               </p>
            </div>"""

if "inf-scrubber" not in text:
    scrubber_html = """
            </div>

            <!-- Global Timeline Scrubber -->
            <div class="col-span-1 lg:col-span-2 glass-card p-4 rounded-2xl border border-white/5 shadow-xl flex flex-col items-center mt-2 group relative">
                <div class="w-full flex items-center justify-between text-[10px] text-slate-500 font-mono px-1 mb-1">
                    <span id="scrub-start">00:00:00</span>
                    <span id="scrub-end" class="text-emerald-500">Live Scrubber</span>
                </div>
                <!-- Interactive slider -->
                <input type="range" min="0" max="100" value="0" class="w-full appearance-none bg-slate-800 h-2 rounded-full outline-none [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:bg-emerald-400 [&::-webkit-slider-thumb]:rounded-full cursor-pointer hover:bg-slate-700 transition-all border border-white/10" id="inf-scrubber">
                
                <!-- Spectral Analysis (FFT) underneath scrubber -->
                <div class="w-full h-10 mt-3 rounded overflow-hidden relative border border-white/5 bg-black opacity-50 group-hover:opacity-100 transition-opacity">
                   <p class="absolute inset-0 flex items-center justify-center text-[8px] text-slate-600 tracking-widest font-black uppercase">LinearAccelerometer FFT Spectrum Profile</p>
                   <canvas id="fft-canvas" class="w-full h-full relative z-10"></canvas>
                </div>
            </div>"""
            
    text = text.replace(video_div_end, video_div_end + scrubber_html)
    
    with open("/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html", "w") as f:
        f.write(text)
    print("Scrubber and FFT layout injected!")
else:
    print("Scrubber already injected.")
