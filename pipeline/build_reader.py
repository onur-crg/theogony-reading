#!/usr/bin/env python3
"""Build a self-contained reading view from unchanged, tracked translation runs."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET
from site_seo import metadata, write_discovery_files
from site_legal import DOCUMENT_STYLE, BACK_LINK, BACK_STYLE, BACK_SCRIPT, document_header, document_footer, render_legal_pages

ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "pipeline" / "tests"
OUTPUT = ROOT / "theogony-reader.html"
INFO_OUTPUT = ROOT / "translation.html"
HOME_OUTPUT = ROOT / "index.html"
OUTLINE = ROOT / "content" / "leseabsaetze.md"
GREEK_SOURCE = ROOT / "sources" / "tlg0020.tlg001.perseus-grc2.xml"


def deleted_verse_labels() -> set[str]:
    root = ET.parse(GREEK_SOURCE).getroot()
    return {line.get('n') for line in root.iter('{http://www.tei-c.org/ns/1.0}l')
            if any(child.tag.rsplit('}', 1)[-1] == 'del' for child in line.iter())}


DELETED_LABELS = deleted_verse_labels()

EARLY = [TESTS / f"batch-2026-10-15-{a:03d}-{b:03d}.json" for a, b in
         ((1, 62), (63, 115), (116, 173), (174, 225), (226, 286), (287, 336))]
REMAINDER = [TESTS / f"remainder-2026-10-16-{a:03d}-{b:03d}.json" for a, b in
             ((337, 382), (383, 428), (429, 484), (485, 534), (535, 589),
              (590, 653), (654, 710), (711, 774), (775, 838), (839, 900),
              (901, 962), (963, 1022))]
IMPROVED = [TESTS / f"cli-{a}-{b}-reader-16-v3.json" for a, b in
            ((53, 62), (94, 103), (265, 286))]
VARIANT = TESTS / "variant-929a-929t-2026-10-16-v2.json"
INPUTS = EARLY + REMAINDER + IMPROVED + [VARIANT]
VERSE_RANGES = [(1,52),(53,62),(63,115),(116,173),(174,225),(226,286),(287,336),
                (337,382),(383,428),(429,484),(485,534),(535,589),(590,653),
                (654,710),(711,774),(775,838),(839,900),(901,962),(963,1022)]


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def outline() -> dict[str, tuple[int, int, str]]:
    result = {}
    pattern = re.compile(r"^\| (p\d{3}) \| (\d+)[–-](\d+) \| (.*?) \|$")
    for line in OUTLINE.read_text().splitlines():
        match = pattern.match(line)
        if match:
            sid, start, end, heading = match.groups()
            result[sid] = (int(start), int(end), heading)
    return result


def aliases(section: dict) -> dict[str, int]:
    found = {card["label"]: i for i, card in enumerate(section["cards"])}
    for i, card in enumerate(section["cards"]):
        label = card["label"]
        if label.startswith("The ") and label[4:5].isupper():
            found.setdefault(label[4:], i)
        if " / " in label:
            parts = label.split(" / ")
        elif " and " in label:
            parts = label.split(" and ")
        else:
            parts = []
        if parts and all(part[:1].isupper() and part.replace("-", "").isalpha()
                         for part in parts):
            for part in parts:
                found.setdefault(part, i)
        if ", the " in label:
            first = label.split(", the ", 1)[0]
            if first[:1].isupper() and first.isalpha():
                found.setdefault(first, i)
    return found


def linked_text(text: str, section: dict) -> str:
    """Escape agent text, adding links only around matching card labels."""
    mapping = aliases(section)
    keys = sorted(mapping, key=len, reverse=True)
    pattern = re.compile(r"(?<!\w)(?:" + "|".join(re.escape(k) for k in keys) + r")(?!\w)", re.I) if keys else None
    pieces = []
    cursor = 0
    for match in pattern.finditer(text) if pattern else []:
        pieces.append(esc(text[cursor:match.start()]))
        label = match.group(0)
        index = next(mapping[key] for key in keys if key.casefold() == label.casefold())
        target = f"note-{section['id']}-{index}"
        pieces.append(f'<a class="term" href="#{target}" data-note="{target}" aria-label="Explain {esc(label)}">{esc(label)}</a>')
        cursor = match.end()
    pieces.append(esc(text[cursor:]))
    return ''.join(pieces)


def linked_paragraphs(section: dict) -> str:
    return ''.join('<p>' + linked_text(paragraph, section).replace('\n','<br>') + '</p>'
                   for paragraph in re.split(r"\n\s*\n", section["translation"].strip()))


def load_verse_runs():
    result = {}
    for a,b in VERSE_RANGES:
        suffix = '-v2' if (a,b)==(53,62) else ''
        path = TESTS / f'verse-aligned-2026-10-16-{a:03d}-{b:03d}{suffix}.json'
        data = json.loads(path.read_text())
        metrics = json.loads(path.with_suffix('.metrics.json').read_text())
        assert [v['n'] for v in data['verses']] == list(range(a,b+1)),path
        assert metrics['prompt_version'] == 'verse-aligned-16-v2',path
        for verse in data['verses']:
            result[verse['n']] = (verse['text'],path,metrics)
    assert set(result)==set(range(1,1023))
    # A focused, tracked regeneration replaces the problematic relationship passage.
    override = TESTS / 'verse-aligned-2026-10-16-265-286-v3.json'
    data = json.loads(override.read_text())
    metrics = json.loads(override.with_suffix('.metrics.json').read_text())
    assert metrics['prompt_version'] == 'verse-aligned-16-v3'
    assert [v['n'] for v in data['verses']] == list(range(265,287))
    for verse in data['verses']:
        result[verse['n']] = (verse['text'],override,metrics)
    return result


def linked_verses(section: dict, verse_runs: dict) -> str:
    lines=[]
    for n in range(section['start'],section['end']+1):
        text,_,_=verse_runs[n]
        disputed = str(n) in DELETED_LABELS
        klass = 'verse-unit disputed' if disputed else 'verse-unit'
        marker = '<span class="dagger" aria-hidden="true">†</span>' if disputed else ''
        label = f'Verse {n}, marked for deletion in the Greek source' if disputed else f'Verse {n}'
        lines.append(f'<span class="{klass}" id="v{n}"><sup class="verse-number" aria-label="{label}">{n}{marker}</sup>&nbsp;<span class="verse-text">{linked_text(text,section)}</span></span>')
    return '<p class="verse-flow">'+' '.join(lines)+'</p>'


def load_variant_verse_run():
    path = TESTS / 'verse-aligned-2026-10-16-929a-929t.json'
    data = json.loads(path.read_text())
    metrics = json.loads(path.with_suffix('.metrics.json').read_text())
    expected = [f'929{chr(c)}' for c in range(ord('a'),ord('t')+1)]
    assert [v['n'] for v in data['verses']] == expected
    return {v['n']:v['text'] for v in data['verses']}, path, metrics


def linked_variant_verses(section: dict, variant_run) -> str:
    lines,_,_ = variant_run
    output=[]
    group=[]
    for label,text in lines.items():
        disputed = label in DELETED_LABELS
        klass = 'verse-unit disputed' if disputed else 'verse-unit'
        marker = '<span class="dagger" aria-hidden="true">†</span>' if disputed else ''
        aria = f'Verse {label}, marked for deletion in the Greek source' if disputed else f'Verse {label}'
        group.append(f'<span class="{klass}" id="v{label}"><sup class="verse-number" aria-label="{aria}">{label}{marker}</sup>&nbsp;<span class="verse-text">{linked_text(text,section)}</span></span>')
        if label == '929f':
            output.append('<p class="verse-flow">'+' '.join(group)+'</p>')
            output.append('<p class="variant-gap">Gap in the Greek source after 929f</p>')
            group=[]
    if group:
        output.append('<p class="verse-flow">'+' '.join(group)+'</p>')
    return ''.join(output)


def load_sections():
    selected = {}
    for path in INPUTS:
        data = json.loads(path.read_text())
        metrics = json.loads(path.with_suffix(".metrics.json").read_text())
        for section in data["sections"]:
            selected[section["id"]] = (section, path, metrics)
    expected = outline()
    assert set(selected) == set(expected) | {"v929"}, (set(selected) ^ (set(expected) | {"v929"}))
    numbered = [selected[f"p{i:03d}"] for i in range(1, 66)]
    for section, _, _ in numbered:
        start, end, _ = expected[section["id"]]
        assert (section["start"], section["end"]) == (start, end), section["id"]
    return numbered, selected["v929"], expected


def render_section(item, headings, verse_runs=None, variant_run=None, variant=False):
    section, path, metrics = item
    sid = section["id"]
    start, end = section["start"], section["end"]
    heading = "Additional lines after verse 929" if variant else headings[sid][2]
    range_text = "929a–929t" if variant else f"{start}–{end}"
    title_tag = "h3" if variant else "h2"
    classes = "passage variant" if variant else "passage"
    article_id = 'variant-929' if variant else sid
    result = [f'<article class="{classes}" data-range="{start}–{end}" id="{article_id}" aria-labelledby="title-{sid}">',
              '<header class="passage-head">',
              f'<{title_tag} id="title-{sid}"><a class="title-link" href="#summary-{sid}" data-summary="summary-{sid}" aria-label="Read summary of {esc(heading)}">{esc(heading)}</a></{title_tag}>',
              '</header>']
    if variant:
        result.append('<p class="variant-note">These extra lines are a separate textual variant. They are outside the 1,022 numbered verses. The Greek source has a gap after 929f, and 929s is marked as disputed.</p>')
    if variant_run is not None:
        result.append(f'<div class="reading-text verse-lines">{linked_variant_verses(section,variant_run)}</div>')
    elif verse_runs is None:
        result.append(f'<div class="reading-text"><span class="verse-marker" aria-label="Verses {esc(range_text)}">{esc(range_text)}</span>{linked_paragraphs(section)}</div>')
    else:
        result.append(f'<div class="reading-text verse-lines">{linked_verses(section,verse_runs)}</div>')
    if not variant and verse_runs is not None and any(str(n) in DELETED_LABELS for n in range(start, end + 1)):
        result.append('<details class="textual-note"><summary>About the † mark</summary><p>The Greek edition marks these lines for deletion. They are included here with † so you can recognise the edition’s textual judgement. This concerns the Greek source, rather than a reported translation error. <a href="translation.html">About the text and translation</a></p></details>')
    result.append(f'<aside class="summary-fallback" id="summary-{sid}" aria-label="Summary"><p>{esc(section["summary"])}</p><a href="#{article_id}">Back to passage</a></aside>')
    result.append('</article>')
    return ''.join(result)


def run_documents(path: Path, label: str) -> str:
    prompt = path.with_suffix('.prompt.txt')
    record = path.with_suffix('.metrics.json')
    assert prompt.is_file() and record.is_file(), path
    return (f'<a href="pipeline/tests/{esc(prompt.name)}" aria-label="{esc(label)} prompt">Prompt</a>'
            f'<a href="pipeline/tests/{esc(record.name)}" aria-label="{esc(label)} run record">Record</a>')


def render_information(numbered, variant, headings, verse_runs, variant_run):
    rows = []
    for section, path, metrics in numbered + [variant]:
        sid = section['id']
        is_variant = sid == 'v929'
        start, end = section['start'], section['end']
        heading = 'Additional lines after verse 929' if is_variant else headings[sid][2]
        range_text = '929a–929t' if is_variant else f'{start}–{end}'
        article_id = 'variant-929' if is_variant else sid
        if is_variant:
            _, verse_path, verse_metrics = variant_run
        else:
            _, verse_path, verse_metrics = verse_runs[start]
            assert all(verse_runs[n][1] == verse_path for n in range(start, end + 1))
        rows.append(
            f'<li class="passage-record" id="info-{sid}"><header class="record-heading"><span class="range">{esc(range_text)}</span>'
            f'<a class="record-title" href="theogony-reader.html#{article_id}">{esc(heading)}</a></header>'
            '<div class="record-body"><section class="record-group" aria-label="Reading text provenance"><h3>Reading text</h3>'
            f'<p class="record-model">{esc(verse_metrics["model"])} · {esc(verse_metrics["effort"])} · {esc(verse_metrics["prompt_version"])}</p>'
            f'<nav class="record-documents" aria-label="Reading text documents for {esc(heading)}">{run_documents(verse_path, "Reading text")}</nav></section>'
            '<section class="record-group" aria-label="Summary and notes provenance"><h3>Summary &amp; notes</h3>'
            f'<p class="record-model">{esc(metrics["model"])} · {esc(metrics["prompt_version"])}</p>'
            f'<nav class="record-documents" aria-label="Summary and notes documents for {esc(heading)}">{run_documents(path, "Summary and notes")}</nav></section></div></li>'
        )
    info_style = """
    :root{--paper:#dedede;--ink:#1b2c48;--green:#075fce;--muted:#61748d;--line:#cbd5e2}
    *{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:2rem}body{margin:0;background:var(--paper);color:var(--ink);font:1rem/1.6 'Helvetica Neue',-apple-system,Arial,sans-serif}a{color:var(--green);text-underline-offset:.2em}a:focus-visible{outline:3px solid #b08a48;outline-offset:4px}.wrap{max-width:56rem;margin:auto;padding:2rem clamp(1.25rem,5vw,3rem) 5rem}.back{text-decoration:none;font-weight:600}.privacy-action{padding:.7rem 1rem;border:1px solid var(--green);border-radius:.4rem;background:transparent;color:var(--green);font:inherit;cursor:pointer}h1,h2{font-family:Baskerville,Didot,'Iowan Old Style',Georgia,serif;font-weight:400;-webkit-text-stroke:.3px currentColor;line-height:1.13}h1{font-size:clamp(3rem,7vw,5.5rem);margin:3rem 0 1rem}h2{font-size:clamp(2.15rem,5vw,3.1rem);margin:0 0 1rem}.intro{max-width:42rem;color:var(--muted);font-size:1.1rem}.section{padding:3rem 0;border-bottom:1px solid var(--line)}.index{display:flex;flex-wrap:wrap;gap:.5rem 1.4rem;margin:2rem 0}.index a{white-space:nowrap}.runs{list-style:none;padding:0;margin:1.5rem 0}.runs li{padding:1.15rem 0;border-bottom:1px solid var(--line);scroll-margin-top:2rem}.info-heading{display:flex;gap:1rem;align-items:baseline;font-size:1.1rem;font-weight:600}.range{min-width:6.5rem;color:var(--muted);font-size:.82rem;font-variant-numeric:tabular-nums}.runs p{margin:.2rem 0 .2rem 7.5rem;color:var(--muted);font-size:.87rem}.runs p a{color:var(--green)}.placeholder{max-width:42rem;padding:1rem 1.2rem;border:1px solid var(--line);border-radius:.5rem;background:#fffefb}.footer{padding:2rem 0;font-size:.85rem;color:var(--muted)}@media(max-width:600px){.info-heading{display:block}.range{display:block}.runs p{margin-left:0}}
    """
    info_style += """a:focus-visible{outline-color:#075fce}.placeholder{background:#f7f9fc}.back{display:inline-block}.index a{padding:.35rem 0}::selection{background:#b8d5f6;color:#1b2c48}h1,h2{font-family:Optima,'Avenir Next',Arial,sans-serif;font-weight:800;text-transform:uppercase;letter-spacing:.005em;-webkit-text-stroke:0}h1{font-size:clamp(2.7rem,6vw,4.8rem)}h2{font-size:clamp(1.9rem,4vw,2.7rem)}"""
    edition_style = r"""
.edition-page{padding-top:2.6rem;max-width:54rem}.edition-hero{max-width:43rem;margin:0 auto 2rem;text-align:center}.edition-kicker{font-size:.72rem;letter-spacing:.15em;font-weight:700;color:var(--green);text-transform:uppercase;margin:0 0 .8rem}.edition-page h1{font-size:clamp(2.8rem,7vw,4.6rem);color:var(--green);margin:0 0 1.25rem;line-height:1}.edition-lead{font-size:clamp(1.15rem,2.4vw,1.4rem);line-height:1.5;max-width:34rem;margin:0 auto}.edition-note{max-width:40rem;text-align:left;margin:0 auto;padding:.8rem 0 1.8rem}.edition-note h2{font:700 1.05rem/1.5 'Helvetica Neue',Arial,sans-serif;margin:0 0 .7rem;text-transform:none;letter-spacing:0}.edition-note p{font-size:.95rem;line-height:1.75;margin:0 0 .8rem;color:var(--muted)}.edition-note p:last-child{margin-bottom:0}.edition-page .document-footer{margin-top:1.5rem}.passage-catalog{max-width:40rem;margin:0 auto;padding-top:1.6rem;border-top:1px solid var(--line)}.catalog-heading{text-align:left}.catalog-heading h2{font-size:clamp(1.65rem,4vw,2.3rem);text-transform:none;margin:0 0 .6rem}.catalog-heading p{font-size:.9rem;margin:0;color:var(--muted)}.edition-page .runs{margin:1.5rem 0;list-style:none}.edition-page .runs li{display:grid;grid-template-columns:3.8rem minmax(0,1fr);column-gap:1.1rem;padding:1.7rem 0;border:0;border-bottom:1px solid #b4c0ce;scroll-margin-top:1.5rem}.edition-page .runs li[hidden]{display:none}.record-heading{display:contents}.record-heading .range{grid-column:1;grid-row:1/3;min-width:0;font:.82rem/1.6 'Helvetica Neue',Arial,sans-serif;color:var(--muted);padding-top:.15rem;font-variant-numeric:tabular-nums}.record-title{grid-column:2;display:block;font:800 clamp(1.1rem,2.6vw,1.35rem)/1.3 Optima,'Avenir Next',Georgia,serif;text-decoration:none;color:var(--ink);margin:0 0 1rem}.record-title:hover{color:var(--green)}.record-body{grid-column:2;display:grid;gap:.9rem}.record-group{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:.15rem 1rem;min-width:0}.record-group h3{grid-column:1;grid-row:1;font:500 .8rem/1.5 'Helvetica Neue',Arial,sans-serif;color:var(--ink);margin:0}.edition-page .record-body p{grid-column:1/-1;grid-row:2;margin:0;font:.7rem/1.6 'Helvetica Neue',Arial,sans-serif;color:var(--muted);overflow-wrap:anywhere}.record-documents{grid-column:2;grid-row:1;display:flex;gap:.8rem;align-items:baseline}.record-documents a{font-size:.75rem;line-height:1.5;color:var(--green);text-decoration:underline;text-decoration-thickness:1px;text-decoration-color:#075fce55;text-underline-offset:.2em}.record-documents a:hover{text-decoration-color:var(--green)}.passage-record:target .record-title{color:var(--green)}.record-search{display:block;margin:1.1rem 0;color:var(--muted);font-size:.85rem}.record-search[hidden]{display:none}.record-search input{display:block;width:100%;margin-top:.5rem;padding:.8rem 1rem;border:1px solid #9db2cc;border-radius:.5rem;background:transparent;color:var(--ink);font:inherit}.record-search input:focus-visible{outline:2px solid var(--green);outline-offset:2px}.record-empty{color:var(--muted)}.passage-record:target{scroll-margin-top:1rem}.passage-record:target .record-title{color:var(--green)}
@media(max-width:650px){.edition-page{padding-top:2rem}.edition-hero{margin-bottom:1.5rem}.edition-note{padding:1.3rem 0 1.6rem}.edition-note p{font-size:.9rem}.edition-page .runs li{grid-template-columns:2.8rem minmax(0,1fr);column-gap:.8rem;padding:1.4rem 0}}@media(max-width:400px){.edition-page .runs li{grid-template-columns:1fr}.record-heading .range{grid-column:1;grid-row:auto;margin-bottom:.4rem;font-size:.72rem}.record-title,.record-body{grid-column:1}.record-group{column-gap:.6rem}.record-documents{gap:.6rem}}

"""
    records_script = r"""
const search=document.getElementById('record-search'),records=[...document.querySelectorAll('.runs>li')];
document.getElementById('record-search-label').hidden=false;
search.addEventListener('input',()=>{const query=search.value.toLowerCase().trim().replace(/[–—]/g,'-');let count=0;for(const row of records){const text=row.querySelector('.record-heading').textContent.toLowerCase().replace(/[–—]/g,'-');row.hidden=!text.includes(query);if(!row.hidden)count++}document.getElementById('record-empty').hidden=count>0});
function openLinkedRecord(){const id=location.hash.slice(1);if(!id.startsWith('info-'))return;const record=document.getElementById(id);if(record){search.value='';records.forEach(row=>row.hidden=false);document.getElementById('record-empty').hidden=true;requestAnimationFrame(()=>record.scrollIntoView({block:'start'}))}}
openLinkedRecord();addEventListener('hashchange',openLinkedRecord);
"""
    common_style = info_style + DOCUMENT_STYLE + edition_style
    page = [
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        metadata('translation.html'), '<style>', common_style,
        '</style></head><body>', document_header(), '<main class="wrap edition-page">',
        '<header class="edition-hero"><h1>Translation</h1>',
        '<p class="edition-lead">A modern English reading of Hesiod’s <em>Theogony</em>.</p></header>',
        '<section class="edition-note" aria-labelledby="source-title"><h2 id="source-title">From the Greek</h2><p>Based on the <a href="sources/tlg0020.tlg001.perseus-grc2.xml">Perseus text</a>, edited by Hugh G. Evelyn-White (1914). The poem has 1,022 numbered verses; an additional variant follows verse 929.</p>',
        '<p>Titles, summaries and name notes are reading aids. A † identifies a line marked for deletion in the Greek edition.</p><p><a href="data/theogony.json" download="theogony.json">Download the edition as JSON</a> · <a href="https://github.com/onur-crg/theogony-reading/blob/main/data/README.md">Data format and examples</a></p></section>',
        '<section class="passage-catalog" aria-labelledby="catalog-title"><header class="catalog-heading"><h2 id="catalog-title">Passage records</h2><p>Sources, prompts and generation records for all 66 passages.</p></header>',
        '<label class="record-search" hidden id="record-search-label">Find a passage<input id="record-search" type="search" placeholder="Title or verse range" autocomplete="off" aria-controls="passage-records"></label>',
        '<ol class="runs" id="passage-records" aria-label="Sources for every passage">', ''.join(rows),
        '</ol><p class="record-empty" id="record-empty" role="status" hidden>No matching passages.</p></section>',
        document_footer('translation.html'), '</main><script>', BACK_SCRIPT, records_script,
        '</script></body></html>'
    ]
    INFO_OUTPUT.write_text(''.join(page))
    # Preserve the former record-page address and its fragment bookmarks.
    (ROOT / 'translation-records.html').write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta name="robots" content="noindex"><title>Passage records · Theogony</title></head>'
        '<body><p><a href="translation.html#passage-records">View the passage records</a></p>'
        '<script>location.replace("translation.html"+(location.hash||"#passage-records"));</script></body></html>')
    render_legal_pages(ROOT, info_style + DOCUMENT_STYLE)


def render_homepage(items):
    style = """
    :root{--paper:#dedede;--ink:#1b2c48;--blue:#075fce;--muted:#526780;--line:#b6c3d2}
    *{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font:1rem/1.5 'Helvetica Neue',-apple-system,Arial,sans-serif}a{color:inherit}a:focus-visible{outline:3px solid var(--blue);outline-offset:4px}::selection{background:#9ac4f6;color:var(--ink)}
    .shell{width:min(100% - clamp(2.5rem,8vw,7rem),1320px);margin:auto}.site-header{display:flex;justify-content:space-between;align-items:center;gap:1.5rem;padding:1.3rem 0;border-bottom:1px solid var(--line)}.wordmark{font:800 1.55rem/1 Optima,'Avenir Next',sans-serif;letter-spacing:.015em;text-decoration:none;color:var(--blue)}.site-nav{display:flex;gap:clamp(1rem,3vw,2rem);flex-wrap:wrap}.site-nav a{text-decoration:none;font-size:.92rem;font-weight:600}.site-nav a:hover{text-decoration:underline;text-underline-offset:.25em}
    .hero{padding:2rem 0 2.5rem;overflow:hidden}.hero-top,.hero-bottom{display:flex;justify-content:space-between;align-items:center;width:min(100% - 3rem,1100px);margin:0 auto;pointer-events:none}.hero-top{margin-bottom:.8rem}.hero-bottom{margin-top:1.5rem}.hero-motif{object-fit:contain;display:block;width:112px;height:112px;color:var(--blue);flex:0 0 auto}.hero-copy{text-align:center;width:min(100% - 3rem,680px);margin:0 auto;padding:0}.eyebrow{margin:0 0 .8rem;color:var(--blue);font-size:.8rem;font-weight:700;letter-spacing:.18em;text-transform:uppercase}.temple-mark{width:min(100%,620px);margin:0 auto 1.7rem;color:var(--blue);container-type:inline-size}.temple-capital,.temple-base{display:block;width:100%;height:auto;overflow:visible}.temple-capital{margin-bottom:-.55rem}.temple-base{margin-top:.1rem}.temple-mark svg{fill:none;stroke:currentColor;stroke-width:10;stroke-linecap:round;stroke-linejoin:round}.hero h1{margin:0;padding:0 5%;color:var(--blue);font:800 clamp(2rem,9vw,6rem)/.85 Optima,'Avenir Next',sans-serif;font-size:15cqw;letter-spacing:-.035em}.hero-copy>p:not(.eyebrow){max-width:630px;margin:0 auto;color:var(--blue);font-size:clamp(1.15rem,2.1vw,1.6rem);line-height:1.48}.actions{display:flex;justify-content:center;flex-wrap:wrap;gap:.75rem;margin-top:2rem}.button{display:inline-flex;align-items:center;justify-content:center;min-height:3.15rem;padding:.7rem 1.25rem;border:1.5px solid var(--blue);border-radius:999px;background:var(--blue);color:#fff;text-decoration:none;font-size:.9rem;font-weight:700}.button.secondary{background:var(--paper);color:var(--blue)}.button:hover{filter:brightness(.9)}
    .gods-section{background:var(--blue);color:var(--paper)}.gods-heading{margin:0;padding:2rem clamp(1.25rem,5vw,5rem) .5rem;font:800 clamp(1.4rem,3vw,2.6rem)/1.1 Optima,'Avenir Next',sans-serif;text-transform:uppercase;letter-spacing:.02em}.god-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr))}.god-button{display:flex;flex-direction:column;min-width:0;margin:0;padding:0;border:0;border-radius:0;background:none;color:inherit;font:inherit;cursor:pointer;text-align:center}.god-stage{display:block;padding:1rem .35rem 0;overflow:hidden}.god-art{display:block;width:100%;height:auto;overflow:hidden;transform-origin:50% 85%;transition:transform .25s ease}.god-name{display:flex;justify-content:center;align-items:center;gap:.65rem;width:100%;margin-top:auto;padding:1.15rem .5rem;background:var(--paper);color:var(--blue);font-size:.85rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase}.god-button:focus-visible{outline:3px solid var(--paper);outline-offset:-5px}.god-button:focus-visible .god-name{text-decoration:underline;text-underline-offset:.3em}@media(hover:hover) and (pointer:fine){.god-button:hover .god-art{transform:scale(1.045)}.god-button:hover .god-name{text-decoration:underline;text-underline-offset:.3em}}.god-button:focus-visible .god-art{transform:scale(1.045)}.god-dialog{width:min(28rem,calc(100% - 2rem));max-height:calc(100dvh - 3rem);padding:2rem;border:1px solid var(--blue);border-radius:1rem;background:var(--paper);color:var(--ink);box-shadow:0 1rem 4rem #10254430}.god-dialog::backdrop{background:#10254499}.god-dialog h2{margin:.6rem 2rem 1rem 0;color:var(--blue);font:800 2.5rem/1 Optima,'Avenir Next',sans-serif}.god-dialog p{line-height:1.6}.god-dialog .god-context-label{display:block;margin-bottom:.3rem;color:var(--muted);font-size:.7rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase}.god-dialog .god-read{display:inline-block;margin-top:.75rem;color:var(--blue);font-weight:600;text-underline-offset:.2em}.god-close{position:absolute;top:.7rem;right:.7rem;display:grid;place-items:center;width:2.5rem;height:2.5rem;border:0;border-radius:50%;background:none;color:var(--blue);font-size:1.8rem;cursor:pointer}.god-close:hover{background:#075fce15}
    .story{padding:5rem 0 6rem}.story-header{display:flex;justify-content:space-between;align-items:end;gap:2rem;margin-bottom:2.4rem}.story h2{margin:0;font:800 clamp(2.6rem,5vw,4.8rem)/1 Optima,'Avenir Next',sans-serif;color:var(--blue);letter-spacing:-.025em}.story-header p{max-width:25rem;margin:0;color:var(--muted)}.paths{display:grid;grid-template-columns:repeat(3,1fr);border-top:1px solid var(--blue);border-bottom:1px solid var(--blue)}.path{display:flex;flex-direction:column;gap:.8rem;min-width:0;padding:1.3rem;text-decoration:none}.passage-art{object-fit:contain;display:block;flex:none;width:100%;height:280px;margin:0 0 .7rem;overflow:hidden;transition:transform .2s ease}.path:hover .passage-art{transform:translateY(-3px)}.path+.path{border-left:1px solid var(--blue)}.path:hover{background:#d2def0}.path .range{font-size:.75rem;font-weight:700;letter-spacing:.12em;color:var(--blue)}.path strong{font:800 clamp(1.3rem,2.1vw,2rem)/1.15 Optima,'Avenir Next',sans-serif;color:var(--ink)}.path .path-cta{margin-top:auto;padding-top:.8rem;color:var(--muted);font-size:.9rem}.footer{display:flex;justify-content:space-between;gap:1.5rem;flex-wrap:wrap;padding:2rem 0;border-top:1px solid var(--line);font-size:.85rem}.footer p{margin:0;color:var(--muted)}.footer nav{display:flex;flex-wrap:wrap;gap:1rem}.footer a{color:var(--blue)}
    @media(max-width:1000px){.paths{display:block}.path{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);column-gap:2rem;row-gap:.75rem;align-items:center;padding:1.6rem 1rem}.path+.path{border-left:0;border-top:1px solid var(--blue)}.passage-art{grid-column:1;grid-row:1/4;height:290px;margin:0}.path .range,.path strong,.path .path-cta{grid-column:2}.path .range{align-self:end}.path strong{align-self:start;font-size:clamp(1.5rem,3vw,2rem)}.path .path-cta{align-self:start;margin-top:0;padding-top:0}.path .path-cta{white-space:normal}}@media(max-width:600px){.path{grid-template-columns:minmax(0,.9fr) minmax(0,1.1fr);column-gap:1rem}.passage-art{height:230px}.path strong{font-size:clamp(1.2rem,4.5vw,1.65rem)}.path .range{font-size:.65rem}.path .path-cta{font-size:.83rem}}@media(max-width:420px){.path{display:flex;align-items:stretch;gap:.75rem;padding:1.5rem .4rem}.passage-art{height:250px;margin-bottom:.5rem}.path strong{font-size:1.6rem}.path .path-cta{padding-top:.5rem}.path .range,.path strong,.path .path-cta{align-self:auto}}
    @media(max-width:850px){.hero-motif{width:96px;height:96px}.story-header{display:block}.story-header p{margin-top:1rem}}@media(max-width:600px){.site-header{flex-wrap:nowrap;gap:1rem;padding:1rem 0}.wordmark{font-size:1.25rem}.site-nav{width:auto;margin-left:auto;flex-direction:column;align-items:flex-end;gap:.25rem}.site-nav a{font-size:.78rem;line-height:1.4;font-weight:500}.hero{padding:1.25rem 0 1.5rem}.hero-top,.hero-bottom{width:calc(100% - 2rem)}.hero-top{margin-bottom:1rem}.hero-bottom{margin-top:1.25rem}.hero-motif{width:78px;height:78px}.hero-copy{width:calc(100% - 2rem)}.eyebrow{font-size:.65rem;letter-spacing:.13em}.actions{gap:.6rem;margin-top:1.5rem}.button{font-size:.83rem;padding:.7rem 1rem}.hero h1{font-size:15cqw}.temple-mark{margin-bottom:1.4rem}.temple-capital{margin-bottom:-.3rem}.temple-base{margin-top:.05rem}.hero-copy>p:not(.eyebrow){font-size:1.1rem}.gods-heading{font-size:1.35rem;padding:1.3rem 1rem .5rem}.god-stage{padding:.6rem .15rem 0}.god-name{font-size:.63rem;padding:.9rem .25rem;gap:.35rem}.god-dialog{padding:1.5rem}.story{padding:4rem 0}.paths{display:block}.path{padding:1.5rem 1rem}.path+.path{border-left:0;border-top:1px solid var(--blue)}}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}.passage-art,.god-art{transition:none}.path:hover .passage-art,.god-button:hover .god-art,.god-button:focus-visible .god-art{transform:none}}
    """
    # Generated from the existing art with the former SVG crop/colour transforms.
    # Standalone files are shared by the browser cache, not embedded in the HTML.
    artwork = json.loads((ROOT / 'assets/optimized/manifest.json').read_text())

    def artwork_image(key, css_class, *, lazy=False):
        art = artwork[key]
        assert (ROOT / art['file']).is_file(), art['file']
        loading = 'lazy' if lazy else 'eager'
        return (f'<img class="{css_class}" src="{art["file"]}" width="{art["width"]}" height="{art["height"]}" '
                f'alt="" aria-hidden="true" loading="{loading}" decoding="async">')

    def hero_motif(name, box):
        return artwork_image(name, f'hero-motif motif-{name}')

    def passage_art(filename):
        return artwork_image(filename.removesuffix('.png'), 'passage-art', lazy=True)

    hero_top = '<div class="hero-top">' + hero_motif('vase', (46, 86, 192, 263)) + hero_motif('scroll', (1267, 105, 250, 231)) + '</div>'
    hero_bottom = '<div class="hero-bottom">' + hero_motif('lyre', (18, 708, 188, 212)) + hero_motif('twig', (1296, 721, 195, 193)) + '</div>'
    god_specs = [('gaia', 'Gaia', 'p032', 0, 647), ('zeus', 'Zeus', 'p006', 647, 648), ('athena', 'Athena', 'p002', 1295, 647)]
    god_cards = {}
    god_buttons = []
    for key, name, sid, offset, width in god_specs:
        section = next(section for section, _, _ in items if section['id'] == sid)
        card = next(card for card in section['cards'] if card['label'] == name)
        god_cards[key] = {'name': name, 'general': card['general'], 'here': card['here'], 'passage': sid, 'start': section['start'], 'end': section['end']}
        god_buttons.append(
            f'<button class="god-button" type="button" data-god="{key}" aria-label="About {name}" aria-haspopup="dialog" aria-controls="god-dialog">'
            '<span class="god-stage">' + artwork_image(key, 'god-art', lazy=True)
            + f'</span><span class="god-name">{name}</span></button>')
    god_section = '<section class="gods-section" aria-labelledby="gods-title"><h2 class="gods-heading" id="gods-title">Meet the gods</h2><div class="god-grid">' + ''.join(god_buttons) + '</div></section>'
    god_dialog = ('<dialog class="god-dialog" id="god-dialog" aria-labelledby="god-title" aria-describedby="god-general">'
                  '<button class="god-close" id="god-close" type="button" aria-label="Close information">×</button>'
                  '<span class="god-context-label">Meet the gods</span><h2 id="god-title"></h2><p id="god-general"></p>'
                  '<p><span class="god-context-label">In the poem</span><span id="god-here"></span></p>'
                  '<a class="god-read" id="god-read" href="theogony-reader.html">Read this passage →</a></dialog>')
    god_data = json.dumps(god_cards, ensure_ascii=True).replace('<', '\\u003c')
    god_script = """
    const gods = __GOD_DATA__;
    const godDialog = document.getElementById('god-dialog');
    let godTrigger = null;
    document.querySelectorAll('[data-god]').forEach(button => {
      button.addEventListener('click', () => {
        const god = gods[button.dataset.god];
        godTrigger = button;
        document.getElementById('god-title').textContent = god.name;
        document.getElementById('god-general').textContent = god.general;
        document.getElementById('god-here').textContent = god.here;
        const link = document.getElementById('god-read');
        link.href = 'theogony-reader.html#' + god.passage;
        link.textContent = 'Read verses ' + god.start + '–' + god.end + ' →';
        godDialog.showModal();
      });
    });
    document.getElementById('god-close').addEventListener('click', () => godDialog.close());
    godDialog.addEventListener('click', event => {
      if (event.target !== godDialog) return;
      const bounds = godDialog.getBoundingClientRect();
      if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) godDialog.close();
    });
    godDialog.addEventListener('close', () => godTrigger?.focus({preventScroll: true}));
    """.replace('__GOD_DATA__', god_data)
    page = [
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#dedede">', metadata('index.html'), '<style>', style,
        '</style></head><body><div class="shell"><header class="site-header"><a class="wordmark" href="index.html">THEOGONY</a><nav class="site-nav" aria-label="Main navigation"><a href="theogony-reader.html">Read the poem</a><a href="translation.html">Translation</a></nav></header></div>',
        '<main><section class="hero">' + hero_top + '<div class="hero-copy"><p class="eyebrow">Hesiod’s ancient Greek poem</p><div class="temple-mark"><svg class="temple-capital" viewBox="0 0 700 74" aria-hidden="true" focusable="false"><path d="M44 49 C36 50 33 37 46 33 C60 28 70 47 55 62 C35 84 0 55 22 23 Q32 10 48 10 H652 Q668 10 678 23 C700 55 665 84 645 62 C630 47 640 28 654 33 C667 37 664 50 656 49"/><path d="M78 36 H622"/></svg><h1>THEOGONY</h1><svg class="temple-base" viewBox="0 0 700 34" aria-hidden="true" focusable="false"><rect x="36" y="5" width="628" height="24" rx="12"/></svg></div><p>How did the Greek gods and the world around them begin? Read the poem in clear English, with short passages and explanations whenever you need them.</p><div class="actions"><a class="button" href="theogony-reader.html">Continue reading <span aria-hidden="true">&nbsp;→</span></a><a class="button secondary" href="theogony-reader.html#p001">Start at verse 1</a></div></div>' + hero_bottom + '</section>',
        god_section,
        '<section class="story shell" aria-labelledby="story-title"><div class="story-header"><h2 id="story-title">Open a passage</h2><p>Begin with the Muses, jump to the first beings, or follow the family struggle that leads toward Zeus.</p></div><div class="paths">',
        '<a class="path" href="theogony-reader.html#p001">' + passage_art('passage-muses-v1.png') + '<span class="range">VERSE 1–8</span><strong>The Muses dance on Helicon</strong><span class="path-cta">Start the poem →</span></a>',
        '<a class="path" href="theogony-reader.html#p010">' + passage_art('passage-first-beings-v1.png') + '<span class="range">VERSE 116–125</span><strong>The first beings</strong><span class="path-cta">Explore the beginning →</span></a>',
        '<a class="path" href="theogony-reader.html#p032">' + passage_art('passage-cronus-v3.png') + '<span class="range">VERSE 453–467</span><strong>Cronus swallows his children</strong><span class="path-cta">Follow the story →</span></a></div></section></main>',
        '<footer class="footer shell"><p>Hesiod · Theogony. AI-assisted reading draft.</p><nav aria-label="Site information"><a href="translation.html">Translation and sources</a><a href="imprint.html">Imprint / Impressum</a><a href="privacy.html">Privacy</a><a href="reuse.html">Reuse and licence</a><a href="https://github.com/onur-crg/theogony-reading">GitHub</a></nav></footer>', god_dialog, '<script>', god_script, '</script></body></html>'
    ]
    HOME_OUTPUT.write_text(''.join(page))

def render_notes(items):
    result = ['<section id="glossary" class="glossary" aria-labelledby="glossary-title"><h2 id="glossary-title">Name and word notes</h2><p>Short explanations from the translation runs, kept separately from the reading text.</p>']
    for section, _, _ in items:
        for index, card in enumerate(section["cards"]):
            target = f"note-{section['id']}-{index}"
            result.append(f'<div class="note" id="{target}" data-label="{esc(card["label"])}" data-general="{esc(card["general"])}" data-here="{esc(card["here"])}">')
            result.append(f'<h3>{esc(card["label"])} <small>Lines {section["start"]}–{section["end"]}</small></h3>')
            result.append(f'<p>{esc(card["general"])}</p><p><strong>Here:</strong> {esc(card["here"])}</p>')
            article_id = 'variant-929' if section['id']=='v929' else section['id']
            result.append(f'<a href="#{article_id}">Back to passage</a></div>')
    result.append('</section>')
    return ''.join(result)


STYLE = r"""
:root{--paper:#dedede;--sheet:#f7f9fc;--ink:#1b2c48;--muted:#61748d;--line:#cbd5e2;--green:#075fce;--gold:#5688ca;--tint:#dbe7f6;--reading-size:1.31rem;color-scheme:light}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:5rem}body{margin:0;background:var(--paper);color:var(--ink);font-family:Georgia,Palatino,'Times New Roman',serif}a{color:inherit}button{font:inherit}button:focus-visible,a:focus-visible,summary:focus-visible{outline:3px solid #b08a48;outline-offset:4px}.skip{position:absolute;left:-100vw;top:0;background:white;padding:.8rem;z-index:20}.skip:focus{left:1rem}.topbar{position:sticky;top:0;z-index:12;display:flex;align-items:center;justify-content:space-between;gap:1rem;min-height:4.4rem;padding:.65rem clamp(1rem,3vw,3rem);background:rgba(251,249,243,.95);border-bottom:1px solid var(--line);backdrop-filter:blur(16px);font:500 .83rem/1.3 system-ui,sans-serif}.brand{color:var(--ink);font:600 1.13rem Georgia,serif;text-decoration:none;white-space:nowrap}.topbar .status{color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.controls{display:flex;align-items:center;gap:.4rem}.controls button,.toc-button{border:1px solid var(--line);background:var(--sheet);color:var(--ink);border-radius:999px;min-width:2.15rem;height:2.15rem;padding:0 .7rem;cursor:pointer}.toc-button{display:none}.progress{position:absolute;left:0;bottom:-1px;height:2px;background:var(--gold);width:0}.layout{display:grid;grid-template-columns:minmax(16rem,19rem) minmax(0,1fr);max-width:90rem;margin:auto;gap:clamp(2rem,6vw,7rem);padding:0 clamp(1rem,3vw,3rem)}.sidebar{position:sticky;top:4.4rem;height:calc(100vh - 4.4rem);overflow:auto;padding:2.6rem 1rem 2rem 0;border-right:1px solid var(--line);font-family:system-ui,sans-serif}.sidebar-title{font-size:.72rem;letter-spacing:.13em;text-transform:uppercase;color:var(--muted);margin:0 0 1rem}.toc-list{list-style:none;padding:0;margin:0}.toc-list a{display:grid;grid-template-columns:3.5rem 1fr;gap:.5rem;text-decoration:none;color:#63716b;padding:.5rem .6rem;border-radius:.4rem;font-size:.79rem;line-height:1.35}.toc-list a:hover,.toc-list a[aria-current="location"]{background:#e9eee7;color:var(--green)}.toc-list .verse{font-variant-numeric:tabular-nums;color:#839089}.toc-list .variant-link{margin-top:.5rem;border-top:1px solid var(--line)}.reader{min-width:0;max-width:56rem;padding:0 0 6rem}.hero{padding:clamp(5rem,10vw,9rem) 0 6rem;border-bottom:1px solid var(--line)}.eyebrow,.hero-note{font-family:system-ui,sans-serif;color:var(--muted)}.eyebrow{font-size:.76rem;letter-spacing:.18em;text-transform:uppercase}.hero h1{font-weight:400;font-size:clamp(4rem,8.5vw,7.6rem);letter-spacing:-.055em;line-height:.98;margin:1.1rem 0 1.2rem}.hero .byline{font-size:1.4rem;color:var(--green);margin:0 0 2rem}.hero-deck{max-width:38rem;font-size:clamp(1.22rem,2vw,1.55rem);line-height:1.5;margin:0 0 2rem}.hero-note{font-size:.85rem;line-height:1.6;max-width:38rem}.start-link{display:inline-block;margin-top:1.5rem;font:600 .82rem system-ui,sans-serif;text-decoration:none;color:var(--green);border-bottom:1px solid var(--gold);padding-bottom:.3rem}.passage{padding:5rem 0 5.5rem;border-bottom:1px solid var(--line);scroll-margin-top:4.5rem}.passage-head{margin-bottom:2.7rem}.passage-meta{display:flex;gap:1.2rem;font:600 .75rem system-ui,sans-serif;letter-spacing:.12em;text-transform:uppercase;color:var(--green)}.passage-meta span+span:before{content:'•';color:var(--gold);margin-right:1.2rem}.passage h2,.passage h3{font-size:clamp(2.15rem,4vw,3.4rem);font-weight:400;line-height:1.12;letter-spacing:-.035em;margin:1.05rem 0 0;max-width:42rem}.reading-text{font-size:var(--reading-size);line-height:1.76;max-width:39rem}.reading-text p{margin:0 0 1.45rem}.term{color:var(--green);text-decoration:underline;text-decoration-color:#b4a36e;text-decoration-thickness:1px;text-underline-offset:.18em}.term:hover{text-decoration-color:var(--green);background:#eaf0e7}.summary{max-width:39rem;margin-top:2.6rem;padding:1.05rem 1.2rem;background:var(--tint);border-radius:.35rem;font-family:system-ui,sans-serif;font-size:.94rem;line-height:1.6}.summary summary{display:flex;justify-content:space-between;cursor:pointer;font-weight:650;color:var(--green);list-style:none}.summary summary::-webkit-details-marker{display:none}.summary[open] summary span{transform:rotate(45deg)}.summary p{margin:1rem 0 0}.source{font:.78rem/1.6 system-ui,sans-serif;color:var(--muted);margin-top:1.3rem}.source summary{cursor:pointer;width:max-content}.source p{margin:.4rem 0}.source a{color:var(--green)}.next{display:inline-block;font:600 .82rem system-ui,sans-serif;color:var(--green);text-decoration:none;margin-top:2.2rem;border-bottom:1px solid var(--gold);padding-bottom:.3rem}.variant{background:#f3f0e7;margin:0 -2rem;padding:4.5rem 2rem}.variant-note,.review-note{max-width:39rem;font:.86rem/1.55 system-ui,sans-serif;padding:.85rem 1rem;border-left:2px solid var(--gold);background:#fffaf0;margin:0 0 2rem}.review-note{background:#fff7ed;border-color:#b46e4a}.glossary{padding:5rem 0}.glossary>h2{font-weight:400;font-size:2.5rem;margin:0 0 .5rem}.glossary>p{font: .9rem/1.5 system-ui,sans-serif;color:var(--muted)}.note{font:.87rem/1.55 system-ui,sans-serif;max-width:39rem;border-bottom:1px solid var(--line);padding:.8rem 0;scroll-margin-top:5rem}.note h3{margin:.2rem 0;font-size:1rem}.note h3 small{font-size:.72rem;font-weight:400;color:var(--muted)}.note p{margin:.25rem 0}.note a{color:var(--green)}.note:target{background:#f2f3e8}.note:not(:target){display:none}.glossary:target .note{display:block}.glossary button{cursor:pointer}dialog{border:1px solid #d8dfd5;background:var(--sheet);color:var(--ink);width:min(calc(100vw - 2rem),26rem);padding:1.6rem 1.7rem 1.4rem;border-radius:.6rem;box-shadow:0 1.5rem 4rem #213a2b33;font-family:system-ui,sans-serif}dialog::backdrop{background:#20332866;backdrop-filter:blur(2px)}dialog h2{font:400 1.7rem Georgia,serif;margin:.25rem 2rem 1rem 0}dialog p{font-size:.94rem;line-height:1.55}dialog .here{border-top:1px solid var(--line);padding-top:.9rem}dialog .close{float:right;border:0;background:none;color:var(--muted);font-size:1.3rem;cursor:pointer}.footer{padding:2rem 0;font:.78rem/1.5 system-ui,sans-serif;color:var(--muted)}
.passage h2,.passage h3{margin-top:0}.verse-marker{display:block;margin:0 0 .8rem;color:var(--green);font:650 .83rem/1.4 system-ui,sans-serif;letter-spacing:.035em;font-variant-numeric:tabular-nums}
.verse-line{display:grid;grid-template-columns:2.7rem minmax(0,1fr);gap:.8rem;align-items:start;margin:.08rem 0;scroll-margin-top:5rem}.verse-number{color:var(--green);font:650 .8rem/1.5 system-ui,sans-serif;font-variant-numeric:tabular-nums;padding-top:.46rem;text-align:right}.verse-text{min-width:0}.verse-line:target{background:#ecf2e9;border-radius:.2rem}
.verse-line.disputed{background:#f4f0e7}.verse-number sup{font-size:.65em;color:var(--gold);margin-left:.08rem}
.verse-flow{max-width:39rem;margin:0 0 1.45rem!important;line-height:1.83}.verse-unit{display:inline;scroll-margin-top:5rem}.verse-unit:target{background:#ecf2e9}.verse-unit.disputed{background:#f4f0e7}.verse-number{display:inline;float:none;padding:0;margin:0;color:var(--green);font:650 .63em/1 system-ui,sans-serif;vertical-align:super;text-align:initial;font-variant-numeric:tabular-nums}.verse-number .dagger{font-size:.8em;color:var(--gold);margin-left:.08em}
.variant-gap{margin:1.2rem 0 1.2rem 3.5rem!important;color:var(--muted);font:italic .9rem/1.4 system-ui,sans-serif}
.hero,.passage,.sidebar,.topbar,.toc-list .variant-link,.note{border:0}.hero{padding-bottom:4rem}.passage{padding:4rem 0 5rem}.passage-head{margin-bottom:2.2rem}.title-link{color:inherit;text-decoration:none;text-decoration-color:transparent;text-underline-offset:.14em}.title-link:hover{color:var(--green);text-decoration:underline;text-decoration-color:var(--gold);text-decoration-thickness:1px}.summary-fallback{display:none;max-width:39rem;background:var(--tint);padding:1rem 1.2rem;margin:2rem 0;font:.94rem/1.6 system-ui,sans-serif}.summary-fallback:target{display:block}.summary-fallback p{margin:0 0 .8rem}.summary-fallback a{color:var(--green)}
@media(max-width:850px){.layout{display:block;padding:0 clamp(1.25rem,5vw,3rem)}.sidebar{position:fixed;z-index:11;left:0;top:4.4rem;height:calc(100vh - 4.4rem);width:min(85vw,22rem);padding:1.5rem;background:var(--sheet);box-shadow:1rem 0 2rem #263b3322;transform:translateX(-110%);transition:transform .2s}.sidebar.open{transform:translateX(0)}.toc-button{display:inline-block}.reader{margin:auto}.hero{padding-top:5rem}.passage{padding:4rem 0}.variant{margin:0 -1.25rem;padding:4rem 1.25rem}}@media(max-width:480px){:root{--reading-size:1.16rem}.topbar{padding:.5rem 1rem}.topbar .brand{font-size:1rem}.controls button{min-width:2rem;padding:0 .4rem}.passage h2,.passage h3{font-size:2.15rem}.reading-text{line-height:1.7}.verse-line{grid-template-columns:2rem minmax(0,1fr);gap:.65rem}.verse-number{font-size:.72rem;padding-top:.42rem}}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}.sidebar{transition:none}}@media print{.topbar,.sidebar,.summary,.source,.next,dialog{display:none!important}.layout{display:block}.reader{max-width:none}.passage{break-inside:avoid}.note{display:block!important}.term{text-decoration:none}}
@media(max-width:480px){.verse-number{font-size:.63em;padding:0}.verse-flow{line-height:1.75}}
:root{--reading-size:1.2rem}body{font-family:'Helvetica Neue',-apple-system,BlinkMacSystemFont,Arial,sans-serif}.brand,.hero h1,.passage h2,.passage h3,dialog h2{font-family:Baskerville,Didot,'Iowan Old Style',Georgia,serif;font-weight:400;-webkit-text-stroke:.3px currentColor}.hero h1{font-size:clamp(4.4rem,9vw,8.4rem);line-height:.94;letter-spacing:-.035em}.passage h2,.passage h3{font-size:clamp(2.45rem,4.1vw,3.65rem);line-height:1.12;letter-spacing:-.022em}.reading-text{max-width:42rem;font-family:'Helvetica Neue',-apple-system,BlinkMacSystemFont,Arial,sans-serif;font-weight:400;letter-spacing:-.008em}.verse-flow{max-width:42rem;line-height:1.82}.hero-deck{font-family:'Helvetica Neue',-apple-system,BlinkMacSystemFont,Arial,sans-serif;font-size:clamp(1.14rem,1.8vw,1.38rem);line-height:1.58}
@media(max-width:480px){:root{--reading-size:1.08rem}.passage h2,.passage h3{font-size:clamp(2.2rem,8vw,2.8rem)}.verse-flow{line-height:1.76}}
.controls .info-link{display:inline-flex;align-items:center;height:2.15rem;padding:0 .7rem;border:1px solid var(--line);border-radius:999px;background:var(--sheet);color:var(--ink);text-decoration:none}.controls .info-link:hover{color:var(--green);border-color:var(--green)}@media(max-width:480px){.controls .info-link{display:none}}.footer nav{display:flex;flex-wrap:wrap;gap:.35rem .65rem}.footer a{color:var(--green);text-underline-offset:.2em}.footer p{margin:.7rem 0 0}
.topbar{background:rgba(222,222,222,.97)}.toc-list a{color:var(--muted)}.toc-list .verse{color:#6c819c}.toc-list a:hover,.toc-list a[aria-current="location"]{background:#d9e6f5}.term{text-decoration-color:#78a9e4}.term:hover{background:#d9e6f5}.verse-unit:target,.verse-line:target,.note:target{background:#d6e5f7}.verse-unit.disputed,.verse-line.disputed{background:transparent}.verse-number .dagger{color:var(--green)}.textual-note{margin:1.5rem 0 0;max-width:42rem;color:var(--muted);font:.8rem/1.6 system-ui,sans-serif}.textual-note summary{cursor:pointer;width:fit-content;color:var(--green)}.textual-note p{margin:.6rem 0}.textual-note a{color:var(--green)}.variant{background:#dbe3ef}.variant-note{background:#edf3fb}.review-note{background:#fff4e7}.summary-fallback{background:#dbe7f6}dialog{border-color:#b8cbe1;background:var(--sheet);box-shadow:0 1.5rem 4rem #1b2c4833}dialog::backdrop{background:#172d4b66}.sidebar{background:transparent}button:focus-visible,a:focus-visible,summary:focus-visible{outline-color:#075fce}@media(max-width:850px){.sidebar{background:var(--sheet);box-shadow:1rem 0 2rem #1b2c4822}}
.topbar{min-height:4.5rem;padding:1rem clamp(1.25rem,4vw,3.5rem);border-bottom:1px solid var(--line);backdrop-filter:none;font-family:'Helvetica Neue',-apple-system,Arial,sans-serif}.topbar .brand{color:var(--green);font-size:1.75rem;letter-spacing:-.02em;line-height:1}.controls{gap:1.55rem}.controls button,.controls .info-link{min-width:0;height:auto;padding:.3rem 0;border:0;border-radius:0;background:transparent;color:var(--ink);font:600 .9rem/1.3 'Helvetica Neue',-apple-system,Arial,sans-serif;text-decoration:none}.controls button:hover,.controls .info-link:hover{color:var(--green);text-decoration:underline;text-underline-offset:.25em}.controls #smaller,.controls #larger{color:var(--muted);font-weight:500}.controls #smaller:hover,.controls #larger:hover{color:var(--green)}@media(max-width:650px){.topbar{padding:.9rem 1.25rem}.topbar .brand{font-size:1.35rem}.controls{gap:.85rem}}@media(max-width:480px){.topbar .brand{font-size:1.15rem}.controls{gap:.65rem}.controls .info-link{display:none}.controls button{font-size:.8rem}}
.topbar .brand,.hero h1,.passage h2,.passage h3{font-family:Optima,'Avenir Next',Arial,sans-serif;font-weight:800;text-transform:uppercase;letter-spacing:.005em;-webkit-text-stroke:0}.topbar .brand{font-size:1.65rem}.hero h1{font-size:clamp(3.7rem,7vw,6.8rem);line-height:1.02}.passage h2,.passage h3{font-size:clamp(1.7rem,3.15vw,2.65rem);line-height:1.15;max-width:46rem}@media(max-width:650px){.topbar .brand{font-size:1.25rem}}@media(max-width:480px){.topbar .brand{font-size:1.1rem}.passage h2,.passage h3{font-size:clamp(1.55rem,6.2vw,2.2rem)}}
.toc-button{display:inline-flex;align-items:center}.toc-button[aria-expanded="true"]{color:var(--green);text-decoration:underline;text-underline-offset:.25em}.sidebar[hidden],.toc-scrim[hidden]{display:none}.layout.toc-collapsed{grid-template-columns:minmax(0,1fr)}.toc-collapsed .reader{width:100%;margin-inline:auto}.sidebar-heading{display:flex;align-items:center;justify-content:space-between;gap:.75rem;margin-bottom:1rem}.sidebar-heading .sidebar-title{margin:0}.sidebar-close{width:2rem;height:2rem;flex:none;border:0;background:transparent;color:var(--green);font:400 1.4rem/1 system-ui,sans-serif;cursor:pointer}.toc-scrim{display:none}.sidebar{top:4.4rem;height:calc(100dvh - 4.4rem)}
@media(max-width:850px){.topbar{height:4.4rem;min-height:4.4rem;padding:.75rem 1rem}.sidebar{top:4.4rem;height:calc(100dvh - 4.4rem);background:var(--paper);border-right:1px solid #b6c3d2;box-shadow:.7rem 0 2rem #1b2c4820}.toc-scrim{display:block;position:fixed;z-index:10;inset:4.4rem 0 0;border:0;border-radius:0;background:#172d4b45}.toc-list a{color:var(--ink)}.toc-list a:hover,.toc-list a[aria-current="location"]{background:#075fce12;color:var(--green)}}

.reader>.passage{padding-block:2.25rem}.reader>.passage:first-of-type{padding-top:2.7rem}.passage-head{margin-bottom:1.5rem}.passage h2,.passage h3{margin-top:0}.reader-title-accessible{position:absolute;width:1px;height:1px;margin:-1px;padding:0;overflow:hidden;clip-path:inset(50%);white-space:nowrap}.settings-label-short{display:none}.reading-notice{position:fixed;z-index:20;bottom:1rem;left:50%;transform:translateX(-50%);width:min(42rem,calc(100% - 2rem));padding:1.2rem 1.4rem;background:var(--paper);color:var(--ink);border:1px solid #9db2cc;border-radius:.8rem;box-shadow:0 .5rem 2rem #1b2c4826;font:.88rem/1.5 'Helvetica Neue',Arial,sans-serif}.reading-notice[hidden]{display:none}.reading-notice h2{font:600 1rem/1.3 'Helvetica Neue',Arial,sans-serif;margin:0 0 .35rem}.reading-notice p{margin:0 0 .8rem;color:var(--muted)}.reading-notice a{color:var(--green)}.reading-notice-actions{display:flex;gap:.6rem;flex-wrap:wrap}.reading-notice-actions button{flex:1;min-height:2.65rem;padding:.55rem .8rem;border:1px solid var(--green);border-radius:999px;background:transparent;color:var(--green);font:600 .88rem/1.3 'Helvetica Neue',Arial,sans-serif;cursor:pointer}.reading-notice-actions button:hover{background:#075fce12}#remember-yes{background:var(--green);color:var(--paper)}#remember-yes:hover{background:#064fa9}#remember-no[aria-pressed="true"]{box-shadow:inset 0 0 0 1px var(--green)}@media(max-width:480px){.settings-label-long{display:none}.settings-label-short{display:inline}.reading-notice{bottom:.5rem;padding:1rem;width:calc(100% - 1rem)}}
@media(max-width:650px){.settings-label-long{display:none}.settings-label-short{display:inline}}
.reader-settings-dialog{width:min(26rem,calc(100% - 2rem));padding:1.6rem;border-radius:.8rem;background:var(--paper)}.reader-settings-dialog h2{font:800 1.65rem/1.2 Optima,'Avenir Next',Arial,sans-serif;color:var(--green);margin:.1rem 2rem 1.5rem 0}.settings-row{padding:1.1rem 0;border-top:1px solid var(--line)}.settings-row h3{font:600 .95rem/1.4 'Helvetica Neue',Arial,sans-serif;margin:0 0 .65rem}.text-size-control{display:flex;align-items:center;justify-content:space-between;gap:1rem}.text-size-control button,.settings-change{min-height:2.6rem;padding:.5rem .85rem;border:1px solid var(--green);border-radius:999px;background:transparent;color:var(--green);font:600 .9rem/1.3 'Helvetica Neue',Arial,sans-serif;cursor:pointer}.text-size-control button:disabled{opacity:.4;cursor:default}.text-size-control output{font:.9rem/1.4 'Helvetica Neue',Arial,sans-serif;color:var(--ink)}.settings-description{font:.85rem/1.6 'Helvetica Neue',Arial,sans-serif;color:var(--muted);margin:.5rem 0 0}.settings-choice{display:flex;justify-content:space-between;align-items:center;gap:1rem}.settings-choice p{margin:0;font:.9rem/1.4 'Helvetica Neue',Arial,sans-serif;color:var(--ink)}.settings-help{font:.8rem/1.6 'Helvetica Neue',Arial,sans-serif;color:var(--muted);margin:.8rem 0 0}.settings-help a{color:var(--green)}


"""


SCRIPT = r"""
const rememberKey='theogonyRememberPreferencesV1';let rememberChoice=null,rememberEnabled=false;
try{rememberChoice=localStorage.getItem(rememberKey)}catch(_){}
rememberEnabled=rememberChoice==='enabled';
const sidebar=document.getElementById('sidebar'), tocButton=document.getElementById('toc-button');
const tocMedia=matchMedia('(max-width:850px)'),tocScrim=document.getElementById('toc-scrim');
const tocPreferenceKey='theogonyDesktopContentsV1';let desktopTocOpen=true;
if(rememberEnabled)try{desktopTocOpen=localStorage.getItem(tocPreferenceKey)!=='hidden'}catch(_){}
function setToc(open,persist=false,keepPosition=false){
  const position=keepPosition&&!tocMedia.matches?readingPosition():null;
  sidebar.hidden=!open;sidebar.classList.toggle('open',open);
  document.querySelector('.layout').classList.toggle('toc-collapsed',!open);
  tocButton.setAttribute('aria-expanded',String(open));
  tocButton.setAttribute('aria-label',open?'Hide contents':'Show contents');
  tocScrim.hidden=!(open&&tocMedia.matches);
  if(persist&&!tocMedia.matches){desktopTocOpen=open;if(rememberEnabled)try{localStorage.setItem(tocPreferenceKey,open?'shown':'hidden')}catch(_){}}
  if(position&&position.id!=='top')requestAnimationFrame(()=>{const verse=document.getElementById(position.id);if(verse)scrollBy(0,verse.getBoundingClientRect().top-position.offset)});
}
setToc(tocMedia.matches?false:desktopTocOpen);
tocButton.addEventListener('click',()=>setToc(sidebar.hidden,true,true));
document.getElementById('toc-close').addEventListener('click',()=>{setToc(false,true,true);tocButton.focus({preventScroll:true})});
tocScrim.addEventListener('click',()=>setToc(false));
sidebar.addEventListener('click',event=>{if(tocMedia.matches&&event.target.closest('a'))setToc(false)});
document.addEventListener('keydown',event=>{if(event.key==='Escape'&&!sidebar.hidden&&!document.querySelector('dialog[open]')){setToc(false,true,true);tocButton.focus({preventScroll:true})}});
tocMedia.addEventListener('change',()=>setToc(tocMedia.matches?false:desktopTocOpen));
const noteDialog=document.getElementById('note-dialog');let previousFocus=null;
document.addEventListener('click',e=>{const link=e.target.closest('a[data-note]');if(!link||!noteDialog.showModal)return;const note=document.getElementById(link.dataset.note);if(!note)return;e.preventDefault();previousFocus=link;document.getElementById('note-title').textContent=note.dataset.label;document.getElementById('note-general').textContent=note.dataset.general;document.getElementById('note-here').textContent=note.dataset.here;noteDialog.showModal();});
noteDialog.addEventListener('close',()=>previousFocus?.focus());document.getElementById('dialog-close').addEventListener('click',()=>noteDialog.close());noteDialog.addEventListener('click',e=>{if(e.target===noteDialog)noteDialog.close()});
const summaryDialog=document.getElementById('summary-dialog');let previousSummaryFocus=null;
document.addEventListener('click',e=>{const link=e.target.closest('a[data-summary]');if(!link||!summaryDialog.showModal)return;const summary=document.getElementById(link.dataset.summary);if(!summary)return;e.preventDefault();previousSummaryFocus=link;document.getElementById('summary-title').textContent=link.textContent;document.getElementById('summary-text').textContent=summary.querySelector('p').textContent;summaryDialog.showModal()});
summaryDialog.addEventListener('close',()=>previousSummaryFocus?.focus());document.getElementById('summary-close').addEventListener('click',()=>summaryDialog.close());summaryDialog.addEventListener('click',e=>{if(e.target===summaryDialog)summaryDialog.close()});
const root=document.documentElement;let size=0;if(rememberEnabled)try{size=Number(localStorage.getItem('theogonyReadingSize')||0)}catch(_){}function applySize(){const base=matchMedia('(max-width:480px)').matches?1.08:1.2;root.style.setProperty('--reading-size',`${Math.max(.96,Math.min(1.7,base+size*.1))}rem`);document.getElementById('reading-size-label').textContent=size===0?'Default':`${size>0?'+':''}${size} step${Math.abs(size)===1?'':'s'}`;document.getElementById('smaller').disabled=size<=-2;document.getElementById('larger').disabled=size>=4}function saveSize(){if(rememberEnabled)try{localStorage.setItem('theogonyReadingSize',size)}catch(_){}applySize()}applySize();addEventListener('resize',applySize);document.getElementById('smaller').addEventListener('click',()=>{size=Math.max(-2,size-1);saveSize()});document.getElementById('larger').addEventListener('click',()=>{size=Math.min(4,size+1);saveSize()});
const passages=[...document.querySelectorAll('.passage:not(.variant)')],progress=document.getElementById('progress');const observer=new IntersectionObserver(entries=>{for(const entry of entries){if(entry.isIntersecting){const id=entry.target.id;for(const link of document.querySelectorAll('.toc-list a'))link.removeAttribute('aria-current');const active=document.querySelector(`.toc-list a[href="#${id}"]`);active?.setAttribute('aria-current','location');break}}},{rootMargin:'-15% 0px -70% 0px'});passages.forEach(p=>observer.observe(p));
const positionKey='theogonyReadingPositionV1',verseLines=[...document.querySelectorAll('.verse-unit')];let savingEnabled=false,saveTimer;
function readingPosition(){
  const probe=110;let low=0,high=verseLines.length-1,index=-1;
  while(low<=high){const middle=(low+high)>>1;if(verseLines[middle].getBoundingClientRect().top<=probe){index=middle;low=middle+1}else high=middle-1}
  if(index<0)return {id:'top',offset:0,scrollY:Math.round(scrollY)};
  const line=verseLines[index];return {id:line.id,offset:Math.round(line.getBoundingClientRect().top),scrollY:Math.round(scrollY)};
}
function savePosition(){
  if(!savingEnabled||!rememberEnabled)return;
  try{localStorage.setItem(positionKey,JSON.stringify(readingPosition()))}catch(_){}
  if(location.hash){
    const anchor=document.getElementById(location.hash.slice(1));
    if(anchor&&Math.abs(anchor.getBoundingClientRect().top)>260){try{history.replaceState(history.state,'',location.href.split('#')[0])}catch(_){}}
  }
}
function schedulePositionSave(){if(!savingEnabled||!rememberEnabled)return;clearTimeout(saveTimer);saveTimer=setTimeout(savePosition,400)}
function restorePosition(){
  let saved=null;if(rememberEnabled)try{saved=JSON.parse(localStorage.getItem(positionKey)||'null')}catch(_){}
  if(!location.hash&&saved&&typeof saved.id==='string'&&Number.isFinite(saved.scrollY)){
    try{history.scrollRestoration='manual'}catch(_){}
    const line=saved.id==='top'?null:document.getElementById(saved.id);
    const target=line&&Number.isFinite(saved.offset)?scrollY+line.getBoundingClientRect().top-saved.offset:saved.scrollY;
    const prior=document.documentElement.style.scrollBehavior;document.documentElement.style.scrollBehavior='auto';scrollTo(0,Math.max(0,target));requestAnimationFrame(()=>{document.documentElement.style.scrollBehavior=prior});
  }
  requestAnimationFrame(()=>requestAnimationFrame(()=>{savingEnabled=true;if(location.hash)schedulePositionSave()}));
}
if(document.readyState==='complete')restorePosition();else addEventListener('load',restorePosition,{once:true});
addEventListener('pagehide',savePosition);document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden')savePosition()});addEventListener('hashchange',()=>{if(savingEnabled)setTimeout(savePosition,450)});
let queued=false;addEventListener('scroll',()=>{if(queued)return;queued=true;requestAnimationFrame(()=>{const max=document.documentElement.scrollHeight-innerHeight;progress.style.width=(max>0?scrollY/max*100:0)+'%';schedulePositionSave();queued=false})},{passive:true});
const readingNotice=document.getElementById('reading-notice'),rememberYes=document.getElementById('remember-yes'),rememberNo=document.getElementById('remember-no');
let settingsOpener=null;
function updateReadingNotice(){
  rememberYes.setAttribute('aria-pressed',String(rememberChoice==='enabled'));
  rememberNo.setAttribute('aria-pressed',String(rememberChoice==='disabled'));
  readingNotice.hidden=rememberChoice==='enabled'||rememberChoice==='disabled';
  document.getElementById('remember-status').textContent=rememberEnabled?'Remembering on this device':'Not remembered';
}
function chooseRemember(enabled){
  rememberEnabled=enabled;rememberChoice=enabled?'enabled':'disabled';
  try{localStorage.setItem(rememberKey,rememberChoice)}catch(_){}
  if(enabled){
    try{localStorage.setItem('theogonyReadingSize',size);localStorage.setItem(tocPreferenceKey,desktopTocOpen?'shown':'hidden')}catch(_){}
    savePosition();
  }else{
    [positionKey,'theogonyReadingSize',tocPreferenceKey].forEach(key=>{try{localStorage.removeItem(key)}catch(_){}});
  }
  updateReadingNotice();
  // Keep keyboard focus on a visible control when the notice closes.
  (settingsOpener||document.getElementById('reader-settings-button')).focus({preventScroll:true});settingsOpener=null;
}
rememberYes.addEventListener('click',()=>chooseRemember(true));rememberNo.addEventListener('click',()=>chooseRemember(false));
const settingsDialog=document.getElementById('reader-settings-dialog'),settingsButton=document.getElementById('reader-settings-button');
let reopenNotice=false;
settingsButton.addEventListener('click',()=>{readingNotice.hidden=true;settingsDialog.showModal()});
document.getElementById('settings-close').addEventListener('click',()=>settingsDialog.close());
settingsDialog.addEventListener('close',()=>{if(reopenNotice){reopenNotice=false;readingNotice.hidden=false;rememberYes.focus({preventScroll:true})}else{updateReadingNotice();settingsButton.focus({preventScroll:true})}});
document.querySelectorAll('[data-reading-settings]').forEach(button=>button.addEventListener('click',()=>{settingsOpener=settingsButton;reopenNotice=true;settingsDialog.close()}));
updateReadingNotice();
addEventListener('storage',event=>{if(event.key===rememberKey||event.key===null){try{rememberChoice=localStorage.getItem(rememberKey)}catch(_){rememberChoice=null}rememberEnabled=rememberChoice==='enabled';updateReadingNotice()}});

"""


def main():
    write_discovery_files(ROOT)
    numbered, variant, headings = load_sections()
    verse_runs = load_verse_runs()
    variant_run = load_variant_verse_run()
    all_items = numbered + [variant]
    parts = ['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
             '<meta name="theme-color" content="#dedede">', metadata('theogony-reader.html'),
             '<style>', STYLE + BACK_STYLE, '</style></head><body id="top"><a class="skip" href="#reading">Skip to reading</a>',
             '<header class="topbar"><div class="reader-brand-group">' + BACK_LINK + '<a class="brand" href="index.html" aria-label="Theogony home">THEOGONY</a></div><nav class="controls" aria-label="Reading navigation">',
             '<button class="toc-button" id="toc-button" aria-controls="sidebar" aria-expanded="false">Contents</button>',
             '<button id="reader-settings-button" type="button" aria-label="Reader settings" aria-haspopup="dialog" aria-controls="reader-settings-dialog"><span class="settings-label-long">Reader settings</span><span class="settings-label-short" aria-hidden="true">Settings</span></button></nav><span class="progress" id="progress"></span></header>',
             '<button class="toc-scrim" id="toc-scrim" type="button" aria-label="Close contents" hidden></button><div class="layout"><nav class="sidebar" id="sidebar" aria-label="Passages"><div class="sidebar-heading"><p class="sidebar-title">Contents · 65 passages</p><button class="sidebar-close" id="toc-close" type="button" aria-label="Hide contents">×</button></div><ol class="toc-list">']
    for section, _, _ in numbered:
        sid = section["id"]
        parts.append(f'<li><a href="#{sid}"><span class="verse">{section["start"]}–{section["end"]}</span><span>{esc(headings[sid][2])}</span></a></li>')
        if sid == "p058":
            parts.append('<li><a class="variant-link" href="#variant-929"><span class="verse">929a–t</span><span>Additional lines · variant</span></a></li>')
    parts += ['</ol></nav><main class="reader" id="reading"><h1 class="reader-title-accessible">Hesiod · Theogony</h1>']
    for item in numbered:
        section = item[0]
        parts.append(render_section(item, headings, verse_runs=verse_runs))
        if section["id"] == "p058":
            parts.append(render_section(variant, headings, variant_run=variant_run, variant=True))
    parts.append(render_notes(all_items))
    parts.append('<footer class="footer"><nav aria-label="Site information"><a href="index.html">Home</a> · <a href="translation.html">Translation and sources</a> · <a href="imprint.html">Imprint / Impressum</a> · <a href="privacy.html">Privacy</a> · <a href="reuse.html">Reuse and licence</a><a href="https://github.com/onur-crg/theogony-reading">GitHub</a></nav><p>AI-assisted reading draft.</p></footer></main></div>')
    parts.append('<dialog id="note-dialog" aria-labelledby="note-title"><button class="close" id="dialog-close" type="button" aria-label="Close explanation">×</button><h2 id="note-title"></h2><p id="note-general"></p><p class="here"><strong>Here:</strong> <span id="note-here"></span></p></dialog>')
    parts.append('<dialog id="summary-dialog" aria-labelledby="summary-title"><button class="close" id="summary-close" type="button" aria-label="Close summary">×</button><h2 id="summary-title"></h2><p id="summary-text"></p></dialog>')
    parts.append('<dialog class="reader-settings-dialog" id="reader-settings-dialog" aria-labelledby="settings-title"><button class="close" id="settings-close" type="button" aria-label="Close reader settings">×</button><h2 id="settings-title">Reader settings</h2><section class="settings-row"><h3>Text size</h3><div class="text-size-control"><button id="smaller" type="button" aria-label="Make text smaller">A−</button><output id="reading-size-label" aria-live="polite">Default</output><button id="larger" type="button" aria-label="Make text larger">A+</button></div></section><section class="settings-row"><h3>Reading memory</h3><div class="settings-choice"><p id="remember-status" role="status"></p><button class="settings-change" type="button" data-reading-settings>Change</button></div><p class="settings-description">Save your place, text size and contents preference on this device.</p></section><p class="settings-help">Tap a passage title for a summary, or an underlined name for an explanation. <a href="privacy.html">Privacy</a></p></dialog>')
    parts.append('<section class="reading-notice" id="reading-notice" role="region" aria-labelledby="reading-notice-title" hidden><h2 id="reading-notice-title">Remember where you stopped?</h2><p>Optional. Save your place, text size and contents preference on this device. No tracking. Change your choice in Reader settings. <a href="privacy.html">Privacy</a></p><div class="reading-notice-actions"><button id="remember-yes" type="button">Remember</button><button id="remember-no" type="button">Don’t remember</button></div></section>')
    parts.extend(['<script>', SCRIPT, BACK_SCRIPT, '</script></body></html>'])
    OUTPUT.write_text(''.join(parts))
    render_information(numbered, variant, headings, verse_runs, variant_run)
    render_homepage(all_items)
    print(f"Built {OUTPUT}: {len(numbered)} numbered passages, 1 variant, {sum(len(x[0]['cards']) for x in all_items)} notes")
    print(f"Built {INFO_OUTPUT}: sources for {len(all_items)} passages plus standalone imprint, privacy and reuse pages")
    print(f"Built {HOME_OUTPUT}: homepage")


if __name__ == "__main__":
    main()
