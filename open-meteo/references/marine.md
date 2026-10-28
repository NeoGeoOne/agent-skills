# Marine Weather API — reference

Base URL: `https://marine-api.open-meteo.com/v1/marine` (alias `marine`).
Ocean waves, swell, currents, and sea-surface conditions from global/regional
wave models (ECMWF WAM, DWD GWAM/EWAM, MeteoFrance MFWAM/currents, NCEP
GFS-Wave). Same request/response grammar as the Forecast API.

## Coverage caveat — oceans only (the #1 marine gotcha)
Data exists **only over water**. The API snaps to the nearest wave-model cell.
Points on land or too far inland return `null` for every timestep — verified
even with `cell_selection=sea`. For a coastal location, nudge the coordinate a
few km seaward and/or set `cell_selection=sea`. If a place-name geocode lands you
inland (a city center), move the point offshore before querying.

## Required
`latitude`, `longitude` (comma-separate for bulk). Supply at least one of
`current=`, `hourly=`, `daily=`.

## Hourly / current variables
Directions in ° (0–360, direction *from*); periods in seconds; heights in m or
ft per `length_unit`.
- **Total sea state:** `wave_height`, `wave_direction`, `wave_period`.
- **Wind waves:** `wind_wave_height`, `wind_wave_direction`, `wind_wave_period`,
  `wind_wave_peak_period`.
- **Swell (primary):** `swell_wave_height`, `swell_wave_direction`,
  `swell_wave_period`, `swell_wave_peak_period`.
- **Secondary/tertiary swell** (only some models):
  `secondary_swell_wave_height|direction|period|peak_period`,
  `tertiary_swell_wave_height|direction|period|peak_period`.
- **Ocean / sea level** (model-dependent): `ocean_current_velocity` (uses
  `wind_speed_unit`), `ocean_current_direction` (direction *toward*),
  `sea_surface_temperature` (°C), `sea_level_height_msl` (tide vs MSL; can be
  negative), `invert_barometer_height`.

## Daily variables
Heights/periods are daily **maxima**; directions are daily **dominant**:
`wave_height_max`, `wave_direction_dominant`, `wave_period_max`,
`wind_wave_height_max`, `wind_wave_direction_dominant`, `wind_wave_period_max`,
`wind_wave_peak_period_max`, `swell_wave_height_max`,
`swell_wave_direction_dominant`, `swell_wave_period_max`,
`swell_wave_peak_period_max`.

## Params
- `length_unit`: `metric` (m, default) | `imperial` (ft). Affects **only**
  wave/swell heights, `sea_level_height_msl`, `invert_barometer_height`. Does
  NOT convert `ocean_current_velocity` (that uses `wind_speed_unit`), SST
  (always °C unless `temperature_unit=fahrenheit`), directions, or periods.
- `wind_speed_unit`: `kmh` (default) | `ms` | `mph` | `kn` — governs
  `ocean_current_velocity`.
- `cell_selection`: `nearest` (default) | `sea` | `land`.
- `forecast_days` 0–16 (default 7); `past_days` 0+; `start_date`/`end_date`.
- `timezone` (GMT default | auto | IANA), `temperature_unit`, `timeformat`.
- `models`: `best_match` (default), `ecmwf_wam025`, `gwam`, `ewam` (Europe,
  higher-res), `meteofrance_wave` (richer swell partitions),
  `meteofrance_currents` (source of `ocean_current_*`), `ncep_gfswave025`,
  `ncep_gfswave016`, `era5_ocean` (historical).

## Model-availability quirk (not an error)
When a chosen model doesn't produce a requested variable, Open-Meteo returns it
with unit `"undefined"` and **all-`null` values** instead of erroring (e.g.
`ewam` returns `tertiary_swell_*` and `ocean_current_velocity` as undefined).
Ocean currents / SST / secondary+tertiary swell come from specific models — if
you need them, pick a model that carries them (`meteofrance_wave`,
`meteofrance_currents`).

## Response / errors
Standard shape: metadata + `current`/`hourly`/`daily` with paired `*_units`.
Errors HTTP 400 `{"error":true,"reason":...}` (bad `cell_selection`,
`forecast_days` out of 0–16, lat/lon length mismatch, bad `models`). Commercial
host: `customer-marine-api.open-meteo.com` with `&apikey=`.
