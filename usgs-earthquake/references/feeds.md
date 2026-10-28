# Real-time GeoJSON summary feeds — reference

Base: `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/`

Pre-baked, CDN-cached static files for "latest earthquakes" — fast, free, zero
params. Refreshed ~**once a minute** (`Cache-Control: public, max-age=60`), data
delayed up to ~5 min. Use feeds for dashboards / "anything big lately?"; use the
FDSN `query` endpoint (see `query.md`) the moment the user constrains by place,
exact time range, magnitude threshold, or event type.

## Feed URL pattern
`summary/{mag}_{period}.{format}`

- `mag ∈ significant | 4.5 | 2.5 | 1.0 | all`
- `period ∈ hour | day | week | month`
- `format ∈ geojson | csv | atom` (geojson is the default/most useful)

**The full matrix** (20 combinations for geojson):

| | hour | day | week | month |
|---|---|---|---|---|
| **significant** | significant_hour | significant_day | significant_week | significant_month |
| **M4.5+** | 4.5_hour | 4.5_day | 4.5_week | 4.5_month |
| **M2.5+** | 2.5_hour | 2.5_day | 2.5_week | 2.5_month |
| **M1.0+** | 1.0_hour | 1.0_day | 1.0_week | 1.0_month |
| **all** | all_hour | all_day | all_week | all_month |

Examples:
- `.../summary/significant_month.geojson` — notable quakes, past month.
- `.../summary/4.5_day.geojson` — M4.5+ worldwide, past day.
- `.../summary/all_hour.geojson` — everything, past hour.
- `.../summary/all_day.csv` — CSV variant.

"significant" = events with high `sig` (≈ ≥600 — magnitude + felt reports + PAGER
impact). The `all` feeds can be large (thousands of tiny events per week).

## Response
A GeoJSON `FeatureCollection` — identical Feature schema to the query endpoint
(see `geojson.md`). Feed `metadata` carries `generated` (epoch ms), `url`,
`title` (e.g. "USGS Significant Earthquakes, Past Month"), `status`, `api`
(`2.4.0` for feeds vs `2.7.0` for query), and **`count`** (feeds include a count;
the query endpoint does not).

## Gotchas
- Feeds have **no filtering** — you get the whole bucket. Need M5+ near Tokyo in
  a specific week? That's a `query`, not a feed.
- A **nonexistent feed filename returns HTTP 200** (static CDN file), not 404 —
  so validate the `{mag}_{period}` name against the matrix above rather than
  relying on a 404.
- CSV/Atom variants exist; legacy KML too. For programmatic use prefer geojson.
