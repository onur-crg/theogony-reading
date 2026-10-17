# Contributing

Reports of unclear passages, source discrepancies and reader bugs are welcome.
Please include a verse range or page URL, what you expected and what you found.
For translation issues, cite the relevant Greek wording or a reliable source
when possible. Do not include private contact details in public issues.

## Website changes

1. Create a branch and edit the source files, not `publish/` by hand.
2. Install `requirements.txt` in a virtual environment.
3. Run `python scripts/build.py`.
4. Check the homepage, reader and affected documents on narrow and wide screens.
5. Commit the source changes and rebuilt `publish/` together.

After editing original art, use `python scripts/build.py --images` and include
the new optimized exports and manifest. The default build reuses committed
exports to avoid unnecessary platform-dependent image-encoder changes.

## Editorial integrity

English reading text, summaries and glossary notes in `pipeline/tests/` are
recorded generation outputs. Do not manually rewrite these files and present the
result as the original run. A proposed new reading needs a new recorded output,
exact prompt, source range, model/settings and checksums. Technical provenance
does not establish translation quality. Discuss editorial changes separately
from layout fixes. This repository includes the selected runs consumed by this
edition, not every historical experiment.

Do not commit credentials, `.env` files, `.vercel`, session logs or private
workspace material. Software contributions use MIT; edition-content
contributions follow the separate terms in `NOTICE.md`. Do not contribute
material you do not have permission to share.
