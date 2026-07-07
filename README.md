# 📡 Paper Radar (Public Administration edition)

A personal paper-tracking radar. Every day it pulls new articles from seven
public administration journals through Crossref, scores and ranks them against
your own research interests (PSM, ethical behavior, Do No Harm, and so on), and
lays them out on a page that reads well on a phone.

The idea comes from [drpwchen/paper-radar](https://github.com/drpwchen/paper-radar),
rebuilt on **GitHub Actions + GitHub Pages** so there is no server to run, no
Cloudflare, and nothing to install.

## Architecture

```
GitHub Actions (daily, 6:00 AM Taipei time)
    └─ fetch_and_score.py
         ├─ pull ~30 days of new articles (abstracts included) from 7 journals via the Crossref API
         ├─ score by the keyword weights in interest_model.json
         └─ write docs/papers.json and commit
GitHub Pages (/docs)
    └─ index.html reads papers.json and renders it
         └─ ✅ read / ⭐ read later / 👍👎 kept in the browser's localStorage
```

## Files

| File | Purpose |
|---|---|
| `config.json` | Which journals to track (ISSN), how many days back, how long to keep |
| `interest_model.json` | Keyword weight table — **edit this to change your taste** |
| `fetch_and_score.py` | Fetch + score script (standard library only) |
| `docs/index.html` | The front-end page |
| `docs/papers.json` | Auto-generated data, incl. cached `abstract_zh` translations (do not edit by hand) |
| `.github/workflows/update.yml` | Daily auto-update schedule |

## Local testing

```bash
python3 fetch_and_score.py        # fetch and generate docs/papers.json
python3 -m http.server -d docs    # open http://localhost:8000 to preview
```

## Deployment (one-time setup)

1. Create a new repo on GitHub (for example `paper-radar`) and push this folder to it.
2. Repo → **Settings → Pages** → set Source to `Deploy from a branch`, Branch to
   `main`, folder to `/docs`, then click Save.
3. Repo → **Actions** → confirm the workflow is enabled (for the first run you can
   trigger it by hand with Run workflow).
4. The site lives at `https://<your-account>.github.io/paper-radar/`.

> Note: GitHub Pages on a free account is always a public page, though it carries
> a `noindex` tag so search engines skip it. The page shows nothing but a list of
> papers; your read and star marks stay in your own browser and are never uploaded.

## Traditional-Chinese abstracts (optional)

Each abstract can carry a Traditional-Chinese translation, shown on the page
behind a **🌐 中譯** button. Translation runs inside the GitHub Action using the
Gemini API, so the key never touches the public page, and each abstract is
translated once and cached in `papers.json` by DOI.

To turn it on:

1. Get a free API key from [Google AI Studio](https://aistudio.google.com/apikey).
2. In the repo, go to **Settings → Secrets and variables → Actions → New
   repository secret**, name it `GEMINI_API_KEY`, and paste the key.
3. Re-run the workflow (Actions → Run workflow). New abstracts are translated on
   each run; already-translated ones are reused.

Without the secret the script simply skips translation, so nothing breaks if you
leave it off. The free tier (Gemini 2.5 Flash) is well within limits here, since
only new papers are translated each day. Note that abstracts are already public,
and free-tier requests may be used by Google to improve their models.

## Adjusting your taste

- **Add a journal:** add one `{"name": "...", "issn": "..."}` entry to `journals`
  in `config.json` (use the electronic ISSN).
- **Change weights:** edit `interest_model.json`. Score = Σ weight × (title hits × 2 + abstract hits).
- **Change the update time:** edit the cron in `.github/workflows/update.yml` (it runs on UTC).

When a score looks off, read the keyword tags lit up on the high-scoring cards,
lower the weight on the ones you don't want, add the topics you keep missing, and
the change takes effect the next day.
