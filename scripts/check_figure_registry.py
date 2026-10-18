#!/usr/bin/env python3
"""Validate shared identities, exact local context, source records and first links."""
import hashlib,json,re,sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'pipeline'))
import build_reader as r
from figure_registry import load_registry

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class FigureLinks(HTMLParser):
 def __init__(self):super().__init__();self.entities=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='a' and a.get('data-entity'):self.entities.append(a['data-entity'])

def main():
 entities,local,records=load_registry()
 raw,rawvar,_=r.load_sections(resolve_registry=False);resolved,var,_=r.load_sections()
 before={s['id']:s for s,_,_ in raw+[rawvar]}
 greek={e.get('n'):' '.join(''.join(e.itertext()).split()) for e in ET.parse(r.GREEK_SOURCE).getroot().iter('{http://www.tei-c.org/ns/1.0}l')}
 for path,m in records:
  assert digest(path)==m['output_sha256']
  assert digest(path.with_suffix('.prompt.txt'))==m['prompt_sha256']
  assert digest(r.GREEK_SOURCE)==m['source_sha256']
  assert m['tool_event_count']==0 and m['cli_exit']==0
 for eid,e in entities.items():
  assert len(e['general'].split())<=32,(eid,'too long')
  assert e['bindings'],eid
  for proof in e['evidence']:assert proof['greek'] in greek[proof['verse']],(eid,'bad Greek evidence')
 verses=r.load_verse_runs();extra=r.load_variant_verse_run()[0]
 for section,_,_ in resolved+[var]:
  sid=section['id'];originals={c['id']:c for c in before[sid]['cards']}
  for card in section['cards']:
   origin=card.get('origin_card_id',card['id']);assert card['here']==originals[origin]['here'],(sid,origin,'changed Here')
   assert card.get('verse_labels')==originals[origin].get('verse_labels'),(sid,origin,'changed scope')
   if 'entity_id' in card:
    entry=entities[card['entity_id']]
    assert card['general']==entry['general'] and card['label']==entry['name'],(sid,origin)
   elif card.get('origin_card_id'):
    assert card['general']==originals[origin]['general']
    assert sid=='p015' and origin in ['p015-cythera','p015-cyprus']
   else:assert card==originals[origin],(sid,origin,'changed local definition')
  texts=extra if sid=='v929' else {str(n):verses[n][0] for n in range(section['start'],section['end']+1)}
  potential=FigureLinks();actual=FigureLinks();seen=set()
  for n,text in texts.items():
   potential.feed(r.linked_text(text,section,n))
   actual.feed(r.linked_text(text,section,n,seen))
  assert set(potential.entities)<=set(actual.entities),(sid,'lost figure link',set(potential.entities)-set(actual.entities))
  assert all(c==1 for c in Counter(actual.entities).values()),(sid,'repeated figure link')
 # Shared aliases and namesakes are explicit identity decisions.
 def binding(sid,card_id):return {eid for eid,e in entities.items() for b in e['bindings'] if (b['section_id'],b['card_id'])==(sid,card_id)}
 assert binding('p020','p020-doris-mother')!=binding('p020','p020-doris-daughter')
 assert binding('p002','p002-zeus')==binding('p059','p059-zeus')
 assert binding('p017','p017-night')==binding('p049','p049-night')
 for left,right in [(('p006','p006-erato'),('p020','p020-erato')),(('p006','p006-urania'),('p025','p025-urania')),(('p020','p020-agave'),('p062','p062-agave')),(('p020','p020-autonoe'),('p062','p062-autonoe'))]:
  assert binding(*left) and binding(*right) and binding(*left).isdisjoint(binding(*right)),(left,right)
 edition=json.loads((ROOT/'data/theogony.json').read_text())
 standalone=json.loads((ROOT/'data/figures.json').read_text())
 assert standalone['figures']==edition['figures']
 assert standalone==json.loads((ROOT/'publish/data/figures.json').read_text())
 print(f'Verified {len(entities)} shared figure identities: source evidence, all unchanged Here notes, consistent general text and one link per figure per passage.')
if __name__=='__main__':main()
