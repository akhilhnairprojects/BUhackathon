"""Recolour the notebook charts into the web app's palette for the simplified deck.

Each pixel is read as a blend of one chart colour with white (anti-aliasing), and re-blended from the
matching app colour with the app's paper ground, so edges stay smooth.

    python deck/build/recolor_charts.py            # writes outputs/figures/deck/<name>.png
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "outputs" / "figures"
OUT = SRC / "deck"
OUT.mkdir(exist_ok=True)

hexrgb = lambda h: np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], dtype=float)
# chart colour (src/style.py)  ->  app colour (web/styles.css)
MAP = [
    ("#1F2A44", "#17150F"),   # ink
    ("#B8BEC9", "#CFC6B2"),   # context grey -> sand
    ("#D1495B", "#B1372B"),   # accent (bad) -> brick
    ("#2A9D8F", "#4A6B48"),   # good -> olive
    ("#3A6EA5", "#45413A"),   # blue -> dark neutral
    ("#E9A23B", "#A9761D"),   # amber -> ochre
    ("#5B6477", "#76715F"),   # subtitle -> muted
    ("#7A8394", "#76715F"),   # source line -> muted
    ("#8A93A6", "#C2BBAA"),   # axis edge -> rule
    ("#E6E9EF", "#E3DDD0"),   # grid -> paper-3
    ("#000000", "#17150F"),   # pure black text
]
WHITE = np.array([255.0, 255.0, 255.0])
PAPER = hexrgb("#F5F2EC")


def recolor(img: Image.Image) -> Image.Image:
    px = np.asarray(img.convert("RGB"), dtype=float)
    h, w, _ = px.shape
    flat = px.reshape(-1, 3)
    d = flat - WHITE                                   # (N,3)
    best_res = np.full(len(flat), np.inf)
    best_a = np.zeros(len(flat))
    best_i = np.zeros(len(flat), dtype=int)
    for i, (s, t) in enumerate(MAP):
        c = hexrgb(s) - WHITE
        a = np.clip((d @ c) / (c @ c), 0, 1)           # blend weight of this colour against white
        res = np.linalg.norm(d - a[:, None] * c, axis=1)
        better = res < best_res
        best_res[better], best_a[better], best_i[better] = res[better], a[better], i
    targets = np.array([hexrgb(t) for _, t in MAP])
    out = best_a[:, None] * targets[best_i] + (1 - best_a[:, None]) * PAPER
    return Image.fromarray(out.reshape(h, w, 3).round().astype(np.uint8))


NAMES = sys.argv[1:] or ["02_disruption_by_hour", "14_carrier_route_adjusted", "10_weather_conditions", "17_nonstop_vs_onestop", "23_policy_impact"]
for n in NAMES:
    recolor(Image.open(SRC / f"{n}.png")).save(OUT / f"{n}.png")
    print("recoloured", n)
