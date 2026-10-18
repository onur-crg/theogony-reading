#!/usr/bin/env python3
"""Prepare an explicit source snapshot for bounded shared-note generation."""
import json,sys
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'pipeline'))
import build_reader as r

def main():
 numbered,variant,_=r.load_sections(resolve_registry=False)
 verses=r.load_verse_runs();extras=r.load_variant_verse_run()[0]
 greek={e.get('n'):' '.join(''.join(e.itertext()).split()) for e in ET.parse(r.GREEK_SOURCE).getroot().iter('{http://www.tei-c.org/ns/1.0}l')}
 rows=[]
 for section,_,_ in numbered+[variant]:
  lines=extras if section['id']=='v929' else {str(n):verses[n][0] for n in range(section['start'],section['end']+1)}
  cards=[]
  for i,card in enumerate(section['cards']):
   cards.append({**card,'matching_aliases':[a for a,k in r.aliases(section).items() if k==i]})
  rows.append({'id':section['id'],'verses':[{'n':n,'greek':greek[n],'english':t} for n,t in lines.items()],'cards':cards})
 target=ROOT/'reviews/figure-registry-input.prompt.txt'
 target.write_text((ROOT/'pipeline/figure_registry.prompt.txt').read_text()+'\nSOURCE SNAPSHOT:\n'+json.dumps(rows,ensure_ascii=False))
 print(target)
if __name__=='__main__':main()
