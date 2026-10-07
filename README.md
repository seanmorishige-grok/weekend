# Weekend Ideas

Family weekend activity digests — mobile-first site for Crest View (ages 4 & 2).

**Live:** https://seanmorishige-grok.github.io/weekend/

## Weekly publish

```bash
# 0. Weather tile: fetch Sat/Sun Morning (9–12) + Afternoon (3–7) blocks into the JSON
#    (Open-Meteo, NWS fallback; date comes from the filename)
python3 weather_blocks.py --json path/to/weekend-digest-YYYY-MM-DD.json

# 1. Update / write the weekend JSON (v7+ schema), following RESEARCH_CHECKLIST.md
#    (incl. per-pick good_to_know: parking / bring / hours_note / link)
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

## Design

`render_site.py` renders the calm **v2** design by default (index.html, weekends/<date>.html, archive.html).
Fallback to the original autumn design with `--design v1`. Preview a single page without touching
index/archive with `--out preview.html` (add `--publish` to push just that file).
v2 also reads `/workspace/digests/sources.json` for the "Where these come from" section.

## Research checklist (every pick, every week)

Full list: [`RESEARCH_CHECKLIST.md`](RESEARCH_CHECKLIST.md). Each pick needs its usual fields (name, town, hook,
why, drive, hours_short, cost, suggested, rain plan, restaurants). It also gets an optional **Good to know** block,
taken from the venue's **official page** for that weekend:

```json
"good_to_know": {
  "parking":    "Parking & passes: lot cost, garages, Discover Pass / NW Forest Pass, free-day exceptions",
  "bring":      "What to bring: only venue-specific stuff (own books to sign, costumes, cash-only, no food on board)",
  "hours_note": "Non-obvious hours: Sat only, last entry, timed tickets, sells out, reservations",
  "link":       "https://official-page-or-tickets",
  "link_label": "Tickets & info"
}
```

Rules:
- Use only verified info from the official page. **Leave a field "" rather than guess.**
- No stroller or restroom info. Don't repeat drive, cost, length, or tags here; they're already on the card.
- If every field is empty, the card shows no "Good to know" dropdown. Older JSON without the key still renders fine.

## Layout

- `index.html` — latest weekend
- `weekends/YYYY-MM-DD.html` — archived copy
- `archive.html` — list of weekends
- `data/YYYY-MM-DD.json` — source JSON
- `manifest.webmanifest` + `assets/` — add-to-home-screen / icons
- `render_site.py` — static site generator
- `RESEARCH_CHECKLIST.md` — what to verify for each pick every week (incl. Good to know)
- `weather_blocks.py` — Sat/Sun AM/PM forecast → `weather_blocks` key (rendered as the weather tile)

Every activity and restaurant/treat name links to Google Maps (`maps/search/?api=1&query=...`) in a new tab.
