# Weather Forecast API — reference

Base URL: `https://api.open-meteo.com/v1/forecast` (alias `forecast`).
The primary weather endpoint: current conditions plus forecasts up to 16 days
ahead and up to 92 days of recent past. Free, no API key.

## Required parameters
- `latitude`, `longitude` (WGS84, decimal degrees). Comma-separate for multiple
  locations in one call (e.g. `latitude=52.52,48.85&longitude=13.41,2.35`) — the
  response then becomes a JSON **array**, one object per location.
- Supply at least one of `current=`, `hourly=`, `daily=`, `minutely_15=` or the
  response is metadata only.

## `current=` variables (single most-recent value)
`temperature_2m`, `relative_humidity_2m`, `apparent_temperature`, `is_day`
(1 day / 0 night), `precipitation`, `rain`, `showers`, `snowfall`,
`weather_code`, `cloud_cover`, `pressure_msl`, `surface_pressure`,
`wind_speed_10m`, `wind_direction_10m`, `wind_gusts_10m`. (Most hourly variables
also work here.) The `current` object also carries an `interval` (seconds).

## `hourly=` variables
**Core:** `temperature_2m`, `relative_humidity_2m`, `dew_point_2m`,
`apparent_temperature`, `precipitation_probability`, `precipitation`, `rain`,
`showers`, `snowfall`, `snow_depth`, `weather_code`, `pressure_msl`,
`surface_pressure`, `cloud_cover`, `cloud_cover_low`, `cloud_cover_mid`,
`cloud_cover_high`, `visibility`, `evapotranspiration`,
`et0_fao_evapotranspiration`, `vapour_pressure_deficit`.

**Wind:** `wind_speed_10m|80m|120m|180m`, `wind_direction_10m|80m|120m|180m`,
`wind_gusts_10m`.

**Temperature aloft:** `temperature_80m`, `temperature_120m`, `temperature_180m`.

**Soil temperature:** `soil_temperature_0cm|6cm|18cm|54cm`.
**Soil moisture (m³/m³):** `soil_moisture_0_to_1cm`, `soil_moisture_1_to_3cm`,
`soil_moisture_3_to_9cm`, `soil_moisture_9_to_27cm`, `soil_moisture_27_to_81cm`.

**Solar radiation (W/m², averaged over the *preceding* hour):**
`shortwave_radiation`, `direct_radiation`, `diffuse_radiation`,
`direct_normal_irradiance`, `global_tilted_irradiance`, `terrestrial_radiation`.
Add the `_instant` suffix for point-in-time values (e.g.
`shortwave_radiation_instant`). Use `tilt` (0–90°) and `azimuth` (0°=S, −90°=E,
90°=W, ±180°=N) with `global_tilted_irradiance`.

**Additional:** `uv_index`, `uv_index_clear_sky`, `sunshine_duration`,
`wet_bulb_temperature_2m`, `total_column_integrated_water_vapour`, `cape`,
`lifted_index`, `convective_inhibition`, `freezing_level_height`,
`boundary_layer_height`.

**Pressure-level variables** at 19 levels (1000, 975, 950, 925, 900, 850, 800,
700, 600, 500, 400, 300, 250, 200, 150, 100, 70, 50, 30 hPa) — append the level:
`temperature_{L}hPa`, `relative_humidity_{L}hPa`, `cloud_cover_{L}hPa`,
`wind_speed_{L}hPa`, `wind_direction_{L}hPa`, `geopotential_height_{L}hPa`.

## `daily=` variables (one value per day — set `timezone`!)
`weather_code`, `temperature_2m_max`, `temperature_2m_min`,
`temperature_2m_mean`, `apparent_temperature_max|min|mean`, `sunrise`, `sunset`,
`daylight_duration` (s), `sunshine_duration` (s), `uv_index_max`,
`uv_index_clear_sky_max`, `precipitation_sum`, `rain_sum`, `showers_sum`,
`snowfall_sum`, `precipitation_hours`, `precipitation_probability_max|mean|min`,
`wind_speed_10m_max`, `wind_gusts_10m_max`, `wind_direction_10m_dominant`,
`shortwave_radiation_sum`, `et0_fao_evapotranspiration`.

## `minutely_15=` variables (15-minute; native in Central Europe & North America)
`temperature_2m`, `relative_humidity_2m`, `dew_point_2m`,
`apparent_temperature`, `precipitation`, `rain`, `showers`, `snowfall`,
`snowfall_height`, `freezing_level_height`, `sunshine_duration`, `weather_code`,
`wind_speed_10m|80m`, `wind_direction_10m|80m`, `wind_gusts_10m`, `visibility`,
`cape`, `lightning_potential`, and the radiation set (+`_instant`). Windowed by
`forecast_minutely_15` / `past_minutely_15` or `start_minutely_15` /
`end_minutely_15` (`yyyy-mm-ddThh:mm`).

## Time parameters
- `timezone`: `GMT` (default) | IANA name (e.g. `Europe/Berlin`) | `auto`
  (resolve from coordinates — the right choice for daily data).
- `timeformat`: `iso8601` (default) | `unixtime` (epoch seconds, always UTC).
- `forecast_days` 0–16 (default 7); `past_days` 0–92 (default 0).
- `forecast_hours` / `past_hours` for hour-granular sliding windows.
- `start_date` / `end_date` (`yyyy-mm-dd`) for an explicit range; `start_hour` /
  `end_hour` (`yyyy-mm-ddThh:mm`) for an explicit hourly range.

## Models & grid cell
- `models=`: `auto` (default, seamless best mix) or one/more comma-separated IDs:
  `icon_seamless`, `icon_global`, `icon_eu`, `icon_d2`, `gfs_seamless`,
  `gfs_global`, `gfs_hrrr`, `ecmwf_ifs025`, `ecmwf_aifs025_single`,
  `jma_seamless`, `gem_seamless`, `meteofrance_seamless`, `arome_france`,
  `metno_seamless`, `knmi_seamless`, `ukmo_seamless`, `meteoswiss_icon_ch1`, …
  Requesting multiple models **suffixes each variable with the model name**
  (e.g. `temperature_2m_gfs_seamless`).
- `cell_selection`: `land` (default) | `sea` | `nearest`.
- `elevation`: override the grid-cell elevation used for downscaling;
  `elevation=nan` disables statistical downscaling.

## Response shape
Top-level: `latitude`, `longitude` (snapped to grid), `generationtime_ms`,
`utc_offset_seconds`, `timezone`, `timezone_abbreviation`, `elevation`. Then per
block: `current`/`current_units`, `hourly`/`hourly_units`, `daily`/`daily_units`,
`minutely_15`/`minutely_15_units`. `hourly`/`daily` are columnar (`time` array +
one parallel array per variable, index-aligned). `null` where a model lacks data.

## Gotchas
- Hourly radiation is a mean over the *preceding* hour; use `_instant` for
  point-in-time. `is_day` is `1`/`0`, not boolean. `daylight_duration` /
  `sunshine_duration` are seconds.
- Set `timezone` for daily aggregates or day boundaries fall on UTC midnight.
- A typo'd variable → HTTP 400 "Cannot initialize … from invalid String value".
