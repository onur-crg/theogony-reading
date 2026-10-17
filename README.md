# Theogony

An illustrated English reading of Hesiod’s poem about the origins of the world
and the Greek gods.

**[Read the edition](https://theogony-reading.vercel.app/)** ·
[Translation and sources](https://theogony-reading.vercel.app/translation.html) ·
[Reuse and licence](https://theogony-reading.vercel.app/reuse.html)

![Gaia, Zeus and Athena, illustrated on cobalt blue](assets/theogony-share.jpg)

## A poem made easier to explore

Read 1,022 numbered verses in 65 short passages, with an additional textual
variant after verse 929. Tap a passage heading for a summary, or an underlined
name for a short explanation. The reader includes adjustable text size, a
collapsible contents list and optional memory for your place on the same device.
The homepage introduces Gaia, Zeus and Athena through hand-drawn illustrations.

This is an **AI-assisted reading edition**, not a critical scholarly edition.
The English text and explanatory notes can contain errors and have not received
a complete independent scholarly review. The original Greek poem is public
domain. The XML source is the Perseus digitisation of Hugh G. Evelyn-White’s
1914 edition. A dagger (†) preserves the Greek edition’s deletion marks.

## Run locally

Python 3.11 or newer is sufficient for the build. CI uses Python 3.13.

```sh
git clone https://github.com/Onur3107/theogony-reading.git
cd theogony-reading
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/build.py
python -m http.server 8000 --directory publish
```

Open `http://localhost:8000`. On Windows, activate the environment with
`.venv\Scripts\activate` instead. Rebuilding uses the included generation
outputs. It makes **no model calls** and requires no API keys or Codex login.
Only Pillow is needed in addition to Python’s standard library.

## Project layout

```text
assets/             Original artwork, optimized exports and optional analytics glue
content/            Passage boundaries used by the build
pipeline/           Page generators, asset exporter and validation tools
pipeline/tests/     Exact selected prompts, generated outputs and run records
scripts/            Build and release verification commands
sources/            Unchanged Perseus Greek XML and separate source licence
publish/            Curated deployable static website, committed for Vercel
```

Edit generators in `pipeline/` and source assets. Rebuild with
`python scripts/build.py`, then commit the source changes and `publish/`
together. Do not edit generated pages directly. To regenerate optimized art from
the included originals, run `python scripts/build.py --images`.

GitHub Actions rebuilds the edition, checks that committed HTML matches its
generators, validates local links, and verifies the checksums of released files
and every selected prompt/output pair. Hashes establish integrity, not accuracy.
See [CONTRIBUTING.md](CONTRIBUTING.md) for editorial and code contributions.

## How the text was produced

The running English verses and the summaries/name notes were generated in
separate recorded runs. On the website, each passage links to the model, exact
prompt and run record for both layers. This repository preserves all selected
run inputs required to rebuild the current edition, including earlier inputs
that are partly superseded. It does not include discarded design experiments,
private agent sessions, account state or the surrounding personal workspace.
Generation records retain their original model/version labels. This repository
does not imply that those labels are available through another API or account.

Illustrations and the favicon were generated with AI and prepared for the
site’s cobalt-and-gray visual style. Optimized WebP exports preserve the prepared
RGBA pixels losslessly; original PNGs remain included. The website uses system
fonts and ordinary HTML, CSS and JavaScript. No frontend framework or visitor
AI service is required.

## Privacy and hosting

The public edition is hosted on Vercel. Reading memory is optional and stays on
the device. Cookie-free Vercel visit statistics load only after separate
visitor consent; refusal, Do Not Track and Global Privacy Control prevent that
script from loading. Consent can be withdrawn on the Privacy page. Reading
positions, search terms and glossary clicks are not sent as analytics events.
Only consented, unblocked visits appear in the statistics.

The default analytics loader is restricted to the official production hostname.
The build never embeds hosting credentials. **If you publish a fork, replace the
operator/contact details, canonical origin and hosting/privacy statements with
your own actual configuration.** The published legal texts are specific to this
operator and are not a reusable legal-compliance template.

Vercel should deploy the `publish` root directory as a static project, with no
install or build command. Source files remain available here, while only the
curated publication folder is hosted. Pushes to `main` can publish updates;
other branches can receive preview deployments. See [DEPLOYMENT.md](DEPLOYMENT.md).

## Reuse

| Part | Licence |
| --- | --- |
| Website software and developer documentation | [MIT](LICENSE) |
| Original edition content and illustrations, to the extent rights are held | [CC BY 4.0](LICENSE-CONTENT.md) |
| Perseus Greek XML | [Separate Perseus/Tufts notice](sources/perseus-license.md), CC BY-SA 4.0 unless otherwise indicated |

Content attribution should name this edition and Onur Cirag, link to the source
website and licence, and identify changes. AI-generated material may not be
copyright-protected; the notice does not restrict public-domain material or
create exclusive rights. See [NOTICE.md](NOTICE.md) for scope and attribution.

## Feedback

Open an issue with a verse range or page link for corrections and technical
problems. For private contact, use the address in the
[legal notice](https://theogony-reading.vercel.app/imprint.html).
