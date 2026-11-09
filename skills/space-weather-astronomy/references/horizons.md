# JPL Horizons API — reference

Endpoint: `GET https://ssd.jpl.nasa.gov/api/horizons.api` (no key). File/POST
variant for long inputs: `POST .../api/horizons_file.api` (multipart:
`format=json`, `input=@batchfile`; batch file starts `!$$SOF` then `KEY='value'`
lines). Docs: https://ssd-api.jpl.nasa.gov/doc/horizons.html

## Request grammar
- `format=json` (default) or `text`. **Both return the same plain-text report**;
  json wraps it as `{"signature", "result": "<one giant string>", ["error"]}`.
- All other params are ALL-CAPS, values traditionally single-quoted
  (`COMMAND='499'`). Single-token values work unquoted; **multi-word values must
  be quoted** (`STEP_SIZE='1 d'`). URL-encode inside values: space `%20`,
  **`;` → `%3B`** (unencoded `;` splits the query → HTTP 400), `=` → `%3D`,
  `,` → `%2C`.
- Errors are **HTTP 200** with a top-level `error` field (bad date, missing
  COMMAND, output too large) — EXCEPT "no matches" and ambiguous-name match
  lists, which have **no `error` field**; detect real data by the presence of
  `$$SOE`. HTTP 400 only for malformed query strings.

## COMMAND — body IDs
- **Planet centers = N99**: 10 Sun, 199 Mercury, 299 Venus, 399 Earth, 499 Mars,
  599 Jupiter, 699 Saturn, 799 Uranus, 899 Neptune, 999 Pluto. `301` Moon.
- **Bare 1–9 = system barycenters** (0 = solar-system barycenter). `'1'` is NOT
  Ceres and not Mercury-the-planet.
- **Moons = NII**: 401 Phobos, 501 Io, 502 Europa, 606 Titan, 901 Charon…
- **Spacecraft = negative**: -170 JWST, -125544 ISS (TLE-based, ~4-week horizon),
  -31 Voyager 1, -48 Hubble. Outside a mission's span → `error`.
- **Small bodies need a trailing `;`** (encode `%3B`): `'99942;'` (IAU number),
  `'DES=2004 MN4;'` (designation), `'Apophis;'` (name — may be ambiguous).
  `DES=` takes designations/SPK-IDs, **not** IAU numbers (SPK ≈ number+2000000).
  Comets: add `CAP;`/`NOFRAG` for a unique apparition (`'DES=1P;CAP;'`).
- Ambiguous names return a match-list table; select by record number + `;`
  (record numbers change — never cache). `COMMAND='MB'` lists all major bodies.
- Object data only: `MAKE_EPHEM='NO'&OBJ_DATA='YES'` (no times needed).

## Common parameters
| Param | Default | Notes |
|---|---|---|
| `EPHEM_TYPE` | OBSERVER | OBSERVER (sky), VECTORS (XYZ states), ELEMENTS (orbital), SPK, APPROACH |
| `CENTER` | Geocentric | `'500@399'` geocenter; `'coord@399'`+`SITE_COORD` topocentric; `'568@399'` MPC observatory; `'500@10'` Sun; `'500@0'` SSB |
| `SITE_COORD` | — | `'E-lon,lat,alt-km'` — east-longitude deg (west negative OK), geodetic lat deg, altitude **km** |
| `START_TIME`/`STOP_TIME` | — | `'2026-07-06'`, `'2026-Jul-06 12:00'`, `'JD 2461227.5'` |
| `STEP_SIZE` | '60 min' | `'1 d'`,`'1 h'`,`'10 m'`,`'1 mo'`; bare integer = N equal intervals (only way <1 min; min 0.5 s) |
| `TLIST` | — | up to 10,000 discrete times (use POST file for long lists); `TLIST_TYPE=JD\|MJD\|CAL` |
| `OBJ_DATA` | **YES** | set `'NO'` to skip the physical-data preamble |
| `MAKE_EPHEM` | YES | |
| `CSV_FORMAT` | NO | `'YES'` = comma rows (trailing comma; flags become separate fields) |
| `TIME_ZONE` | — | `'+02:00'` shifts in/out to civil time |

## OBSERVER quantities (`QUANTITIES='4,9,20,…'`)
**Default is `'A'` = ALL 49 (~80 columns) — always specify.** Key codes:
| # | Meaning | Units |
|---|---|---|
| 1 / 2 | astrometric / apparent RA & DEC | HMS/DMS (`ANG_FORMAT='DEG'` for decimal) |
| 4 | **apparent azimuth & elevation** (topocentric only; n.a. geocentric). Az: N=0, E=90 | deg |
| 9 | **visual magnitude** + surface brightness (n.a. at unmodeled phase angles) | mag |
| 10 | **illuminated fraction** (Moon phase %) | % |
| 13 | angular diameter | arcsec |
| 19 | heliocentric range & rate | AU (or `RANGE_UNITS='KM'`), km/s |
| 20 | **observer range & rate** (Earth↔target distance) | AU/km, km/s (rate always km/s) |
| 23 | solar elongation + `/T` (evening sky) or `/L` (morning sky) | deg |
| 24 | phase angle | deg |
| 25 | target–Moon separation & Moon illum% | deg, % |
| 29 | constellation | IAU 3-letter |
Extras: `APPARENT='REFRACTED'` (refraction), `SKIP_DAYLT='YES'`, `ELEV_CUT='10'`,
`AIRMASS`, `SOLAR_ELONG` (row filters — they inject message lines INSIDE the
$$SOE block; only lines starting with a date are data).

## Output anatomy & rise/set
Rows sit between `$$SOE` and `$$EOE`. After the timestamp: **solar flag** (`*`
day, `C`/`N`/`A` twilight, blank dark) then **lunar flag** (`m` Moon up) — event
markers `r`(ise) `t`(ransit) `s`(et) `e`(lev-max) override the lunar column on
the first row AFTER the event (step must be ≤ 30 min).
**Exact rise/set:** `R_T_S_ONLY='TVH'` (true visual horizon: refraction+dip; also
`GEO`, `RAD`) with `STEP_SIZE='1 m'` → compact r/t/s-only table (~1–2 min
accuracy). `ELEV_CUT` re-references rise/set to a custom elevation.
Header always echoes the site (`Center geodetic : E-lon, lat, alt`) and
`1 au = 149597870.700 km` — use it to sanity-check.

## VECTORS / ELEMENTS (for programming)
- `EPHEM_TYPE='VECTORS'`: `VEC_TABLE` 1–6 (3=state+LT,RG,RR default),
  `OUT_UNITS='KM-S'|'AU-D'|'KM-D'`, `REF_PLANE='ECLIPTIC'|'FRAME'`,
  `VEC_CORR='NONE'|'LT'|'LT+S'`, `VEC_LABELS='NO'` (or CSV) for parsing.
  Columns: JDTDB, X,Y,Z (km|au), VX,VY,VZ (km/s|au/d), LT, RG, RR.
- `EPHEM_TYPE='ELEMENTS'`: osculating EC,QR,IN,OM,W,Tp,N,MA,TA,A,AD,PR (TDB only).
- **VECTORS/ELEMENTS default to TDB times; OBSERVER is UT.**

## Limits & etiquette
Output hard cap ≈ **90,024 lines** (error suggests changing step-size). No formal
rate limit — serialize requests, cache; 503 = overloaded, back off. No CORS
headers (server-side calls only). Citation: "Giorgini, JD and JPL Solar System
Dynamics Group, NASA/JPL Horizons On-Line Ephemeris System."
