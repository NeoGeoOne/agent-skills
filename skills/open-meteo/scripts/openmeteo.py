#!/usr/bin/env python3
"""openmeteo.py — a dependency-free command-line client for every Open-Meteo API.

Why this exists: every Open-Meteo task repeats the same plumbing — turn a place
name into coordinates, build a query string, call the right host, handle the
`{"error":true,"reason":...}` body, and line up parallel arrays into something a
human can read. This script does all of that with the Python standard library
only (urllib), so it runs anywhere Python 3 does with no `pip install`.

The free Open-Meteo tier needs no API key. For a commercial key, pass
`apikey=YOUR_KEY` and set `--host customer` (routes to customer-api.open-meteo.com).

Common uses
-----------
  # Resolve a place to coordinates (top matches)
  python openmeteo.py geocode "Tokyo"

  # 7-day daily forecast for a place, as an aligned table with decoded weather
  python openmeteo.py fetch forecast --place "Tokyo" \
      daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max \
      timezone=auto forecast_days=7 --table --decode

  # Any endpoint by alias or full URL, with raw JSON out
  python openmeteo.py fetch air-quality latitude=28.61 longitude=77.21 \
      current=pm2_5,us_aqi

  # The WMO weather_code -> text table
  python openmeteo.py codes

Endpoint aliases (see fetch --help): forecast, archive/historical,
historical-forecast, air-quality, marine, climate, flood, ensemble,
elevation, geocoding. A full https URL also works in place of an alias.
"""
import argparse
import json
import sys
import urllib.parse
import urllib.request
import urllib.error

# --- Endpoint registry ------------------------------------------------------
# Each Open-Meteo product lives on its own host but shares the same query
# conventions. "free" hosts need no key; the customer host takes &apikey=.
HOSTS = {"free": "api.open-meteo.com", "customer": "customer-api.open-meteo.com"}

ENDPOINTS = {
    "forecast":            ("free",     "/v1/forecast"),
    "archive":             ("archive",  "/v1/archive"),
    "historical":          ("archive",  "/v1/archive"),   # alias
    "historical-forecast": ("hist-fc",  "/v1/forecast"),
    "air-quality":         ("air",      "/v1/air-quality"),
    "marine":              ("marine",   "/v1/marine"),
    "climate":             ("climate",  "/v1/climate"),
    "flood":               ("flood",    "/v1/flood"),
    "ensemble":            ("ensemble", "/v1/ensemble"),
    "elevation":           ("free",     "/v1/elevation"),
    "geocoding":           ("geo",      "/v1/search"),
}
# Product hosts that are fixed (not switchable via --host). The free/customer
# split only applies to the general forecast + elevation endpoints.
SPECIAL_HOSTS = {
    "archive":   "archive-api.open-meteo.com",
    "hist-fc":   "historical-forecast-api.open-meteo.com",
    "air":       "air-quality-api.open-meteo.com",
    "marine":    "marine-api.open-meteo.com",
    "climate":   "climate-api.open-meteo.com",
    "flood":     "flood-api.open-meteo.com",
    "ensemble":  "ensemble-api.open-meteo.com",
    "geo":       "geocoding-api.open-meteo.com",
}

# --- WMO weather interpretation codes --------------------------------------
WMO = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Light freezing drizzle", 57: "Dense freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Slight snowfall", 73: "Moderate snowfall", 75: "Heavy snowfall",
    77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}


def resolve_url(endpoint, host_choice):
    """Turn an alias (or a full URL) into a concrete https URL base."""
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        return endpoint
    if endpoint not in ENDPOINTS:
        die(f"unknown endpoint '{endpoint}'. Known: {', '.join(ENDPOINTS)} — or pass a full https URL.")
    host_key, path = ENDPOINTS[endpoint]
    host = HOSTS[host_choice] if host_key == "free" else SPECIAL_HOSTS[host_key]
    return f"https://{host}{path}"


def http_get(url):
    """GET a URL, returning parsed JSON. Surfaces Open-Meteo's error body clearly."""
    req = urllib.request.Request(url, headers={"User-Agent": "openmeteo.py/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            reason = json.loads(raw).get("reason", raw)
        except Exception:
            reason = raw
        die(f"HTTP {e.code} from Open-Meteo: {reason}\nURL: {url}")
    except urllib.error.URLError as e:
        die(f"network error: {e.reason}\nURL: {url}")
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return body  # e.g. CSV when format=csv was requested
    if isinstance(data, dict) and data.get("error"):
        die(f"Open-Meteo error: {data.get('reason', data)}\nURL: {url}")
    return data


def build_url(base, params):
    """params: list of 'key=value' strings. Values are passed through verbatim
    (already comma-joined for lists) and URL-encoded safely."""
    pairs = []
    for p in params:
        if "=" not in p:
            die(f"parameter '{p}' must be key=value")
        k, v = p.split("=", 1)
        pairs.append((k, v))
    qs = urllib.parse.urlencode(pairs, safe=",:")
    sep = "&" if "?" in base else "?"
    return f"{base}{sep}{qs}" if qs else base


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


# --- Table / CSV rendering --------------------------------------------------
TIMESERIES_BLOCKS = ("minutely_15", "hourly", "daily")


def flatten_block(block, decode=False):
    """A block is {'time':[...], var:[...], ...}. Return (headers, rows)."""
    keys = [k for k in block.keys() if k != "time"]
    headers = ["time"] + keys
    rows = []
    n = len(block.get("time", []))
    for i in range(n):
        row = [str(block["time"][i])]
        for k in keys:
            col = block[k]
            row.append("" if i >= len(col) or col[i] is None else str(col[i]))
        rows.append(row)
    if decode and "weather_code" in keys:
        wc_idx = headers.index("weather_code")
        headers.insert(wc_idx + 1, "weather")
        for row in rows:
            try:
                row.insert(wc_idx + 1, WMO.get(int(float(row[wc_idx])), "?"))
            except (ValueError, TypeError):
                row.insert(wc_idx + 1, "?")
    return headers, rows


def print_table(headers, rows):
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    fmt = "  ".join("{:<%d}" % w for w in widths)
    print(fmt.format(*headers))
    print(fmt.format(*["-" * w for w in widths]))
    for row in rows:
        print(fmt.format(*row))


def print_csv(headers, rows):
    import csv
    w = csv.writer(sys.stdout)
    w.writerow(headers)
    w.writerows(rows)


def render_timeseries(data, as_csv=False, decode=False):
    """Print every time-series block present as its own table/CSV."""
    printed = False
    for name in TIMESERIES_BLOCKS:
        if isinstance(data, dict) and name in data and isinstance(data[name], dict):
            headers, rows = flatten_block(data[name], decode=decode)
            if not as_csv:
                print(f"== {name} ==")
            (print_csv if as_csv else print_table)(headers, rows)
            if not as_csv:
                print()
            printed = True
    if isinstance(data, dict) and "current" in data and isinstance(data["current"], dict):
        cur = data["current"]
        if not as_csv:
            print("== current ==")
        items = list(cur.items())
        if decode and "weather_code" in cur:
            try:
                items.append(("weather", WMO.get(int(float(cur["weather_code"])), "?")))
            except (ValueError, TypeError):
                pass
        (print_csv if as_csv else print_table)(["field", "value"], [[k, str(v)] for k, v in items])
        printed = True
    if not printed:
        die("no time-series (hourly/daily/minutely_15/current) block found to tabulate; drop --table to see raw JSON.")


# --- Subcommands ------------------------------------------------------------
def cmd_geocode(args):
    base = f"https://{SPECIAL_HOSTS['geo']}/v1/search"
    url = build_url(base, [
        f"name={args.name}", f"count={args.count}",
        f"language={args.language}", "format=json",
    ])
    data = http_get(url)
    results = data.get("results", []) if isinstance(data, dict) else []
    if not results:
        die(f"no geocoding matches for '{args.name}'. Try a shorter or more specific name.")
    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return
    headers = ["name", "admin1", "country", "lat", "lon", "elev", "timezone", "population"]
    rows = [[
        str(r.get("name", "")), str(r.get("admin1", "")), str(r.get("country", "")),
        str(r.get("latitude", "")), str(r.get("longitude", "")), str(r.get("elevation", "")),
        str(r.get("timezone", "")), str(r.get("population", "")),
    ] for r in results]
    print_table(headers, rows)
    top = results[0]
    print(f"\nTop match: {top.get('name')} -> latitude={top.get('latitude')} longitude={top.get('longitude')}")


def cmd_fetch(args):
    params = list(args.params)
    # --place geocodes and injects latitude/longitude so the caller can name a city.
    if args.place:
        geo = f"https://{SPECIAL_HOSTS['geo']}/v1/search"
        gd = http_get(build_url(geo, [f"name={args.place}", "count=1", "format=json"]))
        res = gd.get("results", []) if isinstance(gd, dict) else []
        if not res:
            die(f"could not geocode --place '{args.place}'")
        lat, lon = res[0]["latitude"], res[0]["longitude"]
        params = [f"latitude={lat}", f"longitude={lon}"] + params
        print(f"# {args.place} -> latitude={lat} longitude={lon} ({res[0].get('name')}, {res[0].get('country','')})",
              file=sys.stderr)
    base = resolve_url(args.endpoint, args.host)
    url = build_url(base, params)
    if args.print_url:
        print(url)
        return
    data = http_get(url)
    if args.table or args.csv:
        render_timeseries(data, as_csv=args.csv, decode=args.decode)
    elif isinstance(data, str):
        print(data)
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_codes(args):
    print("WMO weather interpretation codes (weather_code):")
    for code in sorted(WMO):
        print(f"  {code:>2}  {WMO[code]}")


def main():
    p = argparse.ArgumentParser(
        prog="openmeteo.py",
        description="Dependency-free client for the Open-Meteo API family (no API key needed).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Endpoint aliases: " + ", ".join(ENDPOINTS) + " (or a full https URL).",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("geocode", help="resolve a place name to coordinates")
    g.add_argument("name")
    g.add_argument("--count", type=int, default=5)
    g.add_argument("--language", default="en")
    g.add_argument("--json", action="store_true", help="raw JSON instead of a table")
    g.set_defaults(func=cmd_geocode)

    f = sub.add_parser("fetch", help="call any Open-Meteo endpoint with key=value params")
    f.add_argument("endpoint", help="alias (forecast, archive, air-quality, marine, climate, flood, ensemble, elevation, geocoding) or a full https URL")
    f.add_argument("params", nargs="*", help="key=value pairs, e.g. latitude=52.5 longitude=13.4 hourly=temperature_2m")
    f.add_argument("--place", help="geocode this place name and inject latitude/longitude")
    f.add_argument("--host", choices=list(HOSTS), default="free", help="free (default) or customer (needs apikey=)")
    f.add_argument("--table", action="store_true", help="render hourly/daily/current blocks as aligned tables")
    f.add_argument("--csv", action="store_true", help="render blocks as CSV")
    f.add_argument("--decode", action="store_true", help="add a text column for weather_code")
    f.add_argument("--print-url", action="store_true", help="print the built URL and exit (don't call)")
    f.set_defaults(func=cmd_fetch)

    c = sub.add_parser("codes", help="print the WMO weather_code -> text table")
    c.set_defaults(func=cmd_codes)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
