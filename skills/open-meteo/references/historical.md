# Historical weather — reference (two products)

There are **two** historical products on **different hosts**. Choose first:

- **Archive / ERA5** (`archive`) — long, homogeneous reanalysis, **1940 →
  ~yesterday**, ~25 km (ERA5) or ~11 km (ERA5-Land). Best for climatology,
  decade-over-decade comparisons, or any date before 2021. The safe default for
  "what was the weather in <month/year>."
- **Historical Forecast** (`historical-forecast`) — the archived *actual past
  runs* of the high-resolution operational forecast models, **~2021-03-23 →
  ~2 days ago**, ~1–11 km. Best for the last few years at high resolution, or
  forecast backtesting ("what did the forecast actually say").

Neither has a `current` block — for "right now" use the Forecast API with
`current=`/`past_days=`.

---

## Archive (ERA5) — `https://archive-api.open-meteo.com/v1/archive`

### Required
`latitude`, `longitude`, `start_date`, `end_date` (`YYYY-MM-DD`, inclusive,
`end ≥ start`). Plus at least one of `hourly=` or `daily=`.

### Date range (verified)
Earliest `1940-01-01` (before → HTTP 400 "out of allowed range"). Latest allowed
`end_date` is ~yesterday on the default seamless blend (~1–2 day latency). If you
pin `models=era5` you may lose the last ~5 days (ERA5-final delay).

### `models=` (default = seamless ERA5 blend)
| Value | Resolution | Cadence | Coverage |
|---|---|---|---|
| `era5` | 0.25° (~25 km) | hourly | 1940–present |
| `era5_land` | 0.1° (~11 km) | hourly | 1950–present (finer land detail) |
| `era5_ensemble` | 0.5° (~55 km) | 3-hourly | 1940–present (uncertainty spread) |
| `ecmwf_ifs` | ~9 km | hourly | 2017–present, no delay |
| `cerra` | ~5 km | hourly | 1985–June 2021 (Europe only) |

Requesting multiple models **suffixes each variable with the model name**
(`temperature_2m_mean_era5`, `…_era5_land`). Out-of-coverage cells → `null`.

### Hourly variables
Temperature/humidity: `temperature_2m`, `relative_humidity_2m`, `dew_point_2m`,
`apparent_temperature`, `wet_bulb_temperature_2m`, `vapour_pressure_deficit`.
Pressure: `pressure_msl`, `surface_pressure`. Precip: `precipitation`, `rain`,
`snowfall`, `snow_depth`. Cloud: `cloud_cover`, `cloud_cover_low|mid|high`.
Wind: `wind_speed_10m|100m`, `wind_direction_10m|100m`, `wind_gusts_10m`.
Radiation: `shortwave_radiation`, `direct_radiation`, `diffuse_radiation`,
`direct_normal_irradiance`, `global_tilted_irradiance`,
`terrestrial_solar_radiation` (+`_instant` variants).
Soil temp: `soil_temperature_0_to_7cm|7_to_28cm|28_to_100cm|100_to_255cm`.
Soil moisture: `soil_moisture_0_to_7cm|7_to_28cm|28_to_100cm|100_to_255cm`.
Other: `weather_code`, `et0_fao_evapotranspiration`, `sunshine_duration`,
`is_day`.

### Daily variables (aggregated in the selected `timezone` — set it!)
`weather_code`, `temperature_2m_max|min|mean`, `apparent_temperature_max|min|mean`,
`precipitation_sum`, `rain_sum`, `snowfall_sum`, `precipitation_hours`,
`sunrise`, `sunset`, `daylight_duration`, `sunshine_duration`,
`wind_speed_10m_max`, `wind_gusts_10m_max`, `wind_direction_10m_dominant`,
`shortwave_radiation_sum`, `et0_fao_evapotranspiration`.

### Units / time
`temperature_unit` (celsius|fahrenheit), `wind_speed_unit`
(kmh|ms|mph|kn), `precipitation_unit` (mm|inch). `timezone` (IANA | GMT |
`auto`), `timeformat` (iso8601|unixtime). `cell_selection` (land|sea|nearest),
`elevation` override.

### Common task: compare two periods
Fetch each range with `daily=temperature_2m_max`, average each series yourself,
report the difference. Set `timezone` so the daily maxima align to local days.
Example (Phoenix Julys): two calls with `start_date/end_date` of
`2023-07-01..2023-07-31` and `1990-07-01..1990-07-31`, then mean each.

---

## Historical Forecast — `https://historical-forecast-api.open-meteo.com/v1/forecast`

**Same `/v1/forecast` path, parameters, and variable grammar as the live
Forecast API** (see `forecast.md`) — only the host differs. Supports `hourly=`,
`daily=`, `minutely_15=`, `current=`, `models=`, all the unit/time params, and
pressure levels.

### Required
`latitude`, `longitude`, and a date window (`start_date`/`end_date`, or relative
`past_days`).

### Date range
Data back to **~2021-03-23** on `best_match` (per-model start dates vary; some
models reach 2016–2018). Ends ~2 days before present.

### Models (`models=`, default `best_match`)
`ecmwf_ifs025`, `ecmwf_aifs025`, `gfs_seamless`, `gfs_global`, `gfs_hrrr`,
`icon_seamless`, `icon_global`, `icon_eu`, `icon_d2`, `gem_seamless`,
`meteofrance_arome_france`, `jma_seamless`, `metno_nordic`,
`knmi_harmonie_arome_europe`, `ukmo_global_deterministic_10km`,
`meteoswiss_icon_ch1`, … A bad slug → HTTP 400 "Cannot initialize MultiDomains
from invalid String value". (Note: `ecmwf_ifs_hres` is **not** valid — use
`ecmwf_ifs025`.) Pinning a model snaps to that model's grid (e.g. `ecmwf_ifs025`
snaps to the 0.25° cell).

## Shared gotchas
- **Rate limits can appear as a 200 body error** (`{"error":true,"reason":
  "Minutely API request limit exceeded…"}`) on the historical-forecast host —
  check the `error` field, not just the status. Space out bursts.
- Multi-model requests suffix every variable name with the model — parse
  accordingly.
- Always pass `timezone` for daily stats so days align to local midnight.
