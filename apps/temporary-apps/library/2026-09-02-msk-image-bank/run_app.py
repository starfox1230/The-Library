"""Launch the local MSK Image Bank in a browser.

The app itself is static HTML/JS. This tiny server makes the same folder work
reliably from localhost and opens Chrome when it is available.
"""
from __future__ import annotations

import functools
import http.server
import os
from pathlib import Path
import shutil
import subprocess
import webbrowser


ROOT = Path(__file__).resolve().parent
PORT = 8765
URL = f"http://127.0.0.1:{PORT}/index.html"


def open_browser() -> None:
    candidates = [
        shutil.which("chrome"),
        os.environ.get("PROGRAMFILES", "") + r"\Google\Chrome\Application\chrome.exe",
        os.environ.get("LOCALAPPDATA", "") + r"\Google\Chrome\Application\chrome.exe",
    ]
    chrome = next((path for path in candidates if path and Path(path).exists()), None)
    if chrome:
        subprocess.Popen([chrome, URL], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        webbrowser.open(URL)


def main() -> None:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    print(f"MSK Image Bank running at {URL}")
    print("Keep this window open while using the app. Press Ctrl+C to stop it.")
    open_browser()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
