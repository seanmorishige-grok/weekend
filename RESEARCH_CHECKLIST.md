# Weekly research checklist — More Good Days

Use this every week, for each of the ~10 picks in `weekend-digest-YYYY-MM-DD.json`.
Family: kids 4 & 2, naps 1–3 PM, home base Snoqualmie, WA.

## Per pick (core fields)
- [ ] `name`, `town`, `hook`, `why` (shown as "Details:")
- [ ] `drive`: minutes from Snoqualmie
- [ ] `hours_short`: actual hours for the dates that weekend, short form (e.g. "10–4", "Sat 10–4")
- [ ] `cost`
- [ ] `suggested`: `{ "part": "Morning|Afternoon|Either", "duration": "1–2 hrs" }`, fitting around naps
- [ ] `rain_plan`, if it's an outdoor pick
- [ ] `restaurants` / treats nearby (the "Eat nearby" dropdown)
- [ ] Note which sources you used in `sources.json` (`cited_in`, `last_verified`)

## Good to know (optional `good_to_know` object)
Check each pick's **official page** (venue, park agency, library, or ticket page) for that weekend:

| Field | What goes in it | Examples |
|---|---|---|
| `parking` | Parking & passes | Lot cost and garages; Discover Pass vs. NW Forest Pass; state free days (they don't cover federal land) |
| `bring` | Venue-specific things to bring or leave | Own books to sign, costumes, cash-only, no food on the train, leave pets home |
| `hours_note` | Hours exceptions that aren't obvious | Sat only, last entry, timed or reserved tickets, sells out, activity stops early |
| `link` (+ `link_label`) | Official website or ticket link | Event page, tickets page, park page |

Rules:
- **Verified only. Leave a field `""` rather than guess.** Don't use third-party listings for parking or payment unless they quote the venue.
- **No stroller or restroom info.** The renderer also strips any sentence that mentions those.
- Don't repeat drive, cost, length, or tags (they're already on the card) or the regular hours (`hours_short`).
- If nothing useful is left, leave out `good_to_know` or keep every field empty. The card then shows no dropdown.

```json
"good_to_know": {
  "parking": "Sat Oct 10 is a Discover Pass free day. Sunday needs a Discover Pass ($10/day).",
  "bring": "",
  "hours_note": "Book tickets online. Last entry 3 PM.",
  "link": "https://redbarnfarm.com/",
  "link_label": "Tickets & info"
}
```
