# Geocoding & Elevation APIs — reference

Two small, key-less lookup services on their own paths. Geocoding is the glue
for every other product; elevation is a static terrain lookup.

---

## Geocoding API — `https://geocoding-api.open-meteo.com/v1/search`

Turns a place name into coordinates (+ timezone, country, elevation). This is
how you resolve a user's city/place into the `latitude`/`longitude` every other
Open-Meteo product requires. **Dedicated host** — not `api.open-meteo.com`.

### Endpoints
- `GET /v1/search?name=…` — fuzzy search; returns a `results` array.
- `GET /v1/get?id=…` — look up one place by its numeric GeoNames `id`; returns a
  **single flat object** (no `results` wrapper). This is an ID lookup, not
  coordinate→name reverse geocoding (Open-Meteo has no lat/lon reverse geocoder).

### Search params
| Param | Default | Notes |
|---|---|---|
| `name` | (required) | Search string; ≥ 2 chars for useful results; fuzzy. |
| `count` | 10 | Number of results, **max 100** (over → HTTP 400). |
| `language` | `en` | ISO 639-1 code; localizes `name`/`country`/`admin1..4`. Coordinates are unaffected. |
| `format` | `json` | `json` or `protobuf`. |

### Result fields
`id` (GeoNames), `name`, `latitude`, `longitude`, `elevation` (m),
`feature_code` (e.g. `PPLC` capital, `PPLA` region seat, `PPL` populated place),
`country_code`, `country`, `country_id`, `admin1…admin4` (+ `_id`s),
`timezone` (IANA — pass straight to a weather API's `timezone`), `population`,
`postcodes` (array). **Not every field is always present** — small places omit
`admin2+`, `population`, `postcodes`. Fields arrive out of source order; parse by
key, never position.

### Usage pattern
1. `search?name={place}&count=1` → take `results[0]`.
2. Read `latitude`, `longitude`, and optionally `timezone`/`elevation`/`country`.
3. Call the target product with those coordinates.
For ambiguous names ("Springfield") use `count>1` and disambiguate by
`admin1`/`country`/`population` (results are roughly relevance/population-ordered).

### Defensive gotcha — the `results` key can be ABSENT
A successful but zero-match search (gibberish, or a 1-char `name`) returns
**HTTP 200 with only `{"generationtime_ms":…}` and no `results` field**. Naive
`data["results"]` will `KeyError` — always `data.get("results", [])`. (The
bundled `openmeteo.py` already does this.) Missing `name` entirely → HTTP 400.
The `/get` response is unwrapped — don't read `results[0]` from it.

---

## Elevation API — `https://api.open-meteo.com/v1/elevation`

Terrain elevation (metres above MSL) for one or more coordinates, from the
Copernicus DEM GLO-90 (~90 m resolution). Shares the main `api.open-meteo.com`
host. Pure static lookup — no time/timezone/models/units params.

### Params
`latitude`, `longitude` — a single value or **parallel comma-separated lists of
up to 100** coordinates, zipped index-by-index (equal lengths required).

### Response
`{"elevation":[38.0]}` — one float (metres) per input point, in request order.
Ocean/sea points return ~0.

### Gotchas
Length mismatch or a missing coordinate → HTTP 400 "…must have the same number
of elements". Cap 100 points/call — batch larger sets. Values are 90 m-cell
averages, not survey-grade. (Note the naming overlap: on the Forecast API
`elevation` is an *input* for downscaling; here it's the *output*.)
