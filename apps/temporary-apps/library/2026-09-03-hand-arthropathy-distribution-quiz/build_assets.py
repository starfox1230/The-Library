"""Build the blank hand radiograph and site overlays from the supplied variants.

The source images are the six labeled distribution diagrams supplied for this app.
The blue pixels are treated as annotations; the grayscale image is recovered from
the pixels that remain unannotated in the other variants.
"""

from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
SOURCE_FILES = [
    "source-oa.png",
    "source-erosive-oa.png",
    "source-ra.png",
    "source-psa.png",
    "source-cppd.png",
    "source-gout.png",
]

REGIONS = {
    "dip": (244, 42, 486, 137),
    "pip": (244, 132, 486, 260),
    "thumb-ip": (112, 230, 216, 333),
    "mcp": (252, 244, 484, 357),
    "thumb-mcp": (148, 344, 239, 431),
    "thumb-cmc": (221, 431, 322, 503),
    "triscaphe": (286, 454, 385, 543),
    "radiocarpal": (342, 486, 448, 592),
    "distal-radioulnar": (381, 525, 472, 614),
}


def blue_mask(image: np.ndarray) -> np.ndarray:
    red, green, blue = image[..., 0], image[..., 1], image[..., 2]
    return (
        (blue > 55)
        & ((blue - red) > 5)
        & ((blue - green) > 2)
    )


def write_png(path: Path, image: np.ndarray) -> None:
    Image.fromarray(np.clip(image, 0, 255).astype(np.uint8), "RGBA" if image.shape[-1] == 4 else "RGB").save(path)


def build_blank(images: list[np.ndarray], masks: list[np.ndarray]) -> np.ndarray:
    stack = np.stack(images)
    valid = ~np.stack(masks)
    clean = np.median(stack, axis=0).astype(np.float32)
    for y in range(stack.shape[1]):
        for x in range(stack.shape[2]):
            candidates = stack[:, y, x, :][valid[:, y, x]]
            if len(candidates):
                clean[y, x] = np.median(candidates, axis=0)

    # The labels occupy the otherwise empty upper-left black panel. Reconstruct
    # that panel with row-wise background tones, preserving its subtle gradient.
    for y in range(0, 108):
        left_tone = np.median(clean[y, 0:20], axis=0)
        panel_tone = np.median(clean[y, 220:250], axis=0)
        clean[y, 0:108] = left_tone
        clean[y, 108:250] = panel_tone

    # The credit block is over the dark right margin. Fill it from the adjacent
    # dark margin so no identifying text remains in the quiz image.
    clean[545:, 480:] = np.array([15, 15, 15], dtype=np.uint8)
    return clean.astype(np.uint8)


def build_overlays(masks: list[np.ndarray]) -> None:
    union = np.logical_or.reduce(masks)
    height, width = union.shape
    for slug, (x1, y1, x2, y2) in REGIONS.items():
        site = np.zeros((height, width, 4), dtype=np.uint8)
        region = union.copy()
        region[:y1] = False
        region[y2:] = False
        region[:, :x1] = False
        region[:, x2:] = False
        site[region, 0] = 43
        site[region, 1] = 135
        site[region, 2] = 235
        site[region, 3] = 172
        write_png(ASSETS / f"site-{slug}.png", site)


def main() -> None:
    images = [np.array(Image.open(ASSETS / name).convert("RGB")) for name in SOURCE_FILES]
    if len({image.shape for image in images}) != 1:
        raise SystemExit("Source images do not share dimensions")
    masks = [blue_mask(image) for image in images]
    write_png(ASSETS / "blank-hand.png", build_blank(images, masks))
    build_overlays(masks)
    print(f"Built blank-hand.png and {len(REGIONS)} site overlays from {len(images)} source diagrams.")


if __name__ == "__main__":
    main()
