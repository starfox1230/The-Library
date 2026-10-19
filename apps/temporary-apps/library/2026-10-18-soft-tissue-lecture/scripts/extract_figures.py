"""Rebuild caption-free figures from the two lecture PDFs. Requires PyMuPDF and Pillow."""
from pathlib import Path
import hashlib
import json
import fitz
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
# CT coordinates were manually mapped on 857 x 1109 page renders, then checked
# against the printed figure numbers and captions. Never infer page adjacency.
CT = {
 1: (2, [(56,390,286,879)]), 2: (2, [(303,649,533,879)]), 3: (2, [(550,610,781,879)]),
 4: (3, [(78,102,430,314)]), 5: (3, [(78,651,430,901),(449,651,802,901)]),
 6: (4, [(56,102,286,331)]), 7: (4, [(303,102,533,331)]),
 8: (4, [(56,520,286,694),(303,538,533,694)]),
 9: (5, [(78,102,430,314)]), 10: (5, [(571,102,801,332)]),
 11: (5, [(78,434,307,888)]), 12: (5, [(325,682,554,889)]), 13: (5, [(571,682,801,889)]),
 14: (6, [(56,102,286,331)]), 15: (6, [(427,102,781,321)]),
 16: (6, [(427,342,781,571)]), 17: (6, [(550,589,781,859)]),
 18: (7, [(78,102,307,310)]), 19: (7, [(325,102,555,310)]),
 20: (7, [(78,472,307,929)]), 21: (7, [(325,472,555,689)])
}
# Embedded MRI figures contain the original panel letters but no captions.
MR = {1:(5,12),2:(5,14),3:(6,19),4:(6,21),5:(7,26),6:(7,28),7:(7,30),8:(7,32),
      9:(8,37),10:(9,42),11:(9,44),12:(11,52),13:(12,57),14:(12,59),15:(13,64),
      16:(14,69),17:(14,71),18:(15,76),19:(15,78),20:(16,83),21:(17,88)}

def main():
    out = ROOT / 'figures'
    out.mkdir(exist_ok=True)
    manifest = []
    ct = fitz.open(ROOT / 'papers/ct-soft-tissue-masses.pdf')
    for number, (page, regions) in CT.items():
        pg = ct[page-1]
        parts = []
        for box in regions:
            rect = fitz.Rect(box[0]/857*pg.rect.width, box[1]/1109*pg.rect.height,
                             box[2]/857*pg.rect.width, box[3]/1109*pg.rect.height)
            pix = pg.get_pixmap(matrix=fitz.Matrix(3,3), clip=rect, alpha=False)
            parts.append(Image.frombytes('RGB', (pix.width,pix.height), pix.samples))
        if len(parts)==1:
            im=parts[0]
        else:
            im=Image.new('RGB',(sum(x.width for x in parts)+24,max(x.height for x in parts)+52),'#11151c')
            draw=ImageDraw.Draw(im)
            offset=0
            for label,part in zip(['A','B'],parts):
                im.paste(part,(offset,48)); draw.text((offset+8,4),label,fill='white',font=ImageFont.load_default(size=32)); offset+=part.width+24
        file=f'ct-{number:02}.webp'
        im.save(out/file,quality=94)
        manifest.append(dict(id=f'ct-{number}',paper='ct',figure=number,page=page,regions=regions,file=f'figures/{file}',width=im.width,height=im.height))
    mr=fitz.open(ROOT/'papers/mri-systematic-approach.pdf')
    for number,(page,xref) in MR.items():
        pix=fitz.Pixmap(mr,xref)
        if pix.n!=3: pix=fitz.Pixmap(fitz.csRGB,pix)
        im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
        file=f'mr-{number:02}.webp'
        im.save(out/file,quality=95)
        manifest.append(dict(id=f'mr-{number}',paper='mr',figure=number,page=page,xref=xref,file=f'figures/{file}',width=im.width,height=im.height))
    for n in ['ct-soft-tissue-masses.pdf','mri-systematic-approach.pdf']:
        print(n,hashlib.sha256((ROOT/'papers'/n).read_bytes()).hexdigest())
    reader=ROOT/'reader'; reader.mkdir(exist_ok=True)
    for key,doc in [('ct',ct),('mr',mr)]:
        for i,pg in enumerate(doc):
            pix=pg.get_pixmap(matrix=fitz.Matrix(1.85,1.85),alpha=False)
            Image.frombytes('RGB',(pix.width,pix.height),pix.samples).save(reader/f'{key}-{i+1:02}.webp',quality=89)
    (ROOT/'figure-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    # QA contact sheets include every final figure, with its stable ID.
    for paper in ['ct','mr']:
        entries=[m for m in manifest if m['paper']==paper]
        sheet=Image.new('RGB',(1400,((len(entries)+3)//4)*330),'#ddd')
        draw=ImageDraw.Draw(sheet)
        for i,m in enumerate(entries):
            im=Image.open(ROOT/m['file']); im.thumbnail((338,297))
            x=(i%4)*350; y=(i//4)*330
            sheet.paste(im,(x+(350-im.width)//2,y+25))
            draw.text((x+8,y+6),f"{m['id']} / PDF p{m['page']}",fill='black')
        qa=ROOT/'qa'; qa.mkdir(exist_ok=True)
        sheet.save(qa/f'{paper}-contact.jpg',quality=90)
    print('Extracted',len(manifest),'figures; captions excluded from quiz images.')

if __name__=='__main__': main()
