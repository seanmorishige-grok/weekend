#!/usr/bin/env python3
"""Render the weekend digest as a mobile-first static site for GitHub Pages.

Usage:
  python3 render_site.py [json] [--site-dir DIR] [--date YYYY-MM-DD] [--publish]

Weather: run weather_blocks.py --json <json> first; it adds a "weather_blocks"
key that renders as the Sat/Sun Morning/Afternoon tile (legacy "weather" strip
is used only when weather_blocks is absent).

--publish runs: git add -A && git commit && git push (from site dir).
--design v2 (default) renders the calm design to index.html, weekends/<date>.html
and archive.html; --design v1 renders the original autumn design.
--out FILE renders only that one file (preview); index/archive/data untouched.
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
    return html.escape("" if s is None or s is False else str(s), quote=True)


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
.top{margin:0 0 22px;position:relative}
.gear{position:absolute;top:-12px;right:-12px;width:44px;height:44px;border:0;background:none;padding:0;cursor:pointer;color:var(--soft);display:flex;align-items:center;justify-content:center;-webkit-tap-highlight-color:transparent}
.gear svg{display:block}
.gear:active{color:var(--muted)}
.gear:focus-visible{outline:2px solid var(--line);outline-offset:-6px;border-radius:8px}
.top .kick{padding-right:44px}
.sheet{position:fixed;inset:0;z-index:20;display:flex;align-items:flex-end;justify-content:center}
.sheet[hidden]{display:none}
.sheet-bg{position:absolute;inset:0;background:rgba(35,32,28,.35)}
.sheet-card{position:relative;background:var(--bg);width:100%;max-width:600px;max-height:88vh;overflow:auto;-webkit-overflow-scrolling:touch;border-radius:20px 20px 0 0;padding:20px 20px max(24px,env(safe-area-inset-bottom));box-shadow:0 -8px 30px rgba(0,0,0,.12);animation:up .22s ease}
@keyframes up{from{transform:translateY(24px);opacity:.6}to{transform:none;opacity:1}}
.sheet-top{display:flex;justify-content:space-between;align-items:center;margin:0 0 4px}
.sheet-top h2{margin:0;font:700 22px/1.2 Georgia,serif;letter-spacing:0;text-transform:none;color:var(--ink)}
.sheet-x{width:34px;height:34px;border:0;background:var(--line);border-radius:999px;color:var(--muted);font-size:14px;cursor:pointer}
.hx{font-size:15px;line-height:1.5;color:var(--muted);margin:6px 0 4px}
.hk{padding:14px 0 0}
.hk label,.hk .kl{display:block;font:600 13px -apple-system,Arial,sans-serif;color:var(--soft);margin:0 0 7px;letter-spacing:.02em}
.seg{display:flex;background:var(--line);border-radius:12px;padding:3px;gap:3px}
.seg button{flex:1;min-height:42px;border:0;background:none;border-radius:9px;font:600 15px -apple-system,Arial,sans-serif;color:var(--muted);cursor:pointer;-webkit-tap-highlight-color:transparent}
.seg button[aria-checked="true"]{background:var(--card);color:var(--ink);box-shadow:0 1px 3px rgba(0,0,0,.12)}
.seg button:focus-visible{outline:2px solid var(--acc);outline-offset:-2px}
.hk input{width:100%;box-sizing:border-box;min-height:44px;border:1px solid var(--line);border-radius:12px;background:var(--card);padding:10px 12px;font:16px -apple-system,Arial,sans-serif;color:var(--ink)}
.hk input:focus{outline:2px solid var(--acc);outline-offset:-1px;border-color:transparent}
.save{display:block;width:100%;min-height:48px;margin:18px 0 0;border:0;border-radius:12px;background:var(--acc);color:#fff;font:600 16px -apple-system,Arial,sans-serif;cursor:pointer}
.save:active{opacity:.85}
.hsaved{font-size:14px;color:var(--acc);margin:10px 0 0;min-height:20px;text-align:center}
.gl2 a{color:var(--acc);font-weight:600}
.hs-src{color:var(--acc);font-size:14px;font-weight:600}
@media (min-width:700px){.sheet{align-items:center}.sheet-card{border-radius:20px}}
.kick{font:600 12px/1 -apple-system,BlinkMacSystemFont,Arial,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:var(--acc);margin:0 0 10px}
h1{font:700 28px/1.15 Georgia,"Times New Roman",serif;margin:0 0 6px;letter-spacing:-.01em}
.sub{color:var(--muted);font-size:14px;margin:0}
.tag{color:var(--soft);font-size:13px;margin:4px 0 0}
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
/* plans count + restore */
.rs{margin:2px 2px 0;text-align:center}
.rs .done{font-size:13px;color:var(--soft);margin:0 0 6px}
.rs button{background:none;border:0;padding:4px 0;font-size:13px;color:var(--soft);text-decoration:underline;text-underline-offset:3px;cursor:pointer}
.cd{position:relative}
.no{font:400 15px Georgia,serif;color:var(--soft);margin-right:8px}
.cd h3{padding-right:34px}
.cx{position:absolute;top:12px;right:12px;z-index:1}
.cx button{font:600 13px -apple-system,Arial,sans-serif;cursor:pointer;border-radius:999px}
.cx-x{width:30px;height:30px;border:0;background:transparent;color:var(--soft);font-size:15px!important;line-height:30px;padding:0}
.cx-x:active{background:var(--line)}
.cx-q{display:inline-flex;gap:6px;background:var(--card);padding-left:6px;box-shadow:-14px 0 12px var(--card)}
.cx-q[hidden]{display:none}
.cx-yes{border:0;background:#D93A3A;color:#fff;padding:6px 12px}
.cx-no{border:1px solid var(--line);background:var(--card);color:var(--ink);padding:5px 12px}
.gone{opacity:0;margin-top:0!important;margin-bottom:0!important;padding-top:0!important;padding-bottom:0!important;border-width:0!important}
.anim{overflow:hidden;transition:height .28s ease,opacity .2s ease,margin .28s ease,padding .28s ease}
.toast{position:fixed;left:50%;bottom:max(20px,env(safe-area-inset-bottom));transform:translateX(-50%);background:#23201C;color:#fff;border-radius:999px;padding:8px 8px 8px 18px;font-size:14px;display:flex;gap:14px;align-items:center;box-shadow:0 6px 24px rgba(0,0,0,.18);z-index:9;max-width:calc(100% - 32px)}
.toast[hidden]{display:none}
.toast button{background:transparent;border:0;color:#9FD9C4;font:600 14px -apple-system,Arial,sans-serif;padding:6px 10px;cursor:pointer}
/* idea cards */
.cd{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px 18px 6px;margin:0 0 14px;scroll-margin-top:16px}
.cd h3{font:700 20px/1.25 Georgia,serif;margin:0}
.cd h3 a:active{color:var(--acc)}
.town{font-size:13px;color:var(--soft);margin:3px 0 0}
.hook{font-size:15px;margin:10px 0 0}
.sugg{font-size:13px;font-style:italic;color:var(--soft);margin:6px 0 0}
.why{font-size:14px;color:var(--muted);margin:12px 0 0}
.why b{color:var(--ink);font-weight:600}
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
details.src{margin:32px 0 0;padding:0 2px;border-top:1px solid var(--line)}
details.src summary{color:var(--muted);font-weight:500;font-size:13px}
.sg{padding:8px 0;border-top:1px solid var(--line);font-size:13px;line-height:1.7}
.sg:first-child{border-top:0}
.st2{font:600 11px/1.4 -apple-system,Arial,sans-serif;letter-spacing:.06em;text-transform:uppercase;color:var(--soft)}
.sg a{color:var(--muted);text-decoration:underline;text-decoration-color:var(--line);text-underline-offset:3px}
.nw2{display:inline-block;font:600 10px/1 -apple-system,Arial,sans-serif;color:var(--acc);background:var(--accbg);border-radius:999px;padding:2px 6px;vertical-align:1px}
.ft{margin:24px 0 0;text-align:center;font-size:12px;color:var(--soft)}
.ft a{color:var(--acc)}
@media (max-width:359px){.wx2{grid-template-columns:1fr}.w{padding-left:14px;padding-right:14px}}
"""

JS_V2 = r"""
(function(){
var KEY='weekend-cleared:'+(window.WEEKEND_DATE||location.pathname);
var cleared=[];try{cleared=JSON.parse(localStorage.getItem(KEY)||'[]')}catch(e){}
function save(){try{localStorage.setItem(KEY,JSON.stringify(cleared))}catch(e){}}
function els(n){return [document.getElementById('idea-'+n)].filter(Boolean)}
function name(n){var c=document.getElementById('idea-'+n),a=c&&c.querySelector('h3 a');return a?a.textContent:''}
function refresh(){
  var cards=[].slice.call(document.querySelectorAll('article.cd')),n=cards.filter(function(c){return !c.hidden}).length;
  var left=document.getElementById('left');if(left)left.textContent=n;
  document.getElementById('alldone').hidden=n>0;
  var b=document.getElementById('showc');document.getElementById('nc').textContent=cleared.length;b.hidden=!cleared.length;
}
function collapse(el){
  el.style.height=el.offsetHeight+'px';el.classList.add('anim');el.offsetHeight;
  el.classList.add('gone');el.style.height='0px';
  var done=function(){el.hidden=true;el.classList.remove('anim','gone');el.style.height='';refresh()};
  var t=setTimeout(done,400);
}
function expand(el){
  el.hidden=false;el.classList.add('anim','gone');el.style.height='0px';el.offsetHeight;
  el.classList.remove('gone');el.style.height=el.scrollHeight+'px';
  setTimeout(function(){el.classList.remove('anim');el.style.height=''},400);
}
var toastT,lastN=null;
function toast(n){
  var t=document.getElementById('toast');lastN=n;
  document.getElementById('tmsg').textContent='Cleared '+name(n);
  t.hidden=false;clearTimeout(toastT);toastT=setTimeout(function(){t.hidden=true;lastN=null},5000);
}
function clear(n){
  n=String(n);if(cleared.indexOf(n)>=0)return;
  cleared.push(n);save();els(n).forEach(collapse);toast(n);
}
function restore(n){
  n=String(n);var i=cleared.indexOf(n);if(i<0)return;
  cleared.splice(i,1);save();els(n).forEach(expand);setTimeout(refresh,0);refresh();
}
// initial state (no animation)
cleared.forEach(function(n){els(n).forEach(function(el){el.hidden=true})});refresh();
document.getElementById('undo').addEventListener('click',function(){
  if(lastN!==null)restore(lastN);document.getElementById('toast').hidden=true;lastN=null;
});
document.getElementById('showc').addEventListener('click',function(){cleared.slice().forEach(restore)});

// ---- card ✕ : two-step
var armed=null,armT;
function disarm(){if(!armed)return;armed.querySelector('.cx-q').hidden=true;armed.querySelector('.cx-x').hidden=false;armed=null;clearTimeout(armT)}
document.querySelectorAll('.cx').forEach(function(cx){
  cx.querySelector('.cx-x').addEventListener('click',function(ev){
    ev.stopPropagation();disarm();armed=cx;
    cx.querySelector('.cx-x').hidden=true;cx.querySelector('.cx-q').hidden=false;cx.querySelector('.cx-no').focus({preventScroll:true});
    armT=setTimeout(disarm,4000);
  });
  cx.querySelector('.cx-no').addEventListener('click',function(ev){ev.stopPropagation();disarm()});
  cx.querySelector('.cx-yes').addEventListener('click',function(ev){ev.stopPropagation();var n=cx.dataset.n;disarm();clear(n)});
});
document.addEventListener('click',function(ev){if(armed&&!armed.contains(ev.target))disarm()},true);

// ---- How we pick sheet (gear): 3 knobs + free text, saved on this phone, Save opens a prefilled text
var how=document.getElementById('how'),gear=document.getElementById('gear'),PK='mgd-prefs';
if(how&&gear){
  var prefs={};try{prefs=JSON.parse(localStorage.getItem(PK)||'{}')||{}}catch(e){}
  var segs=how.querySelectorAll('.seg'),also=document.getElementById('how-also'),msg=document.getElementById('how-saved');
  var pick=function(seg,btn){seg.querySelectorAll('button').forEach(function(b){var on=b===btn;b.setAttribute('aria-checked',on?'true':'false');b.tabIndex=on?0:-1})};
  segs.forEach(function(seg){
    var bs=[].slice.call(seg.querySelectorAll('button')),cur=bs.filter(function(b){return b.dataset.v===prefs[seg.dataset.k]})[0]||bs.filter(function(b){return b.getAttribute('aria-checked')==='true'})[0]||bs[0];
    pick(seg,cur);
    bs.forEach(function(b,i){
      b.addEventListener('click',function(){pick(seg,b)});
      b.addEventListener('keydown',function(ev){var d=ev.key==='ArrowRight'||ev.key==='ArrowDown'?1:ev.key==='ArrowLeft'||ev.key==='ArrowUp'?-1:0;if(!d)return;ev.preventDefault();var n=bs[(i+d+bs.length)%bs.length];pick(seg,n);n.focus()});
    });
  });
  if(prefs.also)also.value=prefs.also;
  var val=function(k){var b=how.querySelector('.seg[data-k="'+k+'"] [aria-checked="true"]');return b?b.dataset.v:''};
  document.getElementById('how-save').addEventListener('click',function(){
    var p={drive:val('drive'),vibe:val('vibe'),lean:val('lean'),also:also.value.trim().slice(0,140),saved:new Date().toISOString()};
    try{localStorage.setItem(PK,JSON.stringify(p))}catch(e){}
    var t='Good Days settings: Drive='+p.drive+', Vibe='+p.vibe+', Lean='+p.lean+(p.also?', Also: '+p.also:'');
    var url='sms:'+how.dataset.sms+'?&body='+encodeURIComponent(t);
    msg.textContent='Saved ✓ Opening Messages to send it to us.';
    (window.mgdOpenSms||function(u){location.href=u})(url);
  });
  var openHow=function(){msg.textContent='';how.hidden=false;document.body.style.overflow='hidden';how.querySelector('.sheet-x').focus({preventScroll:true})};
  var closeHow=function(){how.hidden=true;document.body.style.overflow='';if(location.hash==='#how')history.replaceState(null,'',location.pathname+location.search);gear.focus({preventScroll:true})};
  gear.addEventListener('click',openHow);
  how.querySelectorAll('[data-close]').forEach(function(x){x.addEventListener('click',closeHow)});
  document.addEventListener('keydown',function(ev){if(ev.key==='Escape'&&!how.hidden)closeHow()});
  document.getElementById('how-src').addEventListener('click',function(ev){
    ev.preventDefault();closeHow();var d=document.getElementById('sources');
    if(d){d.open=true;d.scrollIntoView({behavior:'smooth',block:'start'})}
  });
  if(location.hash==='#how')openHow();
}

})();
"""


def _hours_short(idea: dict) -> str:
    """Actual opening hours, short form. Prefers JSON 'hours_short'; falls back to clipped hours_detail.
    (The suggested 'time_block' is intentionally not rendered in v2.)"""
    return (idea.get("hours_short") or _clip_meta(idea.get("hours_detail")) or "").strip()


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
        rating = ''
    known = " — ".join(x for x in (r.get("known_for"), r.get("praise")) if x)
    kid = f'<div class="x">{e(r["kid_note"])}</div>' if r.get("kid_note") else ""
    return (
        f'<div class="fr"><div class="h"><a href="{e(url)}" target="_blank" rel="noopener noreferrer">{e(name)}</a>{rating}</div>'
        f'<div class="k">{e(known)}</div>{kid}</div>'
    )


_GTK_SKIP = re.compile(r"\b(stroller|restroom|bathroom|toilet|changing table)s?\b", re.I)


def _gtk_clean(txt) -> str:
    """Keep only sentences that aren't stroller/restroom info (not wanted in Good to know)."""
    t = (txt or "").strip()
    if not t:
        return ""
    parts = re.split(r"(?<=[.!?;])\s+", t)
    return " ".join(p for p in parts if not _GTK_SKIP.search(p)).strip()


def good_to_know_v2(idea: dict) -> str:
    """'Good to know' dropdown: parking & passes, what to bring, hours notes, official link.
    Reads optional JSON idea.good_to_know = {parking, bring, hours_note, link, link_label}.
    Omitted entirely when there is nothing useful."""
    g = idea.get("good_to_know") or {}
    if not isinstance(g, dict):
        return ""
    rows = []
    for label, key in (("Parking &amp; passes", "parking"), ("What to bring", "bring"), ("Hours note", "hours_note")):
        val = g.get(key)
        if isinstance(val, list):
            val = "; ".join(str(x) for x in val if x)
        val = _gtk_clean(val)
        if val:
            rows.append(f'<p><b>{label}.</b> {e(val)}</p>')
    link = g.get("link")
    if isinstance(link, dict):
        url, lbl = link.get("url"), link.get("label")
    else:
        url, lbl = link, g.get("link_label")
    if url and str(url).startswith(("http://", "https://")):
        rows.append(f'<p class="gl2"><a href="{e(url)}" target="_blank" rel="noopener noreferrer">{e(lbl or "Official website")} ↗</a></p>')
    if not rows:
        return ""
    return f'<details class="gtk"><summary>Good to know</summary><div class="dt">{"".join(rows)}</div></details>'


def card_v2(idea: dict) -> str:
    num = int(idea.get("num") or 0)
    name = idea.get("name") or ""
    url = maps_url(name, town=idea.get("town"), address=idea.get("address"), food_area=idea.get("food_area"))
    meta = [
        ("🚗", _clip_meta(idea.get("drive"))),
        ("🕙", _hours_short(idea)),
        ("", _clip_meta(idea.get("cost"))),
    ]
    meta_html = "".join(f'<span>{(i + " ") if i else ""}{e(t)}</span>' for i, t in meta if t)
    gtk_html = good_to_know_v2(idea)
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
    sg = idea.get("suggested") or {}
    sg_txt = " · ".join(x for x in (sg.get("part"), sg.get("duration") or _clip_meta(idea.get("outing_length"))) if x)
    sugg_html = f'<p class="sugg">Good for: {e(sg_txt)}</p>' if sg_txt else ""
    why_html = f'<p class="why"><b>Details:</b> {e(idea["why"])}</p>' if idea.get("why") else ""
    rain = f'<div class="rain"><b>☔ Rain plan</b> · {e(idea["rain_backup"])}</div>' if idea.get("rain_backup") else ""
    return f"""<article class="cd" id="idea-{num}" data-n="{num}">
<div class="cx" data-n="{num}"><button type="button" class="cx-x" aria-label="Clear {e(name)}">✕</button><span class="cx-q" hidden><button type="button" class="cx-yes" aria-label="Confirm clear {e(name)}">Clear</button><button type="button" class="cx-no" aria-label="Keep {e(name)}">Keep</button></span></div>
<h3><span class="no">{num}</span><a href="{e(url)}" target="_blank" rel="noopener noreferrer">{e(name)}</a></h3>
<div class="town">{e(idea.get("town") or "")}</div>
<p class="hook">{e(idea.get("hook") or "")}</p>
<div class="meta">{meta_html}</div>
{sugg_html}
{why_html}
{rain}
{gtk_html}
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


SOURCES_PATH = Path("/workspace/digests/sources.json")


def sources_v2(path: Path = SOURCES_PATH) -> str:
    """Quiet collapsible 'Where these come from' list, grouped by type; new ones tagged."""
    try:
        reg = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return ""
    srcs = reg.get("sources") or []
    if not srcs:
        return ""
    order = reg.get("types") or []
    types = order + sorted({x.get("type") for x in srcs if x.get("type") not in order})
    rows = []
    for t in types:
        items = sorted((x for x in srcs if x.get("type") == t), key=lambda x: (not x.get("new"), (x.get("name") or "").lower()))
        if not items:
            continue
        links = " · ".join(
            f'<a href="{e(x["url"])}" target="_blank" rel="noopener noreferrer">{e(x.get("name"))}</a>'
            + (' <span class="nw2">New</span>' if x.get("new") else "")
            for x in items
        )
        rows.append(f'<div class="sg"><div class="st2">{e(t[:1].upper() + t[1:])}</div><div>{links}</div></div>')
    n_new = sum(1 for x in srcs if x.get("new"))
    q = f"{len(srcs)} sources" + (f" · {n_new} new" if n_new else "")
    return (
        f'<details class="src" id="sources"><summary>Where these come from<span class="q">{e(q)}</span></summary>'
        f'<div class="dt">{"".join(rows)}</div></details>'
    )


BRAND_V2 = "More Good Days"
BRAND_SHORT_V2 = "Good Days"  # home-screen label (iOS truncates ~12 chars)

# "How we pick" sheet: a few big knobs (saved per phone; Save opens a prefilled text to the Linq line)
HOW_SMS_V2 = "+16282909234"
KNOBS_V2 = [  # (key, label, options, default)
    ("drive", "Drive", ["Close", "Medium", "Farther"], "Close"),
    ("vibe", "Vibe", ["Calm", "Mix", "Adventurous"], "Mix"),
    ("lean", "Indoor / outdoor", ["Indoor", "Mix", "Outdoor"], "Mix"),
]
HOW_EXPLAINER_V2 = (
    "Every pick works for a 4- and a 2-year-old and is timed around the 1–3 PM nap. "
    "Real food is always close by, from family restaurants to breweries with food trucks and room to play. "
    "Verified local events come first, then tried-and-true favorites."
)


def how_sheet_v2() -> str:
    knobs = "".join(
        f'<div class="hk"><div class="kl" id="k-{k}">{e(lbl)}</div>'
        f'<div class="seg" role="radiogroup" aria-labelledby="k-{k}" data-k="{k}">'
        + "".join(
            f'<button type="button" role="radio" data-v="{e(o)}" aria-checked="{"true" if o == d else "false"}"'
            f' tabindex="{0 if o == d else -1}">{e(o)}</button>'
            for o in opts
        )
        + "</div></div>"
        for k, lbl, opts, d in KNOBS_V2
    )
    return (
        f'<div id="how" class="sheet" role="dialog" aria-modal="true" aria-labelledby="how-h" data-sms="{HOW_SMS_V2}" hidden>'
        '<div class="sheet-bg" data-close="1"></div>'
        '<div class="sheet-card"><div class="sheet-top"><h2 id="how-h">How we pick</h2>'
        '<button type="button" class="sheet-x" data-close="1" aria-label="Close How we pick">✕</button></div>'
        f'<p class="hx">{e(HOW_EXPLAINER_V2)}</p>'
        '<a href="#sources" class="hs-src" id="how-src">Where these come from →</a>'
        f'{knobs}'
        '<div class="hk"><label for="how-also">Anything else?</label>'
        '<input id="how-also" type="text" maxlength="140" placeholder="e.g. more train stuff" autocomplete="off" enterkeyhint="done"></div>'
        '<button type="button" class="save" id="how-save">Save</button>'
        '<p class="hsaved" id="how-saved" role="status" aria-live="polite"></p>'
        '</div></div>'
    )


TAGLINE_V2 = "Hand-picked each week: toddler-friendly, short drives, real food nearby."


def render_weekend_html_v2(data: dict, *, prefix: str = "", weekend_date: str = "") -> str:
    meta = data.get("meta") or {}
    title = meta.get("title") or "Weekend Adventures"
    subtitle = meta.get("subtitle") or ""
    ideas = data.get("ideas") or []
    nap = data.get("nap_conflicts")
    nap_html = ""
    if nap:
        items = nap if isinstance(nap, list) else [nap]
        nap_html = '<h2>Nap conflicts</h2><section class="panel"><ul class="lst">' + "".join(f"<li>{e(x)}</li>" for x in items) + "</ul></section>"
    fb = data.get("filler_bank")
    fb_html = ""
    if fb:
        body = e(fb) if isinstance(fb, str) else "<ul class=lst>" + "".join(f"<li>{e(x)}</li>" for x in fb) + "</ul>"
        fb_html = f'<h2>Also worth a look</h2><section class="panel"><div class="dt" style="padding:12px 0">{body}</div></section>'
    m = re.search(r"—\s*(.+)$", title)
    kick = BRAND_V2
    dates = m.group(1).strip() if m else (weekend_date or "")
    page_title = f"{BRAND_V2} · {dates}" if dates else BRAND_V2
    sub_v2 = " · ".join(x for x in (dates, "near Snoqualmie") if x)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#FAF8F4">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="{BRAND_SHORT_V2}">
<meta name="application-name" content="{BRAND_V2}">
<meta name="description" content="{e(BRAND_V2 + " · " + sub_v2 + ". " + TAGLINE_V2)}">
<title>{e(page_title)}</title>
<link rel="manifest" href="{prefix}manifest.webmanifest">
<link rel="apple-touch-icon" href="{prefix}assets/apple-touch-icon.png">
<link rel="icon" type="image/png" sizes="192x192" href="{prefix}assets/icon-192.png">
<style>{CSS_V2}</style>
</head>
<body>
<div class="w">
<header class="top">
<button type="button" class="gear" id="gear" aria-label="How we pick" aria-haspopup="dialog" aria-controls="how"><svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg></button>
<p class="kick">{e(kick)}</p>
<h1>{e(title)}</h1>
<p class="sub">{e(sub_v2)}</p>
<p class="tag">{TAGLINE_V2}</p>
<nav class="nav"><a href="{prefix}./">This weekend</a><a href="{prefix}archive.html">Archive</a></nav>
</header>
{weather_v2(data)}
<h2 id="plans">Plans · <span id="left">{len(ideas)}</span></h2>
{"".join(card_v2(i) for i in ideas)}
<div class="rs"><p class="done" id="alldone" hidden>All cleared.</p><button type="button" id="showc" hidden>Show cleared (<span id="nc">0</span>)</button></div>
{nap_html}
{fb_html}
{sources_v2()}
<footer class="ft">{BRAND_V2} · <a href="{prefix}archive.html">Archive</a>{(" · " + e(weekend_date)) if weekend_date else ""}</footer>
</div>
{how_sheet_v2()}
<div id="toast" class="toast" role="status" aria-live="polite" hidden><span id="tmsg">Cleared</span><button type="button" id="undo" aria-label="Undo clear">Undo</button></div>
<script>window.WEEKEND_DATE={json.dumps(weekend_date)};{JS_V2}</script>
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


def render_archive_html_v2(entries: list[dict]) -> str:
    """v2 (calm) archive list page."""
    items = "".join(
        f'<li><a href="{e(x["href"])}"><b style="color:var(--ink)">{e(x["date"])}</b> · {e(x["title"])}</a></li>'
        for x in entries
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#FAF8F4">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="{BRAND_SHORT_V2}">
<meta name="application-name" content="{BRAND_V2}">
<title>Archive · {BRAND_V2}</title>
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="assets/apple-touch-icon.png">
<link rel="icon" type="image/png" sizes="192x192" href="assets/icon-192.png">
<style>{CSS_V2}</style>
</head>
<body>
<div class="w">
<header class="top">
<p class="kick">{BRAND_V2}</p>
<h1>Archive</h1>
<p class="sub">Past weekends</p>
<p class="tag">{TAGLINE_V2}</p>
<nav class="nav"><a href="./">This weekend</a><a href="archive.html">Archive</a></nav>
</header>
<section class="panel"><ul class="lst">{items or "<li>No weekends yet.</li>"}</ul></section>
<footer class="ft">{BRAND_V2}</footer>
</div>
</body>
</html>"""


def write_manifest(site_dir: Path, design: str = "v2") -> None:
    v2 = design == "v2"
    manifest = {
        "name": BRAND_V2 if v2 else "Weekend Ideas",
        "short_name": BRAND_SHORT_V2 if v2 else "Weekend",
        "description": (BRAND_V2 + " · " + TAGLINE_V2) if v2 else "Family weekend activity digests",
        "start_url": "./",
        "display": "standalone",
        "background_color": "#FAF8F4" if v2 else "#FBF6EE",
        "theme_color": "#FAF8F4" if v2 else "#1B5E4A",
        "icons": [
            {"src": "assets/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "assets/icon-512.png", "sizes": "512x512", "type": "image/png"},
        ],
    }
    (site_dir / "manifest.webmanifest").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def infer_date(data: dict, json_path: Path) -> str:
    m = re.search(r"(20\d{2}-\d{2}-\d{2})", json_path.name)
    if m:
        return m.group(1)
    title = (data.get("meta") or {}).get("title") or ""
    # weak fallback
    return date.today().isoformat()


def build_site(json_path: Path, site_dir: Path, weekend_date: str | None = None, design: str = "v2") -> dict:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    wd = weekend_date or infer_date(data, json_path)
    site_dir.mkdir(parents=True, exist_ok=True)
    (site_dir / "weekends").mkdir(exist_ok=True)
    (site_dir / "assets").mkdir(exist_ok=True)
    (site_dir / "data").mkdir(exist_ok=True)

    # copy JSON into data/
    dest_json = site_dir / "data" / f"{wd}.json"
    dest_json.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if design == "v2":
        index_html = render_weekend_html_v2(data, prefix="", weekend_date=wd)
        archive_page = render_weekend_html_v2(data, prefix="../", weekend_date=wd)
    else:
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
    arch = render_archive_html_v2(entries) if design == "v2" else render_archive_html(entries)
    (site_dir / "archive.html").write_text(arch, encoding="utf-8")
    write_manifest(site_dir, design)

    # ensure icons exist (no-op if already present)
    return {
        "date": wd,
        "index_bytes": len(index_html.encode("utf-8")),
        "ideas": len(data.get("ideas") or []),
        "site_dir": str(site_dir),
        "design": design,
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
    p.add_argument("--design", choices=["v1", "v2"], default="v2", help="v2 = calm design (default); v1 = original autumn design (fallback)")
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
    info = build_site(json_path, site_dir, weekend_date=args.date, design=args.design)
    print(f"Built {info['site_dir']} for {info['date']} ({info['design']}): {info['ideas']} ideas, index {info['index_bytes']} bytes")

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
        tile = 'class="panel wx2"' if args.design == "v2" else 'class="wt"'
        for needle in (tile, "Forecast updated", "Morning", "Afternoon"):
            if needle not in index:
                print(f"MISSING weather tile piece {needle}", file=sys.stderr)
                return 4
        wb_dates = [d.get("date") for d in wb["days"]]
        if info["date"] not in wb_dates:
            print(f"WARNING: weather_blocks covers {wb_dates}, not weekend {info['date']} — rerun weather_blocks.py", file=sys.stderr)
    else:
        print("note: no weather_blocks in JSON; showing legacy weather strip (run weather_blocks.py first)", file=sys.stderr)

    if args.design == "v2":
        for bad in ("Nicer", "About the same", "Why it works"):
            if bad in index:
                print(f"UNEXPECTED {bad}", file=sys.stderr)
                return 5

    if args.publish:
        msg = args.message or f"Publish weekend digest {info['date']}"
        publish(site_dir, msg)
        print("Published.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
