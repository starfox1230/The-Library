"""Local-only performance comparison window; independent from Anki's webviews."""
import argparse
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import types
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT=Path(__file__).parent
pkg=types.ModuleType('afterglow_preview')
pkg.__path__=[str(ROOT)]
sys.modules[pkg.__name__]=pkg
AudioListener=importlib.import_module(pkg.__name__+'.audio').AudioListener
MusicMotion=importlib.import_module(pkg.__name__+'.motion').MusicMotion


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--no-browser',action='store_true')
    args=parser.parse_args()
    audio=AudioListener();motion=MusicMotion();lock=threading.Lock()
    last_request=[time.monotonic()]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):
            pass
        def do_GET(self):
            path=self.path.split('?',1)[0]
            if self.headers.get('Host') not in ('127.0.0.1:'+str(self.server.server_port),'localhost:'+str(self.server.server_port)):
                self.send_error(403);return
            if path=='/state':
                with lock:
                    last_request[0]=time.monotonic()
                    state=audio.snapshot(35)
                    state.update(motion.feed(last_request[0],state))
                data=json.dumps(state).encode();mime='application/json'
            else:
                files={'/':ROOT/'standalone.html','/standalone.html':ROOT/'standalone.html',
                       '/web/afterglow.js':ROOT/'web/afterglow.js','/web/liquid.js':ROOT/'web/liquid.js',
                       '/web/particles.js':ROOT/'web/particles.js','/web/afterglow.css':ROOT/'web/afterglow.css'}
                files['/web/club.js']=ROOT/'web/club.js'
                files['/web/waves.js']=ROOT/'web/waves.js'
                target=files.get(path)
                if not target:self.send_error(404);return
                data=target.read_bytes();mime='text/html' if target.suffix=='.html' else 'text/css' if target.suffix=='.css' else 'text/javascript'
            self.send_response(200);self.send_header('Content-Type',mime+'; charset=utf-8')
            self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)))
            self.end_headers()
            try:self.wfile.write(data)
            except (BrokenPipeError,ConnectionResetError):pass
        def do_POST(self):
            if self.path!='/stop' or self.headers.get('Origin') not in (None,'http://127.0.0.1:'+str(self.server.server_port)):
                self.send_error(403);return
            self.send_response(204);self.end_headers()
            threading.Thread(target=self.server.shutdown,daemon=True).start()
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    url='http://127.0.0.1:'+str(server.server_port)+'/'
    def idle_watch():
        while time.monotonic()-last_request[0]<90:time.sleep(2)
        server.shutdown()
    audio.start()
    threading.Thread(target=idle_watch,daemon=True).start()
    if args.no_browser:
        print(url,flush=True)
    else:
        edge=Path(os.environ.get('ProgramFiles(x86)','C:/Program Files (x86)'))/'Microsoft/Edge/Application/msedge.exe'
        if edge.exists():
            subprocess.Popen([str(edge),'--app='+url,'--new-window'])
        else:
            import webbrowser
            webbrowser.open(url)
    try:server.serve_forever()
    finally:audio.stop();server.server_close()


if __name__=='__main__':
    main()
