from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"
OUTPUT = ROOT / "web_assets.py"
ASSET_NAMES = ("overlay.css", "overlay.js", "card_timer.css", "card_timer.js")


def main() -> None:
    assets: dict[str, str] = {}
    for name in ASSET_NAMES:
        asset_path = WEB_DIR / name
        if not asset_path.exists():
            raise SystemExit(f"Missing required web asset: {asset_path}")
        assets[name] = asset_path.read_text(encoding="utf-8")

    lines = [
        "from __future__ import annotations",
        "",
        "# Auto-generated fallback copies of required web assets for packaging resilience.",
        "WEB_ASSETS = {",
    ]
    for name in ASSET_NAMES:
        lines.append(f"    {name!r}: {assets[name]!r},")
    lines.extend(("}", ""))
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
