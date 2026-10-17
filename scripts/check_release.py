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
