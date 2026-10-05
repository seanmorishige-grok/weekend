# Weekend Ideas

Family weekend activity digests — mobile-first site for Crest View (ages 4 & 2).

**Live:** https://seanmorishige-grok.github.io/weekend/

## Weekly publish

```bash
# 1. Update / write the weekend JSON (v7+ schema)
# 2. Render into this repo (or /workspace/weekend-site)
python3 render_site.py path/to/weekend-digest-YYYY-MM-DD.json \
  --site-dir . \
  --date YYYY-MM-DD

# 3. Commit + push (or use --publish)
git add -A
git commit -m "Publish weekend digest YYYY-MM-DD"
git push origin main

# One-shot:
python3 render_site.py path/to.json --site-dir . --date YYYY-MM-DD --publish \
  --message "Publish weekend digest YYYY-MM-DD"
```

GitHub Pages serves from the `main` branch root. After push, Pages rebuilds in ~30–60s.

## Layout

- `index.html` — latest weekend
- `weekends/YYYY-MM-DD.html` — archived copy
- `archive.html` — list of weekends
- `data/YYYY-MM-DD.json` — source JSON
- `manifest.webmanifest` + `assets/` — add-to-home-screen / icons
- `render_site.py` — static site generator

Every activity and restaurant/treat name links to Google Maps (`maps/search/?api=1&query=...`) in a new tab.
