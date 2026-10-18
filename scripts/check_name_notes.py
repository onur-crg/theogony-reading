#!/usr/bin/env python3
"""Verify accepted note-only deltas, source evidence and real rendered link reachability."""
import hashlib,json,sys
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'pipeline'))
import build_reader as reader

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Links(HTMLParser):
 def __init__(self):super().__init__();self.targets=set()
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='a' and 'data-note' in a:self.targets.add(a['data-note'])

def main():
 audit_path=ROOT/'reviews/personifications-audit.json'
 audit=json.loads(audit_path.read_text())
 audit_metrics=json.loads(audit_path.with_suffix('.metrics.json').read_text())
 assert digest(audit_path)==audit_metrics['output_sha256']
 assert digest(audit_path.with_suffix('.prompt.txt'))==audit_metrics['prompt_sha256']
 assert [s['id'] for s in audit['sections']]==[f'p{i:03d}' for i in range(1,66)]+['v929']
 baseline={}
 for path in reader.INPUTS:
  for section in json.loads(path.read_text())['sections']:baseline[section['id']]=section
 numbered,variant,_=reader.load_sections(resolve_registry=False);current={s['id']:s for s,_,_ in numbered+[variant]}
 verses=reader.load_verse_runs();extra=reader.load_variant_verse_run()[0]
 from xml.etree import ElementTree as ET
 greek={e.get('n'):' '.join(''.join(e.itertext()).split()) for e in ET.parse(reader.GREEK_SOURCE).getroot().iter('{http://www.tei-c.org/ns/1.0}l')}
 all_revised={}
 expected_by_section={sid:{c['id']:c for c in section['cards']} for sid,section in baseline.items()}
 evidence_by_card={}
 for filename in json.loads((ROOT/'pipeline/note_revisions.json').read_text()):
  path=reader.TESTS/filename;run=json.loads(path.read_text());metrics=json.loads(path.with_suffix('.metrics.json').read_text())
  assert digest(path)==metrics['output_sha256']
  assert digest(path.with_suffix('.prompt.txt'))==metrics['prompt_sha256']
  assert metrics['source_sha256']==digest(reader.GREEK_SOURCE)
  assert metrics['tool_event_count']==0 and metrics['cli_exit']==0
  for revision in run['sections']:
   sid=revision['id'];old=baseline[sid];new=current[sid]
   for field in ['id','start','end','heading','translation','summary']:assert new[field]==old[field],(sid,field)
   expected=expected_by_section[sid]
   for card_id in revision['remove_ids']:
    assert card_id in expected,(sid,card_id)
    expected.pop(card_id)
   expected.update({c['id']:c for c in revision['cards']})
   evidence={e['card_id']:e for e in revision['evidence']}
   texts=extra if sid=='v929' else {str(n):verses[n][0] for n in range(new['start'],new['end']+1)}
   links=Links()
   for n,text in texts.items():links.feed(reader.linked_text(text,new,n))
   for card in revision['cards']:
    assert card['id'] in evidence,(sid,card['id'],'missing Greek evidence')
    assert evidence[card['id']]['verse'] in texts,(sid,card['id'],'bad source verse')
    e=evidence[card['id']]
    assert e['greek'] in greek[e['verse']],(sid,card['id'],'Greek quote does not occur in stated verse')
    assert set(card.get('verse_labels',[]))<=texts.keys(),(sid,card['id'],'bad link scope')
    all_revised[(sid,card['id'])]=card
    evidence_by_card[(sid,card['id'])]=evidence[card['id']]
 for sid,expected in expected_by_section.items():
  assert {c['id']:c for c in current[sid]['cards']}==expected,sid
 for (sid,card_id),card in all_revised.items():
  new=current[sid]
  texts=extra if sid=='v929' else {str(n):verses[n][0] for n in range(new['start'],new['end']+1)}
  links=Links()
  for n,text in texts.items():links.feed(reader.linked_text(text,new,n))
  index=next(i for i,c in enumerate(new['cards']) if c['id']==card_id)
  assert f'note-{sid}-{index}' in links.targets,(sid,card_id,'no actual rendered link')
 # Doris must distinguish the mother and her namesake daughter at actual occurrences.
 if 'p020' in current and current['p020'].get('_note_updates'):
  s=current['p020'];targets=[]
  for n in [241,250]:
   html=reader.linked_text(verses[n][0],s,n)
   import re
   match=re.search(r'data-note="([^"]+)"[^>]*>Doris</a>',html);assert match,(n,html)
   targets.append(match.group(1))
  assert targets[0]!=targets[1],targets
 # Catalogue coverage is checked from the named source list, not just from the
 # set of cards returned by the generator.
 import re
 catalogues = {
  'p018': ['Strife','Toil','Forgetfulness','Hunger','Sorrows','Clashes','Battles','Murders','Slaughter','Quarrels','lying Words','Arguments','Lawlessness','Ruin','Oath'],
  'p020': 'Ploto Eucrante Sao Amphitrite Eudora Thetis Galene Glauce Cymothoe Speio Thoe Halia Pasithea Erato Eunice Melite Eulimene Agave Doto Proto Pherusa Dynamene Nesaea Actaea Protomedea Doris Panopea Galatea Hippothoe Hipponoe Cymodoce Cymatolege Cymo Eione Halimede Glauconome Pontoporea Leagora Euagora Laomedea Polynoe Autonoe Lysianassa Euarne Psamathe Menippe Neso Eupompe Themisto Pronoe'.split(),
  'p057': 'Eunomia Dike Eirene Clotho Lachesis Atropos Aglaia Euphrosyne Thalia'.split(),
 }
 assert len(catalogues['p020']) == 50
 for sid,names in catalogues.items():
  section=current[sid]
  for name in names:
   occurrences=[]
   for n in range(section['start'],section['end']+1):
    text=verses[n][0]
    if re.search(r'(?<!\w)'+re.escape(name)+r'(?!\w)',text):
     html=reader.linked_text(text,section,n)
     # Every occurrence must be inside a glossary link, possibly a group link.
     linked=' '.join(re.findall(r'<a class="term"[^>]*>(.*?)</a>',html))
     assert re.search(r'(?<!\w)'+re.escape(name)+r'(?!\w)',linked),(sid,n,name)
     occurrences.append(n)
   assert occurrences,(sid,name)
 print(f'Verified {len(all_revised)} revised/new cards: exact output, original summaries/text, Greek evidence, verse scopes and reachable links. All 50 Nereids and the personification catalogues are linked.')
if __name__=='__main__':main()
