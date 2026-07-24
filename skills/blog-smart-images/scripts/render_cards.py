#!/usr/bin/env python3
"""render_cards.py — screenshot brand-card frames from an HTML file (Playwright).

Usage:
  python3 render_cards.py --html filled-cards.html --frames hero,og,fig-1 --out raw/
Each frame is an element with that id in the HTML (see templates/card-base.html).
Set PLAYWRIGHT_CHROMIUM if the default executable path differs.
"""
import argparse, asyncio, os
from playwright.async_api import async_playwright

async def run(html, frames, out):
    os.makedirs(out, exist_ok=True)
    exe = os.environ.get("PLAYWRIGHT_CHROMIUM")
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=exe) if exe else await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 2400, "height": 1500})
        await page.goto("file://" + os.path.abspath(html))
        await page.wait_for_timeout(500)
        for fid in frames:
            await page.locator(f"#{fid}").screenshot(path=os.path.join(out, f"{fid}.png"))
            print("rendered", fid)
        await browser.close()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", required=True); ap.add_argument("--frames", required=True)
    ap.add_argument("--out", default="raw")
    a = ap.parse_args()
    asyncio.run(run(a.html, [f.strip() for f in a.frames.split(",") if f.strip()], a.out))
