"""Build deterministic PNG icons and package only public extension source files."""
from pathlib import Path
import struct
import zlib
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parent
EXT = ROOT / 'extension'


def icon(size):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))

    pixels = bytearray()
    for y in range(size):
        pixels.append(0)
        for x in range(size):
            # A cream bookmark on forest green. No external assets or image packages.
            u, v = x / size, y / size
            mark = .29 <= u <= .71 and .19 <= v <= .80 and not (v > .64 + abs(u - .5) * .76)
            pixels.extend((248, 246, 235, 255) if mark else (35, 75, 58, 255))
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(bytes(pixels), 9)) + chunk(b'IEND', b'')


if __name__ == '__main__':
    (EXT / 'icons').mkdir(exist_ok=True)
    for size in (16, 48, 128):
        (EXT / 'icons' / f'{size}.png').write_bytes(icon(size))
    files = ['manifest.json', 'background.js', 'core.js', 'content.js', 'options.html', 'options.css', 'options.js', 'icons/16.png', 'icons/48.png', 'icons/128.png']
    with ZipFile(ROOT / 'next-up-chrome-extension.zip', 'w', ZIP_DEFLATED) as archive:
        for name in files:
            entry = ZipInfo(name, date_time=(2026, 10, 23, 0, 0, 0))
            entry.compress_type = ZIP_DEFLATED
            archive.writestr(entry, (EXT / name).read_bytes())
    print(f'Packaged {len(files)} files: next-up-chrome-extension.zip')
