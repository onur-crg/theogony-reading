#!/usr/bin/env python3
"""Verify every released file and every selected generation record."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'pipeline'))
import build_reader

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

release = ROOT/'publish'
manifest = json.loads((release/'publication-manifest.json').read_text())
for relative, expected in manifest['files'].items():
    path = Path(relative)
    assert not path.is_absolute() and '..' not in path.parts, relative
    assert not any(part.startswith('.') for part in path.parts), relative
    assert digest(release/path) == expected, relative
records = list((ROOT/'pipeline/tests').glob('*.metrics.json'))
for record in records:
    data = json.loads(record.read_text())
    output = record.with_suffix('').with_suffix('.json')
    prompt = record.with_suffix('').with_suffix('.prompt.txt')
    assert digest(output) == data['output_sha256'], output
    assert digest(prompt) == data['prompt_sha256'], prompt
assert digest(ROOT/'sources/tlg0020.tlg001.perseus-grc2.xml') == '550bd27b82d0c1720d7592b9b170c18b6c0bf88d54318ab71a28eb2b17728826'
numbered, variant, headings = build_reader.load_sections()
assert len(numbered) == 65 and len(build_reader.load_verse_runs()) == 1022
assert len(build_reader.load_variant_verse_run()[0]) == 20
for filename in ['index.html','theogony-reader.html','translation.html','imprint.html','privacy.html','reuse.html']:
    assert 'assets/site-analytics-v1.js' in (release/filename).read_text(), filename
print(f'Verified {len(manifest["files"])} release files, {len(records)} exact generation records, Greek source hash, 1,022 numbered verses and 20 variant verses.')

# Check the reusable data contract and every verse against the rendered reader.
from html.parser import HTMLParser
from jsonschema import Draft202012Validator, FormatChecker

data = json.loads((ROOT/'data/theogony.json').read_text())
schema = json.loads((ROOT/'data/theogony.schema.json').read_text())
Draft202012Validator.check_schema(schema)
Draft202012Validator(schema, format_checker=FormatChecker()).validate(data)
assert data == json.loads((release/'data/theogony.json').read_text())
assert schema == json.loads((release/'data/theogony.schema.json').read_text())
assert [p['id'] for p in data['passages']] == [f'p{i:03d}' for i in range(1,66)]
main_verses = [v for passage in data['passages'] for v in passage['verses']]
assert [v['label'] for v in main_verses] == [str(i) for i in range(1,1023)]
assert len(data['variants']) == 1 and data['variants'][0]['after_verse'] == '929'
extra_verses = data['variants'][0]['verses']
assert [v['label'] for v in extra_verses] == [f'929{chr(i)}' for i in range(ord('a'),ord('t')+1)]
assert data['variants'][0]['source_gaps_after'] == ['929f']
for exported, (section,path,metrics) in zip(data['passages']+data['variants'], numbered+[variant]):
    assert exported['summary'] == section['summary']
    assert exported['notes'] == section['cards']
    if section['id'] != 'v929':
        assert exported['title'] == headings[section['id']][2]
        assert exported['verse_range'] == {'start':str(section['start']),'end':str(section['end'])}
    assert exported['provenance']['summary_and_notes'] == metrics['run_id']
    if section.get('_note_updates'):
        assert exported['provenance']['note_updates'] == [m['run_id'] for _,m in section['_note_updates']]
    run_ids = [exported['provenance']['reading_text'], exported['provenance']['summary_and_notes']] + exported['provenance'].get('note_updates', []) + exported['provenance'].get('figure_registry', [])
    for run_id in run_ids:
        run = data['records'][run_id]
        assert digest(ROOT/run['output_file']) == run['output_sha256']
        assert digest(ROOT/run['prompt_file']) == run['prompt_sha256']
        metrics_record = json.loads((ROOT/run['record_file']).read_text())
        assert metrics_record['run_id'] == run_id
        assert (run['model'],run['reasoning_effort'],run['prompt_version']) == (metrics_record['model'],metrics_record['effort'],metrics_record['prompt_version'])

class ReaderVerses(HTMLParser):
    def __init__(self):
        super().__init__(); self.label = None; self.depth = 0; self.parts = []; self.verses = {}
    def handle_starttag(self,tag,attrs):
        a = dict(attrs); classes = a.get('class','').split()
        if tag == 'span' and 'verse-unit' in classes:
            self.label = a['id'][1:]
        if tag == 'span' and 'verse-text' in classes:
            self.depth = 1; self.parts = []
        elif self.depth:
            self.depth += 1
    def handle_data(self,text):
        if self.depth: self.parts.append(text)
    def handle_endtag(self,tag):
        if self.depth:
            self.depth -= 1
            if not self.depth:
                assert self.label not in self.verses
                self.verses[self.label] = ''.join(self.parts)

rendered = ReaderVerses(); rendered.feed((release/'theogony-reader.html').read_text())
exported_verses = {v['label']:v['text'] for v in main_verses+extra_verses}
assert rendered.verses == exported_verses, 'Export differs from the published reading text'
for v in main_verses+extra_verses:
    assert v['marked_for_deletion'] == (v['label'] in build_reader.DELETED_LABELS)
note_count = sum(len(p['notes']) for p in data['passages']+data['variants'])
assert note_count == sum(len(s['cards']) for s,_,_ in numbered+[variant])
print(f'Validated central JSON Schema and exact equality of all 1,042 rendered verses, 66 summaries, 65 section titles and {note_count} name notes.')

if (ROOT/'pipeline/note_revisions.json').exists():
    from check_name_notes import main as check_name_notes
    check_name_notes()

if (ROOT/'pipeline/figure_registry_runs.json').exists():
    from check_figure_registry import main as check_figure_registry
    check_figure_registry()
