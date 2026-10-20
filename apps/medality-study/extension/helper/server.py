"""Manually launched, token-protected loopback video downloader."""
import json
import re
import secrets
import threading
import uuid
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from yt_dlp import YoutubeDL

BASE = Path(__file__).resolve().parent
DEST = Path.home() / 'Downloads' / 'Medality'
JOBS = {}
LOCK = threading.Lock()
TOKEN = ''

def validate(data):
    page = urlparse(data.get('page', ''))
    if page.scheme != 'https' or not (page.hostname in ('medality.com', 'mrionline.com') or (page.hostname or '').endswith(('.medality.com', '.mrionline.com'))):
        raise ValueError('Open a Medality lesson first.')
    video = data.get('video', '')
    if not re.fullmatch(r'https://player\.vimeo\.com/video/[0-9]+(?:\?h=[a-zA-Z0-9]+)?', video):
        raise ValueError('No supported Vimeo lecture found.')
    return video, data['page']

def download(job, video, page):
    def progress(info):
        if info['status'] == 'downloading':
            total = info.get('total_bytes') or info.get('total_bytes_estimate')
            JOBS[job]['message'] = ('Downloading track: %.0f%%' % (100 * info.get('downloaded_bytes', 0) / total)) if total else 'Downloading lecture…'
        elif info['status'] == 'finished':
            JOBS[job]['message'] = 'Combining audio and video…'
    try:
        DEST.mkdir(parents=True, exist_ok=True)
        with YoutubeDL({'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/bestvideo+bestaudio/best',
                        'merge_output_format': 'mp4', 'outtmpl': str(DEST / '%(title).150B [%(id)s].%(ext)s'),
                        'http_headers': {'Referer': page}, 'noplaylist': True, 'quiet': True,
                        'windowsfilenames': True, 'progress_hooks': [progress], 'overwrites': False}) as ydl:
            info = ydl.extract_info(video, download=True)
            filename = str(Path(ydl.prepare_filename(info)).with_suffix('.mp4'))
        JOBS[job].update(state='complete', message='Saved in Downloads / Medality', filename=filename)
    except Exception as exc:
        JOBS[job].update(state='error', message=str(exc)[:350])

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass
    def authorized(self):
        return self.headers.get('Host') == '127.0.0.1:18764' and secrets.compare_digest(self.headers.get('X-Medality-Token', ''), TOKEN)
    def respond(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def do_GET(self):
        if not self.authorized():
            return self.respond(403, {'error': 'Unauthorized'})
        job = JOBS.get(self.path.removeprefix('/jobs/'))
        self.respond(200 if job else 404, job or {'error': 'Unknown download'})
    def do_POST(self):
        if not self.authorized():
            return self.respond(403, {'error': 'Unauthorized'})
        if self.path != '/download':
            return self.respond(404, {'error': 'Unknown action'})
        try:
            size = int(self.headers.get('Content-Length', 0))
            if not 0 < size < 4096:
                raise ValueError('Invalid request')
            video, page = validate(json.loads(self.rfile.read(size)))
            with LOCK:
                if any(v['state'] == 'working' for v in JOBS.values()):
                    return self.respond(409, {'error': 'A lecture is already downloading. Wait for it to finish.'})
                job = uuid.uuid4().hex
                JOBS[job] = {'state': 'working', 'message': 'Starting download…'}
            threading.Thread(target=download, args=(job, video, page), daemon=True).start()
            self.respond(202, {'job': job})
        except (ValueError, TypeError, KeyError) as exc:
            self.respond(400, {'error': str(exc)})

if __name__ == '__main__':
    token_file = BASE / 'token.txt'
    TOKEN = token_file.read_text().strip() if token_file.exists() else secrets.token_urlsafe(32)
    token_file.write_text(TOKEN)
    config = BASE.parent / 'helper-config.js'
    config.write_text('self.MEDALITY_HELPER_TOKEN = ' + json.dumps(TOKEN) + ';\n')
    print('Helper running. Reload extension once, refresh lesson, then click Download video. Close this window to stop.', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 18764), Handler).serve_forever()
