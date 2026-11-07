"""Print the index.html that Vercel serves: local paths swapped for the Blob store, optionally without the
"how it was calculated" lines (the simple variant at trip-risk-checker-simple.vercel.app).

    python web/make_index.py            # full version
    python web/make_index.py --simple   # explanations hidden
"""
import sys
from pathlib import Path

BLOB = "https://hukavnj3yh9m64a5.public.blob.vercel-storage.com/trip-risk"
s = (Path(__file__).resolve().parent / "index.html").read_text(encoding="utf-8")
s = s.replace('href="./styles.css"', f'href="{BLOB}/styles.css"').replace('src="./app.js"', f'src="{BLOB}/app.js"').replace('"./data"', f'"{BLOB}"')
if "--simple" in sys.argv:
    s = s.replace("</head>", "<style>.how, .how-note { display: none; }</style>\n</head>")
sys.stdout.write(s)
