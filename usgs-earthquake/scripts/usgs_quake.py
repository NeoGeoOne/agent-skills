#!/usr/bin/env python3
"""usgs_quake.py — a dependency-free command-line client for the USGS Earthquake API.

Every earthquake task repeats the same plumbing: build an FDSN query or grab a
real-time feed, then untangle GeoJSON where time is epoch-milliseconds and the
geometry is [longitude, latitude, depth] (not lat,lon!). This script does all of
that with the Python standard library only (urllib) — no `pip install`, no API
key (USGS data is public domain; please attribute the USGS).

Commands
--------
  # Real-time summary feed: {mag}_{period}, mag in significant|4.5|2.5|1.0|all,
  # period in hour|day|week|month
  python usgs_quake.py feed significant_week
  python usgs_quake.py feed 4.5_day --table

  # Generic FDSN query with key=value params (see the reference for all of them).
  # --count hits the /count endpoint first (do this before big pulls!).
  python usgs_quake.py query starttime=2024-01-01 endtime=2024-01-08 minmagnitude=6 --table
  python usgs_quake.py query --near "Los Angeles" maxradiuskm=100 minmagnitude=3 \
      starttime=2024-01-01 --table
  python usgs_quake.py query minmagnitude=4.5 minlatitude=32 maxlatitude=42 \
      minlongitude=-125 maxlongitude=-114 starttime=2023-01-01 endtime=2024-01-01 \
      --count
  python usgs_quake.py query minmagnitude=4.5 ... --csv --out quakes.csv

  # One event's full detail (magnitude, alert, tsunami flag, products list)
  python usgs_quake.py event us6000jllz

`--near "<place>"` resolves a place name to latitude/longitude via the free,
keyless Open-Meteo geocoder as a convenience (USGS has no geocoder). Pair it
with maxradiuskm=. All times are UTC.
"""
import argparse
import json
import sys
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone

QUERY = "https://earthquake.usgs.gov/fdsnws/event/1/query"
COUNT = "https://earthquake.usgs.gov/fdsnws/event/1/count"
FEED = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/{}.geojson"
GEOCODE = "https://geocoding-api.open-meteo.com/v1/search"

FEED_MAGS = ("significant", "4.5", "2.5", "1.0", "all")
FEED_PERIODS = ("hour", "day", "week", "month")


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def http_get(url):
    """GET a URL. Returns bytes. Surfaces USGS error bodies (incl. the 20000-limit 400)."""
    req = urllib.request.Request(url, headers={"User-Agent": "usgs_quake.py/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace").strip()
        hint = ""
        if e.code == 400 and "20000" in body:
            hint = "\nhint: narrow the time window / area / magnitude, or run with --count first and paginate (limit + offset)."
        if e.code in (204, 404):
            hint = "\n(no events matched your filters.)"
        die(f"HTTP {e.code} from USGS: {body or e.reason}{hint}\nURL: {url}")
    except urllib.error.URLError as e:
        die(f"network error: {e.reason}\nURL: {url}")


def get_json(url):
    raw = http_get(url)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        snippet = raw.decode("utf-8", "replace").strip()[:200]
        die(f"expected JSON but USGS returned something else (transient server error?): {snippet}\nURL: {url}")


def build_query_url(base, params):
    """params: list of 'key=value' strings, passed through verbatim (URL-encoded)."""
    pairs = []
    for p in params:
        if "=" not in p:
            die(f"parameter '{p}' must be key=value")
        k, v = p.split("=", 1)
        pairs.append((k, v))
    qs = urllib.parse.urlencode(pairs, safe=",:+-")
    sep = "&" if "?" in base else "?"
    return f"{base}{sep}{qs}" if qs else base


def geocode(place):
    url = build_query_url(GEOCODE, [f"name={place}", "count=1", "format=json"])
    data = get_json(url)
    res = data.get("results", []) if isinstance(data, dict) else []
    if not res:
        die(f"could not geocode --near '{place}'")
    r = res[0]
    print(f"# {place} -> latitude={r['latitude']} longitude={r['longitude']} "
          f"({r.get('name')}, {r.get('country','')})", file=sys.stderr)
    return r["latitude"], r["longitude"]


ALERT = {"green": "GREEN", "yellow": "YELLOW", "orange": "ORANGE", "red": "RED"}


def ms_to_utc(ms):
    if ms is None:
        return ""
    try:
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError, OverflowError):
        return str(ms)


def feature_rows(features):
    """Turn GeoJSON features into (headers, rows). Time is epoch-ms UTC;
    geometry coordinates are [lon, lat, depth_km]."""
    headers = ["time (UTC)", "mag", "type", "depth_km", "alert", "tsu", "place", "id"]
    rows = []
    for f in features:
        p = f.get("properties", {}) or {}
        g = (f.get("geometry") or {}).get("coordinates") or [None, None, None]
        depth = g[2] if len(g) > 2 else None
        rows.append([
            ms_to_utc(p.get("time")),
            "" if p.get("mag") is None else f"{p.get('mag'):.1f}",
            str(p.get("magType") or ""),
            "" if depth is None else f"{depth:.0f}",
            ALERT.get(p.get("alert"), ""),
            "Y" if p.get("tsunami") else "",
            str(p.get("place") or ""),
            str(f.get("id") or ""),
        ])
    return headers, rows


def print_table(headers, rows):
    widths = [len(h) for h in headers]
    for row in rows:
        for i, c in enumerate(row):
            widths[i] = max(widths[i], len(c))
    fmt = "  ".join("{:<%d}" % w for w in widths)
    print(fmt.format(*headers))
    print(fmt.format(*["-" * w for w in widths]))
    for row in rows:
        print(fmt.format(*row))


def cmd_feed(args):
    name = args.name
    if "_" not in name or name.rsplit("_", 1)[0] not in FEED_MAGS or name.rsplit("_", 1)[1] not in FEED_PERIODS:
        die(f"feed name must be <mag>_<period>; mag in {FEED_MAGS}, period in {FEED_PERIODS} (e.g. significant_week)")
    data = get_json(FEED.format(name))
    meta = data.get("metadata", {})
    feats = data.get("features", [])
    print(f"# {meta.get('title','USGS feed')} — {meta.get('count', len(feats))} events "
          f"(generated {ms_to_utc(meta.get('generated'))})", file=sys.stderr)
    if args.table or not args.json:
        h, r = feature_rows(feats)
        print_table(h, r)
    else:
        print(json.dumps(data, indent=2))


def cmd_query(args):
    params = list(args.params)
    if args.near:
        lat, lon = geocode(args.near)
        params = [f"latitude={lat}", f"longitude={lon}"] + params
    if args.count:
        url = build_query_url(COUNT, params + ["format=geojson"])
        data = get_json(url)
        print(data.get("count", data))
        return
    if args.csv:
        url = build_query_url(QUERY, [p for p in params if not p.startswith("format=")] + ["format=csv"])
        text = http_get(url).decode("utf-8", "replace")
        if args.out:
            with open(args.out, "w") as f:
                f.write(text)
            print(f"# wrote {text.count(chr(10))} lines to {args.out}", file=sys.stderr)
        else:
            print(text)
        return
    url = build_query_url(QUERY, [p for p in params if not p.startswith("format=")] + ["format=geojson"])
    if args.print_url:
        print(url)
        return
    data = get_json(url)
    feats = data.get("features", [])
    meta = data.get("metadata", {})
    print(f"# {meta.get('count', len(feats))} events matched", file=sys.stderr)
    if args.table:
        h, r = feature_rows(feats)
        print_table(h, r)
    else:
        print(json.dumps(data, indent=2))


def cmd_event(args):
    url = build_query_url(QUERY, [f"eventid={args.eventid}", "format=geojson"])
    data = get_json(url)
    p = data.get("properties", {}) or {}
    g = (data.get("geometry") or {}).get("coordinates") or [None, None, None]
    print(f"Event {data.get('id')}: {p.get('title')}")
    print(f"  time (UTC): {ms_to_utc(p.get('time'))}")
    print(f"  magnitude : {p.get('mag')} {p.get('magType') or ''}")
    print(f"  location  : lat {g[1]}, lon {g[0]}, depth {g[2]} km")
    print(f"  place     : {p.get('place')}")
    print(f"  alert     : {p.get('alert')}   tsunami flag: {p.get('tsunami')}   significance: {p.get('sig')}")
    print(f"  felt      : {p.get('felt')} reports   cdi: {p.get('cdi')}   mmi: {p.get('mmi')}")
    print(f"  status    : {p.get('status')}   url: {p.get('url')}")
    prods = list((p.get("products") or {}).keys())
    if prods:
        print(f"  products  : {', '.join(sorted(prods))}")


def main():
    ap = argparse.ArgumentParser(
        prog="usgs_quake.py",
        description="Dependency-free client for the USGS Earthquake API (no key needed; times are UTC).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("feed", help="fetch a real-time summary feed, e.g. significant_week")
    f.add_argument("name", help="<mag>_<period> — mag: significant|4.5|2.5|1.0|all, period: hour|day|week|month")
    f.add_argument("--table", action="store_true")
    f.add_argument("--json", action="store_true", help="raw GeoJSON instead of a table")
    f.set_defaults(func=cmd_feed)

    q = sub.add_parser("query", help="FDSN event query with key=value params")
    q.add_argument("params", nargs="*", help="e.g. starttime=2024-01-01 minmagnitude=6 maxradiuskm=100")
    q.add_argument("--near", help="geocode this place to latitude/longitude (pair with maxradiuskm=)")
    q.add_argument("--count", action="store_true", help="return only the number of matching events (do this before big pulls)")
    q.add_argument("--table", action="store_true", help="render matched events as a table")
    q.add_argument("--csv", action="store_true", help="request format=csv (use --out to save)")
    q.add_argument("--out", help="write output to this file")
    q.add_argument("--print-url", action="store_true", help="print the built URL and exit")
    q.set_defaults(func=cmd_query)

    e = sub.add_parser("event", help="fetch one event's detail by eventid")
    e.add_argument("eventid")
    e.set_defaults(func=cmd_event)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
