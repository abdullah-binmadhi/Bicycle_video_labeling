import re

with open("desktop-app/src/renderer.js", "r") as f:
    content = f.read()

# Change visibility default from true to false
pattern_visible = re.compile(r"window\.classState\[surface\]\s*=\s*\{\s*visible:\s*true,\s*color:\s*defColor\s*\};", re.DOTALL)
replacement_visible = r"""window.classState[surface] = {
            visible: false,
            color: defColor
        };"""

content_new, count = pattern_visible.subn(replacement_visible, content)

# Change renderer.js to remove 'hidden' correctly from flex-container by removing hidden and adding flex
pattern_legend_show = re.compile(
    r"if\s*\(container\.parentElement\)\s*\{\s*container\.parentElement\.classList\.remove\('hidden'\);\s*\}",
    re.DOTALL
)
replacement_legend_show = r"""if (container.parentElement) {
        container.parentElement.classList.remove('hidden');
        container.parentElement.classList.add('flex'); // Because the new layout uses flex-col
    }"""

content_new2, count2 = pattern_legend_show.subn(replacement_legend_show, content_new)

if count > 0 or count2 > 0:
    with open("desktop-app/src/renderer.js", "w") as f:
        f.write(content_new2)
    print(f"Patched js defs, {count} visible changes, {count2} display changes.")
else:
    print("Failed to replace visible true in js")
