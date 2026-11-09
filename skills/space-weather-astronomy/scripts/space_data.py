#!/usr/bin/env python3
"""space_data.py — dependency-free CLI for JPL Horizons/CNEOS and NOAA SWPC.

Two very different data worlds, one keyless client (Python stdlib only):

  JPL side (astronomy / solar system)
    horizons  — ephemerides for any planet/moon/asteroid/comet/spacecraft.
                Handles the API's quirk of returning a TEXT report inside JSON
                and extracts the $$SOE..$$EOE data rows for you.
    cad       — asteroid/comet close approaches to Earth (CNEOS), with lunar-
                distance conversion and size estimates from H magnitude.
    fireball  — recent atmospheric fireball events (CNEOS).

  NOAA SWPC side (space weather)
    swpc kp        — planetary K-index, latest values + G-scale interpretation
    swpc scales    — current + 3-day forecast NOAA R/S/G scales
    swpc wind      — real-time solar wind (speed, density, Bz) from DSCOVR
    swpc flares    — latest GOES X-ray flare
    swpc alerts    — active SWPC alerts/watches/warnings
    swpc forecast  — the human-readable 3-day forecast text
    swpc aurora --lat LAT --lon LON — OVATION aurora probability at a point
    swpc get PATH  — any other services.swpc.noaa.gov product, auto-formatted

Examples
--------
  # Where is Mars tonight from a city? (topocentric az/el, magnitude, distance)
  python space_data.py horizons COMMAND=499 --place "San Francisco" \
      START_TIME=2026-07-07 STOP_TIME=2026-07-08 STEP_SIZE="1 h" \
      QUANTITIES=4,9,20 --soe

  # Current Earth-Mars distance (geocentric, one instant)
  python space_data.py horizons COMMAND=499 EPHEM_TYPE=OBSERVER \
      CENTER=500@399 TLIST=2026-07-07 QUANTITIES=20 --soe

  # Asteroids passing within 1 lunar distance this month
  python space_data.py cad dist-max=1LD date-min=2026-07-01 date-max=2026-07-31

  # Space weather now
  python space_data.py swpc scales
  python space_data.py swpc kp --tail 8

No API keys. Data: courtesy NASA/JPL-Caltech (Horizons, CNEOS) and NOAA SWPC.
"""
import argparse
import json
import math
import sys
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone

HORIZONS = "https://ssd.jpl.nasa.gov/api/horizons.api"
SSD = "https://ssd-api.jpl.nasa.gov/{}.api"
SWPC = "https://services.swpc.noaa.gov"
GEOCODE = "https://geocoding-api.open-meteo.com/v1/search"

AU_KM = 149_597_870.7
LD_KM = 384_400.0


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def http_get(url, timeout=90):
    req = urllib.request.Request(url, headers={"User-Agent": "space_data.py/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:400]
        die(f"HTTP {e.code}: {body or e.reason}\nURL: {url}")
    except urllib.error.URLError as e:
        die(f"network error: {e.reason}\nURL: {url}")


def get_json(url):
    raw = http_get(url)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        die(f"expected JSON, got: {raw[:200]!r}\nURL: {url}")


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


def geocode(place):
    data = get_json(f"{GEOCODE}?name={urllib.parse.quote(place)}&count=1&format=json")
    res = data.get("results") or []
    if not res:
        die(f"could not geocode --place '{place}'")
    r = res[0]
    print(f"# {place} -> lat={r['latitude']} lon={r['longitude']} elev={r.get('elevation', 0)}m "
          f"({r.get('name')}, {r.get('country','')})", file=sys.stderr)
    return r["latitude"], r["longitude"], (r.get("elevation") or 0) / 1000.0  # alt in km


# ---------------- JPL Horizons ----------------
def cmd_horizons(args):
    params = {"format": "json"}
    for p in args.params:
        if "=" not in p:
            die(f"parameter '{p}' must be KEY=value")
        k, v = p.split("=", 1)
        params[k.upper() if k.lower() != "format" else "format"] = v
    if args.place:
        lat, lon, alt_km = geocode(args.place)
        # Topocentric site: CENTER='coord@399' + SITE_COORD='E-lon,lat,alt(km)'
        params.setdefault("CENTER", "coord@399")
        params.setdefault("SITE_COORD", f"{lon},{lat},{alt_km:.3f}")
    # Horizons prepends pages of physical data by default; keep output lean
    # unless the caller explicitly asked for the object-data page.
    if params.get("MAKE_EPHEM", "YES").strip("'\"").upper() != "NO":
        params.setdefault("OBJ_DATA", "NO")
    # Horizons expects values single-quoted; urlencode handles the rest.
    qs = urllib.parse.urlencode({k: f"'{v}'" if k != "format" else v for k, v in params.items()},
                                quote_via=urllib.parse.quote)
    url = f"{HORIZONS}?{qs}"
    if args.print_url:
        print(url)
        return
    data = get_json(url)
    if "error" in data:
        die(f"Horizons error: {data['error']}\nURL: {url}")
    result = data.get("result", "")
    if args.json:
        print(json.dumps(data, indent=2))
        return
    if args.soe:
        # Extract the ephemeris rows between $$SOE and $$EOE (the data lives
        # inside a plain-text report embedded in the JSON).
        if "$$SOE" not in result:
            print(result, file=sys.stderr)
            die("no $$SOE ephemeris block in the response — see the report above "
                "(often a parameter problem or an ambiguous-name match list).")
        block = result.split("$$SOE", 1)[1].split("$$EOE", 1)[0].strip("\n")
        # also show the column header line(s) just above $$SOE for context
        head = result.split("$$SOE", 1)[0].rstrip().splitlines()
        for line in reversed(head[-6:]):
            if line.strip() and not set(line.strip()) <= {"*", "-", " "}:
                print(f"# columns: {line.strip()}", file=sys.stderr)
                break
        print(block)
    else:
        print(result)


# ---------------- CNEOS: close approaches & fireballs ----------------
def h_to_diameter(h):
    """Estimate diameter range (m) from absolute magnitude H (albedo 0.25–0.05)."""
    try:
        h = float(h)
    except (TypeError, ValueError):
        return ""
    d_min = 1329 / math.sqrt(0.25) * 10 ** (-h / 5) * 1000  # bright surface -> smaller
    d_max = 1329 / math.sqrt(0.05) * 10 ** (-h / 5) * 1000  # dark surface -> bigger
    if d_max >= 1000:
        return f"~{d_min/1000:.1f}-{d_max/1000:.1f} km"
    return f"~{d_min:.0f}-{d_max:.0f} m"


def cmd_cad(args):
    qs = "&".join(args.params) if args.params else ""
    url = SSD.format("cad") + ("?" + qs if qs else "")
    data = get_json(url)
    fields = data.get("fields", [])
    rows = data.get("data") or []
    print(f"# {data.get('count', len(rows))} close approaches", file=sys.stderr)
    if not rows:
        print("(none matched)")
        return
    idx = {f: i for i, f in enumerate(fields)}
    out = []
    for r in rows:
        dist_au = float(r[idx["dist"]])
        out.append([
            r[idx["des"]],
            r[idx["cd"]],
            f"{dist_au * AU_KM / LD_KM:.2f}",
            f"{dist_au * AU_KM:,.0f}",
            f"{float(r[idx['v_rel']]):.1f}",
            str(r[idx["h"]]),
            h_to_diameter(r[idx["h"]]),
        ])
    print_table(["object", "closest (TDB)", "dist (LD)", "dist (km)", "v_rel km/s", "H", "est. size"], out)


def cmd_fireball(args):
    qs = "&".join(args.params) if args.params else "limit=10&sort=-date"
    data = get_json(SSD.format("fireball") + "?" + qs)
    fields = data.get("fields", [])
    rows = data.get("data") or []
    print(f"# {data.get('count', len(rows))} fireballs", file=sys.stderr)
    idx = {f: i for i, f in enumerate(fields)}
    out = []
    for r in rows:
        def g(k):
            v = r[idx[k]] if k in idx else None
            return "" if v is None else str(v)
        out.append([g("date"), g("energy"), g("impact-e"), g("lat") + (g("lat-dir") or ""),
                    g("lon") + (g("lon-dir") or ""), g("alt"), g("vel")])
    print_table(["date (UTC)", "energy (kt rad.)", "impact (kt)", "lat", "lon", "alt km", "vel km/s"], out)


# ---------------- NOAA SWPC ----------------
def kp_to_g(kp):
    kp = float(kp)
    if kp >= 9: return "G5 extreme storm"
    if kp >= 8: return "G4 severe storm"
    if kp >= 7: return "G3 strong storm"
    if kp >= 6: return "G2 moderate storm"
    if kp >= 5: return "G1 minor storm"
    if kp >= 4: return "active"
    return "quiet"


def swpc_json(path):
    return get_json(SWPC + path)


def columnar_rows(data):
    """Normalize SWPC list products. Two shapes exist:
    - array-of-arrays with a header row (older /products style)
    - array-of-objects (e.g. the current noaa-planetary-k-index.json)
    Returns (headers, rows-of-lists) either way."""
    if isinstance(data, list) and data:
        if isinstance(data[0], list):
            return data[0], data[1:]
        if isinstance(data[0], dict):
            hdr = list(data[0].keys())
            return hdr, [[d.get(k) for k in hdr] for d in data]
    return None, None


def cmd_swpc(args):
    p = args.product
    if p == "kp":
        data = swpc_json("/products/noaa-planetary-k-index.json")
        hdr, rows = columnar_rows(data)
        ti, ki = hdr.index("time_tag"), hdr.index("Kp")
        out = [[str(r[ti]), str(r[ki]), kp_to_g(r[ki])] for r in rows[-args.tail:]]
        print_table(["time (UTC, 3-hr)", "Kp", "level"], out)
    elif p == "kp-forecast":
        data = swpc_json("/products/noaa-planetary-k-index-forecast.json")
        hdr, rows = columnar_rows(data)
        out = [[str(c) for c in r] + [kp_to_g(r[1])] for r in rows[-args.tail:]]
        print_table(hdr + ["level"], out)
    elif p == "scales":
        data = swpc_json("/products/noaa-scales.json")
        # keyed object: "0"=today obs, "1".."3"=forecast days, "-1"=yesterday
        order = [k for k in ("-1", "0", "1", "2", "3") if k in data]
        out = []
        for k in order:
            d = data[k]
            when = d.get("DateStamp", "") + (" (obs)" if k in ("-1", "0") else " (fcst)")
            def s(scale):
                v = d.get(scale) or {}
                sc = v.get("Scale")
                return f"{scale}{sc}" if sc not in (None, "0", 0) else "-"
            out.append([when, s("R"), s("S"), s("G"),
                        (d.get("G") or {}).get("Text", "")])
        print_table(["day", "radio", "radiation", "geomagnetic", "G text"], out)
    elif p == "wind":
        speed = swpc_json("/products/summary/solar-wind-speed.json")
        mag = swpc_json("/products/summary/solar-wind-mag-field.json")
        sp = speed[0] if isinstance(speed, list) else speed
        mg = mag[0] if isinstance(mag, list) else mag
        print(f"solar wind @ {sp.get('time_tag','')} (real-time, L1):")
        print(f"  speed   : {sp.get('proton_speed')} km/s")
        print(f"  Bz (GSM): {mg.get('bz_gsm')} nT   Bt: {mg.get('bt')} nT")
        print("  (storm fuel = speed >500-600 km/s and/or strongly negative Bz < -10 nT)")
        print("  1-min series: /json/rtsw/rtsw_wind_1m.json and rtsw_mag_1m.json")
    elif p == "flares":
        data = swpc_json("/json/goes/primary/xray-flares-latest.json")
        items = data if isinstance(data, list) else [data]
        for d in items[:3]:
            print(json.dumps(d, indent=2))
    elif p == "alerts":
        data = swpc_json("/products/alerts.json")
        for d in data[: args.tail]:
            msg = (d.get("message") or "").strip().replace("\r", "")
            print(f"=== {d.get('issue_datetime','')} ===")
            print("\n".join(msg.splitlines()[:10]))
            print()
    elif p == "forecast":
        print(http_get(SWPC + "/text/3-day-forecast.txt").decode("utf-8", "replace"))
    elif p == "aurora":
        if args.lat is None or args.lon is None:
            die("aurora needs --lat and --lon")
        data = swpc_json("/json/ovation_aurora_latest.json")  # ~1-2 MB grid
        lon = args.lon % 360
        best, prob = None, 0
        for c in data.get("coordinates", []):
            if abs(c[0] - lon) <= 0.5 and abs(c[1] - args.lat) <= 0.5:
                best, prob = c, c[2]
                break
        print(f"OVATION forecast {data.get('Forecast Time','')}")
        print(f"aurora probability at ({args.lat}, {args.lon}): {prob}%")
    elif p == "get":
        if not args.path:
            die("swpc get needs a PATH like /products/noaa-planetary-k-index.json")
        raw = http_get(SWPC + args.path)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            print(raw.decode("utf-8", "replace"))
            return
        hdr, rows = columnar_rows(data)
        if hdr:
            print_table(hdr, [[str(c) for c in r] for r in rows[-args.tail:]])
        else:
            print(json.dumps(data, indent=2)[:8000])
    else:
        die(f"unknown swpc product '{p}'")


def main():
    ap = argparse.ArgumentParser(
        prog="space_data.py",
        description="Keyless CLI for JPL Horizons/CNEOS (astronomy) and NOAA SWPC (space weather). All times UTC.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    h = sub.add_parser("horizons", help="JPL Horizons ephemeris (KEY=value params, e.g. COMMAND=499)")
    h.add_argument("params", nargs="*", help="Horizons params, e.g. COMMAND=499 START_TIME=2026-07-07 QUANTITIES=4,9,20")
    h.add_argument("--place", help="geocode a place and observe from there (topocentric CENTER/SITE_COORD)")
    h.add_argument("--soe", action="store_true", help="print only the $$SOE..$$EOE ephemeris rows")
    h.add_argument("--json", action="store_true", help="raw JSON envelope")
    h.add_argument("--print-url", action="store_true")
    h.set_defaults(func=cmd_horizons)

    c = sub.add_parser("cad", help="CNEOS close approaches (key=value params, e.g. dist-max=1LD)")
    c.add_argument("params", nargs="*", help="e.g. dist-max=1LD date-min=2026-07-01 date-max=2026-07-31")
    c.set_defaults(func=cmd_cad)

    f = sub.add_parser("fireball", help="CNEOS fireball events")
    f.add_argument("params", nargs="*", help="e.g. limit=10 sort=-date")
    f.set_defaults(func=cmd_fireball)

    s = sub.add_parser("swpc", help="NOAA SWPC products")
    s.add_argument("product", choices=["kp", "kp-forecast", "scales", "wind", "flares", "alerts", "forecast", "aurora", "get"])
    s.add_argument("path", nargs="?", help="for 'get': a services.swpc.noaa.gov path")
    s.add_argument("--tail", type=int, default=8, help="rows/items to show (default 8)")
    s.add_argument("--lat", type=float, help="for 'aurora'")
    s.add_argument("--lon", type=float, help="for 'aurora'")
    s.set_defaults(func=cmd_swpc)

    args, unknown = ap.parse_known_args()
    # argparse won't intersperse KEY=value positionals with flags; recover them.
    stray = [u for u in unknown if "=" in u and not u.startswith("-")]
    bad = [u for u in unknown if u not in stray]
    if bad:
        ap.error(f"unrecognized arguments: {' '.join(bad)}")
    if hasattr(args, "params"):
        args.params = list(args.params) + stray
    elif stray:
        ap.error(f"unexpected parameters: {' '.join(stray)}")
    args.func(args)


if __name__ == "__main__":
    main()
