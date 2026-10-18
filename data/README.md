# Reusable edition data

**[Download the complete JSON](https://theogony-reading.vercel.app/data/theogony.json)** ·
[View on GitHub](theogony.json) · [JSON Schema](theogony.schema.json)

`theogony.json` is the convenient entry point for apps, reading tools and other
projects. It contains the exact selected English reading text used on the
website, together with the passage titles, short summaries and name notes.
You do not need to combine the historical generation files yourself.

## Contents

- 65 passages covering numbered verses 1–1022, in reading order.
- One separate variant with 20 extra lines, 929a–929t.
- 66 summaries and passage-specific name/word notes.
- Licence, attribution, Greek source and links to exact generation records.

All strings are plain Unicode text, not HTML. No HTML links, superscript verse
numbers or dagger characters are inserted into the poem. Treat verse labels as
**strings** so `"929a"` works alongside `"929"`. Never infer verse identity from
an array index. Each verse has its own explicit `label`.

## Structure

| Field | Meaning |
| --- | --- |
| `schema_version` | Data format version, currently `1.0.0`. This is not a text-quality rating or a content revision number. |
| `id`, `title`, `author`, `language`, `website` | Edition metadata. |
| `editorial` | AI-assisted status, review status and explanation of editorial additions. |
| `licence` | Content licence, attribution wording and scope. |
| `source` | Greek edition, unchanged XML checksum, source rights notice and passage-title file. File paths are relative to the repository root. |
| `passages` | The 65 numbered passages, in order. |
| `variants` | Extra material outside the 1,022 numbered verses. Kept separate to avoid silently inserting a variant into the main text. |
| `records` | Generation records indexed by their original run IDs. Most readers can ignore this field. |

Each passage has:

| Field | Meaning |
| --- | --- |
| `id` | Stable section identifier such as `p010`. |
| `title` | The editorial section heading shown in the reader. These are the “subtitles”, not a translation of an original Hesiod heading. |
| `verse_range` | Inclusive start/end verse labels as strings. |
| `reader_url` | Direct link to the passage on the official website. |
| `summary` | Short passage summary. |
| `verses` | Ordered objects with `label`, `text` and `marked_for_deletion`. |
| `notes` | Ordered objects with `id`, `label`, `general` and `here`. `general` identifies the figure or term; `here` explains its role in this passage. Optional `aliases` match other spellings or English names. A nonempty `verse_labels` list limits links to those verses, for example to distinguish two figures named Doris. |
| `provenance` | Run IDs for `reading_text` and the original `summary_and_notes`, resolved in `records`. Optional `note_updates` lists later note-only revision run IDs in application order. |

The separate variant additionally has `after_verse: "929"` and
`source_gaps_after: ["929f"]`. The gap is a statement about the Greek source;
no missing words have been invented. `marked_for_deletion` reflects the Greek
edition's judgement. It is **not** a translation-error flag and should not cause
you to omit a verse accidentally.

## JavaScript example

```js
const response = await fetch(
  'https://theogony-reading.vercel.app/data/theogony.json'
);
if (!response.ok) throw new Error(`Download failed: ${response.status}`);
const edition = await response.json();
if (edition.schema_version !== '1.0.0') throw new Error('Unsupported data format');

const passage = edition.passages.find(p => p.id === 'p010');
console.log(passage.title);             // The first beings
console.log(passage.summary);
console.log(passage.verses.map(v => v.text).join(' '));
console.log(passage.notes);
```

The public data endpoint permits cross-origin reads. No account or API key is
required. A direct request to the JSON file does not execute analytics JavaScript.
For a user interface, insert strings as text, for example with `textContent`,
rather than assuming arbitrary content is trusted HTML.

## Python example

```python
import json
from urllib.request import urlopen

with urlopen('https://theogony-reading.vercel.app/data/theogony.json') as response:
    edition = json.load(response)

for passage in edition['passages']:
    print(passage['title'])
    for verse in passage['verses']:
        print(verse['label'], verse['text'])
```

## Attribution and reuse

Use `licence.attribution` as the suggested credit, adapted reasonably for your
medium. Link to this edition and CC BY 4.0, and identify changes. The licence
applies to original edition content to the extent rights are held. It creates
no rights over public-domain or unprotected AI-generated material. The Greek
XML is a separate source with its own rights notice and is not embedded into
this JSON. See [LICENSE-CONTENT.md](../LICENSE-CONTENT.md) and
[NOTICE.md](../NOTICE.md).

This remains an AI-assisted reading edition with independent content review
pending. Titles, summaries and notes are editorial aids, not Hesiod's own text.

## Rebuilding and versioning

`python scripts/build.py` regenerates this file from the same selected inputs as
the reader. Validation checks the JSON Schema, all 1,042 verse texts against the
rendered reader, all summaries and notes against their recorded outputs, and
all generation checksums. No model is called and no wording is manually edited.

The old date/version-based filenames remain under `pipeline/tests/` as immutable
provenance; normal reuse starts here. Main URLs track the current edition. For
reproducible research, pin a Git commit or release and keep the JSON checksum.
A change to the data shape will change `schema_version`; a content correction
alone need not. Future applications should explicitly check supported versions.

### Note-only revisions

Accepted revisions are selected in `pipeline/note_revisions.json`. Each raw run
contains passage IDs, complete replacement/additional cards, removed card IDs,
and Greek verse evidence. The build replaces cards by stable ID, appends new IDs,
and removes only explicitly listed IDs. It never rewrites generated prose.
Unchanged cards and all summaries retain their original `summary_and_notes`
record; changed/new cards come verbatim from the latest applicable `note_updates` run. Reading verses
retain their separate `reading_text` record. These optional provenance and
matching fields extend the version 1 format without changing existing fields.
