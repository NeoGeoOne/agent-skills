# GeoJSON response structure — reference

Both the feeds and `query?format=geojson` return the **same** Feature schema. The
per-event **detail** doc has a different top-level shape (a bare Feature) and adds
`products`.

## Top-level (FeatureCollection — feeds & list queries)
```json
{
  "type": "FeatureCollection",
  "metadata": { "generated": 1783294007000, "url": "...", "title": "...",
                "status": 200, "api": "2.4.0", "count": 18 },
  "features": [ /* Feature objects */ ],
  "bbox": [minLon, minLat, minDepth, maxLon, maxLat, maxDepth]
}
```
- `metadata.generated` — epoch **ms** UTC. `metadata.count` — **feeds only**; the
  query endpoint emits `limit`/`offset` and **no `count`** (use `len(features)`).
- `bbox` — 6 elements, order `[lon, lat, depth]` for both corners; depth in km.

## Each Feature
```json
{ "type": "Feature", "id": "us6000m0xl",
  "properties": { ... },
  "geometry": { "type": "Point", "coordinates": [longitude, latitude, depth_km] } }
```
- `id` — preferred event id (`net`+`code`, e.g. `us6000m0xl`), reusable as `eventid`.
- **`geometry.coordinates` = `[LON, LAT, DEPTH_km]`** — longitude first; third
  value is depth in km (not elevation). Swapping lon/lat is the #1 mistake.

## `properties` — every field
Observed key order: `mag, place, time, updated, tz, url, detail, felt, cdi, mmi,
alert, status, tsunami, sig, net, code, ids, sources, types, nst, dmin, rms, gap,
magType, type, title`.

| Field | Type | Meaning / units |
|---|---|---|
| `mag` | num\|null | Preferred magnitude. **Can be negative or null.** |
| `place` | str\|null | e.g. `"2 km E of Oak Harbor, Washington"`. |
| `time` | int | Origin time, **epoch MILLISECONDS UTC** (÷1000 for Unix seconds). |
| `updated` | int | Last update, epoch ms UTC. |
| `tz` | int\|null | Minutes from UTC. **Deprecated — effectively always null.** |
| `url` | str | HTML event page. |
| `detail` | str | URL to the per-event detail GeoJSON (has `products`). Absent in the detail doc itself. |
| `felt` | int\|null | Count of "Did You Feel It?" reports (often null). |
| `cdi` | num\|null | Max DYFI community intensity (I–XII). Often null. |
| `mmi` | num\|null | Max ShakeMap modeled intensity (I–XII). Often null. |
| `alert` | str\|null | PAGER: `green`/`yellow`/`orange`/`red`. Null for most events. |
| `status` | str | `automatic` (unreviewed, will change) / `reviewed` / `deleted`. |
| `tsunami` | int | `1` = in a tsunami-capable region (a flag, not a confirmation). |
| `sig` | int | Significance (higher = more notable; unbounded — great quakes >1000). |
| `net` | str | Preferred network code (`us`, `ci`, `nc`, `ak`, `uw`, `hv`, …). |
| `code` | str | Event code within the network. |
| `ids` | str | All ids, comma-wrapped: `",us6000m0xl,..."` — split & drop empties. |
| `sources` | str | Contributors, preferred first, comma-wrapped. |
| `types` | str | Product types available, comma-wrapped. |
| `nst` | int\|null | Stations used. |
| `dmin` | num\|null | Distance to nearest station (degrees; ×111.2 = km). |
| `rms` | num\|null | Travel-time residual (s; lower = better). |
| `gap` | num\|null | Azimuthal gap (deg; smaller ≲180 = better location). |
| `magType` | str\|null | Magnitude method (`mww`, `mb`, `ml`, `md`, …). See `concepts.md`. |
| `type` | str | Event type — **not always `"earthquake"`** (quarry blast, explosion, ice quake, …). |
| `title` | str | Ready-made label, e.g. `"M 7.5 - 2024 Noto Peninsula, Japan Earthquake"`. |

### Null-safety
`mag`, `alert`, `felt`, `cdi`, `mmi`, `nst`, `dmin`, `rms`, `gap`, `tz` can all be
`null`. Always null-check before formatting.

## Per-event DETAIL doc (`detail` URL or `query?eventid=&format=geojson`)
A **bare `Feature`** — **no `metadata`, no `features[]`**. Read `doc.properties`
and `doc.geometry` directly (not `doc.features[0]`). Its `properties` has the same
fields **minus `detail`, plus `products`**.

`properties.products` is a map: product-type → array of product instances (multiple
versions/contributors; highest `preferredWeight` is preferred). Common types:
`origin` (authoritative hypocenter+magnitude), `phase-data`, `moment-tensor`,
`focal-mechanism`, `finite-fault`, `shakemap` (modeled shaking grids/images),
`dyfi` (felt reports), `losspager`/`pager` (fatality/economic loss → drives
`alert`), `ground-failure` (landslide/liquefaction), `oaf` (aftershock forecast),
`nearby-cities`, `impact-text`. Each instance has `id, type, code, source,
updateTime` (epoch ms), `status`, `preferredWeight`, `properties` (product-specific
**string** map), and `contents` (downloadable assets: each with `contentType`,
`length`, `url`, `sha256`).

Most display tasks need only the summary `properties` (mag, place, time, coords,
alert, felt, cdi, mmi, sig) — fetch the detail doc only for authoritative origins,
focal mechanisms, ShakeMap/DYFI assets, or PAGER loss estimates.

## Parsing recipe (Python, stdlib)
```python
import json, urllib.request, datetime as dt
d = json.load(urllib.request.urlopen(
    "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"))
for f in d["features"]:
    p = f["properties"]
    lon, lat, depth_km = f["geometry"]["coordinates"]          # LON, LAT, DEPTH
    when = dt.datetime.fromtimestamp(p["time"]/1000, tz=dt.timezone.utc)  # ms->UTC
    print(f"{when:%Y-%m-%d %H:%M} M{p['mag']} {p['place']} @ {depth_km}km "
          f"alert={p['alert']}")
```
JS: `new Date(p.time)` — no ÷1000 (JS Date is ms).
