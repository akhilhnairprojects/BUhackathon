"""Deploy the web app to Vercel as plain static files (index.html, app.js, styles.css, data/).

    python web/deploy.py            # trip-risk-checker.vercel.app        <- web/app.js, web/styles.css
    python web/deploy.py --simple   # trip-risk-checker-simple.vercel.app <- web/backup/ (frozen copy, whole-number percentages)

Needs the Vercel CLI signed in (npx vercel whoami). The Blob store the app used to read from was
suspended, so everything now ships inside the deployment itself.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SIMPLE = "--simple" in sys.argv
TEAM = "team_BswKfJ5JkfGgKsxvOSGu12Le"
PROJECT = "prj_2Bb4VgS04VQMyIVoR9CE65uBC03J" if SIMPLE else "prj_URW72NTzr9TMshSmVOFhVohHdYLD"
dist = ROOT / ("dist-simple" if SIMPLE else "dist")
if dist.exists():
    shutil.rmtree(dist)
dist.mkdir()
code = ROOT / "backup" if SIMPLE else ROOT
shutil.copy(ROOT / "index.html", dist / "index.html")
shutil.copy(code / "app.js", dist / "app.js")
shutil.copy(code / "styles.css", dist / "styles.css")
shutil.copytree(ROOT / "data", dist / "data")
(dist / "vercel.json").write_text(json.dumps({"cleanUrls": True, "headers": [
    {"source": "/data/(.*)", "headers": [{"key": "Cache-Control", "value": "public, max-age=3600"}]},
    {"source": "/(.*)", "headers": [{"key": "Cache-Control", "value": "public, max-age=60"}]}]}, indent=1))
(dist / ".vercel").mkdir()
(dist / ".vercel" / "project.json").write_text(json.dumps({"projectId": PROJECT, "orgId": TEAM}))
r = subprocess.run(["npx", "--yes", "vercel@latest", "deploy", "--prod", "--yes"], cwd=dist, shell=True, capture_output=True, text=True, env={**__import__("os").environ, "CI": "1"})
print(r.stdout[-800:], r.stderr[-1500:])
