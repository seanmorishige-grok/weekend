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
.wr .we{font-size:24px;line-height:1.1;flex:0 0 auto}
.wr .wi{min-width:0;flex:1}
.wr .wl{font:700 10px/1.3 Arial,sans-serif;letter-spacing:.4px;text-transform:uppercase;color:var(--green)}
.wr .wl span{font-weight:400;color:var(--muted);letter-spacing:0;text-transform:none}
.wr .wc{font-weight:700;font-size:14px;line-height:1.25}
.wr .wn{font-size:13px;color:var(--muted)}
.wr .wn b{color:var(--pumpkin)}
.wr .nw{white-space:nowrap;display:inline-block;margin-right:6px}
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
    """Sat/Sun cards with Morning (9–12) and Afternoon (3–7) rows."""
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
            rain = b.get("rain_pct")
            rain_txt = (
                f' <span class="nw" title="max chance of rain">💧<b>{e(rain)}%</b> rain</span>'
                if rain is not None else ""
            )
            rows.append(
                f'<div class="wr">'
                f'<div class="we" aria-hidden="true">{e(b.get("emoji"))}</div>'
                f'<div class="wi"><div class="wl">{e(b.get("label"))} <span>{e(_short_window(b.get("window") or ""))}</span></div>'
                f'<div class="wc">{e(b.get("condition"))}</div>'
                f'<div class="wn"><span class="nw">🌡️ {e(b.get("temp_range"))}</span>{rain_txt}</div>'
                f'</div></div>'
            )
        cards.append(
            f'<div class="wd"><div class="wd-h">{e(d.get("day") or d.get("short"))} <span>{e(dlabel)}</span></div>'
            f'{"".join(rows)}</div>'
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


# =====================================================================
# v2 design ("calm"): opt-in via --design v2. v1 above stays the default.
# =====================================================================
CSS_V2 = """
:root{--bg:#FAF8F4;--card:#FFF;--line:#ECE6DC;--ink:#23201C;--muted:#6E675E;--soft:#9A9288;--acc:#1B5E4A;--accbg:#EEF4F1}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 -apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI",Roboto,Arial,sans-serif;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}
.w{max-width:600px;margin:0 auto;padding:max(28px,env(safe-area-inset-top)) 20px 56px}
.top{margin:0 0 22px}
.kick{font:600 12px/1 -apple-system,BlinkMacSystemFont,Arial,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:var(--acc);margin:0 0 10px}
h1{font:700 28px/1.15 Georgia,"Times New Roman",serif;margin:0 0 6px;letter-spacing:-.01em}
.sub{color:var(--muted);font-size:14px;margin:0}
.nav{margin:12px 0 0;font-size:14px;display:flex;gap:16px}
.nav a{color:var(--acc);font-weight:600}
.intro{color:var(--muted);font-size:15px;margin:0 0 24px}
h2{font:600 13px/1 -apple-system,BlinkMacSystemFont,Arial,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:var(--soft);margin:32px 0 12px}
.panel{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:6px 16px}
/* weather */
.wx2{display:grid;grid-template-columns:1fr 1fr;gap:0 16px;padding:14px 16px}
.wx2 .d{font:600 15px/1.2 Georgia,serif;margin:0 0 8px}
.wx2 .d span{font:400 13px -apple-system,Arial,sans-serif;color:var(--soft);margin-left:4px}
.wx2 .s{display:flex;gap:8px;align-items:flex-start;padding:8px 0;border-top:1px solid var(--line)}
.wx2 .e{font-size:22px;line-height:1}
.wx2 .l{font-size:12px;color:var(--soft)}
.wx2 .c{font-size:14px;font-weight:600;line-height:1.3}
.wx2 .n{font-size:13px;color:var(--muted)}
.upd{font-size:12px;color:var(--soft);margin:8px 2px 0}
/* quick glance */
.gl a{display:flex;gap:12px;padding:12px 0;border-top:1px solid var(--line)}
.gl a:first-child{border-top:0}
.gl .i{color:var(--acc);font-weight:700;min-width:18px;font-variant-numeric:tabular-nums}
.gl .t{font-weight:600;font-size:15px;line-height:1.3}
.gl .m{display:block;font-size:13px;color:var(--muted);font-weight:400;margin-top:2px}
/* idea cards */
.cd{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px 18px 6px;margin:0 0 14px;scroll-margin-top:16px}
.num{font:600 12px/1 -apple-system,Arial,sans-serif;color:var(--acc);letter-spacing:.06em;margin:0 0 8px}
.cd h3{font:700 20px/1.25 Georgia,serif;margin:0}
.cd h3 a:active{color:var(--acc)}
.town{font-size:13px;color:var(--soft);margin:3px 0 0}
.hook{font-size:15px;margin:10px 0 0}
.meta{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:13px;color:var(--muted);margin:12px 0 0}
.meta span{overflow-wrap:anywhere}
.rain{font-size:14px;color:var(--ink);background:var(--accbg);border-radius:10px;padding:10px 12px;margin:14px 0 0}
.rain b{color:var(--acc);font-weight:600}
details{border-top:1px solid var(--line);margin:14px -18px 0;padding:0 18px}
details+details{margin-top:0}
summary{list-style:none;cursor:pointer;padding:13px 0;font-size:14px;font-weight:600;color:var(--acc);display:flex;justify-content:space-between;align-items:center}
summary::-webkit-details-marker{display:none}
summary:after{content:"";width:7px;height:7px;border-right:2px solid var(--soft);border-bottom:2px solid var(--soft);transform:rotate(45deg);margin:-4px 4px 0 0;transition:transform .15s}
details[open] summary:after{transform:rotate(-135deg);margin-top:4px}
summary .q{font-weight:400;color:var(--soft);margin-left:auto;margin-right:12px;font-size:13px}
.dt{font-size:14px;color:var(--muted);padding:0 0 14px}
.dt p{margin:0 0 10px}
.dt b{color:var(--ink);font-weight:600}
.fa{font-size:13px;color:var(--soft);margin:0 0 6px}
.fr{padding:9px 0;border-top:1px solid var(--line)}
.fr:first-of-type{border-top:0}
.fr .h{display:flex;justify-content:space-between;gap:10px;align-items:baseline}
.fr .h a{font-weight:600;color:var(--ink);font-size:15px;text-decoration:underline;text-decoration-color:var(--line);text-underline-offset:3px}
.fr .r{font-size:13px;color:var(--muted);white-space:nowrap;font-variant-numeric:tabular-nums}
.fr .k{font-size:13px;color:var(--muted);margin-top:2px}
.fr .x{font-size:13px;color:var(--soft);margin-top:2px}
.tl{font:600 11px/1 -apple-system,Arial,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:var(--soft);margin:14px 0 2px}
.lst{margin:0;padding:0;list-style:none}
.lst li{padding:12px 0;border-top:1px solid var(--line);font-size:14px;color:var(--muted)}
.lst li:first-child{border-top:0}
.ft{margin:40px 0 0;text-align:center;font-size:12px;color:var(--soft)}
.ft a{color:var(--acc)}
@media (max-width:359px){.wx2{grid-template-columns:1fr}.w{padding-left:14px;padding-right:14px}}
"""


def _clip_meta(s: str) -> str:
    """Short meta-row form: text before the first '(' / ';' / ' — ' / ' via '. Full text stays in Details."""
    t = (s or "").strip()
    for sep in (" (", ";", " — ", " – ", " via "):
        if sep in t:
            t = t.split(sep, 1)[0]
    return t.strip(" ,")


def _short_reviews(n) -> str:
    try:
        v = int(str(n).replace(",", ""))
    except (TypeError, ValueError):
        return e(n)
    return f"{v/1000:.1f}k".replace(".0k", "k") if v >= 1000 else str(v)


def _food_row_v2(r: dict, idea: dict) -> str:
    name = r.get("name") or ""
    url = maps_url(name, town=idea.get("town"), address=r.get("address"), food_area=idea.get("food_area"))
    if r.get("rating"):
        rv = f" · {_short_reviews(r['reviews'])}" if r.get("reviews") else ""
        rating = f'<span class="r">★ {e(r["rating"])}{rv}</span>'
    else:
        rating = '<span class="r">no rating</span>'
    known = " — ".join(x for x in (r.get("known_for"), r.get("praise")) if x)
    kid = f'<div class="x">{e(r["kid_note"])}</div>' if r.get("kid_note") else ""
    return (
        f'<div class="fr"><div class="h"><a href="{e(url)}" target="_blank" rel="noopener noreferrer">{e(name)}</a>{rating}</div>'
        f'<div class="k">{e(known)}</div>{kid}</div>'
    )


def card_v2(idea: dict) -> str:
    num = int(idea.get("num") or 0)
    name = idea.get("name") or ""
    url = maps_url(name, town=idea.get("town"), address=idea.get("address"), food_area=idea.get("food_area"))
    meta = [
        ("🚗", _clip_meta(idea.get("drive"))),
        ("🕙", _clip_meta(idea.get("time_block"))),
        ("", _clip_meta(idea.get("cost"))),
        ("⏱", _clip_meta(idea.get("outing_length"))),
    ]
    meta_html = "".join(f'<span>{(i + " ") if i else ""}{e(t)}</span>' for i, t in meta if t)
    # full details (nothing dropped)
    det = []
    if idea.get("why"):
        det.append(f'<p><b>Why it works for 4 &amp; 2.</b> {e(idea["why"])}</p>')
    for label, key in (("Hours", "hours_detail"), ("Drive", "drive"), ("When", "time_block"), ("Cost", "cost"), ("Length", "outing_length")):
        if idea.get(key):
            det.append(f'<p><b>{label}.</b> {e(idea[key])}</p>')
    if idea.get("tags"):
        det.append(f'<p><b>Tags.</b> {e(" · ".join(idea["tags"]))}</p>')
    rests = idea.get("restaurants") or []
    meals = [r for r in rests if not r.get("is_treat")]
    treats = [r for r in rests if r.get("is_treat")]
    food = ""
    if rests:
        fa = f'<div class="fa">{e(idea["food_area"])}</div>' if idea.get("food_area") else ""
        mh = "".join(_food_row_v2(r, idea) for r in meals)
        th = "".join(_food_row_v2(r, idea) for r in treats)
        cnt = f"{len(meals)} meal{'s' if len(meals) != 1 else ''}" + (f" · {len(treats)} treat{'s' if len(treats) != 1 else ''}" if treats else "")
        food = (
            f'<details><summary>Eat nearby<span class="q">{cnt}</span></summary><div class="dt">{fa}'
            f'{("<div class=tl>Meals</div>" + mh) if mh else ""}{("<div class=tl>Treats</div>" + th) if th else ""}</div></details>'
        )
    rain = f'<div class="rain"><b>☔ Rain plan</b> · {e(idea["rain_backup"])}</div>' if idea.get("rain_backup") else ""
    return f"""<article class="cd" id="idea-{num}">
<div class="num">IDEA {num}</div>
<h3><a href="{e(url)}" target="_blank" rel="noopener noreferrer">{e(name)}</a></h3>
<div class="town">{e(idea.get("town") or "")}</div>
<p class="hook">{e(idea.get("hook") or "")}</p>
<div class="meta">{meta_html}</div>
{rain}
<details><summary>Why it works &amp; details</summary><div class="dt">{"".join(det)}</div></details>
{food}
</article>"""


def weather_v2(data: dict) -> str:
    wb = data.get("weather_blocks") or {}
    days = wb.get("days") or []
    if not days:
        return weather_strip(data.get("weather") or [])
    cols = []
    for d in days:
        try:
            dl = date.fromisoformat(d.get("date")).strftime("%b %-d")
        except Exception:
            dl = ""
        slots = "".join(
            f'<div class="s"><div class="e" aria-hidden="true">{e(b.get("emoji"))}</div><div>'
            f'<div class="l">{e(b.get("label"))} {e(_short_window(b.get("window") or ""))}</div>'
            f'<div class="c">{e(b.get("condition"))}</div>'
            f'<div class="n">{e(b.get("temp_range"))} · {e(b.get("rain_pct"))}% rain</div></div></div>'
            for b in d.get("blocks") or []
        )
        cols.append(f'<div><div class="d">{e(d.get("day"))}<span>{e(dl)}</span></div>{slots}</div>')
    upd = wb.get("updated_label") or ""
    if upd and not upd.rstrip().endswith("PT"):
        upd += " PT"
    src = f" · {e(wb['source'])}" if wb.get("source") else ""
    return (
        f'<h2 id="weather">Weather</h2><section class="panel wx2" aria-label="Weekend weather">{"".join(cols)}</section>'
        f'<p class="upd">Forecast updated {e(upd)}{src}</p>'
    )


def render_weekend_html_v2(data: dict, *, prefix: str = "", weekend_date: str = "") -> str:
    meta = data.get("meta") or {}
    title = meta.get("title") or "Weekend Adventures"
    subtitle = meta.get("subtitle") or ""
    ideas = data.get("ideas") or []
    glance = "".join(
        f'<a href="#idea-{int(i.get("num") or 0)}"><span class="i">{int(i.get("num") or 0)}</span>'
        f'<span class="t">{e(i.get("name") or "")}<span class="m">{e(_clip_meta(i.get("time_block")))}'
        f'{(" · " + e(_clip_meta(i.get("cost")))) if i.get("cost") else ""}</span></span></a>'
        for i in ideas
    )
    nap = data.get("nap_conflicts")
    nap_html = ""
    if nap:
        items = nap if isinstance(nap, list) else [nap]
        nap_html = '<h2>Nap conflicts</h2><section class="panel"><ul class="lst">' + "".join(f"<li>{e(x)}</li>" for x in items) + "</ul></section>"
    fb = data.get("filler_bank")
    fb_html = ""
    if fb:
        body = e(fb) if isinstance(fb, str) else "<ul class=lst>" + "".join(f"<li>{e(x)}</li>" for x in fb) + "</ul>"
        fb_html = f'<h2>Filler bank</h2><section class="panel"><div class="dt" style="padding:12px 0">{body}</div></section>'
    m = re.search(r"—\s*(.+)$", title)
    kick = f"Family weekend · {m.group(1)}" if m else "Family weekend"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#FAF8F4">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Weekend Ideas">
<meta name="description" content="{e(subtitle or title)}">
<title>{e(title)}</title>
<link rel="manifest" href="{prefix}manifest.webmanifest">
<link rel="apple-touch-icon" href="{prefix}assets/apple-touch-icon.png">
<link rel="icon" type="image/png" sizes="192x192" href="{prefix}assets/icon-192.png">
<style>{CSS_V2}</style>
</head>
<body>
<div class="w">
<header class="top">
<p class="kick">{e(kick)}</p>
<h1>{e(title)}</h1>
<p class="sub">{e(subtitle)}</p>
<nav class="nav"><a href="{prefix}./">This weekend</a><a href="{prefix}archive.html">Archive</a></nav>
</header>
<p class="intro">{e(meta.get("intro") or "")}</p>
{weather_v2(data)}
<h2>At a glance · {len(ideas)} ideas</h2>
<nav class="panel gl">{glance}</nav>
<h2>The ideas</h2>
{"".join(card_v2(i) for i in ideas)}
{nap_html}
{fb_html}
<footer class="ft">Crest View family digests · <a href="{prefix}archive.html">Archive</a>{(" · " + e(weekend_date)) if weekend_date else ""}</footer>
</div>
</body>
</html>"""


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
    p.add_argument("--design", choices=["v1", "v2"], default="v1", help="v1 = current site (default); v2 = calm redesign")
    p.add_argument("--out", default=None, help="Preview mode: write ONLY this file (relative to --site-dir), e.g. preview.html; index/archive/data untouched")
    args = p.parse_args(argv)

    if args.out:
        json_path = Path(args.input)
        site_dir = Path(args.site_dir)
        data = json.loads(json_path.read_text(encoding="utf-8"))
        wd = args.date or infer_date(data, json_path)
        out = site_dir / args.out
        page = render_weekend_html_v2(data, weekend_date=wd) if args.design == "v2" else render_weekend_html(data, weekend_date=wd)
        out.write_text(page, encoding="utf-8")
        print(f"Wrote preview {out} ({args.design}, {len(page.encode())} bytes)")
        for i in data.get("ideas") or []:
            for nm in [i.get("name")] + [r.get("name") for r in i.get("restaurants") or []]:
                if nm and nm not in page and html.escape(nm) not in page:
                    print(f"MISSING {nm}", file=sys.stderr); return 3
        for bad in ("Nicer", "About the same"):
            if bad in page:
                print(f"UNEXPECTED {bad}", file=sys.stderr); return 4
        if args.publish:
            subprocess.run(["git", "add", "--", args.out], cwd=site_dir, check=True)
            st = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=site_dir)
            if st.returncode == 0:
                print("No changes to publish."); return 0
            subprocess.run(["git", "commit", "-m", args.message or f"Preview {args.design} {wd}", "--", args.out], cwd=site_dir, check=True)
            subprocess.run(["git", "push", "origin", "HEAD"], cwd=site_dir, check=True)
            print("Published preview.")
        return 0

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
