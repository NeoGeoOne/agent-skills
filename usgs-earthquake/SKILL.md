---
name: usgs-earthquake
description: >-
  Use this skill any time answering requires actual earthquake records rather than
  general knowledge — whether a quake happened, how big, where, when, or how many,
  for any place or time, however casually phrased. Training data isn't current
  enough — look it up, don't answer from memory. Triggers include: wondering if
  shaking felt just now was really a quake nearby; asking if there was a quake
  somewhere recently or overnight, including one from news or social media;
  comparing earthquake counts or frequency between years or regions (induced
  seismicity); looking up magnitude, depth, epicenter, aftershocks, tsunami flags,
  felt/"Did You Feel It?" reports, ShakeMap intensity, or PAGER alerts for a
  specific event; and writing code, scripts, or automations that fetch, filter,
  count, or monitor quakes (polling for M4+ events near coordinates). Pulls live
  from USGS ANSS ComCat/FDSN, no key needed. Not for plate-tectonics explanations,
  retrofit/structural-safety advice, or earthquakes only referenced in movies or
  fiction.
---

# USGS Earthquake API

The USGS Earthquake Hazards Program exposes the ANSS Comprehensive Catalog
(ComCat) through two services on one host (`earthquake.usgs.gov`). **No API key,
no auth header — ever.** Data is public domain; attribute "U.S. Geological
Survey (USGS)". All times are UTC.

## Step 1: pick the right endpoint

| The user wants… | Endpoint |
|---|---|
| The "latest" quakes / a dashboard bucket (no custom filters) | **Real-time feed**: `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/{mag}_{period}.geojson` |
| A custom search (time window, magnitude, area/radius, depth, type, alert) | **FDSN query**: `https://earthquake.usgs.gov/fdsnws/event/1/query` |
| Just the *number* of matching events (size a request before pulling) | **FDSN count**: `https://earthquake.usgs.gov/fdsnws/event/1/count` |
| Everything about one specific event (products, ShakeMap, PAGER…) | **Detail**: `query?eventid={id}&format=geojson` |

**Feeds** are pre-baked, CDN-cached static files refreshed ~once a minute — fast
and free, but you take whatever bucket exists (no filtering). The feed name is
`{mag}_{period}` where `mag ∈ significant | 4.5 | 2.5 | 1.0 | all` and
`period ∈ hour | day | week | month` (e.g. `significant_week.geojson`,
`2.5_day.geojson`, `all_hour.geojson`). Use a feed for "any big quakes lately?";
use the **query** service the moment the user constrains by place, exact time
range, magnitude threshold, or type.

## The bundled client: `scripts/usgs_quake.py`

Every earthquake task repeats the same plumbing — build a query or grab a feed,
then untangle GeoJSON where **time is epoch-milliseconds** and geometry is
**`[longitude, latitude, depth]`**. `scripts/usgs_quake.py` (Python 3 stdlib
only — no `pip`) handles all of it. Prefer it for lookups and data pulls; drop
to raw URLs or your own code when a task needs something it doesn't cover.

```bash
# Latest significant quakes this month, as a table (time already UTC-formatted,
# magType/alert/tsunami decoded)
python scripts/usgs_quake.py feed significant_week

# Custom search: M6+ worldwide for a week, biggest first
python scripts/usgs_quake.py query starttime=2024-01-01 endtime=2024-01-08 \
    minmagnitude=6 orderby=magnitude --table

# Near a place (auto-geocodes the name to lat/lon) within 100 km, M3+
python scripts/usgs_quake.py query --near "Los Angeles" maxradiuskm=100 \
    minmagnitude=3 starttime=2024-01-01 --table

# Size a big pull FIRST, then export CSV (the query cap is 20,000 events)
python scripts/usgs_quake.py query minmagnitude=4.5 minlatitude=32 maxlatitude=42 \
    minlongitude=-125 maxlongitude=-114 starttime=2023-01-01 endtime=2024-01-01 --count
python scripts/usgs_quake.py query ...same filters... --csv --out ca_quakes.csv

# Everything about one event (magnitude, alert, tsunami flag, products)
python scripts/usgs_quake.py event us6000m0xl
```

`query` takes any FDSN `key=value` params (see `references/query.md`). Flags:
`--near "<place>"` (geocode → inject latitude/longitude; pair with
`maxradiuskm=`), `--count`, `--table`, `--csv`, `--out FILE`, `--print-url`.

## The core workflow

1. **Feed or query?** Use the table above. "Latest / biggest recently" → a feed.
   Any user-specified filter → `query`.
2. **Resolve location if needed.** USGS has no geocoder. For "near `<place>`",
   resolve the place to lat/lon (the client's `--near` does this via a free
   keyless geocoder), then use a **circle** search: `latitude`, `longitude`, and
   `maxradiuskm` (km) or `maxradius` (degrees). For a region, use a **rectangle**
   (`minlatitude/maxlatitude/minlongitude/maxlongitude`).
3. **Count before you pull.** The query service returns **at most 20,000 events**
   per request — over that is an HTTP 400, not a truncated list. For any broad
   search (long span, low magnitude, large area), hit `/count` first; if it's
   over 20,000, narrow (shorter window, higher `minmagnitude`, smaller area) or
   paginate with `limit` (≤20000) + `offset` (**1-based**) and a stable
   `orderby`.
4. **Choose a format.** `geojson` for programmatic use, `csv` for
   spreadsheets/data pulls, `text` (pipe-delimited) for quick tables. Default
   (no `format`) is QuakeML XML — usually not what you want, so set it.
5. **Parse carefully, then present.** Mind the GeoJSON gotchas below. Show a
   clean summary (place, magnitude + type, time UTC, depth, and alert/tsunami
   when set) — not raw JSON.

## GeoJSON parsing — the gotchas that bite everyone

- **`time` and `updated` are epoch MILLISECONDS in UTC**, not seconds and not
  ISO strings (e.g. `1704092409000`). Python: `datetime.fromtimestamp(ms/1000,
  tz=timezone.utc)`. JS: `new Date(ms)` works directly. (CSV/text output uses ISO
  strings instead — only GeoJSON uses ms.)
- **`geometry.coordinates` is `[longitude, latitude, depth_km]`** — longitude
  first, and the third value is **depth in km**, not elevation. Swapping lon/lat
  is the #1 mistake and puts events in the wrong hemisphere.
- **Many fields are `null`:** `mag` can be negative or null; `alert`, `felt`,
  `cdi`, `mmi` are null unless the event was felt/modeled; `tz` is effectively
  always null. Null-check before formatting.
- **`type` isn't always `"earthquake"`** — quarry blasts, explosions, ice quakes,
  etc. appear. Filter with `eventtype=earthquake` if the user wants only quakes.
- **`ids`/`sources`/`types` have leading and trailing commas** (e.g.
  `",us6000m0xl,"`) — split and drop empties.
- **Feeds vs query metadata differ:** feeds give `metadata.count`; the query
  endpoint gives `metadata.limit`/`offset` and **no `count`** — use
  `len(features)`. The per-event **detail** doc is a bare `Feature` (no
  `metadata`, no `features[]`) — read `doc.properties` directly, not
  `doc.features[0]`.

## Interpreting results

- **Magnitude type (`magType`) matters.** USGS reports one *preferred* magnitude.
  `Mww`/`Mw*` (moment) is authoritative for large events; `mb` and `Ms` *saturate*
  and under-report great quakes; `ml`/`md` are for small local events. When
  comparing magnitudes across events, note the type, not just the number.
- **`alert`** (PAGER impact): `green` (no significant impact) < `yellow` (1–99
  deaths / $1M–$100M) < `orange` (100–999 / $100M–$1B) < `red` (1,000+ / $1B+).
  Null for most events.
- **`mmi`** = max modeled shaking (ShakeMap, Modified Mercalli I–XII).
  **`cdi`** = max crowd-sourced "Did You Feel It?" intensity. **`felt`** = number
  of felt reports. All null unless the event was significant/felt.
- **`sig`** (significance, higher = more notable) drives the "significant" feed
  (~≥600). It's an unbounded ranking score — great quakes exceed 1000. Filter
  with `minsig=`.
- **`tsunami: 1`** is a *flag* that the event is in a tsunami-capable region — not
  a confirmation a tsunami occurred.
- **`status`**: `automatic` (machine, unreviewed — will change) vs `reviewed`
  (analyst-checked). Recent quakes are often `automatic`.

See `references/concepts.md` for the full magnitude-type table, PAGER details,
significance formula, catalogs/networks, and attribution.

## Reference files

- `references/query.md` — the FDSN `query`/`count` service: every parameter
  (time, magnitude, depth, rectangle, circle, filters, output control), the other
  methods (`application.json`, `catalogs`, `contributors`, `version`), and all
  output formats with the exact CSV/text columns.
- `references/feeds.md` — the real-time summary feed matrix, cadence, and when to
  use feeds vs the query service.
- `references/geojson.md` — the full GeoJSON response structure, every `properties`
  field with units, and the per-event detail doc + `products`.
- `references/concepts.md` — magnitude types, PAGER alert, ShakeMap MMI / DYFI,
  significance, event types, catalogs & networks, and data terms/attribution.

## Red flags — stop and reconsider if you catch yourself…

- …treating `time` as seconds or an ISO string (it's epoch **ms** in GeoJSON), or
  reading coordinates as `[lat, lon]` (they're `[lon, lat, depth]`).
- …pulling a broad multi-year / low-magnitude / global search without a `/count`
  check first — you'll hit the 20,000-event 400.
- …assuming an empty result is an error. A valid search with zero matches returns
  **HTTP 200** with an empty `FeatureCollection` (the `nodata` code is honored
  only for QuakeML, not geojson/csv/text).
- …using a feed when the user gave a specific place, time range, or magnitude —
  that needs the `query` endpoint.
- …reporting a magnitude without its `magType`, or assuming every event `type` is
  an earthquake.
- …sending an API key or Authorization header. There is none; don't.

## Verification

Before calling a result done: confirm you used the right endpoint (feed vs query),
that a broad pull was `/count`-checked against the 20,000 cap, that times were
converted from epoch-ms to UTC and coordinates read as `[lon, lat, depth]`, and
that magnitudes are shown with their type and any `alert`/`tsunami` flags noted.
