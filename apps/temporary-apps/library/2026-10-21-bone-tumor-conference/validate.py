"""Validate source completeness and reference integrity before publication."""
import argparse
import json
import re
import hashlib
from pathlib import Path


def validate(private):
    root = Path(__file__).resolve().parent
    guide = json.loads((root/'guide.json').read_text(encoding='utf-8'))
    assert len(guide) == 200, len(guide)
    assert len({p['id'] for p in guide}) == len(guide)
    for point in guide:
        assert all(point.get(k) for k in ['id','title','topic','body','prompt','answer','refs']), point['id']
        assert all(ref['source'] in ['helms2','helms3','helms4','acr','rsna'] for ref in point['refs'])
        assert all(rel in {p['id'] for p in guide} for rel in point.get('related', []))
    assert not (root/'corpus.json').exists(), 'Private corpus must not be placed in public app directory'
    assert not (root/'assets').exists(), 'Private source images must remain outside public repository'
    assert not (root/'documents').exists(), 'Complete source PDFs must remain private'
    if private:
        corpus = json.loads((private/'corpus.json').read_text(encoding='utf-8'))
        sources = {s['id']: s for s in corpus['sources']}
        assert {sid:len(s['pages']) for sid,s in sources.items()} == {'helms2':16,'helms3':25,'helms4':20,'acr':17,'rsna':59}
        assert len(corpus['figures']) == 198
        assert len({f['id'] for f in corpus['figures']}) == 198
        for sid, count in [('helms2',41),('helms3',48),('helms4',40)]:
            numbers = {int(f['label'].split('.')[-1]) for f in corpus['figures'] if f['source']==sid}
            assert numbers == set(range(1,count+1)), (sid,numbers)
        assert any(f['id']=='acr-fig9-corrected' and f['page']==17 for f in corpus['figures'])
        assert not any(f['id']=='acr-fig9' for f in corpus['figures'])
        assert 'superseded' in sources['acr']['pages'][12]['warning']
        for point in guide:
            for ref in point['refs']:
                assert 1 <= ref['page'] <= len(sources[ref['source']]['pages']), (point['id'],ref)
        for source in sources.values():
            import fitz
            pdf = private/source['pdf']
            assert pdf.is_file(), source['id']
            assert hashlib.sha256(pdf.read_bytes()).hexdigest() == source['sha256'], source['id']
            with fitz.open(pdf) as document:
                assert len(document) == len(source['pages']), source['id']
            assert len({p['id'] for p in source['pages']}) == len(source['pages'])
            for page in source['pages']:
                assert (private/page['image']).is_file(), page['image']
                assert 'sterlingjones@' not in page['text'].lower()
                assert len({b['id'] for b in page['blocks']}) == len(page['blocks'])
        for figure in corpus['figures']:
            assert figure['caption'], figure['id']
            assert (private/figure['image']).is_file(), figure['id']
            assert (private/figure['contextImage']).is_file(), figure['id']
        print('PASS: 200 points; 137 source pages/slides; 198 atlas entries; all references and local media resolve.')
    else:
        print('PASS: 200 original study points; public source corpus excluded.')


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--private',type=Path)
    validate(parser.parse_args().private)
