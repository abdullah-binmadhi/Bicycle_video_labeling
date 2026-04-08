with open("desktop-app/src/index.html", "r") as f:
    text = f.read()

# Let's find exactly the two trailing `</div>` that don't match.
# Wait! In my patch, I replaced `<!-- Hardest Edge Cases / Misclassifications -->.*?</table>\s*</div>\s*</div>` with ``
# Originally the block was:
#  <!-- Hardest Edge Cases / Misclassifications -->
#  <div class="border border-[#222] bg-[#0c0c0c] p-6 w-full">
#    ...
#    <div class="overflow-x-auto">
#      <table ...>
#      ...
#      </table>
#    </div>
#  </div>
# 
# But let's check `index.html` structure by running an HTML parser to fix it.

from bs4 import BeautifulSoup
try:
    soup = BeautifulSoup(text, 'html.parser')
    with open("desktop-app/src/index.html", "w") as f:
        f.write(soup.prettify(formatter="html"))
    print("Auto-fixed with BeautifulSoup.")
except Exception as e:
    print(e)
