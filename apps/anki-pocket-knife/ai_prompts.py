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
Context: This is a Cloze deletion Anki card where clozes look like {{{{c1::answer}}}} and the final output must remain valid cloze HTML.
Behavior requirements:
- Keep all important information but use fewer words.
- Keep the same cloze numbers so the card still works in Anki.
- Ensure every cloze uses double curly braces on both sides (e.g., {{{{c1::answer}}}}). A single brace on either side is invalid.
- Preserve useful HTML such as <br> tags and image references.
- Do not add hints, commentary, or formatting outside the card itself.
- Output ONLY the revised card text with no quotes, no markdown, and no JSON.

Original card text:
{card_text.strip()}
"""
    return fix_cloze_formatting(_chat_completion(prompt, temperature=0.5, max_tokens=800))


def make_card_even_more_concise(original_text: str, concise_text: str) -> str:
    if not original_text.strip() or not concise_text.strip():
        raise ValueError("Both original and concise card text are required.")
    prompt = f"""
You are refining an existing cloze-deletion Anki card that has already been rewritten once but is still too wordy.
Goal: deliver a shorter, simpler rewrite while preserving the essential facts, the cloze numbering, and HTML formatting so it works with our system.

Rules:
- The new version must be strictly shorter (fewer characters) than the "First concise attempt"; never add filler words.
- You may drop non-essential or adjunct details if they do not change the core fact the learner must recall.
- Prefer simpler phrasing over dense wording. If two facts compete, keep the critical one and omit optional context.
- Keep the same cloze numbers and valid HTML (including <br> tags and image references).
- Ensure every cloze uses double curly braces on both sides (e.g., {{{{c1::answer}}}}). Single braces on either side are invalid.
- Do not add hints, notes, or commentary; output only the card text itself.
- Output ONLY the revised card text. No markdown, quotes, or JSON.

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
You are refining an existing Anki cloze-deletion card to fix "Mind-Reading" ambiguity.

Goal: Rewrite the card so the user knows exactly what is being asked before revealing the cloze.

Rules:
1. Allow Format Change: If the card is a vague sentence (e.g., "In X, Y is {{{{c1::Z}}}}"), convert it to a Question/Answer format using <br><br> if that makes it clearer.
   - Example: "How does X affect Y?<br><br>{{{{c1::It increases Z}}}}"
2. Explicit Relationships: Ensure the text preceding the cloze defines the category (Mechanism, Function, Side Effect, Threshold).
   - Bad: "Mitochondria {{{{c1::make ATP}}}}."
   - Good: "The primary function of mitochondria is to {{{{c1::make ATP}}}}."
3. Preserve Answers: Do not change the text inside the {{{{c1::...}}}} unless absolutely necessary for grammar. Keep the same cloze numbering.
4. Context: If the fact is only true in a specific scenario (e.g., specific disease or age group), add that context only if it is already supported by the card text. Do not invent clinical qualifiers or facts.
5. Preserve useful HTML such as image references.
6. Cloze Formatting: Ensure every cloze uses double curly braces on both sides (e.g., {{{{c1::answer}}}}); never output single braces.

Bad Input: "In competitive inhibition, Vmax {{{{c1::remains unchanged}}}}."
Good Output: "How does competitive inhibition affect Vmax?<br><br>{{{{c1::Remains unchanged}}}}"

Output ONLY the revised card text. No quotes, no markdown.

Original card:
{card_text.strip()}
"""
    return fix_cloze_formatting(_chat_completion(prompt, temperature=0.4, max_tokens=800))


def convert_to_sentence(card_text: str) -> str:
    if not card_text.strip():
        raise ValueError("Card text is empty.")
    prompt = f"""
You are converting a "Question & Answer" style Anki card into a single "Sentence Completion" style card.

Goal: Transform the question and answer into one declarative sentence.

Rules:
1. The text currently inside {{{{c1::...}}}} must remain {{{{c1::...}}}}.
2. Structure the sentence so the {{{{c1::...}}}} content acts as the subject (appearing early in the sentence) if natural.
3. Identify the main term, name, or concept being asked about in the original question and wrap it in {{{{c2::...}}}}.
4. Remove all <br> tags and question marks, except preserve image-reference HTML if present.
5. Ensure the final sentence is grammatically correct.
6. Every cloze must use two curly braces on both sides (e.g., {{{{c1::answer}}}}). Do not output single braces; double-check this before finalizing.
7. Output ONLY the new card text. No quotes, no markdown.

Example:
Input:
What are the three main divisions of the Hebrew Bible that give the name Tanakh?<br><br>{{{{c1::Torah, Nevi'im, and Ketuvim}}}}

Output:
{{{{c1::Torah, Nevi'im, and Ketuvim}}}} are the three main divisions of the Hebrew Bible that give the name {{{{c2::Tanakh}}}}.

Current Card to Convert:
{card_text.strip()}
"""
    return fix_cloze_formatting(_chat_completion(prompt, model=_model("gpt-4o"), temperature=0.3, max_tokens=800))


def make_contrasting_card(card_text: str) -> str:
    if not card_text.strip():
        raise ValueError("Card text is empty.")
    prompt = f"""
You are creating ONE additional Anki cloze-deletion card that pairs with an existing card by testing the contrasting, opposite, or complementary side of the same fact.

Goal:
- Return a single companion card that helps the learner study the other side of the same idea.
- The new card should feel like a matched pair with the original card.

Rules:
1. Keep the same topic as the original card, but test the contrasting or counterpart fact instead of restating the same fact.
2. Preserve the original card's wording pattern, sentence structure, and overall format whenever possible.
   - If the original card is a sentence, keep the companion as a sentence.
   - If the original card uses question/answer format with <br><br>, keep that format if it still fits.
3. Mirror the original cloze pattern when natural.
   - If the original card has one cloze, prefer one cloze.
   - If the original card has multiple parallel clozes, preserve that pattern when it still makes sense.
   - If matching the exact cloze count would make the new card awkward or unclear, prioritize clarity.
4. Keep the new card self-contained and unambiguous on its own.
5. Do not invent unsupported facts. Use the clearest, most standard contrasting or counterpart fact that naturally matches the original.
6. Keep valid cloze HTML and ensure every cloze uses exactly two curly braces on both sides (for example, {{{{c1::answer}}}}).
7. In the new card, start cloze numbering at c1 unless more than one cloze is genuinely needed inside that one card.
8. Output ONLY the new card text. No commentary, bullets, markdown, quotes, or JSON.

Example 1:
Original:
Turning the knob on the {{{{c1::right}}}} of the thermostat will {{{{c2::increase}}}} the temperature.

Good companion:
Turning the knob on the {{{{c1::left}}}} of the thermostat will {{{{c2::decrease}}}} the temperature.

Example 2:
Original:
Which heart chamber pumps blood into the systemic circulation?<br><br>{{{{c1::Left ventricle}}}}

Good companion:
Which heart chamber pumps blood into the pulmonary circulation?<br><br>{{{{c1::Right ventricle}}}}

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
You are simplifying a cloze-deletion Anki card by splitting it into {num_cards} separate, easy-to-study cards.

Rules:
- Return exactly {num_cards} cards.
- Use concise language: one simple fact per card.
- Each card must be fully self-contained and unambiguous on its own. Do not assume other cards provide context; include enough subject detail so the answer is clear even when the blank is hidden.
- Keep valid cloze HTML. Each card should start its own cloze numbering at c1 (use c2, c3 only if a single card truly needs more than one cloze).
- Ensure every cloze uses double curly braces on both sides (e.g., {{{{c1::answer}}}}); never use single braces.
- Preserve useful image-reference HTML on the relevant card when present.
- Do not add hints, notes, or commentary beyond the card text.
- Output ONLY a JSON array of {num_cards} strings. No markdown, code fences, or extra text.

Original card text:
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
The first card is the reference/original card. Treat its format as the target pattern wherever possible.

Goal:
- Return exactly {len(cleaned)} rewritten cards, in the same order as the originals.
- Leave card 1 as close to unchanged as possible; it defines the rough format, sentence/question style, HTML rhythm, and cloze pattern to follow.
- Rewrite card 2 and any later cards so each still tests its own original fact while roughly following card 1's format wherever that works.
- If card 1's exact format does not work for a later card, adapt only as much as needed for clarity and correctness.
- The cards should differ mainly in the information being recalled inside or immediately around the cloze deletion(s).

Rules:
- Preserve the factual meaning of each original card. Do not invent facts.
- Keep each card self-contained, clear, and unambiguous on its own.
- Use card 1's sentence template or question template across the set whenever possible.
- Minimize incidental clues that make one card easier than the others; keep non-answer wording as parallel as possible.
- Preserve each card's existing cloze numbering whenever reasonably possible so the note still behaves the same.
- Keep the answer text inside each cloze as close to the original as possible unless a tiny grammatical adjustment is necessary.
- Preserve useful HTML such as image references.
- Keep valid cloze HTML and ensure every cloze uses exactly two curly braces on both sides (for example, {{{{c1::answer}}}}).
- Do not add commentary, bullets, markdown, or explanations.
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
