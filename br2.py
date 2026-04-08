with open('desktop-app/src/renderer.js', 'r') as f:
    text = f.read()

count = 0
in_str = False
str_char = None
for i, c in enumerate(text):
    if c in ["'", '"', '`']:
        if not in_str:
            in_str = True
            str_char = c
        elif c == str_char:
            if text[i - 1] != '\\':
                in_str = False
    if not in_str:
        if c == '{':
            count += 1
        elif c == '}':
            count -= 1
print("Net brace count:", count)
