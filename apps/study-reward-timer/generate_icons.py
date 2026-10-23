"""Rebuild dependency-free geometric home-screen icons (Pillow only)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import math

HERE = Path(__file__).resolve().parent

def make_icon(maskable=False):
    scale = 3
    size = 512 * scale
    image = Image.new('RGB', (size, size), '#080b15')
    pixels = image.load()
    for y in range(size):
        for x in range(size):
            distance = min(1, math.hypot(x - size / 2, y - size / 2) / (size * .65))
            pixels[x, y] = tuple(round(a * (1-distance) + b * distance) for a,b in zip((25,43,61), (8,11,21)))
    factor = .83 if maskable else 1
    def box(coords):
        return tuple(round((256 + (v-256)*factor)*scale) for v in coords)
    glow = Image.new('RGBA', image.size)
    draw = ImageDraw.Draw(glow)
    draw.arc(box((102,109,410,417)), -60, 240, fill='#72e7ed', width=round(23*factor*scale))
    image = Image.alpha_composite(image.convert('RGBA'), glow.filter(ImageFilter.GaussianBlur(11*scale)))
    draw = ImageDraw.Draw(image)
    draw.ellipse(box((102,109,410,417)), outline='#26374c', width=round(4*scale*factor))
    # Gradient arc and round caps.
    for angle in range(-60, 240):
        t=(angle+60)/300
        color=tuple(round(a*(1-t)+b*t) for a,b in zip((170,255,224),(164,139,255)))
        draw.arc(box((102,109,410,417)), angle, angle+2, fill=color, width=round(13*scale*factor))
    for angle,color in [(-60,'#aaffdf'),(240,'#a48bff')]:
        x,y=256+154*math.cos(math.radians(angle)),263+154*math.sin(math.radians(angle))
        draw.ellipse(box((x-6.5,y-6.5,x+6.5,y+6.5)), fill=color)
    points=[(275,175),(199,281),(251,281),(235,353),(314,239),(260,239)]
    draw.polygon([(round((256+(x-256)*factor)*scale),round((256+(y-256)*factor)*scale)) for x,y in points],fill='#bdfff0')
    draw.rounded_rectangle(box((235,82,277,94)),radius=6*scale,fill='#a79aff')
    return image.convert('RGB')

if __name__ == '__main__':
    standard = make_icon()
    for name,size in [('apple-touch-icon.png',180),('icon-192.png',192),('icon-512.png',512)]:
        standard.resize((size,size),Image.Resampling.LANCZOS).save(HERE/name)
    make_icon(True).resize((512,512),Image.Resampling.LANCZOS).save(HERE/'icon-maskable.png')
