fp = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html"
with open(fp, "r") as f:
    text = f.read()
if "patches.css" not in text:
    text = text.replace("</head>", '  <link rel="stylesheet" href="./patches.css">\n</head>')
    with open(fp, "w") as f:
        f.write(text)
