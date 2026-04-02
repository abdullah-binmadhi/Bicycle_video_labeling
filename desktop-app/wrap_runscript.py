import re

fp = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/renderer.js"
with open(fp, "r") as f:
    text = f.read()

if "function _runScript(scriptKey)" not in text:
    text = text.replace("function runScript(scriptKey) {", """function runScript(scriptKey) {
  try {
    _runScript(scriptKey);
  } catch(e) {
    logToConsole("⚠️ App Error: " + e.toString() + "<br/>" + e.stack, true);
  }
}
function _runScript(scriptKey) {""")
    with open(fp, "w") as f:
        f.write(text)
    print("Wrapped successfully!")
