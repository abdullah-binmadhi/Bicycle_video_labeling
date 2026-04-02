import re

with open("/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html", "r") as f:
    text = f.read()

analytics_nav = """          <li><a id="nav-analytics" class="hover:bg-white/10 text-white font-semibold" onclick="switchView('analytics')">
            <svg class="h-4 w-4 text-emerald-400 drop-shadow-md" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
            7. Model Analytics
          </a></li>"""

if "nav-analytics" not in text:
    nav_str = "6. Real-Time Inference\n          </a></li>"
    text = text.replace(nav_str, nav_str + "\n" + analytics_nav)
    
    with open("/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html", "w") as f:
        f.write(text)
    print("Nav added!")
else:
    print("Nav already there.")
