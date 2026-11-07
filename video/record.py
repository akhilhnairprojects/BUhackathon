"""Record the three screen clips for the walkthrough video (a fake cursor is drawn into the page so the
viewer can follow the clicks). Writes video/assets/clip-*.mp4 and video/assets/clips.json with the
second at which each action happened, for placing captions.

    python video/record.py            # needs the web app running on localhost:8080
"""
import json
import subprocess
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
ASSETS.mkdir(exist_ok=True)
URL = "http://localhost:8080"

INIT = r"""
(() => {
  const css = document.createElement('style');
  css.textContent = '::-webkit-scrollbar{display:none} html{scroll-behavior:auto}';
  const cur = document.createElement('div');
  cur.id = '__cur';
  cur.style.cssText = 'position:fixed;left:-50px;top:-50px;width:24px;height:32px;z-index:999999;pointer-events:none;filter:drop-shadow(0 1px 2px rgba(0,0,0,.35))';
  cur.innerHTML = '<svg width="24" height="32" viewBox="0 0 24 32"><path d="M3 2 L3 25 L9 19.5 L13 29 L17.5 27 L13.5 18 L21 18 Z" fill="#17150F" stroke="#F5F2EC" stroke-width="1.6" stroke-linejoin="round"/></svg>';
  const rip = document.createElement('div');
  rip.id = '__rip';
  rip.style.cssText = 'position:fixed;left:-50px;top:-50px;width:40px;height:40px;border-radius:50%;border:2px solid #B1372B;opacity:0;pointer-events:none;z-index:999998;transform:translate(-50%,-50%)';
  const mount = () => { document.head.append(css); document.body.append(cur, rip); };
  if (document.body) mount(); else document.addEventListener('DOMContentLoaded', mount);
  window.addEventListener('mousemove', e => { cur.style.left = e.clientX + 'px'; cur.style.top = e.clientY + 'px'; });
  window.__ripple = (x, y) => { rip.style.left = x + 'px'; rip.style.top = y + 'px';
    rip.animate([{ opacity: 1, transform: 'translate(-50%,-50%) scale(.35)' }, { opacity: 0, transform: 'translate(-50%,-50%) scale(1.5)' }], { duration: 480, easing: 'ease-out' }); };
})();
"""


class Rec:
    def __init__(self, pw, name):
        self.name = name
        self.ctx = pw.chromium.launch().new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=1,
                                                     record_video_dir=str(ASSETS / "raw"), record_video_size={"width": 1920, "height": 1080})
        self.ctx.add_init_script(INIT)
        self.page = self.ctx.new_page()
        self.t0 = time.time()
        self.marks = []
        self.x, self.y = 960, 540

    def mark(self, label):
        self.marks.append({"t": round(time.time() - self.t0, 2), "label": label})
        print(f"  {self.marks[-1]['t']:6.2f}  {label}")

    def move_to(self, locator, dx=0.5, dy=0.5, steps=30):
        b = locator.bounding_box()
        x, y = b["x"] + b["width"] * dx, b["y"] + b["height"] * dy
        self.page.mouse.move(x, y, steps=steps)
        self.x, self.y = x, y
        return x, y

    def click(self, locator, dx=0.5, dy=0.5, real=True):
        x, y = self.move_to(locator, dx, dy)
        self.page.evaluate(f"window.__ripple({x}, {y})")
        if real:
            locator.click()
        time.sleep(0.25)

    def scroll(self, px, step=120, pause=0.03):
        n = abs(px) // step
        for _ in range(n):
            self.page.mouse.wheel(0, step if px > 0 else -step)
            time.sleep(pause)

    def finish(self):
        path = self.page.video.path()
        self.ctx.close()
        src = Path(path)
        out = ASSETS / f"clip-{self.name}.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-r", "30", "-g", "30", "-pix_fmt", "yuv420p",
                        "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-an", str(out)], check=True)
        src.unlink()
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)],
                                   capture_output=True, text=True).stdout.strip())
        print(f"wrote {out.name} ({dur:.1f} s)")
        return {"file": f"assets/{out.name}", "duration": round(dur, 2), "marks": self.marks}


def wait_results(page):
    page.wait_for_selector(".rcard", timeout=20000)
    time.sleep(0.4)


import sys
ONLY = set(sys.argv[1:])
with sync_playwright() as pw:
    clips = json.loads((ASSETS / "clips.json").read_text()) if (ASSETS / "clips.json").exists() else {}

        # ---- clip 1: check a trip
    if not ONLY or "check" in ONLY:
        r = Rec(pw, "check"); p = r.page
        p.goto(f"{URL}/#check", wait_until="networkidle"); wait_results(p); r.mark("loaded BOS->ORD")
        time.sleep(2.0)
        selects = p.locator("select.select")
        r.click(selects.nth(1), real=False); r.mark("open To")
        selects.nth(1).select_option("DEN"); r.mark("To = DEN"); wait_results(p)
        time.sleep(2.2)
        date = p.locator("input.date")
        r.click(date, dx=0.3, real=False); r.mark("date")
        date.fill("2026-12-15"); date.dispatch_event("change"); r.mark("date = 15 Dec"); wait_results(p)
        time.sleep(2.2)
        r.click(selects.nth(2), real=False); r.mark("open time")
        selects.nth(2).select_option("3"); r.mark("time = afternoon"); wait_results(p)
        time.sleep(1.2)
        r.move_to(p.locator(".rcard.best"), 0.5, 0.45, steps=40); r.mark("hover recommended")
        time.sleep(2.6)
        r.move_to(p.locator(".banner"), 0.3, 0.5, steps=30); r.mark("banner")
        time.sleep(2.0)
        r.scroll(900); r.mark("scrolled to charts")
        time.sleep(0.4)
        r.move_to(p.locator(".chart-title").first, 0.5, 0.5, steps=30)
        time.sleep(2.8)
        r.scroll(600); r.mark("scrolled to worth the stop")
        time.sleep(3.0)
        clips["check"] = r.finish()

        # ---- clip 2: cost of missing
    if not ONLY or "cost" in ONLY:
        r = Rec(pw, "cost"); p = r.page
        p.goto(f"{URL}/#check", wait_until="networkidle"); wait_results(p)
        p.locator("select.select").nth(1).select_option("DEN"); wait_results(p); r.mark("loaded BOS->DEN")
        time.sleep(1.2)
        r.click(p.locator("a.tab", has_text="Cost of missing")); r.mark("open cost page")
        p.wait_for_selector(".range"); time.sleep(2.4)
        ranges = p.locator("input.range")
        b = ranges.nth(0).bounding_box()
        x0 = b["x"] + b["width"] * 0.30 + 2; y0 = b["y"] + b["height"] / 2
        p.mouse.move(x0, y0, steps=35); r.mark("grab meeting slider")
        p.mouse.down(); time.sleep(0.2)
        for i in range(1, 31):
            p.mouse.move(x0 + (b["width"] * 0.36) * i / 30, y0); time.sleep(0.04)
        p.mouse.up(); r.mark("meeting = higher")
        time.sleep(2.2)
        b = ranges.nth(1).bounding_box()
        x0 = b["x"] + b["width"] * 0.333 + 2; y0 = b["y"] + b["height"] / 2
        p.mouse.move(x0, y0, steps=30); p.mouse.down(); time.sleep(0.2)
        for i in range(1, 21):
            p.mouse.move(x0 + (b["width"] * 0.22) * i / 20, y0); time.sleep(0.04)
        p.mouse.up(); r.mark("hour = higher")
        time.sleep(2.0)
        r.move_to(p.locator(".kpi").nth(2), 0.5, 0.5, steps=40); r.mark("hover premium")
        time.sleep(2.4)
        r.move_to(p.locator(".chart-title").last, 0.5, 0.5, steps=40); r.mark("hover chart")
        time.sleep(3.0)
        clips["cost"] = r.finish()

        # ---- clip 3: hubs and airports
    if not ONLY or "hubs" in ONLY:
        r = Rec(pw, "hubs"); p = r.page
        p.goto(f"{URL}/#check", wait_until="networkidle"); wait_results(p)
        time.sleep(0.8)
        r.click(p.locator("a.tab", has_text="Hubs")); r.mark("open hubs page")
        p.wait_for_selector(".rcard.best"); time.sleep(0.5)
        try:
            p.wait_for_selector("svg circle", timeout=15000)
        except Exception:
            pass
        time.sleep(2.0)
        r.move_to(p.locator(".rcard.best"), 0.5, 0.4, steps=40); r.mark("best hub")
        time.sleep(2.2)
        r.scroll(1500); r.mark("scrolled to table")
        time.sleep(2.4)
        r.scroll(1100); r.mark("scrolled to map")
        p.evaluate("document.querySelector('.seg').closest('.card').scrollIntoView({block:'start'}); window.scrollBy(0,-60)")
        time.sleep(1.4)
        seg = p.locator(".seg button", has_text="Adverse-weather"); r.click(seg, real=False); seg.dispatch_event("click"); r.mark("metric = weather")
        time.sleep(1.4)
        msel = p.locator(".seg").locator("xpath=following-sibling::select").first
        r.click(msel, real=False); msel.select_option("6"); r.mark("month = July")
        time.sleep(1.6)
        seg = p.locator(".seg button", has_text="Winter"); r.click(seg, real=False); seg.dispatch_event("click"); r.mark("metric = winter")
        time.sleep(1.2)
        circles = p.locator("svg circle")
        n = circles.count()
        if n:
            r.move_to(circles.nth(min(5, n - 1)), steps=40); r.mark("hover a dot")
        time.sleep(2.8)
        clips["hubs"] = r.finish()

    (ASSETS / "clips.json").write_text(json.dumps(clips, indent=1))
    print(json.dumps(clips, indent=1))
