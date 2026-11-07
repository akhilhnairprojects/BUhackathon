"""Write the HyperFrames compositions from the recorded clips and the narration.

    python video/build_scenes.py     # after narration.py and record.py

Each footage scene is one clip, trimmed to start just before its first narration line; every line is an
<audio> placed where it was spoken during the recording, with a caption card carrying the same words.
index.html is rewritten with the scene durations.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
A = HERE / "assets"
NARR = json.loads((A / "narration.json").read_text(encoding="utf-8"))
CLIPS = json.loads((A / "clips.json").read_text(encoding="utf-8"))
LEAD = 0.8      # seconds of footage before the first line
TAIL = 0.6      # seconds after the last line ends before the scene cuts
CAP_PAD = 0.35  # caption outlives the voice by this much

CSS = """    #root { position: absolute; inset: 0; background: #F5F2EC; }
    #v-{id} { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; object-fit: contain; }
    .cap { position: absolute; left: 96px; right: 96px; bottom: 84px; display: flex; justify-content: center; pointer-events: none; }
    .cap .in { display: flex; align-items: baseline; gap: 22px; max-width: 1560px; background: rgba(23, 21, 15, 0.93); color: #F5F2EC; padding: 20px 34px 22px 30px; border-left: 4px solid #B1372B; font-family: "Inter", sans-serif; font-size: 30px; line-height: 1.3; }
    .cap .n { font-family: "JetBrains Mono", monospace; font-size: 28px; letter-spacing: 0.1em; color: #E5B5AE; flex: none; }"""


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def scene(sid, number_from):
    clip = CLIPS[sid]
    marks = [m for m in clip["marks"] if m["id"] in NARR]
    start = max(0.0, marks[0]["t"] - LEAD)
    last = marks[-1]
    end = min(clip["duration"], last["t"] + NARR[last["id"]]["dur"] + TAIL)
    dur = round(end - start, 2)
    audio, caps, tl = [], [], []
    for i, m in enumerate(marks):
        n = NARR[m["id"]]
        t = round(m["t"] - start, 2)
        d = round(min(n["dur"] + CAP_PAD, dur - t), 2)
        audio.append(f'    <audio id="a-{m["id"]}" class="clip" src="{n["file"]}" data-start="{t}" data-duration="{round(n["dur"], 2)}" data-track-index="2" data-has-audio="true" data-hf-media-start-basis="local"></audio>')
        caps.append(f'    <div id="c-{m["id"]}" class="cap clip" data-start="{t}" data-duration="{d}" data-track-index="1"><div class="in"><span class="n">{number_from + i:02d}</span><span>{esc(n["text"])}</span></div></div>')
        tl.append(f'      tl.fromTo("#c-{m["id"]} .in", {{ opacity: 0, filter: "blur(8px)", y: 12 }}, {{ opacity: 1, filter: "blur(0px)", y: 0, duration: 0.22, ease: "power4.out" }}, {t});')
        tl.append(f'      tl.to("#c-{m["id"]} .in", {{ opacity: 0, filter: "blur(6px)", duration: 0.15, ease: "power3.in" }}, {round(t + d - 0.18, 2)});')
    html = f"""<template>
  <style>
{CSS.replace("{id}", sid)}
  </style>
  <div id="root" data-composition-id="{sid}" data-width="1920" data-height="1080">
    <video id="v-{sid}" class="clip" src="{clip["file"]}" data-start="0" data-duration="{dur}" data-media-start="{round(start, 2)}" data-track-index="0" muted playsinline></video>
{chr(10).join(caps)}
{chr(10).join(audio)}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    tl.fromTo("#v-{sid}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3, ease: "power2.out" }}, 0);
    tl.to("#v-{sid}", {{ opacity: 0, duration: 0.25, ease: "power2.in" }}, {round(dur - 0.28, 2)});
{chr(10).join(tl)}
    window.__timelines["{sid}"] = tl;
  </script>
</template>
"""
    (HERE / "compositions" / f"{sid}.html").write_text(html, encoding="utf-8")
    return dur, number_from + len(marks)


def title_scene(path, sid, lid, dur, extra_tl):
    """Intro/outro: keep the hand-written markup, set the duration and add the voice line."""
    html = path.read_text(encoding="utf-8")
    import re
    html = re.sub(rf'(id="{sid}-stage" class="clip" data-start="0" data-duration=")[^"]*(")', rf'\g<1>{dur}\2', html)
    html = re.sub(r'\n    <audio id="a-[^\n]*\n', "\n", html)
    html = re.sub(r', [0-9.]+\); // OUT', f', {round(dur - 0.3, 2)}); // OUT', html)
    n = NARR[lid]
    aud = f'\n    <audio id="a-{lid}" class="clip" src="{n["file"]}" data-start="{extra_tl}" data-duration="{round(n["dur"], 2)}" data-track-index="2" data-has-audio="true" data-hf-media-start-basis="local"></audio>\n'
    html = html.replace("    </div>\n  </div>\n  <script>", "    </div>" + aud + "  </div>\n  <script>", 1)
    path.write_text(html, encoding="utf-8")


durs = {}
n = 1
for sid in ["check", "cost", "hubs"]:
    durs[sid], n = scene(sid, n)

INTRO_VOICE_AT, OUTRO_VOICE_AT = 0.6, 0.5
durs["intro"] = round(INTRO_VOICE_AT + NARR["in1"]["dur"] + 0.9, 2)
durs["outro"] = round(OUTRO_VOICE_AT + NARR["ou1"]["dur"] + 1.6, 2)
title_scene(HERE / "compositions" / "intro.html", "intro", "in1", durs["intro"], INTRO_VOICE_AT)
title_scene(HERE / "compositions" / "outro.html", "outro", "ou1", durs["outro"], OUTRO_VOICE_AT)

# root timeline: scenes back to back
t = 0.0
rows = []
for sid in ["intro", "check", "cost", "hubs", "outro"]:
    rows.append(f'      <div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" data-start="{round(t, 2)}" data-duration="{durs[sid]}" data-track-index="1" data-track-kind="graphics" data-width="1920" data-height="1080"></div>')
    t += durs[sid]
total = round(t, 2)
idx = HERE / "index.html"
s = idx.read_text(encoding="utf-8")
a = s.index('      <div id="intro"'); b = s.index("    </div>\n    <script>")
s = s[:a] + "\n".join(rows) + "\n" + s[b:]
import re
s = re.sub(r'(data-composition-id="main" data-start="0" data-duration=")[^"]*(")', rf'\g<1>{total}\2', s)
idx.write_text(s, encoding="utf-8")
print({k: v for k, v in durs.items()}, "total", total)
