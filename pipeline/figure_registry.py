"""Resolve shared figure identities while preserving recorded passage context."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
CONFIG=ROOT/'pipeline/figure_registry_runs.json'

def load_registry():
    entities={};local=set();records=[]
    if not CONFIG.exists():return entities,local,records
    for filename in json.loads(CONFIG.read_text()):
        path=ROOT/'pipeline/tests'/filename
        run=json.loads(path.read_text());metrics=json.loads(path.with_suffix('.metrics.json').read_text())
        records.append((path,metrics))
        local.update((c['section_id'],c['card_id']) for c in run['local_cards'])
        assert len({e['id'] for e in run['entities']})==len(run['entities'])
        for entity in run['entities']:
            entities[entity['id']]={**entity,'_path':path,'_metrics':metrics}
    return entities,local,records

def apply_registry(items):
    entities,local,_=load_registry()
    if not entities:return items
    bindings={}
    for eid,entity in entities.items():
        assert entity['evidence'],eid
        for binding in entity['bindings']:
            key=(binding['section_id'],binding['card_id'])
            bindings.setdefault(key,[]).append((eid,binding))
    known={(s['id'],c['id']) for s,_,_ in items for c in s['cards']}
    assert not (bindings.keys() & local), 'A card cannot be both figure and local definition'
    assert bindings.keys() | local == known, ('Registry coverage mismatch', known-(bindings.keys()|local), (bindings.keys()|local)-known)
    # These recorded cards combine a place with a divine epithet. Preserve the
    # original place explanation alongside the new shared figure identity.
    retained_places = {('p015','p015-cythera'): ['Cythera'],
                       ('p015','p015-cyprus'): ['Cyprus']}
    resolved=[]
    for section,path,metrics in items:
        section=dict(section);cards=[];used={}
        for original in section['cards']:
            matches=bindings.get((section['id'],original['id']),[])
            if not matches:
                cards.append(original);continue
            assert len({eid for eid,_ in matches})==len(matches)
            places = retained_places.get((section['id'],original['id']), [])
            for alias in places:
                cards.append({**original,'id':original['id']+'--place',
                              'label':alias,'aliases':[alias],'origin_card_id':original['id']})
            for eid,binding in matches:
                entity=entities[eid]
                card={**original,'id':original['id'] if len(matches)==1 and not places else original['id']+'--'+eid,
                      'label':entity['name'],'general':entity['general'],
                      'entity_id':eid,'origin_card_id':original['id'],
                      'aliases':binding['aliases']}
                cards.append(card)
                used[entity['_metrics']['run_id']]=(entity['_path'],entity['_metrics'])
        section['cards']=cards
        section['_figure_registry_records']=list(used.values())
        resolved.append((section,path,metrics))
    return resolved
