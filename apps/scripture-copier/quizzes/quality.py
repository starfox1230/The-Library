"""Publication gates for newly reviewed quizzes; semantic review remains mandatory."""
import hashlib
import json
import re
from collections import Counter

QUALITY_START = '2026-10-07'
REVIEW_CHECKS = ['source-grounding', 'one-best-answer', 'grammar-and-category',
                 'plausible-distractors', 'no-stem-giveaway', 'no-testwise-clues']

def normalize(text):
    return ' '.join(re.findall(r"\w+", text.casefold()))

def bank_hash(doc):
    return hashlib.sha256(json.dumps(doc['levels'], ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')).encode('utf-8')).hexdigest()

def validate_quality(doc):
    for level, questions in doc['levels'].items():
        seen = set()
        longest = shortest = 0
        positions = []
        for q in questions:
            label = f"{doc['date']} {level} {q['id']}"
            texts = [normalize(o['text']) for o in q['options']]
            if len(set(texts)) != 4:
                raise ValueError(f'{label}: choices differ only by punctuation or casing')
            if seen.intersection(texts):
                raise ValueError(f'{label}: reused answer choice from another question; write item-specific distractors')
            seen.update(texts)
            key = next(i for i,o in enumerate(q['options']) if o['id'] == q['correctOptionId'])
            positions.append(key)
            answer = texts[key]
            if len(answer.split()) >= 2 and f' {answer} ' in f" {normalize(q['question'])} ":
                raise ValueError(f'{label}: stem contains the keyed answer')
            lengths = [len(t.split()) for t in texts]
            if max(lengths) - min(lengths) > max(3, min(lengths) * .5):
                raise ValueError(f'{label}: answer choices have markedly unequal word counts {lengths}')
            others = [n for i,n in enumerate(lengths) if i != key]
            longest += lengths[key] > max(others)
            shortest += lengths[key] < min(others)
        if longest > 4 or shortest > 4:
            raise ValueError(f"{doc['date']} {level}: length predicts answers ({longest} uniquely longest, {shortest} uniquely shortest)")
        counts = Counter(positions)
        if set(counts) != {0,1,2,3} or max(counts.values()) > 3:
            raise ValueError(f"{doc['date']} {level}: unbalanced stored answer positions {dict(counts)}")
    review = doc.get('qualityReview', {})
    if review.get('questionSha256') != bank_hash(doc) or review.get('checks') != REVIEW_CHECKS:
        raise ValueError(f"{doc['date']}: missing or stale content-bound semantic review; read every item before signing")
