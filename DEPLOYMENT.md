# Deploying the edition

The existing production site is https://theogony-reading.vercel.app/.

## Vercel Git integration

The production branch is `main`. The existing Vercel project is connected to
`onur-crg/theogony-reading`, with root directory **`publish`**, framework **Other**,
no install command, no build command, and output directory `.`. The generated
`publish/vercel.json` contains the static response headers. No secret is needed
in this repository or in GitHub Actions.

The public release is committed alongside source so Vercel only needs to serve
static files. Source edits must be rebuilt before pushing. GitHub Actions checks
that generated HTML is current, but is not a deployment-blocking approval gate
unless the project's deployment checks are separately configured.

```sh
python scripts/build.py
git add pipeline assets content scripts publish
git commit
# A normal push of the approved commit to main triggers Vercel after linking.
git push
```

Prefer Git pushes for this connected project. If using Vercel CLI manually,
use this dedicated repository as the checkout and retain the project root
directory `publish`; never deploy the surrounding personal workspace. Linking a
local checkout creates `.vercel`, which is ignored and must not be committed. Never put tokens
or generated `.env` files into the repository. No paid plan or add-on is required
for the static site.

Enable Web Analytics in the existing Vercel project before deploying if you want
its optional consented visitor statistics. The next deployment provisions
`/_vercel/insights/script.js`. Without that feature enabled, leave analytics off
or remove its loader. Analytics is separate from optional reading memory.

## Portfolio preview

The frame-ancestors policy permits this site to appear in the Noto Labs portfolio
on `https://noto-labs.com` and `https://www.noto-labs.com`, as well as its own
origin. Other sites cannot embed it. The portfolio uses a lazy-loaded live iframe
with a separate link for opening the full site.

## Verification

Run `python scripts/build.py`. Check the homepage, verse deep links, contents,
settings, summary/name dialogs, footer links and mobile layout. A build checks
local targets and source hashes; it does not complete independent editorial or
legal review. Confirm the actual host, analytics and consent settings match the
published Privacy page. The Hobby-plan processing-agreement question documented
there remains an open legal point.

## If forking

Replace `SITE_URL` in `pipeline/site_seo.py`, the analytics hostname in
`assets/site-analytics-v1.js`, and operator/hosting information in
`pipeline/site_legal.py`. Remove or replace the upstream GitHub source links.
Rebuild and check canonical URLs, sitemap, social cards and legal pages before
publishing. Preserve the original content/source attribution and licences.
