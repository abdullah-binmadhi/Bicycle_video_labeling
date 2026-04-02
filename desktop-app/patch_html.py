fp = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html"
with open(fp, "r") as f:
    text = f.read()

text = text.replace("Execute Disassembly", "Execute Disassembly 🛠️ (Patched)")
# Hide the workspace output div entirely
old_div = """<div class="flex flex-col">
                <label class="text-xs uppercase tracking-widest font-bold text-slate-400 mb-2">Workspace Output</label>
                <input type="file" webkitdirectory directory class="file-input file-input-bordered file-input-md w-full bg-slate-900/50 border-white/10 text-white" id="extractOutPicker" />
              </div>"""
new_div = """<!-- DIV HIDDEN BY PATCH -->
              <input type="file" webkitdirectory directory class="hidden" id="extractOutPicker" />"""
if old_div in text:
    text = text.replace(old_div, new_div)

with open(fp, "w") as f:
    f.write(text)
print("Patched HTML")
