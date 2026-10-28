# ComCat concepts — interpreting results

USGS ComCat (ANSS Comprehensive Catalog) merges many networks' solutions and
exposes, per event, one **preferred** origin and one **preferred** magnitude
(highest `preferredWeight`). GeoJSON `properties.mag`/`magType` reflect that
single preferred magnitude; alternatives live inside the detail doc's `products`.

## Magnitude types (`magType`)
USGS prefers **moment magnitudes (Mw…)** when computable, falling back to body/
surface/local scales. API returns lowercase codes (`mww`, `mb`, `ml`); display
often capitalizes (`Mww`).

| Code | Name | Usage | Note |
|---|---|---|---|
| `mww` | Moment (W-phase) | ~M5+, teleseismic | **Authoritative for most large events.** |
| `mwc` | Centroid moment | ~M5.5+ | Used if Mww unavailable (e.g. GCMT). |
| `mwb` | Body-wave moment | ~M5.5–7 | Unreliable ≥M7.5. |
| `mwr` | Regional moment | ~M4–6.5 | Authoritative for moderate events <M5. |
| `mwp` | Moment (P-wave) | ~M5–8 | Rapid; early alerts/tsunami. |
| `mb` | Short-period body-wave | ~M4–6.5 | **Saturates ~M6.5+** (under-reports big quakes). |
| `mb_lg`/`MbLg` | Lg regional | ~M3.5–7 | Central/eastern US. |
| `ms`/`ms_20` | 20-s surface-wave | ~M5–8.5 | **Saturates ~M8.3+.** |
| `ml`/`ML` | Local ("Richter") | ~M2–6.5 | Small local events. |
| `md` | Duration/coda | ≤~M4 | When amplitudes clipped. |
| `mfa`/`mint` | Felt-area / intensity | any | Historical/pre-instrumental. |
| `me` | Energy | ~M3.5+ | From radiated energy. |
| `uk`/`Unknown` | — | any | Type not reported. |

**Saturation gotcha:** when comparing magnitudes across events, note the type —
`mb`/`Ms` under-report great quakes. There are ~40 enumerated types (see
`application.json`).

## Event types (`type` result / `eventtype` filter)
Default queries return **all** types. To get only tectonic quakes, filter
`eventtype=earthquake`. Enumerated (~46, space- and underscore-spellings both
occur): `earthquake`, `quarry blast`, `explosion`, `chemical explosion`,
`mining explosion`, `nuclear explosion`, `volcanic eruption`, `ice quake`,
`sonic boom`, `rock burst`, `landslide`, `mine collapse`, `debris avalanche`,
`meteor`, `induced or triggered event`, `other event`, `not reported`, …

## PAGER alert (`alert`)
PAGER = Prompt Assessment of Global Earthquakes for Response. Set by the **higher**
of the estimated-fatalities band and the estimated-economic-loss band:

| Alert | Fatalities | Losses (USD) | Implication |
|---|---|---|---|
| **red** | 1,000+ | $1B+ | Catastrophic; national/international response. |
| **orange** | 100–999 | $100M–$1B | Regional/national response likely. |
| **yellow** | 1–99 | $1M–$100M | Local/regional response. |
| **green** | 0 | < $1M | No significant impact expected. |

`null`/absent when no PAGER product (most events). Details in the `losspager`
product (`alertlevel`, `maxmmi`, fatality/loss histograms).

## Shaking intensity: ShakeMap `mmi` and DYFI `cdi`/`felt`
- **`mmi`** — max modeled **Modified Mercalli Intensity** (ShakeMap, instrumental).
  Scale I–XII: I not felt, IV–V felt widely, VI–VII slight/moderate damage,
  VIII–IX heavy, X+ extreme. It's *shaking* (location-dependent), not magnitude.
- **`cdi`** — max **Community Determined Intensity** from public "Did You Feel
  It?" reports (same I–XII scale). **`felt`** — count of DYFI responses.
- `mmi` (model) and `cdi` (crowd) are independent estimates and often differ.

## Significance (`sig`)
Higher = more notable. Verified formula: `SM = mag×100×(mag/6.5)`;
`SP` = red 2000 / orange 1000 / yellow 500 / green 0; `SD = min(felt,1000)×(cdi/10)`;
`sig = max(SM, SP) + SD`. The **significant** feed uses ~`sig ≥ 600`; filter with
`minsig=`. It's an **unbounded** ranking score — great quakes exceed 1000 (e.g.
2015 M7.8 Nepal = 2820), so don't treat 1000 as a cap.

## Catalogs, networks, preferred solution
- **`net`** — preferred network code: `us` (USGS NEIC global), `nc` (N. California),
  `ci` (S. California), `ak` (Alaska), `nn` (Nevada), `uw` (Pacific NW), `uu`
  (Utah), `hv` (Hawaii), `pr` (Puerto Rico), `ok`/`tx` (Oklahoma/TexNet), …
  `net`+`code` = the authoritative event id.
- **`catalog`** filter — a named authoritative collection: `us`, `nc`, `ci`, `ak`,
  `gcmt` (Global CMT), `iscgem`, `atlas` (ShakeMap Atlas), `official`, `pde`, …
  (~61). Default = ComCat cross-network preferred (best available).
- **`contributor`** filter — who supplied a solution (~28).
- `ids`/`sources` (comma-wrapped) list all associated ids/contributors; `status`
  is `automatic` (unreviewed) or `reviewed`.

## Data terms / attribution
Public domain (U.S. Government work). USGS **requests attribution**, not
permission. Suggested citation: "U.S. Geological Survey, Earthquake Hazards
Program, Advanced National Seismic System (ANSS) Comprehensive Catalog,
https://doi.org/10.5066/F7MS3QZH." Data are preliminary/subject to revision —
respect the `status` field (`automatic` values change). No API key; send none.
