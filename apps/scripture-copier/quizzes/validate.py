"""Validate published CFM quiz JSON against the app's exact daily verse slices."""
import datetime as dt
import json
import re
import sys
from pathlib import Path
from export_quizduel import build_exports

APP = Path(__file__).resolve().parent.parent
QUIZZES = APP / 'quizzes'
LEVELS = ('kid', 'high-school', 'expert')
SOURCE = re.compile(r'^Isaiah (\d+):(\d+)(?:-(?:(\d+):)?(\d+))?$')
FORBIDDEN = re.compile(r'\b(?:all|none) of the above\b', re.I)

def fail(message):
    raise ValueError(message)

def assignments():
    schedule = json.loads((APP / 'cfm-schedule-2026.json').read_text(encoding='utf-8'))
    result = {}
    for week in schedule:
        flat = []
        for reading in week.get('readings', []):
            book = json.loads((APP / 'data' / reading['volume'] / f"{reading['book']}.json").read_text(encoding='utf-8'))
            for chapter in range(reading['chapStart'], reading['chapEnd'] + 1):
                found = next((item for item in book['chapters'] if item['number'] == chapter), None)
                if found is None:
                    fail(f'missing source chapter {reading["book"]} {chapter}')
                flat.extend((reading['display'], chapter, verse) for verse in range(1, len(found['verses']) + 1))
        start = dt.date.fromisoformat(week['start'])
        for offset in range(7):
            count = len(flat) // 7 + (offset < len(flat) % 7)
            begin = offset * (len(flat) // 7) + min(offset, len(flat) % 7)
            result[(start + dt.timedelta(days=offset)).isoformat()] = flat[begin:begin + count]
    return result

def validate(path, daily):
    doc = json.loads(path.read_text(encoding='utf-8'))
    date = path.stem
    if doc.get('date') != date or date not in daily or not daily[date]:
        fail(f'{path}: invalid or empty assignment date')
    if set(doc.get('levels', {})) != set(LEVELS):
        fail(f'{path}: expected exactly three levels')
    assigned = daily[date]
    assigned_refs = [(chapter, verse) for book, chapter, verse in assigned if book == 'Isaiah']
    ids, stems = set(), set()
    for level in LEVELS:
        questions = doc['levels'][level]
        if len(questions) != 10:
            fail(f'{path}: {level} has {len(questions)} questions, expected 10')
        for q in questions:
            if q.get('date') != date or q.get('difficulty') != level:
                fail(f'{path}: question date or level mismatch')
            if not all(isinstance(q.get(key), str) and q[key].strip() for key in ('id', 'question', 'correctOptionId', 'explanation')):
                fail(f'{path}: missing required question field')
            if q['id'] in ids or q['question'].strip().casefold() in stems:
                fail(f'{path}: duplicate ID or stem')
            ids.add(q['id']); stems.add(q['question'].strip().casefold())
            options = q.get('options')
            if not isinstance(options, list) or len(options) != 4:
                fail(f'{path}: question {q["id"]} needs four options')
            option_ids = [o.get('id') for o in options]
            option_texts = [o.get('text', '').strip() for o in options]
            if len(set(option_ids)) != 4 or len(set(t.casefold() for t in option_texts)) != 4 or not all(option_texts):
                fail(f'{path}: duplicate or empty option in {q["id"]}')
            if option_ids.count(q['correctOptionId']) != 1:
                fail(f'{path}: answer key invalid in {q["id"]}')
            if any(FORBIDDEN.search(text) for text in option_texts):
                fail(f'{path}: forbidden option wording in {q["id"]}')
            source = q.get('source', {})
            match = SOURCE.fullmatch(source.get('reference', ''))
            if not match:
                fail(f'{path}: malformed source in {q["id"]}')
            chapter, verse, end_chapter, end_verse = match.groups()
            first = (int(chapter), int(verse))
            last = (int(end_chapter or chapter), int(end_verse or verse))
            if first not in assigned_refs or last not in assigned_refs or assigned_refs.index(first) > assigned_refs.index(last):
                fail(f'{path}: source outside daily assignment in {q["id"]}')
            expected = f'https://www.churchofjesuschrist.org/study/scriptures/ot/isa/{chapter}.{verse}?lang=eng'
            if source.get('url') != expected:
                fail(f'{path}: source URL mismatch in {q["id"]}')
    if doc.get('quizDuel') != build_exports(doc):
        fail(f'{path}: missing or stale QuizDuel exports; run export_quizduel.py --write')
    return len(ids)

def main():
    daily = assignments()
    paths = sorted(QUIZZES.glob('????-??-??.json'))
    if not paths:
        fail('No daily quiz files found')
    total = sum(validate(path, daily) for path in paths)
    print(f'Validated {len(paths)} dates, {total} questions, daily scripture references, and {len(paths) * 3} QuizDuel exports.')

if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(f'Quiz validation failed: {error}', file=sys.stderr)
        sys.exit(1)
