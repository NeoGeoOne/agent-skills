# Air Quality API — reference

Base URL: `https://air-quality-api.open-meteo.com/v1/air-quality` (alias
`air-quality`). **Dedicated host — not `api.open-meteo.com`.** Continental-scale
(~11 km) air quality, pollen, and UV from CAMS (Copernicus Atmosphere
Monitoring Service).

## Required
`latitude`, `longitude` (comma-separate for bulk). Supply `current=` and/or
`hourly=`. **There is no `daily=` block.**

## Key optional params
- `domains`: `auto` (default — CAMS Europe 0.1° inside Europe, CAMS global ~0.4°
  elsewhere) | `cams_europe` | `cams_global`. Pollen and several extra species
  require `cams_europe`.
- `forecast_days`: 0–7 (default 5). **Max 7** — `8` → HTTP 400. `past_days`: 0–92.
- `forecast_hours`/`past_hours`, `start_date`/`end_date`, `start_hour`/`end_hour`.
- `timezone` (auto|IANA|GMT), `timeformat`, `cell_selection` (nearest default).

## Pollutant / chemistry variables (both domains unless noted)
`pm10` (μg/m³), `pm2_5` (μg/m³), `carbon_monoxide` (μg/m³), `carbon_dioxide`
(**ppm** — note the different unit), `nitrogen_dioxide`, `sulphur_dioxide`,
`ozone`, `aerosol_optical_depth` (dimensionless), `dust` (μg/m³).

**CAMS Europe only:** `ammonia`, `nitrogen_monoxide`, `formaldehyde`, `glyoxal`,
`peroxyacyl_nitrates`, `secondary_inorganic_aerosol`. (`methane` is CAMS global.)

## UV
`uv_index`, `uv_index_clear_sky` (dimensionless).

## Pollen (grains/m³) — **Europe only**, needs `cams_europe`
`alder_pollen`, `birch_pollen`, `grass_pollen`, `mugwort_pollen`,
`olive_pollen`, `ragweed_pollen`. Outside Europe / with `cams_global` → `null`.

## Air Quality Indices
**European (`EAQI`):** `european_aqi` (overall), `european_aqi_pm2_5`,
`european_aqi_pm10`, `european_aqi_nitrogen_dioxide` (alias `european_aqi_no2`),
`european_aqi_ozone` (`european_aqi_o3`), `european_aqi_sulphur_dioxide`
(`european_aqi_so2`). Bands: 0–20 good, 20–40 fair, 40–60 moderate, 60–80 poor,
80–100 very poor, >100 extremely poor.

**US (`USAQI`, 0–500):** `us_aqi` (overall), `us_aqi_pm2_5`, `us_aqi_pm10`,
`us_aqi_nitrogen_dioxide` (`us_aqi_no2`), `us_aqi_ozone` (`us_aqi_o3`),
`us_aqi_sulphur_dioxide` (`us_aqi_so2`), `us_aqi_carbon_monoxide` (`us_aqi_co`).
The US family adds a CO sub-index the European one lacks. US AQI bands: 0–50
good, 51–100 moderate, 101–150 unhealthy for sensitive groups, 151–200
unhealthy, 201–300 very unhealthy, 301+ hazardous. PM2.5 health rule of thumb:
under ~12 μg/m³ is good; 35+ is unhealthy for sensitive groups; 55+ unhealthy.

## Response
Same shape as Forecast, minus `daily`: metadata + `current`/`current_units` and
`hourly`/`hourly_units`. Index units are `EAQI`/`USAQI`; dimensionless vars
(`uv_index`, `aerosol_optical_depth`) return an empty `""` unit string.

## Gotchas
- Dedicated host; `forecast_days` max 7; pollen + several species are Europe-only
  (`cams_europe`); `carbon_dioxide` is ppm. AQI sub-pollutants accept long and
  short (`_no2`/`_o3`/`_so2`/`_co`) aliases. Errors: HTTP 400
  `{"error":true,"reason":...}`. Commercial host:
  `customer-air-quality-api.open-meteo.com` with `&apikey=`.
