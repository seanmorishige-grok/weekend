#!/usr/bin/env python3
"""Render the weekend digest as a mobile-first static site for GitHub Pages.

Usage:
  python3 render_site.py [json] [--site-dir DIR] [--date YYYY-MM-DD] [--publish]

Weather: run weather_blocks.py --json <json> first; it adds a "weather_blocks"
key that renders as the Sat/Sun Morning/Afternoon tile (legacy "weather" strip
is used only when weather_blocks is absent).

--publish runs: git add -A && git commit && git push (from site dir).
"""
from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote

# --- visual design (v8 autumn palette) ---
CSS = """
:root{--green:#1B5E4A;--pumpkin:#E07A2F;--cream:#FBF6EE;--card:#FFF;--border:#E6D9C4;--ink:#2C2418;--muted:#6B5E4F;--rain:#E8F2F0;--rainb:#7BA89A;--treat:#FFF5E6}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--cream);color:var(--ink);font:15px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}
a{color:var(--green);text-decoration:underline;text-underline-offset:2px}
a:hover{color:var(--pumpkin)}
.wrap{max-width:640px;margin:0 auto;padding:0 0 48px}
.hd{background:var(--green);color:#fff;padding:20px 16px 18px;text-align:center;border-radius:0 0 12px 12px}
.hd h1{font:700 22px/1.2 Georgia,"Times New Roman",serif;margin:0}
.hd .sub{font-size:13px;color:#D5EDE4;margin:6px 0 0}
.pill{display:inline-block;background:var(--pumpkin);color:#fff;font:700 10px/1 Arial,sans-serif;letter-spacing:.5px;text-transform:uppercase;padding:5px 10px;border-radius:999px;margin-top:10px}
.bd{padding:12px 14px}
.intro{margin:0 0 12px;font-size:14px;color:var(--ink)}
.wx{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:0 0 14px}
.wx .b{background:#FFF9F0;border:1px solid var(--border);border-radius:10px;padding:10px;text-align:center}
.wx .hi{font-weight:700;font-size:16px;color:var(--pumpkin)}
.wx .sm{font-size:12px;color:var(--muted);margin-top:2px}
.wt{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:12px 12px 10px;margin:0 0 12px}
.wt-h{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:2px 8px;margin:0 0 8px}
.wt-h h2{font:700 14px Georgia,serif;color:var(--green);margin:0}
.wt-h .wt-k{font-size:11px;color:var(--muted);white-space:nowrap}
.wt-g{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.wd{background:#FFF9F0;border:1px solid var(--border);border-radius:10px;padding:8px;min-width:0}
.wd-h{font:700 15px Georgia,serif;color:var(--ink);margin:0 0 6px;display:flex;justify-content:space-between;align-items:baseline;gap:4px}
.wd-h span{font:400 11px Arial,sans-serif;color:var(--muted)}
.wr{display:flex;gap:8px;align-items:flex-start;background:var(--card);border:1px solid #F0E6D6;border-radius:8px;padding:7px 8px;margin-top:6px}
.wr.ni{border-color:var(--pumpkin);box-shadow:inset 3px 0 0 var(--pumpkin)}
.wr .we{font-size:24px;line-height:1.1;flex:0 0 auto}
.wr .wi{min-width:0;flex:1}
.wr .wl{font:700 10px/1.3 Arial,sans-serif;letter-spacing:.4px;text-transform:uppercase;color:var(--green)}
.wr .wl span{font-weight:400;color:var(--muted);letter-spacing:0;text-transform:none}
.wr .wc{font-weight:700;font-size:14px;line-height:1.25}
.wr .wn{font-size:13px;color:var(--muted)}
.wr .wn b{color:var(--pumpkin)}
.wr .nw{white-space:nowrap;display:inline-block;margin-right:6px}
.wbg{display:inline-block;background:var(--pumpkin);color:#fff;font:700 10px/1 Arial,sans-serif;letter-spacing:.3px;text-transform:uppercase;padding:3px 7px;border-radius:999px;margin-top:4px}
.wsm{margin-top:6px;text-align:center;font-size:12px;color:var(--muted);background:#F3E8D4;border-radius:999px;padding:3px 8px}
.wt-u{font-size:11px;color:var(--muted);margin:8px 0 0;text-align:right}
@media (max-width:359px){.wt-g{grid-template-columns:1fr}}
.box,.cd,.sec{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:12px 14px;margin:0 0 12px}
.box h2,.sec h2,.eh{font:700 14px Georgia,serif;color:var(--green);margin:0 0 8px}
.ix{display:block;padding:6px 0;border-bottom:1px solid #F0E6D6;color:inherit;text-decoration:none}
.ix:last-child{border-bottom:0}
.ix:hover{background:#FFF9F0;margin:0 -6px;padding-left:6px;padding-right:6px;border-radius:6px}
.ix .n{color:var(--pumpkin);font-weight:700}
.ix .m{color:var(--muted);font-size:13px}
.cd{scroll-margin-top:12px}
.cd .nm{font:700 17px/1.25 Georgia,serif}
.cd .nm a{color:inherit;text-decoration:none;border-bottom:2px solid var(--pumpkin)}
.cd .nm a:hover{color:var(--pumpkin)}
.cd .tw{font-size:13px;color:var(--pumpkin);margin:2px 0 6px}
.cd .hk{font:italic 14px Georgia,serif;color:var(--muted);margin:6px 0}
.nb{display:inline-block;background:var(--pumpkin);color:#fff;border-radius:999px;padding:2px 8px;font:700 13px Arial,sans-serif;margin-right:6px}
.tg{display:inline-block;background:#F3E8D4;color:var(--muted);font-size:11px;padding:2px 7px;border-radius:999px;margin:0 4px 4px 0}
.ch{display:inline-block;background:#F5EDE0;border-radius:8px;padding:4px 8px;font-size:13px;color:var(--ink);margin:0 4px 4px 0}
.wh{font-size:14px;margin-top:8px}
.wh b{color:var(--green)}
.rn{background:var(--rain);border-left:3px solid var(--rainb);padding:8px 10px;margin-top:8px;font-size:13px;border-radius:0 8px 8px 0}
.eh{margin-top:12px}
.fd{border:1px solid var(--border);border-radius:8px;padding:8px 10px;margin-top:6px;font-size:13px;line-height:1.4;background:#FAFAF7}
.fd.tr{background:var(--treat);border-color:#F0D9B0}
.fd a.name{font-weight:700;color:var(--ink);text-decoration:none;border-bottom:1px solid var(--pumpkin)}
.fd a.name:hover{color:var(--pumpkin)}
.fd .st{color:var(--pumpkin);font-weight:700;white-space:nowrap}
.fd .u{color:var(--muted);font-size:12px}
.fd .kid{display:block;margin-top:4px;font-style:italic;color:var(--muted)}
.sec ul{margin:0;padding-left:18px}
.sec li{margin:4px 0}
.ft{text-align:center;padding:16px;font-size:12px;color:#D5EDE4;background:var(--green);border-radius:12px 12px 0 0;margin:24px 14px 0}
.ft a{color:#fff}
.nav{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;padding:10px 14px;font-size:13px}
.nav a{color:var(--green);font-weight:600}
.arch li{margin:8px 0}
@media (min-width:700px){
  .hd{border-radius:0 0 16px 16px;margin:0 0 0}
  body{padding-top:8px}
}
"""

TAG_EMOJI = {
    "seasonal": "🎃",
    "indoor": "🏠",
    "outdoor": "🌲",
    "free": "🆓",
    "farm": "🚜",
    "train": "🚂",
    "museum": "🏛️",
    "hike": "🥾",
    "library": "📚",
    "park": "🌳",
}

CITY_HINTS = (
    "Redmond", "Bellevue", "North Bend", "Snoqualmie", "Kirkland", "Carnation",
    "Fall City", "Issaquah", "Woodinville", "Juanita", "Seattle", "Sammamish",
    "Renton", "Mercer Island", "Newcastle", "Duvall",
)


def e(s) -> str:
    return html.escape(str(s or ""), quote=True)


def core_name(name: str) -> str:
    n = (name or "").strip()
    return re.sub(r"\s*\([^)]*\)\s*$", "", n).strip() or n


def extract_city(name: str, town: str | None, food_area: str | None) -> str:
    blob = " ".join(filter(None, [name, town, food_area]))
    for city in CITY_HINTS:
        if re.search(rf"\b{re.escape(city)}\b", blob, re.I):
            return city
    m = re.search(r"\(([^)]+)\)\s*$", name or "")
    if m:
        inside = m.group(1).split("/")[0].split(",")[0].strip()
        inside = re.sub(r"^(downtown|historic|near|on-site)\s+", "", inside, flags=re.I)
        if inside and len(inside) < 40:
            return inside
    if town:
        t = re.split(r"[/—–,]", town)[0].strip()
        t = re.sub(r"\s+(Senior|Community|Center|Park|Farm|Museum|Library).*$", "", t, flags=re.I)
        if t:
            return t
    return "Washington"


def maps_url(name: str, town: str | None = None, address: str | None = None, food_area: str | None = None) -> str:
    if address and str(address).strip():
        q = str(address).strip()
    else:
        base = core_name(name)
        city = extract_city(name, town, food_area)
        if city.lower() in ("washington", "wa"):
            q = f"{base}, WA"
        else:
            q = f"{base}, {city}, WA"
    return "https://www.google.com/maps/search/?api=1&query=" + quote(q)


def maps_link(label: str, name: str, town: str | None = None, address: str | None = None, food_area: str | None = None, cls: str = "") -> str:
    url = maps_url(name, town=town, address=address, food_area=food_area)
    c = f' class="{cls}"' if cls else ""
    return f'<a{c} href="{e(url)}" target="_blank" rel="noopener noreferrer">{e(label)}</a>'


def stars(r: dict) -> str:
    if r.get("rating") and r.get("reviews"):
        return f'★{e(r["rating"])} ({e(r["reviews"])})'
    if r.get("rating"):
        return f'★{e(r["rating"])}'
    return ""


def tag_span(tag: str) -> str:
    emo = TAG_EMOJI.get(tag.lower(), "•")
    return f'<span class="tg">{emo} {e(tag)}</span>'


def food_row(r: dict, idea: dict) -> str:
    cls = "fd tr" if r.get("is_treat") else "fd"
    mk = "🍦 " if r.get("is_treat") else ""
    name = r.get("name") or ""
    label = f"{mk}{name}"
    link = maps_link(
        label,
        name,
        town=idea.get("town"),
        address=r.get("address"),
        food_area=idea.get("food_area"),
        cls="name",
    )
    st = stars(r)
    st_html = f'<span class="st"> {st}</span>' if st else ""
    parts = []
    if r.get("known_for"):
        parts.append(f'<span class="u">Known for:</span> {e(r["known_for"])}')
    if r.get("praise"):
        parts.append(f'<span class="u">Reviews:</span> {e(r["praise"])}')
    body = " · ".join(parts)
    kid = f'<span class="kid">{e(r["kid_note"])}</span>' if r.get("kid_note") else ""
    return f'<div class="{cls}">{link}{st_html}<br>{body}{kid}</div>'


def glance_hook(idea: dict) -> str:
    hook = (idea.get("hook") or "").strip()
    if len(hook) > 72:
        # prefer end at word, but never require ellipsis mid-sentence for site
        cut = hook[:72].rsplit(" ", 1)[0]
        return cut + "…" if cut else hook[:72]
    return hook


def card(idea: dict) -> str:
    num = int(idea.get("num") or 0)
    name = idea.get("name") or ""
    town = idea.get("town") or ""
    aid = f"idea-{num}"
    name_link = maps_link(
        name,
        name,
        town=town,
        address=idea.get("address"),
        food_area=idea.get("food_area"),
    )
    tags = "".join(tag_span(t) for t in (idea.get("tags") or []))
    chips = []
    if idea.get("drive"):
        chips.append(f'<span class="ch">🚗 {e(idea["drive"])}</span>')
    if idea.get("time_block"):
        chips.append(f'<span class="ch">🕙 {e(idea["time_block"])}</span>')
    if idea.get("cost"):
        chips.append(f'<span class="ch">💵 {e(idea["cost"])}</span>')
    if idea.get("outing_length"):
        chips.append(f'<span class="ch">⏱️ {e(idea["outing_length"])}</span>')
    why = idea.get("why") or ""
    rain = idea.get("rain_backup") or ""
    rests = idea.get("restaurants") or []
    foods = "".join(food_row(r, idea) for r in rests)
    food_area = f'<div class="u" style="margin-top:4px">{e(idea.get("food_area") or "")}</div>' if idea.get("food_area") else ""
    hours = f'<div class="u">Hours: {e(idea["hours_detail"])}</div>' if idea.get("hours_detail") else ""
    return f'''<article class="cd" id="{aid}">
<div class="nm"><span class="nb">{num}</span> {name_link}</div>
<div class="tw">{e(town)}</div>
<div>{tags}</div>
<div class="hk">“{e(idea.get("hook") or "")}”</div>
<div>{"".join(chips)}</div>
{hours}
<div class="wh"><b>Why it works for 4 &amp; 2:</b> {e(why)}</div>
<div class="rn"><b>☔ Rain:</b> {e(rain)}</div>
<div class="eh">Eat nearby</div>
{food_area}
{foods}
</article>'''


def index_row(idea: dict) -> str:
    num = int(idea.get("num") or 0)
    return (
        f'<a class="ix" href="#idea-{num}">'
        f'<b class="n">{num}. </b><b>{e(idea.get("name") or "")}</b>'
        f'<span class="m"> — {e(glance_hook(idea))}</span></a>'
    )


def weather_strip(weather: list) -> str:
    cells = []
    for w in weather or []:
        cells.append(
            f'<div class="b">{e(w.get("emoji"))} <b>{e(w.get("day") or w.get("short"))}</b><div class="hi">{e(w.get("high"))}</div>'
            f'<div class="sm">{e(w.get("summary"))}</div></div>'
        )
    return f'<div class="wx">{"".join(cells)}</div>'


def _short_window(w: str) -> str:
    """'9 AM–12 PM' -> '9–12', '3–7 PM' -> '3–7' (compact label for small cards)."""
    return re.sub(r"\s*(AM|PM)", "", w or "").replace(" ", "")


def weather_tile(wb: dict) -> str:
    """Sat/Sun cards with Morning (9–12) and Afternoon (3–7) rows + Nicer badge."""
    days = (wb or {}).get("days") or []
    if not days:
        return ""
    cards = []
    for d in days:
        try:
            dlabel = date.fromisoformat(d.get("date")).strftime("%b %-d")
        except Exception:
            dlabel = ""
        rows = []
        for b in d.get("blocks") or []:
            ni = bool(b.get("nicer"))
            badge = '<span class="wbg">★ Nicer</span>' if ni else ""
            rain = b.get("rain_pct")
            rain_txt = (
                f' <span class="nw" title="max chance of rain">💧<b>{e(rain)}%</b> rain</span>'
                if rain is not None else ""
            )
            rows.append(
                f'<div class="wr{" ni" if ni else ""}">'
                f'<div class="we" aria-hidden="true">{e(b.get("emoji"))}</div>'
                f'<div class="wi"><div class="wl">{e(b.get("label"))} <span>{e(_short_window(b.get("window") or ""))}</span></div>'
                f'<div class="wc">{e(b.get("condition"))}</div>'
                f'<div class="wn"><span class="nw">🌡️ {e(b.get("temp_range"))}</span>{rain_txt}</div>'
                f'{badge}</div></div>'
            )
        same = '<div class="wsm">About the same</div>' if d.get("nicer") == "same" else ""
        cards.append(
            f'<div class="wd"><div class="wd-h">{e(d.get("day") or d.get("short"))} <span>{e(dlabel)}</span></div>'
            f'{"".join(rows)}{same}</div>'
        )
    upd = wb.get("updated_label") or ""
    src = wb.get("source") or ""
    upd_txt = f"Forecast updated {e(upd)}" if upd else "Forecast"
    if upd and not upd.rstrip().endswith("PT"):
        upd_txt += " PT"
    src_txt = f" · {e(src)}" if src else ""
    return (
        '<section class="wt" id="weather" aria-label="Weekend weather">'
        '<div class="wt-h"><h2>🌤️ Weekend weather</h2>'
        '<span class="wt-k">Morning 9–12 · Afternoon 3–7</span></div>'
        f'<div class="wt-g">{"".join(cards)}</div>'
        f'<p class="wt-u">{upd_txt}{src_txt}</p>'
        '</section>'
    )


def weather_section(data: dict) -> str:
    """New AM/PM tile when 'weather_blocks' exists; else the legacy single-day strip."""
    if (data.get("weather_blocks") or {}).get("days"):
        return weather_tile(data["weather_blocks"])
    return weather_strip(data.get("weather") or [])


def list_block(title: str, items) -> str:
    if not items:
        return ""
    if isinstance(items, str):
        body = e(items)
    else:
        body = "<ul>" + "".join(f"<li>{e(x)}</li>" for x in items) + "</ul>"
    return f'<section class="sec"><h2>{e(title)}</h2>{body}</section>'


def render_weekend_html(data: dict, *, archive: bool = False, weekend_date: str = "") -> str:
    meta = data.get("meta") or {}
    title = meta.get("title") or "Weekend Adventures"
    subtitle = meta.get("subtitle") or ""
    intro = meta.get("intro") or ""
    ideas = data.get("ideas") or []
    nav = (
        '<nav class="nav"><a href="./">This weekend</a><a href="archive.html">Archive</a></nav>'
        if not archive
        else '<nav class="nav"><a href="./">This weekend</a><a href="archive.html">Archive</a></nav>'
    )
    # When serving from weekends/YYYY-MM-DD.html, assets/links need ../
    prefix = "../" if archive else ""
    if archive:
        nav = (
            f'<nav class="nav"><a href="{prefix}">This weekend</a>'
            f'<a href="{prefix}archive.html">Archive</a></nav>'
        )

    head = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#1B5E4A">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Weekend Ideas">
<meta name="description" content="{e(subtitle or title)}">
<title>{e(title)}</title>
<link rel="manifest" href="{prefix}manifest.webmanifest">
<link rel="apple-touch-icon" href="{prefix}assets/apple-touch-icon.png">
<link rel="icon" type="image/png" sizes="192x192" href="{prefix}assets/icon-192.png">
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<header class="hd">
<h1>{e(title)}</h1>
<p class="sub">{e(subtitle)}</p>
<span class="pill">Family weekend</span>
</header>
{nav}
<main class="bd">
<p class="intro">{e(intro)}</p>
{weather_section(data)}
<section class="box">
<h2>Quick glance — {len(ideas)} ideas</h2>
{"".join(index_row(i) for i in ideas)}
</section>
{"".join(card(i) for i in ideas)}
{list_block("Nap conflicts", data.get("nap_conflicts"))}
{list_block("Filler bank", data.get("filler_bank"))}
</main>
<footer class="ft">Crest View family digests · <a href="{prefix}archive.html">Archive</a>
{f'<br><span style="opacity:.8">{e(weekend_date)}</span>' if weekend_date else ""}
</footer>
</div>
</body>
</html>"""
    return head


def render_archive_html(entries: list[dict]) -> str:
    """entries: [{date, title, href}, ...] newest first"""
    items = "".join(
        f'<li><a href="{e(x["href"])}"><b>{e(x["date"])}</b> — {e(x["title"])}</a></li>'
        for x in entries
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#1B5E4A">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Weekend Ideas">
<title>Archive — Weekend Ideas</title>
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="assets/apple-touch-icon.png">
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<header class="hd">
<h1>Archive</h1>
<p class="sub">Past weekend digests</p>
</header>
<nav class="nav"><a href="./">This weekend</a><a href="archive.html">Archive</a></nav>
<main class="bd">
<section class="box arch">
<h2>Weekends</h2>
<ul>{items or "<li>No weekends yet.</li>"}</ul>
</section>
</main>
<footer class="ft">Crest View family digests</footer>
</div>
</body>
</html>"""


def write_manifest(site_dir: Path) -> None:
    manifest = {
        "name": "Weekend Ideas",
        "short_name": "Weekend",
        "description": "Family weekend activity digests",
        "start_url": "./",
        "display": "standalone",
        "background_color": "#FBF6EE",
        "theme_color": "#1B5E4A",
        "icons": [
            {"src": "assets/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "assets/icon-512.png", "sizes": "512x512", "type": "image/png"},
        ],
    }
    (site_dir / "manifest.webmanifest").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def infer_date(data: dict, json_path: Path) -> str:
    m = re.search(r"(20\d{2}-\d{2}-\d{2})", json_path.name)
    if m:
        return m.group(1)
    title = (data.get("meta") or {}).get("title") or ""
    # weak fallback
    return date.today().isoformat()


def build_site(json_path: Path, site_dir: Path, weekend_date: str | None = None) -> dict:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    wd = weekend_date or infer_date(data, json_path)
    site_dir.mkdir(parents=True, exist_ok=True)
    (site_dir / "weekends").mkdir(exist_ok=True)
    (site_dir / "assets").mkdir(exist_ok=True)
    (site_dir / "data").mkdir(exist_ok=True)

    # copy JSON into data/
    dest_json = site_dir / "data" / f"{wd}.json"
    dest_json.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    index_html = render_weekend_html(data, archive=False, weekend_date=wd)
    archive_page = render_weekend_html(data, archive=True, weekend_date=wd)
    (site_dir / "index.html").write_text(index_html, encoding="utf-8")
    (site_dir / "weekends" / f"{wd}.html").write_text(archive_page, encoding="utf-8")

    # archive list: scan weekends/*.html
    entries = []
    for p in sorted((site_dir / "weekends").glob("*.html"), reverse=True):
        d = p.stem
        title = d
        try:
            jd = site_dir / "data" / f"{d}.json"
            if jd.exists():
                title = (json.loads(jd.read_text()).get("meta") or {}).get("title") or d
        except Exception:
            pass
        entries.append({"date": d, "title": title, "href": f"weekends/{d}.html"})
    (site_dir / "archive.html").write_text(render_archive_html(entries), encoding="utf-8")
    write_manifest(site_dir)

    # ensure icons exist (no-op if already present)
    return {
        "date": wd,
        "index_bytes": len(index_html.encode("utf-8")),
        "ideas": len(data.get("ideas") or []),
        "site_dir": str(site_dir),
    }


def publish(site_dir: Path, message: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=site_dir, check=True)
    # commit only if changes
    st = subprocess.run(["git", "status", "--porcelain"], cwd=site_dir, capture_output=True, text=True, check=True)
    if not st.stdout.strip():
        print("No changes to publish.")
        return
    subprocess.run(["git", "commit", "-m", message], cwd=site_dir, check=True)
    subprocess.run(["git", "push", "-u", "origin", "HEAD"], cwd=site_dir, check=True)


def main(argv=None) -> int:
    here = Path(__file__).resolve().parent
    p = argparse.ArgumentParser(description="Render weekend digest site")
    p.add_argument("input", nargs="?", default=str(here / "weekend-digest-2026-10-10-v7.json"))
    p.add_argument("--site-dir", default="/workspace/weekend-site")
    p.add_argument("--date", default=None, help="Weekend date YYYY-MM-DD")
    p.add_argument("--publish", action="store_true", help="git commit + push after render")
    p.add_argument("--message", default=None, help="Commit message for --publish")
    args = p.parse_args(argv)

    json_path = Path(args.input)
    site_dir = Path(args.site_dir)
    info = build_site(json_path, site_dir, weekend_date=args.date)
    print(f"Built {info['site_dir']} for {info['date']}: {info['ideas']} ideas, index {info['index_bytes']} bytes")

    # sanity checks
    index = (site_dir / "index.html").read_text(encoding="utf-8")
    for needle in ("Juanita Bay", "google.com/maps", "viewport", "manifest.webmanifest", "theme-color"):
        if needle not in index:
            print(f"MISSING {needle}", file=sys.stderr)
            return 2
    # every idea + restaurant name linked
    data = json.loads(json_path.read_text(encoding="utf-8"))
    def present(name: str) -> bool:
        if not name:
            return True
        return name in index or html.escape(name) in index

    for idea in data.get("ideas") or []:
        if not present(idea.get("name") or ""):
            print(f"MISSING idea name {idea['name']}", file=sys.stderr)
            return 3
        for r in idea.get("restaurants") or []:
            if not present(r.get("name") or ""):
                print(f"MISSING place {r['name']}", file=sys.stderr)
                return 3

    wb = data.get("weather_blocks") or {}
    if wb.get("days"):
        for needle in ('class="wt"', "Forecast updated", "Morning", "Afternoon"):
            if needle not in index:
                print(f"MISSING weather tile piece {needle}", file=sys.stderr)
                return 4
        wb_dates = [d.get("date") for d in wb["days"]]
        if info["date"] not in wb_dates:
            print(f"WARNING: weather_blocks covers {wb_dates}, not weekend {info['date']} — rerun weather_blocks.py", file=sys.stderr)
    else:
        print("note: no weather_blocks in JSON; showing legacy weather strip (run weather_blocks.py first)", file=sys.stderr)

    if args.publish:
        msg = args.message or f"Publish weekend digest {info['date']}"
        publish(site_dir, msg)
        print("Published.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
