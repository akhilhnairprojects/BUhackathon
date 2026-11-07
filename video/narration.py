"""Narration for the walkthrough: the script, and the voice files made from it.

    python video/narration.py          # writes video/assets/vo/<id>.mp3 and video/assets/narration.json

Voice: Microsoft Edge neural voice (free, no account) through the edge-tts package. record.py reads
narration.json to pace the screen recording, and build_scenes.py places each line on the timeline.
"""
import asyncio
import json
import subprocess
from pathlib import Path

import edge_tts

HERE = Path(__file__).resolve().parent
VO = HERE / "assets" / "vo"
VO.mkdir(parents=True, exist_ok=True)
VOICE = "en-US-AndrewNeural"
RATE = "-6%"

SCRIPT = {
    "intro": [("in1", "This is Trip Risk Checker. Before you book, it tells you the chance that a flight gets you to your meeting an hour late, from a full year of US flights.")],
    "check": [
        ("ck1", "Start on Check a trip. First, choose where you fly from."),
        ("ck2", "Then where you need to be. Any US airport works, not only the ones with a nonstop flight."),
        ("ck3", "Pick your travel date. The day of the week and the month both change the risk."),
        ("ck4", "And choose a departure time."),
        ("ck5", "Every nonstop and same-airline connection is ranked by the chance of arriving an hour late. Under each number, you can read exactly how it was calculated."),
        ("ck6", "The verdict tells you what to book, and how many points safer it is."),
        ("ck7", "Further down: the same route by departure time, and the weather you can expect at both airports in that month."),
        ("ck8", "And whether a stop is worth it: the extra risk, the extra hours, and the fare saving you would need to break even."),
    ],
    "cost": [
        ("co1", "The second page puts a price on that risk."),
        ("co2", "Set what the meeting is worth, and what an hour of your time is worth."),
        ("co3", "If you are staying over, add the nights, the hotel rate and your daily expenses. That spend buys nothing if the meeting is missed, so it counts towards what is at stake."),
        ("co4", "You get the expected cost of the recommended flight, of the riskiest option, and the gap between them: the most a safer fare is worth paying. Each figure shows its own working."),
        ("co5", "Below, what each booking habit costs per trip."),
    ],
    "hubs": [
        ("hb1", "The third page ranks twenty connecting hubs by what happens to one-stop trips through them."),
        ("hb2", "The best and the riskiest hub, then the full table."),
        ("hb3", "The map covers every large and medium airport: disruption rate, adverse-weather days for any month, or winter fragility."),
        ("hb4", "Dot size is departures. Hover any airport for its details."),
    ],
    "outro": [("ou1", "Know the risk before you book. Trip Risk Checker, at trip-risk-checker dot vercel dot app.")],
}


def duration(path: Path) -> float:
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                                capture_output=True, text=True).stdout.strip())


async def main():
    out = {}
    for scene, lines in SCRIPT.items():
        for lid, text in lines:
            mp3 = VO / f"{lid}.mp3"
            for attempt in range(5):   # the service occasionally returns no audio; try again
                try:
                    await edge_tts.Communicate(text, VOICE, rate=RATE).save(str(mp3)); break
                except edge_tts.exceptions.NoAudioReceived:
                    if attempt == 4: raise
                    await asyncio.sleep(2)
            out[lid] = {"scene": scene, "text": text, "file": f"assets/vo/{lid}.mp3", "dur": round(duration(mp3), 2)}
            print(f"{lid:4} {out[lid]['dur']:5.2f}s  {text[:60]}")
    (HERE / "assets" / "narration.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("total speech", round(sum(v["dur"] for v in out.values()), 1), "s")


asyncio.run(main())
