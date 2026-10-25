#!/usr/bin/env python3
"""Rasterize Quiet Harbor's original cottage-and-sprout home-screen icons."""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
COLORS = {"sea": "#173f49", "water": "#64b6ae", "deep": "#285e58", "grass": "#8db56d", "grass_light": "#b0d48b", "roof": "#db855e", "roof_light": "#f3b078", "wall": "#fff0d5", "shadow": "#c8ac89", "ink": "#26494a", "soil": "#9c6d49"}


def draw(size: int, path: Path, maskable: bool = False) -> None:
    scale = 4
    s = size * scale
    im = Image.new("RGB", (s, s), COLORS["sea"])
    d = ImageDraw.Draw(im)
    def xy(points): return [(int(x * s), int(y * s)) for x, y in points]
    # a calm crescent of water and soft light, with the cottage kept in the safe zone
    d.ellipse((s*.06, s*.08, s*.94, s*.94), fill="#204f55")
    d.ellipse((s*.13, s*.13, s*.87, s*.87), fill="#285e60")
    d.polygon(xy([(.15,.68),(.32,.51),(.52,.47),(.79,.58),(.88,.72),(.69,.83),(.36,.84)]), fill=COLORS["grass"])
    d.polygon(xy([(.15,.68),(.36,.79),(.69,.78),(.88,.70),(.79,.82),(.38,.88),(.16,.77)]), fill=COLORS["deep"])
    d.polygon(xy([(.34,.53),(.52,.39),(.70,.53),(.52,.66)]), fill=COLORS["roof"])
    d.polygon(xy([(.52,.39),(.70,.53),(.64,.57),(.52,.48)]), fill=COLORS["roof_light"])
    d.polygon(xy([(.39,.54),(.64,.54),(.64,.72),(.39,.70)]), fill=COLORS["wall"])
    d.polygon(xy([(.64,.54),(.70,.53),(.70,.68),(.64,.72)]), fill=COLORS["shadow"])
    d.rectangle((s*.47,s*.60,s*.54,s*.71), fill=COLORS["ink"])
    d.rectangle((s*.42,s*.57,s*.46,s*.61), fill=COLORS["water"])
    # seedling, with an intentionally simple crisp silhouette at 32px
    d.line(xy([(.28,.63),(.29,.48)]), fill=COLORS["deep"], width=max(2,round(s*.018)))
    d.ellipse((s*.18,s*.43,s*.29,s*.51), fill=COLORS["grass_light"])
    d.ellipse((s*.27,s*.39,s*.37,s*.47), fill=COLORS["grass"])
    d.ellipse((s*.21,s*.73,s*.32,s*.78), fill=COLORS["soil"])
    im.resize((size,size), Image.Resampling.LANCZOS).save(path, optimize=True)


def main() -> None:
    icon_dir = ROOT / "icons"; icon_dir.mkdir(exist_ok=True)
    for name, size in [("apple-touch-icon.png", 180), ("icon-192.png", 192), ("icon-512.png", 512), ("icon-maskable-512.png", 512), ("favicon-32.png", 32)]:
        draw(size, icon_dir / name, name.startswith("icon-maskable"))
    print("Generated 180, 192, 512, maskable 512 and favicon 32 icons.")


if __name__ == "__main__": main()
