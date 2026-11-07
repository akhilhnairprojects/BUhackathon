"""Full-resolution screenshots of the running Streamlit app (localhost:8501) for the pitch deck.

    python deck/build/shoot_app.py
"""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parents[2] / "outputs" / "figures"
TABS = ["Trip Risk Checker", "Policy Simulator", "Hubs & Airports"]

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
    pg.goto("http://localhost:8080/#check", wait_until="networkidle")
    time.sleep(6)
    for i, t in enumerate(["check", "simulate", "hubs"], 1):
        pg.goto(f"http://localhost:8080/#{t}", wait_until="networkidle")
        time.sleep(6)
        pg.mouse.wheel(0, -5000); time.sleep(1)
        pg.screenshot(path=str(OUT / f"app_tab{i}.png"), full_page=False)
        pg.screenshot(path=str(OUT / f"app_tab{i}_full.png"), full_page=True)
        print("saved", f"app_tab{i}.png")
    b.close()
