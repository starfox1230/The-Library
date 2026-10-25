#!/usr/bin/env python3
"""Build reviewable, labeled Kenney sprite sheets from the curated semantic catalog."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT / "assets/catalog.json").read_text(encoding="utf-8"))
OUT = ROOT / "assets/previews"
OUT.mkdir(exist_ok=True)


def main():
    for pack, data in CATALOG["packs"].items():
        frames = list(data["frames"].items())
        for start in range(0, len(frames), 48):
            subset = frames[start:start + 48]
            board = Image.new("RGB", (960, ((len(subset) + 5) // 6) * 120), "#f0ede4")
            draw = ImageDraw.Draw(board)
            for index, (name, item) in enumerate(subset):
                image = Image.open(ROOT / item["src"].removeprefix("./")).convert("RGBA")
                image.thumbnail((146, 86), Image.Resampling.LANCZOS)
                x, y = (index % 6) * 160, (index // 6) * 120
                board.paste(image, (x + (160 - image.width) // 2, y + (90 - image.height) // 2), image)
                draw.text((x + 5, y + 94), name, fill="#243e38")
            board.save(OUT / f"{pack}-{start // 48 + 1:02}.jpg", quality=92, optimize=True)
    print(f"Contact sheets written to {OUT}")


if __name__ == "__main__": main()
