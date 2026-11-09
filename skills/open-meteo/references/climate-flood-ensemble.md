# Climate, Flood & Ensemble APIs — reference

Three specialized products, each on its own host. A recurring rule across all
three: **requesting one model returns unsuffixed variable names; requesting
multiple models suffixes every variable with the model id** — parse both forms.

---

## Climate Change API (CMIP6) — `https://climate-api.open-meteo.com/v1/climate`

Long-term **daily** projections from high-resolution CMIP6 models, statistically
downscaled to ~10 km and bias-corrected against ERA5-Land. For climate-change /
multi-decade trends — **not** weather or short-term forecasting. Daily only.

### Required
`latitude`, `longitude`, `start_date`, `end_date` (`yyyy-mm-dd`, within
**1950-01-01 … 2050-12-31**), `models`, `daily`.

### Models (`models=`) — pick at least one
`CMCC_CM2_VHR4`, `FGOALS_f3_H`, `HiRAM_SIT_HR`, `MRI_AGCM3_2_S` (highest native
res, ~20 km), `EC_Earth3P_HR`, `MPI_ESM1_2_XR`, `NICAM16_8S`. Models can return
`null` at the extreme edge of the range (e.g. `EC_Earth3P_HR` on 2050-12-31).

### Daily variables
`temperature_2m_max|min|mean`, `precipitation_sum`, `rain_sum`, `snowfall_sum`,
`wind_speed_10m_max|mean`, `cloud_cover_mean`,
`relative_humidity_2m_max|min|mean`, `soil_moisture_0_to_10cm_mean`,
`shortwave_radiation_sum` (MJ/m²), `et0_fao_evapotranspiration_sum`,
`pressure_msl_mean`, `dew_point_2m_max|min|mean`.

### Optional
`disable_bias_correction` (default false → set true for raw downscaled output),
`temperature_unit`, `wind_speed_unit`, `precipitation_unit`, `timezone`,
`cell_selection`, `format`.

### Gotchas
Single-vs-multi-model suffix rule (above). A big request (all 7 models × full
1950–2050 × many vars) can hit **HTTP 429** — split into fewer models / shorter
windows. `timezone=UTC` may echo back as `GMT`.

---

## Flood API (GloFAS river discharge) — `https://flood-api.open-meteo.com/v1/flood`

Daily **river discharge (m³/s)** from GloFAS for ~5 km river cells worldwide,
**1984-01-01 → present + forecast** (up to ~210 days). Daily only.

### Required
`latitude`, `longitude` (comma-separate for bulk) + at least one `daily=`
variable. Place the point **on or very near a real river** — non-river cells and
tiny streams read `null` or near-zero.

### `daily=` variables (all m³/s)
`river_discharge` (primary/best estimate — always present),
`river_discharge_mean`, `river_discharge_median`, `river_discharge_max`,
`river_discharge_min`, `river_discharge_p25`, `river_discharge_p75`. The
percentile/min/max/mean/median vars are ensemble statistics — meaningful over
the forecast horizon; for historical dates the ensemble collapses so they equal
`river_discharge`.

### Time / ensemble
`forecast_days` (default 92, treat 210 as the max), `past_days`,
`start_date`/`end_date` (`yyyy-mm-dd`, from 1984-01-01). `ensemble=true` expands
the response to all **50** members `river_discharge_member01 … member50`.

### Gotchas
Daily-only (no hourly/current). `null` is normal off-river or at some early
dates. Pre-1984 → HTTP 400 with the allowed-range message. Commercial host:
`customer-flood-api.open-meteo.com` with `&apikey=`.

---

## Ensemble API — `https://ensemble-api.open-meteo.com/v1/ensemble`

Probabilistic forecasts: each variable is returned **once per ensemble member**,
so you can build spread / percentiles / probabilities.

### Required
`latitude`, `longitude`, **`models=`** (always pass it explicitly), plus at least
one `hourly=` (or `daily=`) variable.

### Model codes (verified) — `_memberNN` columns + 1 unsuffixed control column
| `models=` code | member columns | total (incl. control) | horizon |
|---|---|---|---|
| `icon_seamless` | 39 | 40 | ~7.5 d |
| `icon_global` | 39 | 40 | ~7.5 d |
| `icon_eu` | 39 | 40 | ~5 d |
| `icon_d2` | 19 | 20 | ~2 d |
| `gfs_seamless` | 30 | 31 | ~35 d |
| `gfs025` | 30 | 31 | ~10 d |
| `gfs05` | 30 | 31 | ~35 d |
| `ecmwf_ifs025` | 50 | 51 | ~15 d |
| `ecmwf_aifs025` | 50 | 51 | ~15 d |
| `gem_global` | 20 | 21 | ~16 d |
| `bom_access_global_ensemble` | 17 | 18 | ~10 d |

Avoid deprecated `ecmwf_ifs04` (no members). Docs/domain names like `aigefs025`,
`ukmo_mogreps_g` are **rejected** as `models=` codes — use the table above.

### Member column naming (core concept)
- **Single model:** `temperature_2m` (control / member 0),
  `temperature_2m_member01`, … `temperature_2m_memberNN`. The unsuffixed column
  IS a data column — don't drop it when iterating members.
- **Multiple models:** every column gets the model's internal domain name
  appended (`temperature_2m_member01_icon_seamless_eps`,
  `…_ncep_gefs025`). Members are aligned by index across time, but member01 of
  ICON ≠ member01 of GFS.

### Variables
Same surface set as Forecast (`temperature_2m`, `precipitation`, `wind_speed_10m`,
`cloud_cover`, `weather_code`, radiation, soil layers, `cape`, …) plus
pressure-level variables (`_<level>hPa`) — **availability is model-dependent**; a
variable a model lacks is silently omitted. `daily=` aggregates also expand per
member.

### Time / other
`forecast_days` (default 7, ceiling 35 — model horizon caps effective length),
`past_days`, `start_date`/`end_date`, plus the usual unit/timezone/cell params.

### Errors
Bad model/variable → HTTP 400 "Cannot initialize … from invalid String value".
Commercial host: `customer-ensemble-api.open-meteo.com` with `&apikey=`.
