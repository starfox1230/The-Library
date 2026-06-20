from __future__ import annotations

from pathlib import Path
import urllib.request
import zlib

import genanki


OUT_DIR = Path(__file__).resolve().parent
OUT_FILE = OUT_DIR / "speed-streak-v1.23-special-timing-test.apkg"

ANKING_RAW_BASE = (
    "https://raw.githubusercontent.com/AnKing-VIP/AnKing-Note-Types/"
    "master/Note%20Types/AnKingOverhaul"
)
ANKING_FRONT_URL = f"{ANKING_RAW_BASE}/Front%20Template.html"
ANKING_BACK_URL = f"{ANKING_RAW_BASE}/Back%20Template.html"
ANKING_STYLE_URL = f"{ANKING_RAW_BASE}/Styling.css"


def stable_id(text: str) -> int:
    return zlib.crc32(text.encode("utf-8")) & 0x7FFFFFFF


def fetch_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read().decode("utf-8")


def official_anking_templates() -> tuple[str, str, str]:
    front = fetch_text(ANKING_FRONT_URL)
    back = fetch_text(ANKING_BACK_URL)
    css = fetch_text(ANKING_STYLE_URL)
    return front, back, css


DECK = genanki.Deck(
    stable_id("Speed Streak v1.23 Special Timing Test"),
    "Speed Streak Tests::v1.23 Special Timing",
)


COMMON_CSS = """
.card {
  font-family: Arial, sans-serif;
  font-size: 22px;
  text-align: left;
  color: #222;
  background: #fafafa;
}
.sst-test {
  max-width: 720px;
  margin: 0 auto;
  line-height: 1.45;
}
.sst-title {
  font-size: 15px;
  font-weight: 700;
  color: #3d5f9f;
  margin-bottom: 14px;
}
.sst-prompt {
  margin-bottom: 16px;
}
.sst-answer {
  font-weight: 700;
  color: #165c3a;
  margin-top: 12px;
}
.sst-extra {
  color: #555;
  font-size: 16px;
  margin-top: 14px;
}
input[type=text], input[type=search], input:not([type]) {
  font-size: 20px;
  padding: 8px 10px;
  min-width: 260px;
}
"""


NORMAL_MODEL = genanki.Model(
    stable_id("Speed Streak Test Normal"),
    "Speed Streak Test - Normal",
    fields=[
        {"name": "Title"},
        {"name": "Prompt"},
        {"name": "Answer"},
        {"name": "Extra"},
    ],
    templates=[
        {
            "name": "Normal",
            "qfmt": """
<div class="sst-test">
  <div class="sst-title">{{Title}}</div>
  <div class="sst-prompt">{{Prompt}}</div>
</div>
""",
            "afmt": """
{{FrontSide}}
<hr>
<div class="sst-answer">{{Answer}}</div>
<div class="sst-extra">{{Extra}}</div>
""",
        },
    ],
    css=COMMON_CSS,
)


TYPED_MODEL = genanki.Model(
    stable_id("Speed Streak Test Typed Answer"),
    "Speed Streak Test - Typed Answer",
    fields=[
        {"name": "Title"},
        {"name": "Prompt"},
        {"name": "Answer"},
        {"name": "Extra"},
    ],
    templates=[
        {
            "name": "Typed Answer",
            "qfmt": """
<div class="sst-test">
  <div class="sst-title">{{Title}}</div>
  <div class="sst-prompt">{{Prompt}}</div>
  {{type:Answer}}
</div>
""",
            "afmt": """
{{FrontSide}}
<hr>
<div class="sst-answer">Expected answer: {{Answer}}</div>
<div class="sst-extra">{{Extra}}</div>
""",
        },
    ],
    css=COMMON_CSS,
)


def anking_model() -> genanki.Model:
    front, back, css = official_anking_templates()
    return genanki.Model(
        stable_id("Speed Streak Test Official AnKingOverhaul"),
        "Speed Streak Test - Official AnKingOverhaul",
        fields=[
            {"name": "Text"},
            {"name": "Extra"},
            {"name": "Lecture Notes"},
            {"name": "Missed Questions"},
            {"name": "Pathoma"},
            {"name": "Boards and Beyond"},
            {"name": "First Aid"},
            {"name": "Sketchy"},
            {"name": "Sketchy 2"},
            {"name": "Sketchy Extra"},
            {"name": "Picmonic"},
            {"name": "Pixorize"},
            {"name": "Physeo"},
            {"name": "Bootcamp"},
            {"name": "OME"},
            {"name": "Additional Resources"},
            {"name": "One by one"},
        ],
        templates=[
            {
                "name": "Cloze",
                "qfmt": front,
                "afmt": back,
            },
        ],
        css=css,
        model_type=genanki.Model.CLOZE,
    )


def add_note(
    *,
    model: genanki.Model,
    fields: list[str],
    title: str,
    tags: list[str] | None = None,
) -> None:
    DECK.add_note(
        genanki.Note(
            model=model,
            fields=fields,
            tags=tags or [],
            guid=genanki.guid_for("speed-streak-v1.23-special-timing", title),
        )
    )


def add_normal_note(title: str, prompt: str, answer: str, extra: str, tags: list[str] | None = None) -> None:
    add_note(
        model=NORMAL_MODEL,
        fields=[title, prompt, answer, extra],
        title=title,
        tags=tags,
    )


def add_typed_note(title: str, prompt: str, answer: str, extra: str, tags: list[str] | None = None) -> None:
    add_note(
        model=TYPED_MODEL,
        fields=[title, prompt, answer, extra],
        title=title,
        tags=tags,
    )


def add_anking_note(
    model: genanki.Model,
    *,
    title: str,
    text: str,
    extra: str,
    one_by_one: str,
    tags: list[str] | None = None,
) -> None:
    add_note(
        model=model,
        fields=[
            text,
            extra,
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            one_by_one,
        ],
        title=title,
        tags=tags,
    )


def build_deck() -> None:
    official_anking_model = anking_model()

    add_normal_note(
        "01 Normal baseline",
        "Normal baseline card. This should use the ordinary question and answer timers.",
        "Baseline answer",
        "Expected Speed Streak policy: normal.",
        ["speedstreak_test", "sst_normal"],
    )
    add_typed_note(
        "02 Native typed-answer",
        "Type the word glucose into the answer field.",
        "glucose",
        "Expected Speed Streak policy when enabled: typed-answer extra question time or no-timeout.",
        ["speedstreak_test", "sst_typed_answer"],
    )
    add_normal_note(
        "03 Custom tag extra time",
        "This card tests an exact custom tag match. Configure Speed Streak custom tag to speedstreak::extended_time.",
        "Custom tag answer",
        "Expected Speed Streak policy when enabled: custom tag extra time.",
        ["speedstreak_test", "speedstreak::extended_time"],
    )
    add_normal_note(
        "04 Custom tag no-timeout",
        "This card tests a second exact custom tag. Configure Speed Streak custom tag to speedstreak::untimed.",
        "Untimed tag answer",
        "Expected Speed Streak policy when enabled: custom tag no-timeout.",
        ["speedstreak_test", "speedstreak::untimed"],
    )
    add_typed_note(
        "05 Typed-answer plus tag precedence",
        "Type the word insulin. Also try configuring the custom tag to speedstreak::untimed.",
        "insulin",
        "Expected Speed Streak policy: no-timeout should win if custom tag no-timeout is configured.",
        ["speedstreak_test", "sst_typed_answer", "speedstreak::untimed"],
    )
    add_anking_note(
        official_anking_model,
        title="06 Official AnKing one-by-one",
        text=(
            "One-by-one test: {{c1::alpha}} then {{c1::beta}} then {{c1::gamma}}. "
            "Show the answer and use the AnKing Reveal Next control or the N shortcut."
        ),
        extra="Expected Speed Streak policy when enabled: AnKing one-by-one extra answer time or no-timeout.",
        one_by_one="y",
        tags=["speedstreak_test", "sst_anking_one_by_one"],
    )
    add_anking_note(
        official_anking_model,
        title="07 Official AnKing one-by-one plus custom tag",
        text=(
            "Precedence test: {{c1::first reveal}} then {{c1::second reveal}}. "
            "This card also has speedstreak::untimed."
        ),
        extra="Expected Speed Streak policy: no-timeout should win when the custom tag is configured that way.",
        one_by_one="y",
        tags=["speedstreak_test", "sst_anking_one_by_one", "speedstreak::untimed"],
    )

    package = genanki.Package(DECK)
    package.write_to_file(str(OUT_FILE))
    print(f"Built {OUT_FILE}")


if __name__ == "__main__":
    build_deck()
