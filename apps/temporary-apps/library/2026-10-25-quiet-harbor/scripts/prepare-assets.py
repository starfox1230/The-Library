#!/usr/bin/env python3
"""Rebuild local Kenney atlas files, licenses, source hashes and contact sheets."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from datetime import date
from io import BytesIO
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PACKS = {
    "landscape": {"url": "https://kenney.nl/media/pages/assets/isometric-tiles-landscape/37eb18a8d1-1677695072/kenney_isometric-landscape.zip", "sha256": "18fa4fb22fa18bd4230e2422bc4123c986123c53966846b5a5bc219b331e7d3e", "xml": "landscapeTiles_sheet.xml", "sheet": "landscapeTiles_sheet.png"},
    "buildings": {"url": "https://kenney.nl/media/pages/assets/isometric-tiles-buildings/cfcdb066e1-1677694983/kenney_isometric-buildings.zip", "sha256": "0894214e3b604f3eef53b9fa633340ba4617e24053a6178fa81dab6bac3d6d5e", "xml": "buildingTiles_sheet.xml", "sheet": "buildingTiles_sheet.png"},
    "city": {"url": "https://kenney.nl/media/pages/assets/isometric-tiles-city/7026b2670a-1677695025/kenney_isometric-city.zip", "sha256": "bea03c38f340af6df14949cc7ca23ac68f30d087d4867350424f08b697a7e01c", "xml": "cityTiles_sheet.xml", "sheet": "cityTiles_sheet.png"},
}
LICENSE_DIR = ROOT / "assets" / "licenses"
SPRITE_DIR = ROOT / "assets" / "sprites"
SOURCE_URLS = {"landscape": "https://kenney.nl/assets/isometric-tiles-landscape", "buildings": "https://kenney.nl/assets/isometric-tiles-buildings", "city": "https://kenney.nl/assets/isometric-tiles-city"}
SELECTED = {
    "landscape": [f"landscapeTiles_{i:03}" for i in (10, 15, 16, 22, 67, 75)],
    "buildings": [f"buildingTiles_{i:03}" for i in (1, 3, 4, 9, 10, 12, 14, 17, 18, 20, 25, 26, 27, 30, 32, 33, 34, 40, 41, 46, 92, 93)],
    "city": [f"cityTiles_{i:03}" for i in (36, 43, 44)],
}


def main() -> None:
    catalog = {"license": "CC0-1.0", "attribution": "Game assets by Kenney (kenney.nl), CC0; attribution is appreciated but not required.", "packs": {}, "roles": {"ground": SELECTED["landscape"], "homes": SELECTED["buildings"], "civic": SELECTED["city"]}}
    sources = {"preparedAt": date.today().isoformat(), "license": "CC0-1.0", "attribution": "Kenney (kenney.nl)", "packs": {}}
    SPRITE_DIR.mkdir(parents=True, exist_ok=True)
    for name, pack in PACKS.items():
        archive = urllib.request.urlopen(pack["url"], timeout=60).read()
        digest = hashlib.sha256(archive).hexdigest()
        if digest != pack["sha256"]:
            raise SystemExit(f"{name} archive SHA-256 changed ({digest}); inspect the source before accepting an update.")
        with zipfile.ZipFile(BytesIO(archive)) as z:
            root = ET.fromstring(z.read("Spritesheet/" + pack["xml"]))
            indexed = {}
            for item in root.findall("SubTexture"):
                a = item.attrib
                indexed[Path(a["name"]).stem] = {k: int(a[k]) for k in ("x", "y", "width", "height")}
            sheet = Image.open(BytesIO(z.read("Spritesheet/" + pack["sheet"]))).convert("RGBA")
            frames = {}
            for filename in SELECTED[name]:
                rect = indexed[filename]
                output_name = f"{filename}.png"
                tile = sheet.crop((rect["x"], rect["y"], rect["x"] + rect["width"], rect["y"] + rect["height"]))
                tile.save(SPRITE_DIR / output_name, optimize=True)
                frames[filename] = {"src": f"./assets/sprites/{output_name}", "width": rect["width"], "height": rect["height"]}
            (LICENSE_DIR / f"kenney-{name}.txt").write_bytes(z.read("License.txt"))
        catalog["packs"][name] = {"page": SOURCE_URLS[name], "archiveSha256": digest, "frames": frames}
        sources["packs"][name] = {"page": SOURCE_URLS[name], "downloadUrl": pack["url"], "archiveSha256": digest, "licenseFile": f"./assets/licenses/kenney-{name}.txt", "selectedSprites": [f"{x}.png" for x in SELECTED[name]]}
    (ROOT / "assets" / "catalog.json").write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    (ROOT / "assets" / "sources.json").write_text(json.dumps(sources, indent=2) + "\n", encoding="utf-8")
    print("Prepared 31 selected CC0 sprites, source hashes, licenses and a semantic catalog.")


if __name__ == "__main__":
    main()
