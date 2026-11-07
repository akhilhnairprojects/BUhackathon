"""Record the three screen clips for the walkthrough video, paced to the narration (a fake cursor is drawn
into the page so the viewer can follow the clicks). Writes video/assets/clip-*.mp4 and video/assets/clips.json
with the second at which each narration line starts, for placing the voice and captions.

    python video/narration.py              # first: the voice files and their lengths
    python video/record.py [check|cost|hubs]   # needs the web app running on localhost:8080
"""
import json
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
ASSETS.mkdir(exist_ok=True)
URL = "http://localhost:8080"
NARR = json.loads((ASSETS / "narration.json").read_text(encoding="utf-8"))
PAD = 0.7   # seconds of quiet after each line before the next action

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
        self.said = {}

    def now(self):
        return time.time() - self.t0

    def say(self, lid):
        """The narration line `lid` starts now."""
        self.said[lid] = self.now()
        self.marks.append({"t": round(self.said[lid], 2), "id": lid})
        print(f"  {self.said[lid]:6.2f}  {lid}  {NARR[lid]['text'][:50]}")

    def until(self, lid, extra=0.0):
        """Wait until the line `lid` has finished (plus a pause)."""
        end = self.said[lid] + NARR[lid]["dur"] + PAD + extra
        time.sleep(max(0.0, end - self.now()))

    def hold(self, lid, extra=0.0):
        self.say(lid)
        self.until(lid, extra)

    def move_to(self, locator, dx=0.5, dy=0.5, steps=30):
        b = locator.bounding_box()
        x, y = b["x"] + b["width"] * dx, b["y"] + b["height"] * dy
        self.page.mouse.move(x, y, steps=steps)
        return x, y

    def click(self, locator, dx=0.5, dy=0.5, real=True):
        x, y = self.move_to(locator, dx, dy)
        self.page.evaluate(f"window.__ripple({x}, {y})")
        if real:
            locator.click()
        time.sleep(0.25)

    def drag(self, locator, frac0, frac1, steps=30):
        """Drag a range input's thumb from one fraction of its width to another."""
        b = locator.bounding_box()
        x0 = b["x"] + 8 + (b["width"] - 16) * frac0; y0 = b["y"] + b["height"] / 2
        x1 = b["x"] + 8 + (b["width"] - 16) * frac1
        self.page.mouse.move(x0, y0, steps=30); self.page.mouse.down(); time.sleep(0.2)
        for i in range(1, steps + 1):
            self.page.mouse.move(x0 + (x1 - x0) * i / steps, y0); time.sleep(0.04)
        self.page.mouse.up()

    def scroll(self, px, step=120, pause=0.03):
        for _ in range(abs(px) // step):
            self.page.mouse.wheel(0, step if px > 0 else -step)
            time.sleep(pause)

    def finish(self):
        path = self.page.video.path()
        elapsed = self.now()
        self.ctx.close()
        src = Path(path)
        out = ASSETS / f"clip-{self.name}.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-r", "30", "-g", "30", "-pix_fmt", "yuv420p",
                        "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-an", str(out)], check=True)
        src.unlink()
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)],
                                   capture_output=True, text=True).stdout.strip())
        # the recording starts at the first painted frame, some time after t0: shift the marks onto video time
        offset = round(elapsed - dur, 2)
        marks = [{"t": round(m["t"] - offset, 2), "id": m["id"]} for m in self.marks]
        print(f"wrote {out.name} ({dur:.1f} s; recording started {offset:.2f} s after t0)")
        return {"file": f"assets/{out.name}", "duration": round(dur, 2), "offset": offset, "marks": marks}


def wait_results(page):
    page.wait_for_selector(".rcard", timeout=20000)
    time.sleep(0.4)


ONLY = set(sys.argv[1:])
with sync_playwright() as pw:
    clips = json.loads((ASSETS / "clips.json").read_text()) if (ASSETS / "clips.json").exists() else {}

    # ---- clip 1: check a trip
    if not ONLY or "check" in ONLY:
        r = Rec(pw, "check"); p = r.page
        p.goto(f"{URL}/#check", wait_until="networkidle"); wait_results(p)
        time.sleep(0.6)
        selects = p.locator("select.select")
        r.say("ck1"); r.move_to(selects.nth(0), 0.5, 0.5, steps=40); r.until("ck1")
        r.say("ck2"); r.click(selects.nth(1), real=False); selects.nth(1).select_option("DEN"); wait_results(p); r.until("ck2")
        date = p.locator("input.date")
        r.say("ck3"); r.click(date, dx=0.3, real=False); date.fill("2026-12-15"); date.dispatch_event("change"); wait_results(p); r.until("ck3")
        r.say("ck4"); r.click(selects.nth(2), real=False); selects.nth(2).select_option("3"); wait_results(p); r.until("ck4")
        r.say("ck5"); r.move_to(p.locator(".rcard.best"), 0.5, 0.3, steps=40); time.sleep(2.0); r.move_to(p.locator(".rcard.best .rows"), 0.5, 0.5, steps=40); r.until("ck5")
        r.say("ck6"); r.move_to(p.locator(".banner"), 0.3, 0.5, steps=30); r.until("ck6")
        r.say("ck7"); r.scroll(900); time.sleep(0.3); r.move_to(p.locator(".chart-title").first, 0.5, 0.5, steps=30); r.until("ck7")
        r.say("ck8"); r.scroll(700); time.sleep(0.3); r.move_to(p.locator(".kpi").nth(1), 0.5, 0.5, steps=30); r.until("ck8", 0.4)
        clips["check"] = r.finish()

    # ---- clip 2: cost of missing
    if not ONLY or "cost" in ONLY:
        r = Rec(pw, "cost"); p = r.page
        p.goto(f"{URL}/#check", wait_until="networkidle"); wait_results(p)
        p.locator("select.select").nth(1).select_option("DEN"); wait_results(p)
        time.sleep(0.6)
        r.say("co1"); r.click(p.locator("a.tab", has_text="Cost of missing")); p.wait_for_selector(".range"); r.until("co1")
        ranges = p.locator("input.range")
        r.say("co2"); r.drag(ranges.nth(0), 0.30, 0.60); time.sleep(0.4); r.drag(ranges.nth(1), 1 / 3, 5 / 9, steps=20); time.sleep(0.4); r.drag(ranges.nth(2), 0.30, 0.50, steps=16); r.until("co2")
        r.say("co4"); r.move_to(p.locator(".kpi").nth(0), 0.5, 0.6, steps=40); time.sleep(2.2); r.move_to(p.locator(".kpi").nth(2), 0.5, 0.5, steps=40); r.until("co4")
        r.say("co5"); r.scroll(400); time.sleep(0.3); r.move_to(p.locator(".chart-title").last, 0.5, 0.5, steps=40); r.until("co5", 0.4)
        clips["cost"] = r.finish()

    # ---- clip 3: hubs and airports
    if not ONLY or "hubs" in ONLY:
        r = Rec(pw, "hubs"); p = r.page
        p.goto(f"{URL}/#check", wait_until="networkidle"); wait_results(p)
        time.sleep(0.6)
        r.say("hb1"); r.click(p.locator("a.tab", has_text="Hubs")); p.wait_for_selector(".rcard.best")
        try:
            p.wait_for_selector("svg circle", timeout=15000)
        except Exception:
            pass
        r.until("hb1")
        r.say("hb2"); r.move_to(p.locator(".rcard.best"), 0.5, 0.4, steps=40); time.sleep(1.6); r.scroll(1500); r.until("hb2")
        r.say("hb3"); r.scroll(1100)
        p.evaluate("document.querySelector('.seg').closest('.card').scrollIntoView({block:'start'}); window.scrollBy(0,-60)")
        time.sleep(1.2)
        seg = p.locator(".seg button", has_text="Adverse-weather"); r.click(seg, real=False); seg.dispatch_event("click")
        time.sleep(1.4)
        msel = p.locator(".seg").locator("xpath=following-sibling::select").first
        r.click(msel, real=False); msel.select_option("6")
        time.sleep(1.6)
        seg = p.locator(".seg button", has_text="Winter"); r.click(seg, real=False); seg.dispatch_event("click")
        r.until("hb3")
        r.say("hb4")
        circles = p.locator("svg circle")
        n = circles.count()
        if n:
            r.move_to(circles.nth(min(5, n - 1)), steps=40)
        r.until("hb4", 0.6)
        clips["hubs"] = r.finish()

    (ASSETS / "clips.json").write_text(json.dumps(clips, indent=1))
    print(json.dumps(clips, indent=1))
