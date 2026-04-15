from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "apps" / "anki-pocket-knife" / "review_image_overlay_core.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("review_image_overlay_core", MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_extract_image_sources_collects_common_image_attributes():
    module = _load_module()

    html = """
    <div>
      <img src="front-a.png">
      <img data-src="front-b.png">
      <img data-lazy-src="front-c.png">
      <img data-original="front-d.png">
      <img srcset="front-e.png 1x, front-e@2x.png 2x">
    </div>
    """

    assert module.extract_image_sources(html) == [
        "front-a.png",
        "front-b.png",
        "front-c.png",
        "front-d.png",
        "front-e.png",
    ]


def test_merge_image_sources_dedupes_while_preserving_order():
    module = _load_module()

    merged = module.merge_image_sources(
        ["front-a.png", "front-b.png", "front-a.png"],
        ["front-b.png", "back-a.png", "back-b.png"],
    )

    assert merged == [
        "front-a.png",
        "front-b.png",
        "back-a.png",
        "back-b.png",
    ]
