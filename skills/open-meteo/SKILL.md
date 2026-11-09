---
name: open-meteo
description: >-
  Full access to the Open-Meteo weather API family — current conditions and
  forecasts, historical/archive weather, air quality (AQI/pollen), marine and
  ocean waves, CMIP6 climate projections, river-flood discharge, ensemble
  (probabilistic) models, place-name geocoding, and terrain elevation. No API
  key is required. Use this whenever the user asks about weather, temperature,
  rain, snow, wind, humidity, a forecast for anywhere, past/historical weather,
  air quality, AQI, pollen, UV index, wave/swell/surf/sailing conditions,
  sea-surface temperature, climate trends or projections, flooding or river
  levels, forecast uncertainty/ensembles, or needs to convert a city or place
  name into latitude/longitude — even if they never say "Open-Meteo." Also use
  when writing code or scripts that fetch weather data.
---

# Open-Meteo

Open-Meteo is a free, open weather API. The non-commercial tier needs **no API
key** — you can call it directly. This skill gives you correct, verified access
to *every* Open-Meteo product, a bundled zero-dependency client that removes the
repetitive plumbing, and reference files with the exhaustive variable lists.

Attribution: Open-Meteo data is CC-BY 4.0. When you present data in a shipped
artifact, credit "Weather data by Open-Meteo.com".

## The one thing to get right: pick the correct product host

Each Open-Meteo product lives on its **own hostname**. Using the wrong host is
the most common mistake — `api.open-meteo.com` does *not* serve air quality,
marine, archive, climate, flood, or ensemble data. Route the request first:

| The user wants… | Alias | Base URL |
|---|---|---|
| Current conditions / forecast (up to 16 days ahead, up to 92 days back) | `forecast` | `https://api.open-meteo.com/v1/forecast` |
| Past weather, long consistent record (1940 → ~yesterday, ERA5 reanalysis) | `archive` | `https://archive-api.open-meteo.com/v1/archive` |
| Recent past at high resolution (2021 → ~2 days ago; forecast backtesting) | `historical-forecast` | `https://historical-forecast-api.open-meteo.com/v1/forecast` |
| Air quality, AQI, pollen, atmospheric UV | `air-quality` | `https://air-quality-api.open-meteo.com/v1/air-quality` |
| Ocean waves, swell, currents, sea-surface temperature | `marine` | `https://marine-api.open-meteo.com/v1/marine` |
| Multi-decade climate projections (1950–2050, daily, CMIP6) | `climate` | `https://climate-api.open-meteo.com/v1/climate` |
| River discharge / flood risk (GloFAS) | `flood` | `https://flood-api.open-meteo.com/v1/flood` |
| Probabilistic ensemble members / forecast spread | `ensemble` | `https://ensemble-api.open-meteo.com/v1/ensemble` |
| Place name → coordinates (+ timezone, country, elevation) | `geocoding` | `https://geocoding-api.open-meteo.com/v1/search` |
| Terrain elevation for coordinate(s) | `elevation` | `https://api.open-meteo.com/v1/elevation` |

Choosing between the two "past weather" hosts: use **`archive`** (ERA5) for
anything needing a long, homogeneous record — climatology, decade-over-decade
comparisons, any date before 2021. Use **`historical-forecast`** for the last
few years at high spatial resolution or to check "what did the forecast actually
say." When unsure for a plain "what was the weather in <month> <year>" question,
`archive` is the safe default.

## The bundled client: `scripts/openmeteo.py`

Nearly every task repeats the same steps — geocode a place, build a query
string on the right host, handle the `{"error":true,"reason":...}` body, and
line up parallel arrays into a table. `scripts/openmeteo.py` (Python 3 standard
library only — no `pip install`) does all of that. Prefer it for quick lookups
and data pulls; drop to raw URLs or your own code when a task needs something it
doesn't cover (custom parsing, an app, a non-JSON format).

```bash
# 1. Resolve a place to coordinates (prints matches + the top pick)
python scripts/openmeteo.py geocode "Tokyo"

# 2. Any endpoint by alias, with key=value params. --place geocodes for you.
#    --table renders hourly/daily/current blocks; --decode adds weather text.
python scripts/openmeteo.py fetch forecast --place "Tokyo" \
    daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max \
    timezone=auto forecast_days=7 --table --decode

# 3. Explicit coordinates, another product, raw JSON out
python scripts/openmeteo.py fetch air-quality latitude=28.61 longitude=77.21 \
    current=pm2_5,us_aqi timezone=auto

# 4. Historical archive with a date range, as CSV
python scripts/openmeteo.py fetch archive latitude=33.45 longitude=-112.07 \
    start_date=2023-07-01 end_date=2023-07-31 daily=temperature_2m_max \
    timezone=auto --csv

# Handy: print the WMO weather-code table, or just preview the URL
python scripts/openmeteo.py codes
python scripts/openmeteo.py fetch marine --place "San Diego" \
    hourly=wave_height,swell_wave_height --print-url
```

`fetch` accepts every alias in the routing table above, or a full `https://…`
URL. Flags: `--place NAME` (geocode → inject lat/lon), `--table`, `--csv`,
`--decode` (weather_code → text), `--print-url`, `--host customer` (paid tier,
pair with `apikey=…`). Run `python scripts/openmeteo.py fetch -h` for the rest.

## The core workflow

1. **Resolve location.** If the user gives a place name, geocode it
   (`openmeteo.py geocode "…"` or the `--place` flag). Take `results[0]`, or use
   `count>1` and disambiguate by `admin1`/`country`/`population` for ambiguous
   names like "Springfield." If they give coordinates, skip this. Geocoding also
   returns `timezone`, `elevation`, and `country` you may want to reuse.
2. **Pick the product** from the routing table.
3. **Build the request.** `latitude` + `longitude` are always required (except
   geocoding, which takes `name`). Then request at least one data block —
   `current=`, `hourly=`, `daily=`, or `minutely_15=` — as a comma-separated
   variable list. A request with no data block returns only metadata. Consult
   the reference file for the exhaustive, verified variable list per product.
4. **Set `timezone=auto`** whenever you use `daily=` (or care about local
   clock time). The default is GMT/UTC, which buckets daily min/max/sums and
   sunrise/sunset on UTC midnight — wrong for the user's local day. `auto`
   resolves the zone from the coordinates.
5. **Parse and present.** Read units from the paired `*_units` object rather
   than assuming. `hourly`/`daily` are **columnar**: a `time` array plus one
   parallel array per variable — zip `time[i]` with `variable[i]`. Decode
   `weather_code` via the WMO table below. Present a clean summary, not raw JSON.

## Conventions that apply to every product

- **No key needed.** Just call the host. For a commercial key, switch to the
  `customer-<product>-api.open-meteo.com` host and add `&apikey=YOUR_KEY`
  (`openmeteo.py`: `--host customer`). Never put a key in client-side code.
- **Multiple locations in one call:** pass comma-separated `latitude` and
  `longitude` lists (equal length). The response then becomes a JSON **array**,
  one object per location — the top-level shape switches from object to array.
- **Relative windows beat manual dates for "recent + upcoming":** use
  `forecast_days` (forecast: max 16) and `past_days` (max 92) instead of
  computing `start_date`/`end_date`. Use explicit `start_date`/`end_date`
  (`YYYY-MM-DD`) for fixed historical ranges and the archive/climate/flood APIs.
- **Units** are switchable: `temperature_unit=celsius|fahrenheit`,
  `wind_speed_unit=kmh|ms|mph|kn`, `precipitation_unit=mm|inch`. Match the
  user's locale (e.g. Fahrenheit/mph for a US city).
- **Response formats:** default JSON; also `&format=csv`, `&format=xlsx`, and
  `&format=flatbuffers` (binary, used by the SDK).
- **Grid snapping is normal:** the returned `latitude`/`longitude` differ
  slightly from the request (e.g. `13.41 → 13.419998`) because the point snaps
  to the model grid. Not an error.

## Error handling (read this — one case is non-obvious)

Errors use `{"error": true, "reason": "..."}`. Key order is **not** stable
(`reason` may come first) — check by the `error` key, never by position.

- Bad parameters / dates / variables → **HTTP 400** with that body.
- **Rate limiting sometimes returns HTTP 200 with the error body**, not a 429
  status. On the free tier (~600/min, ~5,000/hour, ~10,000/day) a burst can
  yield `{"error":true,"reason":"Minutely API request limit exceeded..."}` in a
  200 response. So: **always test for the `error` field before parsing data**,
  regardless of status code. Space out bursts; a batch of coordinates in one
  call is cheaper than many separate calls. `openmeteo.py` already surfaces both
  the 400 and the 200-body error forms as a clear message.
- A malformed request (400) should not be retried — fix it. A rate-limit error
  should be retried after a short backoff.

## WMO weather interpretation codes (`weather_code`)

`weather_code` is a WMO code; map it to text when presenting. (`openmeteo.py
--decode` and `codes` do this for you.)

| Code | Meaning | Code | Meaning | Code | Meaning |
|---|---|---|---|---|---|
| 0 | Clear sky | 51 | Light drizzle | 71 | Slight snow |
| 1 | Mainly clear | 53 | Moderate drizzle | 73 | Moderate snow |
| 2 | Partly cloudy | 55 | Dense drizzle | 75 | Heavy snow |
| 3 | Overcast | 56 | Light freezing drizzle | 77 | Snow grains |
| 45 | Fog | 57 | Dense freezing drizzle | 80 | Slight rain showers |
| 48 | Rime fog | 61 | Slight rain | 81 | Moderate rain showers |
| 66 | Light freezing rain | 63 | Moderate rain | 82 | Violent rain showers |
| 67 | Heavy freezing rain | 65 | Heavy rain | 85 | Slight snow showers |
| 95 | Thunderstorm | 96 | Thunderstorm + slight hail | 86 | Heavy snow showers |
| 99 | Thunderstorm + heavy hail | | | | |

## Reference files — exhaustive, verified variable catalogs

Read the relevant one when you need the full variable list, model IDs, date
ranges, or product-specific gotchas. Each was verified against the live API.

- `references/forecast.md` — Weather Forecast API: full `current`/`hourly`/
  `daily`/`minutely_15` variables, pressure levels, solar/tilt, models, cells.
- `references/historical.md` — Archive (ERA5) **and** Historical-Forecast APIs:
  variables, model lists, date ranges, and how to choose between them.
- `references/air-quality.md` — pollutants, pollen (Europe-only), European vs
  US AQI families, `domains`, the 7-day cap.
- `references/marine.md` — waves, swell partitions, currents, SST; the
  oceans-only coverage caveat and per-model variable availability.
- `references/climate-flood-ensemble.md` — Climate (CMIP6), Flood (GloFAS river
  discharge), and Ensemble (probabilistic members) — the three specialized
  products, including the single-vs-multi-model column-naming rules.
- `references/geocoding-elevation.md` — geocoding search/get-by-id fields and
  the elevation lookup, with the missing-`results`-key defensive pattern.

## Red flags — stop and reconsider if you catch yourself…

- …sending an air-quality, marine, archive, climate, flood, or ensemble request
  to `api.open-meteo.com`. Each has its own host (routing table).
- …requesting `daily=` without `timezone=auto` — daily stats will be bucketed
  on UTC, misaligning the user's local day.
- …trusting HTTP 200 alone. Check the `error` field first (rate limits hide in
  200 bodies).
- …reaching for `current=` on the archive/climate/flood APIs — they have no
  `current` block. For "right now," use `forecast` with `current=`.
- …looping N single-coordinate calls when one comma-separated batch would do.
- …inventing a variable name. If a name 400s ("Cannot initialize … from invalid
  String value"), it's wrong — check the reference file for the exact spelling.
- …hand-writing WMO code descriptions from memory. Use the table above.

## Verification

Before calling a result done: confirm you hit the **right host** for the
product; confirm the response has no `error` field; confirm you read values from
the matching `*_units`; and confirm any place name resolved to the location the
user meant (right country/region), not a same-named place elsewhere. For daily
data, confirm `timezone` was set so the days are local.
