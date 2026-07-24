#!/usr/bin/env python3
"""postprocess.py — export a winning candidate to web-ready files (needs Pillow).

Usage:
  python3 postprocess.py --in raw/hero.png --dir images/my-post --name hero-my-post [--og] [--width 1600]
Outputs <dir>/<name>.webp (+ .jpg fallback); with --og also <name>-1200x630.jpg.
"""
import argparse, os
from PIL import Image, ImageEnhance

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True); ap.add_argument("--dir", required=True)
    ap.add_argument("--name", required=True); ap.add_argument("--og", action="store_true")
    ap.add_argument("--width", type=int, default=1600)
    a = ap.parse_args()
    os.makedirs(a.dir, exist_ok=True)
    im = Image.open(a.src).convert("RGB")
    im = ImageEnhance.Color(im).enhance(1.04)
    im = ImageEnhance.Contrast(im).enhance(1.02)
    w = min(a.width, im.width); h = round(im.height * w / im.width)
    web = im.resize((w, h), Image.LANCZOS)
    wp = os.path.join(a.dir, a.name + ".webp"); jp = os.path.join(a.dir, a.name + ".jpg")
    q = 82
    web.save(wp, "WEBP", quality=q, method=6)
    while os.path.getsize(wp) > 150 * 1024 and q > 55:      # size budget
        q -= 6; web.save(wp, "WEBP", quality=q, method=6)
    web.save(jp, "JPEG", quality=max(q + 4, 78), optimize=True, progressive=True)
    print(f"{wp} ({os.path.getsize(wp)//1024} KB), {jp} ({os.path.getsize(jp)//1024} KB)")
    if a.og:
        tw, th = 1200, 630
        scale = max(tw / im.width, th / im.height)
        big = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
        x = (big.width - tw) // 2; y = (big.height - th) // 2
        og = big.crop((x, y, x + tw, y + th))
        op = os.path.join(a.dir, a.name + "-1200x630.jpg")
        og.save(op, "JPEG", quality=88, optimize=True)
        print(f"{op} ({os.path.getsize(op)//1024} KB)")

if __name__ == "__main__":
    main()
