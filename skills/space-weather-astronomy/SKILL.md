---
name: space-weather-astronomy
description: >-
  Live access to the sky and near-Earth space, no API keys: JPL Horizons
  ephemerides (position, rise/set, brightness, and distance of any planet, moon,
  asteroid, comet, or spacecraft, from any place on Earth), JPL CNEOS asteroid
  close approaches / fireballs / impact risk, and NOAA SWPC space weather (Kp
  index, geomagnetic storms, solar flares, radio blackouts, solar wind, aurora
  forecasts). Use whenever a question needs real astronomical or space-weather
  data: can I see the aurora / northern lights tonight, where is Mars or Jupiter
  or the Moon right now, when does a planet rise or set, how far away is a body,
  Moon phase or illumination, ISS or JWST position, any asteroids passing near
  Earth, recent fireballs or meteor impacts, solar flare or geomagnetic storm
  activity, will GPS or radio be affected, current Kp — even if no API is named.
  Also use when writing code that fetches any of this.
---

# Space Weather & Astronomy (JPL Horizons/CNEOS + NOAA SWPC)

Two keyless, public data worlds in one skill: **JPL** answers "where is anything
in the solar system and what's coming near Earth"; **NOAA SWPC** answers "what is
the Sun doing to us right now." No API keys anywhere — never send one.
Attribution: NASA/JPL-Caltech (Horizons/CNEOS) and NOAA SWPC. All times UTC
unless a product says otherwise.

## Step 1: route the question

| The user wants… | Use |
|---|---|
| Position / rise-set / brightness / distance of a planet, Moon, asteroid, comet, spacecraft | **Horizons** `https://ssd.jpl.nasa.gov/api/horizons.api` |
| Asteroids passing close to Earth ("closer than the Moon?") | **cad.api** `https://ssd-api.jpl.nasa.gov/cad.api` |
| Recent fireballs / bolide impacts | **fireball.api** (same host) |
| Long-term impact risk of a specific asteroid | **sentry.api** (same host) |
| Everything known about one asteroid/comet (orbit, size, albedo) | **sbdb.api** (same host) |
| Current Kp / geomagnetic storm / solar flares / radio blackout / solar wind / aurora | **SWPC** `https://services.swpc.noaa.gov/...` (static files, path-only, no params) |
| "Can I see the aurora from X tonight?" | SWPC Kp-forecast + OVATION grid + the Kp↔latitude table below |

## The bundled client: `scripts/space_data.py`

Both providers have hostile-to-naive-code response formats (details below).
`scripts/space_data.py` (Python 3 stdlib only, no pip) handles them. Prefer it;
drop to raw URLs when you need something it doesn't cover.

```bash
# Where is Mars tonight from a city? (geocodes the place, topocentric az/el)
python scripts/space_data.py horizons COMMAND=499 --place "San Francisco" \
    START_TIME=2026-07-07 STOP_TIME=2026-07-08 STEP_SIZE="1 h" QUANTITIES=4,9,20 --soe

# Current Earth-Mars distance (geocentric, single instant)
python scripts/space_data.py horizons COMMAND=499 CENTER=500@399 \
    TLIST=2026-07-07 QUANTITIES=20 --soe

# Exact rise/transit/set times (1-min search, true-visual-horizon)
python scripts/space_data.py horizons COMMAND=499 --place "San Francisco" \
    START_TIME=2026-07-07 STOP_TIME=2026-07-08 STEP_SIZE="1 m" \
    QUANTITIES=4 R_T_S_ONLY=TVH --soe

# Asteroids within 1 lunar distance this month; recent fireballs
python scripts/space_data.py cad dist-max=1LD date-min=2026-07-01 date-max=2026-07-31
python scripts/space_data.py fireball

# Space weather now
python scripts/space_data.py swpc scales        # current + 3-day R/S/G forecast
python scripts/space_data.py swpc kp --tail 8   # recent 3-hour Kp with G levels
python scripts/space_data.py swpc kp-forecast   # predicted Kp out to +3 days
python scripts/space_data.py swpc wind          # solar wind speed + Bz now
python scripts/space_data.py swpc flares        # latest GOES X-ray flare
python scripts/space_data.py swpc aurora --lat 53.55 --lon 9.99   # OVATION % at a point
python scripts/space_data.py swpc forecast      # the human-readable 3-day text
```

## Horizons — the gotchas that break everyone

Horizons returns `{"signature", "result"}` where **`result` is one giant TEXT
report**; the ephemeris rows sit between `$$SOE` and `$$EOE` marker lines. There
is no structured-JSON ephemeris. Also:

- **Errors arrive as HTTP 200.** Check three things: the optional top-level
  `error` field; whether `result` contains `$$SOE`; and whether `result` is a
  *match-list page* (ambiguous name) or "No matches found" — neither sets
  `error`. HTTP 400 only fires for malformed query strings (e.g. an unencoded
  `;`, which the server treats as a parameter separator — **always encode `;` as
  `%3B`** and `=` inside values as `%3D`).
- **Body IDs:** planets are `N99` (199 Mercury … 399 Earth, 499 Mars, 599
  Jupiter…), `10`=Sun, `301`=Moon, moons `5xx`/`6xx`…, **spacecraft are
  negative** (`-170` JWST, `-125544` ISS, `-31` Voyager 1). **Bare `1`–`9` are
  barycenters, not planets or Ceres.** Small bodies need a trailing semicolon:
  `COMMAND='99942;'` (Apophis) or `'DES=2004 MN4;'`. Names are ambiguous
  (`'Mars'`, `'Halley'` return match lists) — prefer numeric IDs.
- **`QUANTITIES` defaults to ALL 49** (~80 columns of mostly n.a.) — always
  specify. The useful set: `4` az/el ("where in my sky", topocentric only), `9`
  visual magnitude, `10` illuminated % (Moon phase), `13` angular size, `20`
  observer distance + rate (AU by default; `RANGE_UNITS='KM'`), `23` solar
  elongation (`/T` evening sky, `/L` morning sky), `29` constellation.
- **`OBJ_DATA` defaults to YES** (pages of physical data before the table) — set
  `'NO'` for lean output.
- **Observing site:** `CENTER='coord@399'` +
  `SITE_COORD='E-lon,lat,alt-km'` (east-longitude degrees, west = negative is
  fine; altitude in **km**). Geocentric = `CENTER='500@399'` — az/el is n.a.
  there. Observatory codes work too (`'568@399'` = Mauna Kea).
- **Rise/set:** the r/t/s/e markers appear in the flag column on the first row
  *after* the event and only when step ≤ 30 min. For exact clock times use
  `R_T_S_ONLY='TVH'` with `STEP_SIZE='1 m'`. Solar-presence flags on each row:
  `*` daylight, `C`/`N`/`A` civil/nautical/astronomical twilight, blank = dark;
  second flag `m` = Moon up.
- Output caps at ~**90,024 lines**; row filters (`SKIP_DAYLT`, `ELEV_CUT`)
  inject message lines *inside* the `$$SOE` block — treat only lines starting
  with a date as data. `CSV_FORMAT='YES'` gives comma rows (trailing comma).
- OBSERVER tables are UT; VECTORS/ELEMENTS default to **TDB**. For programming
  use `EPHEM_TYPE='VECTORS'` (X,Y,Z,VX,VY,VZ; `OUT_UNITS='KM-S'|'AU-D'`).

## CNEOS — close approaches, fireballs, risk

- **cad.api**: `dist-max=1LD` (LD suffix = lunar distances) or au; `date-min`/
  `date-max` (`YYYY-MM-DD`, `now`, `+60`; **encode `+` as `%2B`**). Response is
  **columnar**: zip `fields` with each `data` row; all values are strings. The
  output `dist` is **always au** (× 149,597,870.7 km; ÷ 384,400 for LD). `cd`
  dates are TDB (≈UTC + 69 s — fine for display). When `count` is 0, `fields`/
  `data` are **omitted** — guard. Size from `h`: D(km) ≈ 1329/√albedo ×
  10^(−H/5); H=22 ≈ 110–240 m, H=25 ≈ 15–40 m.
- **fireball.api**: `impact-e` is kt TNT (use this for "how big"); `energy` is
  ×10¹⁰ J radiated; lat/lon/alt/vel are often **null**.
- **sentry.api**: impact monitoring (`ip` probability, `ps_cum` Palermo,
  `ts_max` Torino). Objects removed from Sentry (like Apophis) return HTTP 200
  with an `error` key. **sbdb.api**: one object's orbit/physical data; not-found
  is HTTP **200** with a `message`; ambiguous match is HTTP **300** with a
  candidate list — handle as data.

## SWPC — the gotchas

- **Static files, no query params** — you pick a path. Bad paths → 404 **HTML**
  (never blind-JSON-parse). Files regenerate ~1/min (`max-age=60`) — polling
  faster is pointless.
- **Sniff the shape, don't assume:** some products are arrays of objects, some
  (e.g. `/products/geospace/*`) are **array-of-arrays with a header row**. Check
  whether `data[0]` is a dict or a list.
- **`/products/solar-wind/` is GONE (404)** — old tutorials reference it.
  Real-time solar wind now lives at `/products/summary/solar-wind-speed.json` +
  `solar-wind-mag-field.json` (tiny, latest value) or `/json/rtsw/rtsw_wind_1m.json`
  + `rtsw_mag_1m.json` (1-min series, ~2 MB, newest first, **filter on
  `active==true`**).
- **`noaa-scales.json` keys:** `"-1"`=yesterday observed, `"0"`=current
  observed, `"1"`=forecast for **today** (same date as "0"!), `"2"`=tomorrow,
  `"3"`=day after.
- Key products: Kp 3-hour `/products/noaa-planetary-k-index.json`; Kp forecast
  (+3 days, with `noaa_scale`) `/products/noaa-planetary-k-index-forecast.json`;
  1-min estimated Kp `/json/planetary_k_index_1m.json`; latest flare
  `/json/goes/primary/xray-flares-latest.json`; X-ray flux
  `/json/goes/primary/xrays-6-hour.json` (2 channels per timestamp); alerts
  `/products/alerts.json`; 3-day text `/text/3-day-forecast.txt` (has a Kp
  breakdown table); aurora grid `/json/ovation_aurora_latest.json` (**~900 KB,
  65,160 points — never dump; index [lon 0–359 E, lat, probability%]**).
- Timestamps are UTC even when the `Z` suffix is missing.

## Interpreting space weather (the numbers → meaning)

- **Kp → G-scale:** G1=Kp5, G2=Kp6, G3=Kp7, G4=Kp8, G5=Kp9. Kp 0–2 quiet, 3–4
  unsettled/active.
- **Aurora visibility (geomagnetic latitude, approximate):** Kp5 → ~60°
  (Oslo/Edmonton), Kp7 → ~55° (Hamburg/Seattle), Kp8 → ~50° (London/Chicago),
  Kp9 → ~45–50° (central Europe/N. California). **Geomagnetic ≠ geographic**:
  the pole tilts toward North America, so Hamburg (53.6°N geographic) is only
  ~50° geomagnetic while Edmonton (53.5°N) is ~60°. Viewing also needs darkness
  (high-latitude summer twilight kills it) and clear skies (cross-check clouds
  with the open-meteo skill if installed). For "right now", use the OVATION grid.
- **Flares:** classes A/B/C/M/X, each 10× (X-ray flux; M1=1e-5 W/m²). M/X flares
  → R1–R5 **dayside-only, immediate** HF radio blackouts (R3=X1). GPS is mainly
  degraded by strong G/S events, not small flares.
- **Solar wind:** storm fuel = speed >500–600 km/s and/or sustained
  **southward Bz < −10 nT**. CMEs arrive 1–3 days after eruption; flare X-rays
  hit in 8 minutes.

## Reference files

- `references/horizons.md` — full grammar, body IDs, QUANTITIES catalog,
  topocentric sites, rise/set (R_T_S_ONLY), VECTORS/ELEMENTS, limits, errors.
- `references/cneos.md` — cad, fireball, sentry, sbdb: params, columnar
  envelope, units, error behaviors (including HTTP 300).
- `references/swpc.md` — the verified SWPC product catalog with shapes, sizes,
  cadences, and removed-path traps.
- `references/space-weather-concepts.md` — NOAA G/R/S scales in full, Kp,
  flare classes, aurora visibility, solar-wind drivers, attribution.

## Red flags — stop and reconsider if you catch yourself…

- …treating a Horizons HTTP 200 as success without checking `error`/`$$SOE`, or
  parsing `result` as structured JSON (it's a text report).
- …omitting `QUANTITIES` (you'll get all 49) or requesting az/el with a
  geocentric CENTER (n.a.).
- …using `COMMAND='1'` for Ceres or a planet (barycenter!), or a bare name that
  has a match list, or an unencoded `;`.
- …fetching `/products/solar-wind/...` (removed) or dumping the OVATION grid
  into context (~900 KB).
- …reading cad.api `dist` as km or LD (it's always au), or indexing `data` rows
  without zipping `fields`.
- …promising aurora from a geographic latitude without converting to
  geomagnetic, or ignoring darkness/season.
- …sending an API key. There are none.

## Verification

Before calling a result done: confirm the right provider/endpoint for the
question; for Horizons confirm the response actually contains `$$SOE` data (not
an error/match list) and quantities came from the requested site; for SWPC
confirm the product path returned JSON (not 404 HTML) and values are timestamped
recent; for cad confirm distances were converted from au correctly; and state
Kp/G/flare interpretations consistently with the tables above.
