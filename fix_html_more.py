import re

with open('desktop-app/src/index.html', 'r') as f:
    text = f.read()

# Delete KPI Scorecard
kpi_regex = re.compile(r'<!-- KPI Scorecard -->.*?</div>\s*</div>', re.DOTALL)
text = kpi_regex.sub('', text)

# Delete Hardest Edge Cases / Misclassifications
misclass_regex = re.compile(r'<!-- Hardest Edge Cases / Misclassifications -->.*?</div>\s*</div>\s*</div>\s*</div>', re.DOTALL)
text = misclass_regex.sub('</div>\n        \n</div> <!-- End Scrolling Views Wrapper -->', text)

with open('desktop-app/src/index.html', 'w') as f:
    f.write(text)

