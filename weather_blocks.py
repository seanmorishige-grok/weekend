#!/usr/bin/env python3
"""Fetch Sat/Sun Morning (9 AM–12 PM) and Afternoon (3–7 PM) weather blocks
for Snoqualmie, WA and (optionally) embed them in the weekly digest JSON.

Typical weekly use (before render_site.py):
  python3 weather_blocks.py --json weekend-digest-YYYY-MM-DD-vN.json
  -> writes/overwrites the "weather_blocks" key in that JSON (date inferred
     from the filename, else the coming Saturday).

Other options:
  --weekend YYYY-MM-DD   Saturday of the weekend (overrides inference)
  --out FILE             also write the weather_blocks JSON to FILE
  --source auto|open-meteo|nws   (auto = Open-Meteo, NWS fallback)
  (no --json/--out)      print the weather_blocks JSON to stdout

Sources: Open-Meteo (no key) hourly temperature_2m, precipitation_probability,
precipitation, weathercode, windspeed_10m; NWS api.weather.gov forecastHourly
as a fallback. All times America/Los_Angeles.

Hour handling: temperature & wind are instantaneous on the hour, so a block
uses the samples at its start..end hours inclusive (9,10,11,12 / 15..19).
Rain chance, precipitation and weather code describe the *preceding* hour, so
a block uses the hours ending inside it (10,11,12 / 16..19).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

TZ_NAME = "America/Los_Angeles"
TZ = ZoneInfo(TZ_NAME)
LAT, LON = 47.53, -121.87
LOCATION = "Snoqualmie, WA 98065"
UA = "weekend-digest-weather/1.0 (github.com/seanmorishige-grok/weekend)"

BLOCKS = [
    {"key": "morning", "label": "Morning", "window": "9 AM–12 PM", "start": 9, "end": 12},
    {"key": "afternoon", "label": "Afternoon", "window": "3–7 PM", "start": 15, "end": 19},
]

# "Nicer" thresholds: rain first, then warmth, then wind, then sunnier sky.
RAIN_DIFF = 15     # percentage points of max rain chance
PRECIP_DIFF = 1.0  # mm total precip (when rain chances are similar)
TEMP_DIFF = 3.0    # °F of block average temperature
WIND_DIFF = 5.0    # mph of block max wind
SKY_DIFF = 1.0     # cloud score (0 clear … 3 overcast), final tiebreak


# ---------------------------------------------------------------- fetching
def _get_json(url: str, timeout: int = 25) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_open_meteo(sat: date, sun: date) -> dict[str, dict]:
    q = {
        "latitude": LAT,
        "longitude": LON,
        "hourly": "temperature_2m,precipitation_probability,precipitation,weathercode,windspeed_10m",
        "temperature_unit": "fahrenheit",
        "windspeed_unit": "mph",
        "precipitation_unit": "mm",
        "timezone": TZ_NAME,
        "start_date": sat.isoformat(),
        "end_date": sun.isoformat(),
    }
    d = _get_json("https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(q))
    h = d["hourly"]
    out: dict[str, dict] = {}
    for i, t in enumerate(h["time"]):
        out[t[:13]] = {  # key "YYYY-MM-DDTHH"
            "temp": h["temperature_2m"][i],
            "pop": h["precipitation_probability"][i],
            "precip": h["precipitation"][i],
            "code": h["weathercode"][i],
            "wind": h["windspeed_10m"][i],
        }
    return out


def _nws_code(short: str) -> int:
    """Map an NWS shortForecast to an approximate WMO weather code."""
    s = (short or "").lower()
    if "thunder" in s:
        return 95
    if "snow" in s or "sleet" in s or "flurr" in s:
        return 73
    if "shower" in s:
        return 80
    if "drizzle" in s:
        return 53
    if "rain" in s:
        return 63 if not re.search(r"chance|slight", s) else 80
    if "fog" in s or "haze" in s or "smoke" in s:
        return 45
    if "mostly cloudy" in s or "overcast" in s or s.strip() == "cloudy":
        return 3
    if "partly" in s or "mostly sunny" in s or "mostly clear" in s:
        return 2
    if "sunny" in s or "clear" in s:
        return 0
    return 3


def fetch_nws(sat: date, sun: date) -> dict[str, dict]:
    pts = _get_json(f"https://api.weather.gov/points/{LAT},{LON}")
    hourly = _get_json(pts["properties"]["forecastHourly"])
    out: dict[str, dict] = {}
    for p in hourly["properties"]["periods"]:
        start = datetime.fromisoformat(p["startTime"]).astimezone(TZ)
        if start.date() not in (sat, sun):
            continue
        temp = p.get("temperature")
        if p.get("temperatureUnit") == "C" and temp is not None:
            temp = temp * 9 / 5 + 32
        wind = 0.0
        nums = re.findall(r"\d+", p.get("windSpeed") or "")
        if nums:
            wind = float(max(int(n) for n in nums))
        pop = (p.get("probabilityOfPrecipitation") or {}).get("value") or 0
        # NWS periods describe the hour *starting* at startTime; re-key them by
        # the hour they end at so they line up with Open-Meteo's convention for
        # pop/precip/code. Temperature/wind stay on the start hour.
        k_start = start.strftime("%Y-%m-%dT%H")
        k_end = (start + timedelta(hours=1)).strftime("%Y-%m-%dT%H")
        out.setdefault(k_start, {})
        out[k_start].update({"temp": temp, "wind": wind})
        out.setdefault(k_end, {})
        out[k_end].update({"pop": pop, "precip": None, "code": _nws_code(p.get("shortForecast"))})
    return out


# ---------------------------------------------------------------- summarizing
def cloud_score(codes: list[int]) -> float:
    """0 = clear … 3 = overcast/fog/precip, averaged over the block."""
    sky = [c for c in codes if c is not None]
    if not sky:
        return 3.0
    return round(sum(min(c, 3) if c < 45 else 3 for c in sky) / len(sky), 2)


def condition(codes: list[int], max_pop: float, precip_mm: float) -> tuple[str, str]:
    sky = [c for c in codes if c is not None]
    n = max(len(sky), 1)
    wet = [c for c in sky if c >= 51]
    snowy = [c for c in wet if 71 <= c <= 77 or c in (85, 86)]
    if snowy and len(snowy) * 2 >= n:
        return "🌧️", "Wintry mix"
    if any(c >= 95 for c in wet):
        return "🌧️", "Stormy"
    if max_pop >= 60 and (precip_mm >= 1.0 or len(wet) * 2 >= n):
        return "🌧️", "Rainy"
    # one stray drizzle hour at a low rain chance doesn't make it "Showers"
    if max_pop >= 30 or precip_mm >= 0.5 or (wet and len(wet) * 2 >= n):
        return "🌦️", "Showers"
    fog = [c for c in sky if c in (45, 48)]
    if fog and len(fog) * 2 >= n:
        return "☁️", "Foggy"
    score = cloud_score(sky)
    if score < 0.75:
        return "☀️", "Sunny"
    if score < 1.5:
        return "⛅", "Mostly sunny"
    if score < 2.4:
        return "⛅", "Partly cloudy"
    return "☁️", "Cloudy"


def summarize_block(hours: dict[str, dict], day: date, blk: dict) -> dict:
    ds = day.isoformat()
    inst = [hours.get(f"{ds}T{h:02d}") or {} for h in range(blk["start"], blk["end"] + 1)]
    prev = [hours.get(f"{ds}T{h:02d}") or {} for h in range(blk["start"] + 1, blk["end"] + 1)]
    temps = [x["temp"] for x in inst if x.get("temp") is not None]
    winds = [x["wind"] for x in inst if x.get("wind") is not None]
    pops = [x["pop"] for x in prev if x.get("pop") is not None]
    precs = [x["precip"] for x in prev if x.get("precip") is not None]
    codes = [x["code"] for x in prev if x.get("code") is not None]
    if not temps:
        raise ValueError(f"no forecast hours for {ds} {blk['label']}")
    lo, hi = round(min(temps)), round(max(temps))
    max_pop = int(round(max(pops))) if pops else 0
    precip_mm = round(sum(precs), 2) if precs else None
    emoji, cond = condition(codes, max_pop, precip_mm or 0.0)
    return {
        "key": blk["key"],
        "label": blk["label"],
        "window": blk["window"],
        "emoji": emoji,
        "condition": cond,
        "temp_low": lo,
        "temp_high": hi,
        "temp_range": f"{lo}°F" if lo == hi else f"{lo}–{hi}°F",
        "temp_avg": round(sum(temps) / len(temps), 1),
        "rain_pct": max_pop,
        "precip_in": round(precip_mm / 25.4, 2) if precip_mm is not None else None,
        "wind_max_mph": round(max(winds)) if winds else None,
        "cloud_score": cloud_score(codes),
        "nicer": False,
    }


def pick_nicer(am: dict, pm: dict) -> tuple[str, str]:
    """Return ("morning"|"afternoon"|"same", reason)."""
    dp = am["rain_pct"] - pm["rain_pct"]
    if abs(dp) >= RAIN_DIFF:
        return ("afternoon" if dp > 0 else "morning"), "lower rain chance"
    a_in, p_in = am.get("precip_in") or 0, pm.get("precip_in") or 0
    if abs(a_in - p_in) * 25.4 >= PRECIP_DIFF:
        return ("afternoon" if a_in > p_in else "morning"), "less rain expected"
    dt = pm["temp_avg"] - am["temp_avg"]
    dw = (pm.get("wind_max_mph") or 0) - (am.get("wind_max_mph") or 0)
    if abs(dt) >= TEMP_DIFF:
        warmer = "afternoon" if dt > 0 else "morning"
        # a warmer block that's also much windier isn't clearly nicer
        windier_by = dw if warmer == "afternoon" else -dw
        if windier_by < WIND_DIFF:
            return warmer, "warmer"
    if abs(dw) >= WIND_DIFF:
        return ("morning" if dw > 0 else "afternoon"), "less wind"
    # last tiebreak: clearly sunnier sky
    dc = am.get("cloud_score", 0) - pm.get("cloud_score", 0)
    if abs(dc) >= SKY_DIFF:
        return ("afternoon" if dc > 0 else "morning"), "sunnier"
    return "same", "about the same"


def coming_saturday(today: date) -> date:
    # Saturday today -> today; otherwise the next Saturday.
    return today + timedelta(days=(5 - today.weekday()) % 7)


def build(sat: date, source: str = "auto") -> dict:
    sun = sat + timedelta(days=1)
    hours, used, errs = None, None, []
    order = ["open-meteo", "nws"] if source == "auto" else [source]
    for src in order:
        try:
            hours = fetch_open_meteo(sat, sun) if src == "open-meteo" else fetch_nws(sat, sun)
            used = src
            break
        except Exception as ex:  # noqa: BLE001
            errs.append(f"{src}: {ex}")
    if hours is None:
        raise SystemExit("Weather fetch failed: " + "; ".join(errs))

    now = datetime.now(TZ)
    days = []
    for d in (sat, sun):
        blocks = [summarize_block(hours, d, b) for b in BLOCKS]
        nicer, why = pick_nicer(blocks[0], blocks[1])
        for b in blocks:
            b["nicer"] = b["key"] == nicer
        days.append({
            "date": d.isoformat(),
            "day": d.strftime("%A"),
            "short": d.strftime("%a"),
            "nicer": nicer,
            "nicer_reason": why,
            "blocks": blocks,
        })
    return {
        "location": LOCATION,
        "lat": LAT,
        "lon": LON,
        "timezone": TZ_NAME,
        "source": "Open-Meteo" if used == "open-meteo" else "NWS (api.weather.gov)",
        "weekend": sat.isoformat(),
        "updated": now.isoformat(timespec="minutes"),
        "updated_label": now.strftime("%a %b %-d, %-I:%M %p").replace(":00 ", " ") + " PT",
        "windows": {b["key"]: b["window"] for b in BLOCKS},
        "days": days,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--json", help="weekly digest JSON to update in place (adds 'weather_blocks')")
    p.add_argument("--weekend", help="Saturday date YYYY-MM-DD")
    p.add_argument("--out", help="also write weather_blocks JSON here")
    p.add_argument("--source", default="auto", choices=["auto", "open-meteo", "nws"])
    a = p.parse_args(argv)

    if a.weekend:
        sat = date.fromisoformat(a.weekend)
    elif a.json and re.search(r"20\d{2}-\d{2}-\d{2}", Path(a.json).name):
        sat = date.fromisoformat(re.search(r"20\d{2}-\d{2}-\d{2}", Path(a.json).name).group(0))
    else:
        sat = coming_saturday(datetime.now(TZ).date())
    if sat.weekday() != 5:
        print(f"note: {sat} is a {sat:%A}; using it as day 1 anyway", file=sys.stderr)

    wb = build(sat, a.source)
    txt = json.dumps(wb, indent=2, ensure_ascii=False)
    if a.out:
        Path(a.out).write_text(txt + "\n", encoding="utf-8")
    if a.json:
        jp = Path(a.json)
        data = json.loads(jp.read_text(encoding="utf-8"))
        data["weather_blocks"] = wb
        jp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if not a.json and not a.out:
        print(txt)
    # human summary on stderr
    print(f"{wb['source']} · updated {wb['updated_label']}", file=sys.stderr)
    for d in wb["days"]:
        for b in d["blocks"]:
            star = "  ← nicer" if b["nicer"] else ""
            print(f"{d['short']} {b['label']:<9} {b['emoji']} {b['condition']:<13} {b['temp_range']:>9}  rain {b['rain_pct']:>3}%  wind {b['wind_max_mph']} mph{star}", file=sys.stderr)
        if d["nicer"] == "same":
            print(f"{d['short']}: about the same", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
