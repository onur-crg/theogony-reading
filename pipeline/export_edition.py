#!/usr/bin/env python3
"""Export the exact reading edition, without rewriting any generated content."""
from pathlib import Path
import hashlib
import json
import build_reader as reader
from site_seo import SITE_URL

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT/'data'

def make_edition():
    numbered, variant, headings = reader.load_sections()
    verse_runs = reader.load_verse_runs()
    variant_verses, variant_path, variant_metrics = reader.load_variant_verse_run()
    records = {}
    def reference(path, metrics):
        run_id = metrics['run_id']
        record = {
            'model': metrics['model'], 'reasoning_effort': metrics['effort'],
            'prompt_version': metrics['prompt_version'],
            'output_file': path.relative_to(ROOT).as_posix(),
            'prompt_file': path.with_suffix('.prompt.txt').relative_to(ROOT).as_posix(),
            'record_file': path.with_suffix('.metrics.json').relative_to(ROOT).as_posix(),
            'output_sha256': metrics['output_sha256'], 'prompt_sha256': metrics['prompt_sha256'],
        }
        if run_id in records:
            assert records[run_id] == record, run_id
        records[run_id] = record
        return run_id
    def note_provenance(section, path, metrics):
        result = {'summary_and_notes': reference(path, metrics)}
        if section.get('_note_updates'):
            result['note_updates'] = [reference(p, m) for p, m in section['_note_updates']]
        if section.get('_figure_registry_records'):
            result['figure_registry'] = [reference(p,m) for p,m in section['_figure_registry_records']]
        return result
    from figure_registry import load_registry
    registry,_,_ = load_registry()
    figures = {eid: {'id':eid,'name':entry['name'],'kind':entry['kind'],
                     'general':entry['general'],'evidence':entry['evidence'],
                     'provenance':reference(entry['_path'],entry['_metrics'])}
               for eid,entry in registry.items()}
    passages = []
    for section, note_path, note_metrics in numbered:
        start, end = section['start'], section['end']
        _, reading_path, reading_metrics = verse_runs[start]
        assert all(verse_runs[n][1] == reading_path for n in range(start,end+1))
        passages.append({
            'id': section['id'], 'title': headings[section['id']][2],
            'verse_range': {'start': str(start), 'end': str(end)},
            'reader_url': SITE_URL+'/theogony-reader.html#'+section['id'],
            'summary': section['summary'],
            'verses': [{'label': str(n), 'text': verse_runs[n][0],
                        'marked_for_deletion': str(n) in reader.DELETED_LABELS}
                       for n in range(start,end+1)],
            'notes': section['cards'],
            'provenance': {'reading_text': reference(reading_path,reading_metrics),
                           **note_provenance(section,note_path,note_metrics)},
        })
    section, note_path, note_metrics = variant
    extra = {
        'id': 'v929', 'title': 'Additional lines after verse 929',
        'verse_range': {'start': '929a', 'end': '929t'},
        'reader_url': SITE_URL+'/theogony-reader.html#variant-929',
        'after_verse': '929', 'source_gaps_after': ['929f'],
        'summary': section['summary'],
        'verses': [{'label': label, 'text': text,
                    'marked_for_deletion': label in reader.DELETED_LABELS}
                   for label,text in variant_verses.items()],
        'notes': section['cards'],
        'provenance': {'reading_text': reference(variant_path,variant_metrics),
                       **note_provenance(section,note_path,note_metrics)},
    }
    return {
        '$schema': SITE_URL+'/data/theogony.schema.json',
        'schema_version': '1.0.0', 'id': 'hesiod-theogony-en',
        'title': 'Theogony', 'author': 'Hesiod', 'language': 'en',
        'website': SITE_URL+'/',
        'editorial': {
            'status': 'ai-assisted-reading-edition',
            'independent_review': 'pending',
            'note': 'Passage titles, summaries and name notes are editorial reading aids, not part of Hesiod’s poem. Recorded generation outputs can contain errors. A deletion mark records the Greek edition’s textual judgement, not a reported translation error.',
        },
        'licence': {
            'id': 'CC-BY-4.0', 'url': 'https://creativecommons.org/licenses/by/4.0/',
            'attribution': 'Hesiod, Theogony, AI-assisted English reading edition by Onur Cirag. Source: '+SITE_URL+'/. CC BY 4.0. State any changes.',
            'scope': 'Original edition content to the extent rights are held. No rights are created over public-domain or unprotected AI-generated material. The Greek XML has separate terms.',
        },
        'source': {
            'language': 'grc', 'editor': 'Hugh G. Evelyn-White', 'edition_year': 1914,
            'digitisation': 'Perseus Project, Tufts University',
            'greek_xml': 'sources/tlg0020.tlg001.perseus-grc2.xml',
            'greek_xml_sha256': hashlib.sha256(reader.GREEK_SOURCE.read_bytes()).hexdigest(),
            'licence_notice': 'sources/perseus-license.md',
            'section_titles': 'content/leseabsaetze.md',
        },
        'passages': passages, 'variants': [extra], 'figures': figures, 'records': records,
    }

def main():
    DATA.mkdir(exist_ok=True)
    data = make_edition()
    (DATA/'theogony.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    figure_records = {entry['provenance'] for entry in data['figures'].values()}
    shared = {'schema_version':'1.0.0','figures':data['figures'],'licence':data['licence'],'source':data['source'],
              'records':{key:data['records'][key] for key in sorted(figure_records)}}
    (DATA/'figures.json').write_text(json.dumps(shared,ensure_ascii=False,indent=2)+'\n')
    print(f'Exported {len(data["passages"])} passages and {len(data["variants"])} separate variant with unchanged text and notes.')

if __name__ == '__main__': main()
