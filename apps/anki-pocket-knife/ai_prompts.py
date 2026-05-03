from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

from .settings import get_setting


_CLOZE_TOKEN_RE = re.compile(r"\{+\s*(c\d+::.*?)(?<!\})\}+", re.IGNORECASE | re.DOTALL)


def fix_cloze_formatting(card: str) -> str:
    text = str(card or "").strip()

    def replace(match: re.Match[str]) -> str:
        inner = match.group(1).strip()
        return "{{" + inner + "}}"

    text = _CLOZE_TOKEN_RE.sub(replace, text)
    text = re.sub(r"\{\{\{+(c\d+::.*?)\}\}\}+", r"{{\1}}", text, flags=re.IGNORECASE | re.DOTALL)
    return text.strip()


def normalize_card_text_for_comparison(card: str) -> str:
    text = fix_cloze_formatting(card)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)
    return text.strip().casefold()


def _api_key() -> str:
    import os

    saved_key = str(get_setting("ai_tools_api_key") or "").strip()
    return (saved_key or os.environ.get("OPENAI_API_KEY") or "").strip()


def has_api_key() -> bool:
    return bool(_api_key())


def api_key_source() -> str:
    import os

    if str(get_setting("ai_tools_api_key") or "").strip():
        return "Pocket Knife saved setting"
    if (os.environ.get("OPENAI_API_KEY") or "").strip():
        return "OPENAI_API_KEY environment variable"
    return "not configured"


def _model(default: str = "gpt-4.1") -> str:
    return str(get_setting("ai_tools_model") or default).strip() or default


def _chat_completion(prompt: str, *, model: str | None = None, temperature: float = 0.4, max_tokens: int = 900) -> str:
    key = _api_key()
    if not key:
        raise ValueError("OpenAI API key is not configured. Add it in the Pocket Knife launcher or set OPENAI_API_KEY.")

    payload = {
        "model": model or _model(),
        "messages": [
            {"role": "system", "content": "You are a careful Anki cloze-card editor."},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=70) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI request failed: {detail[:500]}") from exc

    try:
        return str(data["choices"][0]["message"]["content"] or "").strip()
    except Exception as exc:
        raise RuntimeError("OpenAI returned an unexpected response.") from exc


def make_card_briefer(card_text: str) -> str:
    if not card_text.strip():
        raise ValueError("Card text is empty.")
    prompt = f"""
You are refining an existing Anki cloze-deletion card that the user feels is too wordy.
Task: Rewrite the card to be as brief and clear as possible while preserving every key fact and keeping the same cloze numbering.
Rules:
- Keep all important information but use fewer words.
- Keep the same cloze numbers so the card still works in Anki.
- Ensure every cloze uses double curly braces on both sides, such as {{c1::answer}}.
- Preserve useful HTML such as <br> tags and image references.
- Output ONLY the revised card text with no quotes, markdown, or JSON.

Original card text:
{card_text.strip()}
"""
    return fix_cloze_formatting(_chat_completion(prompt, temperature=0.5, max_tokens=800))


def make_card_even_more_concise(original_text: str, concise_text: str) -> str:
    if not original_text.strip() or not concise_text.strip():
        raise ValueError("Both original and concise card text are required.")
    prompt = f"""
You are refining an existing cloze-deletion Anki card that has already been rewritten once but is still too wordy.
Goal: deliver a shorter, simpler rewrite while preserving essential facts, cloze numbering, and HTML formatting.
Rules:
- The new version must be strictly shorter than the first concise attempt.
- Drop non-essential details if they do not change the core fact.
- Keep the same cloze numbers and valid HTML.
- Ensure every cloze uses double curly braces on both sides.
- Output ONLY the card text.

Original card:
{original_text.strip()}

First concise attempt:
{concise_text.strip()}
"""
    return fix_cloze_formatting(_chat_completion(prompt, temperature=0.4, max_tokens=800))


def make_card_unambiguous(card_text: str) -> str:
    if not card_text.strip():
        raise ValueError("Card text is empty.")
    prompt = f"""
You are refining an existing Anki cloze-deletion card to fix mind-reading ambiguity.
Goal: Rewrite the card so the learner knows exactly what is being asked before revealing the cloze.
Rules:
- If a question/answer format with <br><br> is clearer, use it.
- Add enough category, mechanism, scenario, threshold, or relationship context to make the cloze uniquely determined.
- Preserve the answer text inside clozes unless a tiny grammatical change is necessary.
- Keep the same cloze numbering when possible.
- Ensure every cloze uses double curly braces on both sides.
- Output ONLY the revised card text.

Original card:
{card_text.strip()}
"""
    return fix_cloze_formatting(_chat_completion(prompt, temperature=0.4, max_tokens=800))


def convert_to_sentence(card_text: str) -> str:
    if not card_text.strip():
        raise ValueError("Card text is empty.")
    prompt = f"""
Convert this question-and-answer style Anki card into one declarative sentence-completion card.
Rules:
- The text currently inside {{c1::...}} must remain inside {{c1::...}}.
- Identify the main term or concept being asked about and wrap it in {{c2::...}} when natural.
- Remove question marks and unnecessary <br> tags.
- Keep valid double-brace cloze syntax.
- Output ONLY the new card text.

Current card:
{card_text.strip()}
"""
    return fix_cloze_formatting(_chat_completion(prompt, model=_model("gpt-4o"), temperature=0.3, max_tokens=800))


def make_contrasting_card(card_text: str) -> str:
    if not card_text.strip():
        raise ValueError("Card text is empty.")
    prompt = f"""
Create ONE additional Anki cloze-deletion card that pairs with the existing card by testing the contrasting, opposite, or complementary side of the same fact.
Rules:
- Keep the same topic but test the counterpart fact instead of restating the original.
- Preserve the original card's wording pattern and format when natural.
- Mirror the original cloze pattern when natural.
- Keep the new card self-contained and unambiguous.
- Do not invent unsupported facts.
- Start cloze numbering at c1 in the new card.
- Output ONLY the new card text.

Original card:
{card_text.strip()}
"""
    suggestion = fix_cloze_formatting(_chat_completion(prompt, temperature=0.4, max_tokens=900))
    if normalize_card_text_for_comparison(suggestion) == normalize_card_text_for_comparison(card_text):
        raise ValueError("Could not generate a distinct contrasting card.")
    return suggestion


def split_card_into_multiple(card_text: str, num_cards: int = 2) -> list[str]:
    if not card_text.strip():
        raise ValueError("Card text is empty.")
    if num_cards < 2 or num_cards > 4:
        raise ValueError("Card count must be between 2 and 4.")
    prompt = f"""
Split this cloze-deletion Anki card into exactly {num_cards} separate, easy-to-study cards.
Rules:
- Return exactly {num_cards} cards.
- Use concise language and one simple fact per card.
- Each card must be self-contained and unambiguous.
- Each card starts its own cloze numbering at c1.
- Keep valid double-brace cloze syntax.
- Output ONLY a JSON array of {num_cards} strings.

Original card:
\"\"\"{card_text.strip()}\"\"\"
"""
    raw = _chat_completion(prompt, temperature=0.4, max_tokens=1200)
    try:
        cards = json.loads(raw)
    except Exception as exc:
        raise ValueError("Invalid split-card response from AI.") from exc
    if not isinstance(cards, list):
        raise ValueError("Invalid split-card response from AI.")
    cleaned = [fix_cloze_formatting(card) for card in cards if isinstance(card, str) and card.strip()]
    if len(cleaned) != num_cards:
        raise ValueError("AI returned the wrong number of cards.")
    return cleaned


def make_cards_uniform(cards: list[str]) -> list[str]:
    cleaned = [str(card).strip() for card in cards if str(card or "").strip()]
    if len(cleaned) < 2:
        raise ValueError("At least two cards are required.")
    numbered = "\n\n".join(f'{idx}. """{card}"""' for idx, card in enumerate(cleaned, start=1))
    prompt = f"""
Rewrite this small set of related Anki cloze-deletion cards so they become highly uniform and parallel.
Rules:
- Return exactly {len(cleaned)} rewritten cards, in the same order.
- Preserve each original fact.
- Use the same sentence or question template where possible.
- Keep each card self-contained and unambiguous.
- Preserve cloze numbering when reasonably possible.
- Keep valid double-brace cloze syntax.
- Output ONLY a JSON array of {len(cleaned)} strings.

Original cards:
{numbered}
"""
    raw = _chat_completion(prompt, temperature=0.4, max_tokens=2000)
    try:
        rewritten = json.loads(raw)
    except Exception as exc:
        raise ValueError("Invalid uniform-card response from AI.") from exc
    if not isinstance(rewritten, list):
        raise ValueError("Invalid uniform-card response from AI.")
    cleaned_rewrites = [fix_cloze_formatting(card) for card in rewritten if isinstance(card, str) and card.strip()]
    if len(cleaned_rewrites) != len(cleaned):
        raise ValueError("AI returned the wrong number of cards.")
    return cleaned_rewrites


def spellcheck_card_text(card_text: str) -> str:
    if not card_text.strip():
        raise ValueError("Card text is empty.")
    prompt = f"""
Correct spelling, grammar, capitalization, and punctuation in this Anki card text.

Rules:
- Preserve the meaning.
- Preserve Anki cloze syntax exactly, including cloze numbers and double braces.
- Preserve HTML tags and media references.
- Preserve intentional <br> separators, but remove or replace likely unwanted page breaks with a space when a <br>, line break, or paragraph break interrupts the middle of a sentence.
- Do not make the card briefer, more detailed, more unambiguous, or stylistically different unless needed for correctness.
- Output ONLY the corrected card text. No quotes, markdown, or JSON.

Card text:
{card_text.strip()}
"""
    return fix_cloze_formatting(_chat_completion(prompt, temperature=0.1, max_tokens=1200))
