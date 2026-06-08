from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(r"G:\My Drive\0. Radiology\Physics")
SOURCE_JSON = PROJECT_ROOT / "exports" / "quiz_ready.json"
APP_ROOT = Path(__file__).resolve().parents[1] / "apps" / "radiology-physics-review"
DATA_DIR = APP_ROOT / "data"
ASSET_DIR = APP_ROOT / "assets"


def infer_block(question_id: str) -> str:
    match = re.search(r"b(?:lock)?[_-]?(\d+)", question_id, re.IGNORECASE)
    if match:
        return f"Block {int(match.group(1))}"
    return "Block 1"


def infer_question_number(question_id: str) -> int | None:
    numbers = re.findall(r"\d+", question_id)
    return int(numbers[-1]) if numbers else None


def normalize_block(value: object, question_id: str) -> str:
    if isinstance(value, int):
        return f"Block {value}"
    if isinstance(value, str) and value.strip().isdigit():
        return f"Block {int(value)}"
    if value:
        return str(value)
    return infer_block(question_id)


def sync() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ASSET_DIR.mkdir(parents=True, exist_ok=True)

    with SOURCE_JSON.open("r", encoding="utf-8") as handle:
        questions = json.load(handle)

    copied_images = 0
    for item in questions:
        item["block"] = normalize_block(item.get("block") or item.get("block_id"), item.get("id", ""))
        item["question_number"] = item.get("question_number") or infer_question_number(item.get("id", ""))
        rewritten_images = []
        for image_path in item.get("images", []):
            source = PROJECT_ROOT / image_path
            destination = ASSET_DIR / image_path
            if source.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
                copied_images += 1
                rewritten_images.append(("assets" / Path(image_path)).as_posix())
            else:
                rewritten_images.append(image_path.replace("\\", "/"))
        item["images"] = rewritten_images

    output_json = DATA_DIR / "quiz_ready.json"
    with output_json.open("w", encoding="utf-8") as handle:
        json.dump(questions, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    build_info = {
        "source": str(SOURCE_JSON),
        "synced_at": datetime.now().isoformat(timespec="seconds"),
        "question_count": len(questions),
        "copied_images": copied_images,
    }
    with (DATA_DIR / "build_info.json").open("w", encoding="utf-8") as handle:
        json.dump(build_info, handle, indent=2)
        handle.write("\n")

    print(f"Synced {len(questions)} questions and {copied_images} images.")
    print(output_json)


if __name__ == "__main__":
    sync()
