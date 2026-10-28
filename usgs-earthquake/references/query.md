# FDSN Event `query` / `count` service — reference

Base: `https://earthquake.usgs.gov/fdsnws/event/1/query` (service version 2.7.0).
HTTP GET, params in the query string. No key. **All times UTC.** With no time
params the service defaults to roughly the **last 30 days** — "no starttime" does
NOT mean all-time.

## Time
Accept ISO8601: `YYYY-MM-DD`, `YYYY-MM-DDTHH:MM:SS`, optional `Z`. Bare date = UTC midnight.
- `starttime` — events on/after (default: 30 days ago).
- `endtime` — events on/before (default: now).
- `updatedafter` — events *updated* after this time (incremental sync).

## Magnitude / depth
- `minmagnitude`, `maxmagnitude` (decimal; mag can be negative).
- `mindepth`, `maxdepth` (km; range −100 to 1000; defaults −100 / 1000).

## Location — rectangle (mutually exclusive with circle)
`minlatitude`, `maxlatitude` (−90..90), `minlongitude`, `maxlongitude`
(**−360..360**). Antimeridian: let longitude run past ±180 (e.g.
`minlongitude=170&maxlongitude=190` for a Fiji/Tonga box).

## Location — circle (mutually exclusive with rectangle)
Requires `latitude` + `longitude`, plus a radius in **km** (`maxradiuskm`, 0..20001.6)
OR **degrees** (`maxradius`, 0..180) — not both. Optional `minradiuskm` / `minradius`
for a ring. (USGS has no geocoder; resolve place names to lat/lon yourself or via
the bundled client's `--near`.)

## Other filters
| Param | Notes |
|---|---|
| `eventtype` | `earthquake`, `quarry blast`, `explosion`, `ice quake`, `mining explosion`, `nuclear explosion`, `sonic boom`, `landslide`, … Default returns ALL types — filter to `earthquake` for tectonic only. |
| `catalog` / `contributor` | Limit to a named catalog / contributor (list via `/catalogs`, `/contributors`, or `application.json`). |
| `minsig` / `maxsig` | Significance (higher = more notable; "significant" ≈ ≥600). |
| `alertlevel` | PAGER: `green`/`yellow`/`orange`/`red`. Also `minalertlevel`/`maxalertlevel`. |
| `reviewstatus` | `automatic` / `reviewed` / `all` (default all). |
| `mincdi`/`maxcdi`, `minfelt` | DYFI intensity / min felt reports. |
| `minmmi`/`maxmmi` | ShakeMap intensity (0–12). |
| `mingap`/`maxgap` | Azimuthal gap (deg; smaller = better location). |
| `producttype` / `productcode` | e.g. `moment-tensor`, `shakemap`, `losspager`. |
| `eventid` | Return the single event with this id (detail query; enables `includesuperseded`). |

## Output control
| Param | Default | Notes |
|---|---|---|
| `format` | `quakeml` | `geojson`, `csv`, `text`, `kml`, `kmlraw`, `xml`/`quakeml`, `cap`. Set it — the default XML is rarely what you want. |
| `orderby` | `time` | `time` (newest first), `time-asc`, `magnitude` (largest first), `magnitude-asc`. |
| `limit` | server max | 1..**20000**. `limit=20001` → HTTP 400. |
| `offset` | `1` | **1-based** (first record is offset=1). Page with `limit`+`offset` and a stable `orderby`. |
| `nodata` | `204` | HTTP code for a valid-but-empty search. **Format-dependent gotcha** (below). |
| `jsonerror` | `false` | Return errors as a GeoJSON envelope (HTTP 200 with `metadata.status`/`metadata.error`) instead of a plain-text 400. |
| `includeallorigins` / `includeallmagnitudes` | false | Include non-preferred solutions. |
| `includedeleted` | false | Only for `csv`/`geojson` (others → 409). `only` = just deleted. |
| `includesuperseded` | false | Only with `eventid`. |

## The 20,000-event cap (the key limit)
A single result set is capped at **20,000 events**. Exceeding it → **HTTP 400**
with a plain-text body: `NNNNN matching events exceeds search limit of 20000.
Modify the search to match fewer events.` `/count` returns
`{"count":N,"maxAllowed":20000}`.
**Always `/count` first for broad searches**, then narrow or paginate.

## `nodata` is format-dependent (gotcha)
A valid search with **zero** matches:
- `geojson`, `csv`, `text` → **HTTP 200** with an empty document, *regardless of
  `nodata`* (empty FeatureCollection / header-only CSV/text). So don't treat 200
  as "must have results" — check `len(features)`.
- `quakeml`/xml → honors `nodata` (404 with `nodata=404`).
- Unknown `eventid` → **404** (ignores `nodata`).

## Error bodies (verified)
- Oversized: HTTP 400 `... exceeds search limit of 20000 ...`.
- Bad value: HTTP 400 `Bad minmagnitude value "notanumber". Valid values are numeric`.
- Bad format: HTTP 400 listing valid formats.
- With `jsonerror=true` the HTTP status becomes 200 — read `metadata.status`/`metadata.error`.

## Other methods (same base path)
- **`/count`** — same filter params as `/query`, returns just the number
  (`format=geojson` → `{"count":N,"maxAllowed":20000}`; default → plain integer).
- **`/application.json`** — live service config: the enumerated `catalogs`,
  `contributors`, `producttypes`, `eventtypes`, `magnitudetypes`, and parameters.
- **`/catalogs`**, **`/contributors`** — XML lists. **`/version`** → `2.7.0`.
- **`/application.wadl`** — the WADL.

## Output format columns
**CSV header:** `time,latitude,longitude,depth,mag,magType,nst,gap,dmin,rms,net,
id,updated,place,type,horizontalError,depthError,magError,magNst,status,
locationSource,magSource`. (Note CSV order is lat,lon,depth — *opposite* of
GeoJSON's `[lon,lat,depth]`. CSV/text times are ISO strings, not epoch-ms.)
**text** is pipe-delimited: `#EventID|Time|Latitude|Longitude|Depth/km|Author|
Catalog|Contributor|ContributorID|MagType|Magnitude|MagAuthor|EventLocationName|EventType`.
