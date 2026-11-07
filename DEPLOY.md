# Hosting the Trip Risk Checker

The app reads only small precomputed tables (`data/processed/*.parquet` that are committed, plus
`outputs/tables/*.csv`), so the repo is light (~15 MB) and the app runs on free tiers.

## Option A — Streamlit Community Cloud (recommended, free, ~5 minutes)

1. Create an empty repository on GitHub (private is fine), then push this folder:

```bash
git remote add origin https://github.com/<your-user>/trip-risk-checker.git
```

```bash
git push -u origin master
```

2. Go to https://share.streamlit.io, sign in with GitHub, click **New app**.
3. Repository: `<your-user>/trip-risk-checker` · Branch: `master` · Main file path: `app/app.py`.
4. Click **Deploy**. Build takes 2-3 minutes; the URL is `https://<app-name>.streamlit.app`.

The theme in `.streamlit/config.toml` and dependencies in `requirements.txt` are picked up automatically.

## Option B — Hugging Face Spaces (free)

Create a Space with the **Streamlit** SDK, then push this repo to it (`app_file: app/app.py` in the
Space README front matter). Same files, same result.

## Option C — run locally for the demo

```bash
streamlit run app/app.py
```

Keep `deck/build/render_pitch/*.PNG` and `outputs/figures/app_tab*.png` as screenshots in case
the venue has no Wi-Fi.

## Refreshing the data each quarter

Download the new BTS monthly files into `questrom_full_flights_2025/` (or a new year folder,
updating `prep.FULL_DIR`), run `python src/enrich.py download`, then rebuild notebooks 01-07 with
`python src/build_nb.py ...` (see README.md). Commit the regenerated `data/processed` tables and
`outputs/tables` CSVs; the hosted app redeploys on push.

---

# The Vercel web app (live)

**https://trip-risk-checker.vercel.app** — a static Preact app (`web/`), no build step, no framework.

- `web/index.html` is the only file deployed to Vercel (project `trip-risk-checker`, team `akhilhnairprojects-projects`).
- `web/app.js`, `web/styles.css` and the data (`web/data/**`) are served from the project's public Vercel Blob
  store (`trip-risk-data`), which the page loads cross-origin. Libraries (Preact, htm, d3-geo, topojson) come from esm.sh.
- To update code or data: edit the files in `web/`, test locally with `python -m http.server 8080 --directory web`,
  then run `python web/deploy_blob.py` (needs `web/.blob_token`, the project's `BLOB_READ_WRITE_TOKEN` from the Vercel
  dashboard → Storage → trip-risk-data). The live site picks the change up within a minute (60 s cache).
- To change `index.html` itself: Vercel dashboard → project → Deployments → create a deployment from the file, or the
  REST API `POST /v13/deployments` with `files: [{file: "index.html", data: ...}]`.
- Deployment protection is off, so the URL is public. Turn it back on in Project → Settings → Deployment Protection if needed.
