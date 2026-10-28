# NOAA SWPC data services — reference (verified catalog)

Base: `https://services.swpc.noaa.gov` — static files behind a CDN, **no key, no
query params** (you select by path). `cache-control: max-age=60` → polling
faster than 60 s is pointless; use `If-Modified-Since`/`If-None-Match`. CORS `*`
(browser-fetchable). Bad path → 404 **HTML** — never blind-JSON-parse. All
timestamps UTC (with or without `Z` suffix; alerts use `"2026-07-06 11:50:00.833"`).

## Format rule: SNIFF, don't assume
Two shapes coexist and have shifted over time: **array-of-objects** (most root
`/products/*.json` and `/json/*.json` today) and **array-of-arrays with a header
row** (survives in `/products/geospace/*`). Check whether `data[0]` is a dict or
a list. `noaa-scales.json` is a keyed **object**, not an array.
**Removed (404) trap:** the whole legacy `/products/solar-wind/` directory
(plasma-7-day.json, mag-2-hour.json, …) is gone; old tutorials still cite it.

## Kp index
| URL | What |
|---|---|
| `/products/noaa-planetary-k-index.json` | 3-hour Kp, ~7.5 days. Objects: `time_tag, Kp` (float thirds e.g. 3.67), `a_running`, `station_count` |
| `/json/planetary_k_index_1m.json` | 1-min **estimated** Kp, ~6 h window. `kp_index` (int), `estimated_kp` (float), `kp` (string thirds: `"2M"`=1.67, `Z`=exact, `P`=+⅓) |
| `/products/noaa-planetary-k-index-forecast.json` | 3-hour slots, past + **forecast to +3 days**. `time_tag, kp, observed` ∈ observed/estimated/predicted, `noaa_scale` (`"G1"` or null) |

## NOAA scales now + forecast — `/products/noaa-scales.json`
Keyed object; **verified key semantics**: `"-1"` yesterday observed, `"0"`
current observed, `"1"` forecast for **today** (same DateStamp as "0"), `"2"`
tomorrow, `"3"` day after. Each: `DateStamp`, `TimeStamp`, `R`/`S`/`G` blocks
with `Scale` (digit-string or null), `Text`; forecast rows carry probabilities
(`R.MinorProb`/`R.MajorProb`, `S.Prob`) instead of Scale; G forecasts give
predicted max level, no probability.

## Real-time solar wind (L1)
| URL | What |
|---|---|
| `/products/summary/solar-wind-speed.json` | one record: `{proton_speed, time_tag}` — dashboard "now" |
| `/products/summary/solar-wind-mag-field.json` | one record: `{bt, bz_gsm, time_tag}` |
| `/json/rtsw/rtsw_wind_1m.json` | 1-min plasma series (~2.6 MB, **newest first**; multiple `source` rows per time — **filter `active==true`**): `proton_speed/density/temperature` |
| `/json/rtsw/rtsw_mag_1m.json` | 1-min IMF (~1.5 MB): `bt`, `bz_gsm` (the storm-relevant component), GSE/GSM sets |
| `/products/geospace/propagated-solar-wind-1-hour.json` | lightweight combo (few KB, **columnar header-row format**): time, speed, density, temp, bx/by/bz(GSM), bt + arrival time at Earth |

## GOES X-rays & flares (`/json/goes/primary/`)
Window suffixes `-6-hour|-1-day|-3-day|-7-day` — sizes grow fast; use the
smallest. `xrays-6-hour.json`: 1-min flux, **2 records per timestamp** (channels
`0.05-0.4nm` short / `0.1-0.8nm` long — flare class comes from the long channel;
note the feed's field typo `electron_contaminaton`). `xray-flares-latest.json`:
single-element array: `current_class`, `begin/max/end_time`, `max_class` (e.g.
"C3.7"), `max_xrlong` (W/m²). Also `integral-protons-*.json` (≥10 MeV drives the
S-scale), `xray-background-7-day.json`, `suvi-flares-latest.json` (location).

## Aurora
- `/json/ovation_aurora_latest.json` — **~900 KB, 65,160 points — parse, never
  dump.** Object: `Observation Time`, `Forecast Time` (≈30–60 min lead),
  `coordinates: [[lon 0–359 E, lat −90..90, probability% 0–100], …]` on a 1°
  grid; updated ~5 min. West longitudes: `lon_e = lon % 360`.
- `/text/aurora-nowcast-hemi-power.txt` — tiny: hemispheric power (GW); >~50 GW
  active, >~100 GW strong storm.

## Text forecasts & alerts
- `/text/3-day-forecast.txt` — issued ~1230 UTC daily; contains an 8-row × 3-day
  **"NOAA Kp index breakdown"** table (decimal Kp per 3-h block) + R/S
  probabilities. The go-to for "next few nights" questions.
- `/text/27-day-outlook.txt` — weekly (Mondays): date, F10.7, A index, largest Kp.
- `/products/alerts.json` — newest-first objects: `product_id`,
  `issue_datetime`, `message` (full bulletin text; grep `NOAA Scale:` lines;
  types ALERT/WATCH/WARNING/SUMMARY).
- Also: `/products/kyoto-dst.json` (hourly Dst), `/products/10cm-flux-30-day.json`
  (F10.7), `/json/solar_probabilities.json` (flare probabilities),
  `/json/45-day-forecast.json`, `/json/solar_regions.json`.

## Large-file warnings
`ovation_aurora_latest.json` 0.9 MB; `rtsw_*_1m.json` 1.5–2.6 MB;
`enlil_time_series.json` 1.6 MB; `goes/primary/euvs-7-day.json` **16 MB**.
Prefer `/products/summary/*` singletons and the smallest window suffix.
Attribution: NOAA SWPC (US-government public domain); real-time products are
preliminary.
