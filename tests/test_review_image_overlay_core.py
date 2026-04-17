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


def test_build_overlay_entries_from_sources_creates_deduped_single_layer_entries():
    module = _load_module()

    entries = module.build_overlay_entries_from_sources(
        ["front-a.png", "front-b.png", "front-a.png", ""]
    )

    assert entries == [
        {"key": "image::front-a.png", "layers": ["front-a.png"]},
        {"key": "image::front-b.png", "layers": ["front-b.png"]},
    ]


def test_build_image_occlusion_entry_uses_standard_field_names():
    module = _load_module()

    entry = module.build_image_occlusion_entry(
        {
            "Image": '<img src="base.png">',
            "Question Mask": '<img src="question-mask.png">',
            "Answer Mask": '<img src="answer-mask.png">',
        },
        answer_side=False,
    )

    assert entry == {
        "key": "image-occlusion::question::base.png::question-mask.png",
        "layers": ["base.png", "question-mask.png"],
    }


def test_build_image_occlusion_entry_supports_qmask_and_amask_aliases():
    module = _load_module()

    answer_entry = module.build_image_occlusion_entry(
        {
            "Image": '<img src="base.png">',
            "QMask": '<img src="question-mask.png">',
            "AMask": '<img src="answer-mask.png">',
        },
        answer_side=True,
    )

    assert answer_entry == {
        "key": "image-occlusion::answer::base.png::answer-mask.png",
        "layers": ["base.png", "answer-mask.png"],
    }
