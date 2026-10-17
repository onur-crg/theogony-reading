#!/usr/bin/env python3
"""Export existing homepage artwork exactly as rendered, using lossless WebP.

No drawing is regenerated. Crop coordinates and colour/alpha transforms reproduce
build_reader's former SVG viewports, feFlood/SourceAlpha and red-channel filter.
Original artwork is preserved. Hashed outputs can be cached immutably.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
ASSETS=ROOT/'assets'
OUTPUT=ASSETS/'optimized'
BLUE=(7,95,206)
PAPER=(222,222,222)
MOTIFS={'vase':(46,86,192,263),'scroll':(1267,105,250,231),'lyre':(18,708,188,212),'twig':(1296,721,195,193)}
PASSAGES={'passage-muses-v1.png':(16,70,1510,950),'passage-first-beings-v1.png':(36,70,1464,915),'passage-cronus-v3.png':(0,0,1536,1024)}
GODS={'gaia':(0,647),'zeus':(647,648),'athena':(1295,647)}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def crop(image,box):
    x,y,w,h=box
    return image.crop((x,y,x+w,y+h))
def colour_alpha(alpha,colour):
    result=Image.new('RGBA',alpha.size,colour+(0,))
    result.putalpha(alpha)
    return result

def main():
    OUTPUT.mkdir(exist_ok=True)
    entries={}
    def export(key,source,image,operation):
        # Do not reduce resolution or quantize colour. Only transparent padding,
        # unrendered RGB data and PNG encoding overhead are removed.
        temporary=OUTPUT/(key+'.webp')
        image.save(temporary,'WEBP',lossless=True,exact=True,method=6)
        decoded=Image.open(temporary).convert('RGBA')
        assert decoded.tobytes()==image.tobytes(),key
        digest=sha(temporary)
        target=OUTPUT/f'{key}.{digest[:12]}.webp'
        temporary.replace(target)
        entries[key]={'file':target.relative_to(ROOT).as_posix(),'width':image.width,'height':image.height,'bytes':target.stat().st_size,'sha256':digest,'source':source,'source_sha256':sha(ASSETS/source),'operation':operation}
    source='greek-objects-handdrawn-v3.png'
    original=Image.open(ASSETS/source).convert('RGBA')
    for key,box in MOTIFS.items():export(key,source,colour_alpha(crop(original,box).getchannel('A'),BLUE),{'crop':box,'fill':'#075fce','alpha':'source alpha'})
    source='gods-unified-blue-v5.png'
    original=Image.open(ASSETS/source).convert('RGB')
    # The old feColorMatrix used alpha = clamp(2 * red - 0.5).
    alpha=original.getchannel('R').point([max(0,min(255,round(2*r-127.5))) for r in range(256)])
    for key,(offset,width) in GODS.items():export(key,source,colour_alpha(crop(alpha,(offset,0,width,809)),PAPER),{'crop':[offset,0,width,809],'fill':'#dedede','alpha':'clamp(2 * red - 0.5)'})
    for source,box in PASSAGES.items():
        original=Image.open(ASSETS/source).convert('RGBA')
        export(source.removesuffix('.png'),source,colour_alpha(crop(original,box).getchannel('A'),BLUE),{'crop':box,'fill':'#075fce','alpha':'source alpha'})
    # Social previews use the existing complete illustration, without a new design.
    social=Image.open(ASSETS/'gods-unified-blue-v5.png').convert('RGB')
    social=social.resize((1200,500),Image.Resampling.LANCZOS)
    social.save(ASSETS/'theogony-share.jpg','JPEG',quality=88,optimize=True,progressive=True)
    (OUTPUT/'manifest.json').write_text(json.dumps(entries,indent=2)+'\n')
    print(f'Exported {len(entries)} lossless, full-resolution WebP assets: {sum(e["bytes"] for e in entries.values()):,} bytes. All decoded pixels verified.')
    for key,e in entries.items():print(f'{key}: {e["width"]}×{e["height"]}, {e["bytes"]:,} bytes')

if __name__=='__main__':main()
