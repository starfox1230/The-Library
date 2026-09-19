"""Inventory channel tabs and collect English captions; safe to resume.

Run --inventory first, then --transcripts. Inventory-only updates retain saved
transcripts. No audio/video downloads; private and deleted videos are excluded.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import html
import json
from pathlib import Path
import re
import time
import tempfile
import os
import urllib.request
from yt_dlp import YoutubeDL

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'apps/neuroradish-catalog'
CATALOG = OUT / 'catalog.json'
CHANNELS = [
    dict(id='neuroradish', name='NeuroRadish', youtube_id='UCnTMr6JCu3V1ghhlz3vcBcQ', handle='neuroradish'),
    dict(id='learn', name='LearnNeuroradiology', youtube_id='UC6RICkCkDRjxar5rdsVJStA', handle='LearnNeuroradiology'),
    dict(id='neuroradiologist', name='The Neuroradiologist', youtube_id='UCZsvn0TMokxkXasVy5jasHw', handle='TheNeuroradiologist'),
    dict(id='tutorials', name='Radiology Tutorials', youtube_id='UC9Zp0PrjNbs4nwQNdkquRug', handle='radiologytutorials'),
]

def now():
    return datetime.now(timezone.utc).isoformat()

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    # Replace only after the complete JSON is flushed; interruption retains the prior file.
    with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=path.parent,suffix='.tmp',delete=False) as f:
        temporary=Path(f.name)
        try:
            f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
            f.flush()
            os.fsync(f.fileno())
        except BaseException:
            f.close()
            temporary.unlink(missing_ok=True)
            raise
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)

def extract(url, flat=True):
    with YoutubeDL(dict(quiet=True, no_warnings=True, skip_download=True,
                        extract_flat=flat, socket_timeout=25, retries=2)) as ydl:
        return ydl.extract_info(url, download=False)

def natural(text):
    return [int(x) if x.isdigit() else x.lower() for x in re.split(r'(\d+)', text)]

def classify(v):
    t = v['title'].lower()
    if 'buzzword' in t:
        series = 'Buzzword Core Exam'
    elif 'board review' in t and 'rapid' not in t and re.search(r'\bcase\s+\d+', t):
        region = next((s for s in ['brain', 'spine', 'pediatric', 'head/neck'] if s in t), 'mixed')
        series = 'Board Review / ' + region.title()
    elif 'rapid' in t and 'board review' in t:
        series = 'Rapid Anatomy' if 'neuroanatomy' in t else 'Rapid Board Review'
    elif 'neuroradiology sign' in t:
        series = 'Imaging Signs'
    elif 'physics' in t:
        region = next((s for s in ['ultrasound', 'mri', 'ct', 'x-ray'] if s in t), 'general')
        series = region.upper() + ' Physics'
    elif 'anatomy' in t:
        series = 'Anatomy'
    elif 'case' in t or 'quiz' in t:
        series = 'Case Reviews'
    else:
        series = 'Teaching & Tutorials'
    v['series'] = series
    topics = []
    patterns = {
        'Spine': r'spin|cord|vertebr|myelop',
        'Head & neck': r'head.?neck|head and neck|temporal bone|sinus|orbit|skull base|salivary|parotid|laryn|thyroid|neck',
        'Pediatrics & development': r'pediatric|paediatric|congenital|malformation|dysplasia|development|neonat|nf1|tsc',
        'Vascular & stroke': r'vascul|stroke|infarct|aneurysm|hemorrhag|haemorrhag|thromb|angiogra|ischemi',
        'Tumors & masses': r'tumou?r|mass|neoplas|glioma|metasta|lymphoma|meningioma|schwannoma',
        'Infection & inflammation': r'infect|inflamm|abscess|encephal|meningitis|demyelin|multiple sclerosis',
        'Trauma & emergencies': r'trauma|fracture|emergenc|herniation|mass effect',
        'Brain': r'brain|intracranial|cerebr|cerebell|pituitary|hypothalam|limbic|hippocamp',
        'Anatomy': r'anatomy|anatomic',
        'Physics & technique': r'physics|artifact|sequence|diffusion|dwi|t1|t2',
        'Ultrasound': r'ultrasound|doppler|sonograph',
        'Chest & body': r'chest|lung|abdomen|abdominal|liver|renal|kidney|bowel|pancrea|pelvi|cardiac',
        'Musculoskeletal': r'musculoskeletal|shoulder|knee|ankle|wrist|elbow|bone tumor',
    }
    for topic, pattern in patterns.items():
        if re.search(pattern, t):
            topics.append(topic)
    v['topics'] = topics or ['Topic unspecified']
    v['topic_basis'] = 'Title; unspecified case diagnoses have not been inferred'
    match = re.search(r'(?:case\s*#?\s*|#)(\d+)', t)
    v['case_number'] = int(match.group(1)) if match else None

def inventory():
    old = json.loads(CATALOG.read_text(encoding='utf-8')) if CATALOG.exists() else {}
    old_rows = {v['id']: v for v in old.get('videos', [])}
    prior = ROOT / 'exports/neuroradish/neuroradish_video_catalog.json'
    prior_rows = {v['video_id']: v for v in json.loads(prior.read_text(encoding='utf-8'))['videos']}
    videos, channels = {}, []
    for channel in CHANNELS:
        c = dict(channel, url='https://www.youtube.com/channel/' + channel['youtube_id'], tabs={}, playlists=[])
        for tab in ['videos', 'shorts', 'streams']:
            url = c['url'] + '/' + tab
            try:
                data = extract(url)
                entries = [e for e in data.get('entries', []) if e and re.fullmatch(r'[\w-]{11}', e.get('id', ''))]
                c['tabs'][tab] = dict(status='ok', count=len(entries), url=url)
                for e in entries:
                    vid = e['id']
                    p = prior_rows.get(vid, {})
                    if vid not in videos:
                        v = dict(old_rows.get(vid, {}))
                        v.update(id=vid, title=e['title'], channel=channel['id'],
                                 url='https://www.youtube.com/watch?v=' + vid, tabs=[], playlists=[])
                        v.setdefault('duration', e.get('duration') or p.get('duration_seconds') or None)
                        v.setdefault('upload_date', p.get('upload_date', ''))
                        v.setdefault('description', p.get('description', ''))
                        v.setdefault('transcript', dict(status='not_fetched'))
                        videos[vid] = v
                    videos[vid]['tabs'].append(tab)
            except Exception as error:
                msg = str(error)
                absent = 'does not have a' in msg and 'tab' in msg
                c['tabs'][tab] = dict(status='absent' if absent else 'error', count=0, url=url, error=msg[:350])
        # Playlist membership adds useful series context without counting other creators' videos.
        try:
            playlists = extract(c['url'] + '/playlists').get('entries', [])
            for playlist in playlists:
                pid = playlist.get('id')
                if not pid:
                    continue
                detail = extract('https://www.youtube.com/playlist?list=' + pid)
                ids = [e['id'] for e in detail.get('entries', []) if e and e.get('id') in videos and videos[e['id']]['channel'] == c['id']]
                c['playlists'].append(dict(id=pid, title=detail.get('title', playlist.get('title', pid)), count=len(ids)))
                for pos, vid in enumerate(ids, 1):
                    videos[vid]['playlists'].append(dict(id=pid, title=detail.get('title', pid), position=pos))
        except Exception as error:
            c['playlist_error'] = str(error)[:350]
        channels.append(c)
        print(c['name'], {k:(x['status'],x['count']) for k,x in c['tabs'].items()}, flush=True)
    if any('playlist_error' in c or any(t['status']=='error' for t in c['tabs'].values()) for c in channels):
        raise RuntimeError('A channel tab or playlist failed. Existing catalog retained; do not publish a partial inventory.')
    for v in videos.values():
        v['format'] = 'Short' if 'shorts' in v['tabs'] else 'Live archive' if 'streams' in v['tabs'] else 'Video'
        classify(v)
        if v['id'] in prior_rows:
            v['study_order'] = prior_rows[v['id']]['catalog_order']
        else:
            v['study_order'] = 10000
    rows = sorted(videos.values(), key=lambda v:(v['channel'], v['study_order'], natural(v['series']), natural(v['title'])))
    # Reuse saved transcripts by exact video ID. Do not infer source identity from title.
    physics = ROOT / 'apps/core-studying/YT Physics'
    sources = json.loads((physics / 'sources.json').read_text(encoding='utf-8'))['sections']
    for s in sources.values():
        if s['videoId'] in videos and (physics / s['file']).exists():
            v = videos[s['videoId']]
            content = (physics / s['file']).read_text(encoding='utf-8').strip()
            if len(content) > 200:
                path = OUT / 'transcripts' / (v['id'] + '.json')
                save(path, dict(video_id=v['id'], text=content, source='Existing Library transcript', source_file=str((physics/s['file']).relative_to(ROOT)), fetched_at=now()))
                v['transcript'] = dict(status='saved', path='transcripts/'+v['id']+'.json', source='Existing Library transcript', characters=len(content))
    result = dict(version=2, fetched_at=now(), channels=channels, videos=rows,
                  legacy={vid: {k:p.get(k) for k in ['track','category','format']} for vid,p in prior_rows.items()})
    save(CATALOG, result)
    print('Inventory:',len(rows),'videos; formats:',dict(Counter(v['format'] for v in rows)),flush=True)

def fetch_transcript(v):
    try:
        d = extract(v['url'], flat=False)
        metadata = {k:d.get(k) for k in ['duration','description','upload_date']}
        candidates = []
        for source, key in [('Creator captions', 'subtitles'), ('Automatic captions', 'automatic_captions')]:
            tracks = d.get(key) or {}
            languages = sorted((x for x in tracks if x == 'en' or x.startswith('en-')), key=lambda x:(x!='en',x!='en-orig',x))
            for lang in languages:
                for track in tracks[lang]:
                    if track.get('ext') == 'json3':
                        candidates.append((source,lang,track['url']))
        if not candidates:
            return metadata, dict(status='no_english_captions', checked_at=now())
        errors = []
        for source,lang,url in candidates[:3]:
            try:
                req=urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=30) as response:
                    caption = json.load(response)
                lines=[]
                for event in caption.get('events',[]):
                    text=html.unescape(''.join(s.get('utf8','') for s in event.get('segs',[]))).strip()
                    text=re.sub(r'\s+', ' ',text)
                    if not text:
                        continue
                    if lines and lines[-1]['text']==text:
                        continue
                    lines.append(dict(start=round(event.get('tStartMs',0)/1000,3),text=text))
                if not lines:
                    raise ValueError('Empty caption response')
                text='\n'.join(f"[{int(x['start'])//60}:{int(x['start'])%60:02}] {x['text']}" for x in lines)
                save(OUT/'transcripts'/(v['id']+'.json'),dict(video_id=v['id'],text=text,segments=lines,language=lang,source=source,fetched_at=now()))
                return metadata, dict(status='saved',path='transcripts/'+v['id']+'.json',source=source,language=lang,characters=len(text),checked_at=now())
            except Exception as error:
                errors.append(str(error)[:200])
        return metadata,dict(status='fetch_failed',checked_at=now(),error='; '.join(errors))
    except Exception as error:
        return {},dict(status='fetch_failed',checked_at=now(),error=str(error)[:350])

def transcripts(retry=False):
    data=json.loads(CATALOG.read_text(encoding='utf-8'))
    todo=[v for v in data['videos'] if v['transcript']['status']=='not_fetched' or (retry and v['transcript']['status']=='fetch_failed')]
    print('Fetching',len(todo),'remaining transcripts',flush=True)
    failures = 0
    for n,v in enumerate(todo,1):
        metadata,status=fetch_transcript(v)
        for k,value in metadata.items():
            if value is not None:
                v[k]=value
        v['transcript']=status
        save(CATALOG,data)
        print(n,'/',len(todo),dict(Counter(x['transcript']['status'] for x in data['videos'])),flush=True)
        failures = failures + 1 if status['status']=='fetch_failed' else 0
        error = status.get('error','').lower()
        if failures >= 3 or any(x in error for x in ['429','not a bot','ipblocked','too many requests']):
            print('Stopped after access failures. Saved progress; retry later, not in a loop.',flush=True)
            break
        time.sleep(3)
    data['transcripts_checked_at']=now()
    save(CATALOG,data)

def reconcile_saved():
    data=json.loads(CATALOG.read_text(encoding='utf-8'))
    prior=json.loads((ROOT/'exports/neuroradish/neuroradish_video_catalog.json').read_text(encoding='utf-8'))
    data['legacy']={v['video_id']:{k:v.get(k) for k in ['track','category','format']} for v in prior['videos']}
    for v in data['videos']:
        path=OUT/'transcripts'/(v['id']+'.json')
        if path.exists():
            t=json.loads(path.read_text(encoding='utf-8'))
            assert t['video_id']==v['id'] and t['text'].strip()
            v['transcript']=dict(status='saved',path='transcripts/'+path.name,source=t['source'],characters=len(t['text']))
    save(CATALOG,data)
    print(dict(Counter(v['transcript']['status'] for v in data['videos'])))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--inventory',action='store_true')
    parser.add_argument('--transcripts',action='store_true')
    parser.add_argument('--retry',action='store_true')
    parser.add_argument('--reconcile',action='store_true')
    args=parser.parse_args()
    if args.inventory: inventory()
    if args.transcripts: transcripts(args.retry)
    if args.reconcile: reconcile_saved()
