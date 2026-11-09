# JPL CNEOS / SSD auxiliary APIs — reference

Host: `https://ssd-api.jpl.nasa.gov` (GET only — HEAD returns 405; no key, no
CORS). Every response carries `signature: {source, version}`. Numeric values
arrive as **strings** almost everywhere — cast client-side. Errors: HTTP 400
with `{"message", "code", "moreInfo"}` for bad/unknown params.

## cad.api — close approaches ("anything passing near Earth?")
`GET /cad.api` — defaults: `date-min=now`, `date-max=+60` (days), `dist-max=0.05`
(au), `body=Earth`, `neo=true`.
| Param | Notes |
|---|---|
| `date-min`/`date-max` | `YYYY-MM-DD`, `YYYY-MM-DDThh:mm:ss`, JD, `now`, relative `+7` (**encode `+` as `%2B`**) |
| `dist-max`/`dist-min` | au by default; **`LD` suffix for lunar distances** (`dist-max=1LD`) |
| `body` | `Earth` (default), `Moon`, `Mars`, `ALL`… |
| `pha` | `true` = only Potentially Hazardous Asteroids |
| `sort` | `date` (default), `dist`, `v-rel`, `h`, `object`; `-` prefix = desc |
| `des` | restrict to one object; `h-min`/`h-max` size filters; `fullname=true`; `limit` |

**Columnar envelope**: `{count, fields, data:[[...]]}` — zip `fields` with each
row. Fields: `des, orbit_id, jd, cd, dist, dist_min, dist_max, v_rel, v_inf,
t_sigma_f, h`. **`dist` is ALWAYS au** (even with an LD filter): ×149,597,870.7
= km; ÷0.002570 = LD. `cd` is **TDB** (≈UTC+69 s; fine for display). `v_rel`
km/s. **When `count`=0, `fields`/`data` are omitted** — guard.
Size from H (absolute magnitude): `D_km ≈ 1329/√albedo × 10^(−H/5)`; albedo
0.05–0.25 spans: H=18 ≈ 0.5–1.2 km, H=20 ≈ 0.2–0.5 km, H=22 ≈ 110–240 m,
H=25 ≈ 25–60 m, H=28 ≈ 7–15 m.

## fireball.api — bolide/atmospheric-impact events
`GET /fireball.api` — params: `date-min/max`, `energy-min`, `impact-e-min`,
`req-loc=true` (only located events), `vel-comp`, `sort` (`-date` newest first),
`limit` (>0). Columnar like cad (**but `count` is a string here**). Fields:
`date` (UTC), `energy` (**×10¹⁰ J radiated**), `impact-e` (**kt TNT — the "how
big" number**), `lat`+`lat-dir`, `lon`+`lon-dir`, `alt` (km), `vel` (km/s).
**lat/lon/alt/vel are frequently null.** Reference point: Chelyabinsk 2013 =
440 kt impact energy.

## sentry.api — impact-risk monitoring
`GET /sentry.api` — three modes:
- **Summary** (no params / filters `ip-min`, `ps-min`, `h-max`): array of
  **objects** (not columnar): `des`, `ip` (cumulative impact probability),
  `ps_cum`/`ps_max` (Palermo scale: < −2 negligible, > 0 serious), `ts_max`
  (Torino 0–10, can be null), `n_imp`, `range` (years), `diameter` (km), `h`,
  `last_obs`.
- **Object** (`des=101955`): `summary` + per-virtual-impactor rows (date, ip,
  ps, energy Mt).
- **Removed** (`removed=1`): objects taken off the risk list.
**Gotcha:** querying a removed object (e.g. Apophis `des=99942`, removed 2021)
returns HTTP **200** with an `error` key — check the body, not the status.

## sbdb.api — one object's full record
`GET /sbdb.api?sstr=<name|designation|SPK-ID>` (+ `phys-par=1`, `full-prec=1`,
`ca-data=1`, `vi-data=1`, `discovery=1`).
Response: `object` (fullname, des, spkid, neo/pha booleans, orbit_class),
`orbit` (epoch JD; `elements` array of {name,value,sigma,units}: e,a,q,i,om,w,
ma,tp,per,n; `moid` = Earth MOID in au; data_arc, n_obs_used), `phys_par`
(H, G, diameter km, albedo, rot_per h, spectral type).
**Match behavior:** not-found → HTTP **200** with `{"message":"specified object
was not found"}` (no `object` key); ambiguous → HTTP **300** with a candidate
`list` of {name, pdes} — re-query with an exact `pdes`. Handle 300 as data.

## Conversions & attribution
1 au = 149,597,870.7 km; 1 LD = 384,400 km ≈ 0.002570 au. Cite NASA/JPL (each
response's `signature.source` gives the exact API name); human-facing site:
cneos.jpl.nasa.gov.
