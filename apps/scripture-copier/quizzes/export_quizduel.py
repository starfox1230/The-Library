"""Build deterministic QuizDuel exports without changing authored CFM questions."""
import argparse
import json
from pathlib import Path

QUIZZES = Path(__file__).resolve().parent
LEVEL_LABELS = {'kid': 'Kid', 'high-school': 'High School', 'expert': 'PhD / Expert'}


def build_exports(doc):
    exports = {}
    for level, label in LEVEL_LABELS.items():
        questions = []
        for item in doc['levels'][level]:
            options = [option['text'] for option in item['options']]
            answers = [option['text'] for option in item['options']
                       if option['id'] == item['correctOptionId']]
            if (len(options) != 4 or not all(isinstance(text, str) and text.strip() for text in options)
                    or len(set(text.casefold() for text in options)) != 4
                    or len(answers) != 1 or options.count(answers[0]) != 1):
                raise ValueError(f"{item['id']}: invalid QuizDuel answer options")
            source = item['source']
            questions.append({
                'question': item['question'],
                'options': options,
                'correctAnswer': answers[0],
                'explanation': f"{item['explanation']}\n\n{source['reference']}\n{source['url']}",
            })
        exports[level] = {
            'quizName': f"Come Follow Me — {doc['date']} — {label}",
            'questions': questions,
        }
    return exports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='Add or refresh derived quizDuel exports')
    args = parser.parse_args()
    paths = sorted(QUIZZES.glob('????-??-??.json'))
    if not paths:
        raise ValueError('No daily quiz files found')
    changed = 0
    for path in paths:
        doc = json.loads(path.read_text(encoding='utf-8'))
        exports = build_exports(doc)
        if doc.get('quizDuel') != exports:
            if not args.write:
                raise ValueError(f'{path.name}: missing or stale quizDuel exports; rerun with --write')
            doc['quizDuel'] = exports
            path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            changed += 1
    print(f'Checked {len(paths) * 3} QuizDuel exports across {len(paths)} dates; updated {changed} files.')


if __name__ == '__main__':
    main()
