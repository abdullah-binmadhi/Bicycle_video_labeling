import os

fp = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/renderer.js"
with open(fp, "r") as f:
    text = f.read()

# I want to inject extensive tracing in `runScript` and `_runScript`
old_func = """function runScript(scriptKey) {
  try {
    _runScript(scriptKey);
  } catch(e) {
    logToConsole("⚠️ App Error: " + e.toString() + "<br/>" + e.stack, true);
  }
}"""
new_func = """function runScript(scriptKey) {
  try {
    logToConsole("🟢 Starting script execution for: " + scriptKey);
    _runScript(scriptKey);
  } catch(e) {
    logToConsole("⚠️ App Error: " + e.toString() + "<br/>" + e.stack, true);
  }
}"""
text = text.replace(old_func, new_func)

with open(fp, "w") as f:
    f.write(text)
