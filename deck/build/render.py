"""Render every slide of a .pptx to PNG with PowerPoint (COM) for visual QA.

    python deck/build/render.py deck/Arrive_On_Time_Arrive_Ready.pptx deck/build/render
"""
import os
import sys
from pathlib import Path

import pythoncom
import win32com.client

src = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
out.mkdir(parents=True, exist_ok=True)
for f in out.glob("*.PNG"):
    f.unlink()
pythoncom.CoInitialize()
try:                                   # PowerPoint already open (the person may be reading a deck): borrow it, never quit it
    app = win32com.client.GetActiveObject("PowerPoint.Application"); own = False
except Exception:
    app = win32com.client.Dispatch("PowerPoint.Application"); own = True
pres = app.Presentations.Open(str(src), ReadOnly=True, Untitled=False, WithWindow=False)
pres.Export(str(out), "PNG", 1600, 900)
n = pres.Slides.Count
pres.Close()
if own:
    app.Quit()
print(f"rendered {n} slides to {out}")
