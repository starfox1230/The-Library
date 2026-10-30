"""Cache verified public OCR runtime files for the loopback-only QA harness."""
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

root=Path(__file__).resolve().parent
target=root/'qa-output/ocr-assets'
target.mkdir(parents=True,exist_ok=True)
for name,spec in json.loads((root/'ocr-assets.json').read_text(encoding='utf-8')).items():
    path=target/name
    data=path.read_bytes() if path.exists() else b''
    if len(data)!=spec['bytes'] or hashlib.sha256(data).hexdigest()!=spec['sha256']:
        with urlopen(spec['url'],timeout=45) as response:
            data=response.read(spec['bytes']+1)
        if len(data)!=spec['bytes'] or hashlib.sha256(data).hexdigest()!=spec['sha256']:
            raise ValueError(f'Integrity check failed: {name}')
        path.write_bytes(data)
    print(f'Verified public OCR asset: {name}')
