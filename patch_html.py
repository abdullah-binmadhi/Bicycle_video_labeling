html = open("desktop-app/src/index.html", "r").read()
idx = html.find('<head>')
html = html[:idx+6] + '\n<script>window.onerror = function(m, s, l, c, e) { require("fs").appendFileSync("/tmp/ui-err.log", m + "\\n" + (e?e.stack:"") + "\\n"); }; console.log = function() { require("fs").appendFileSync("/tmp/ui-log.log", Array.from(arguments).join(" ") + "\\n"); };</script>\n' + html[idx+6:]
open("desktop-app/src/index.html", "w").write(html)
