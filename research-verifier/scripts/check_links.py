#!/usr/bin/env python3
"""Check URLs you intend to cite: do they resolve, where do they land, what date do they state.

Standard library only. Usage:

    python3 check_links.py URL [URL ...]
    python3 check_links.py --file urls.txt            # one URL per line, blank lines and # comments ignored
    python3 check_links.py --json URL                 # machine-readable output
    python3 check_links.py --timeout 20 URL

Per URL the script reports: HTTP status, final URL after redirects, content type, page title,
date hints found in headers or markup, and flags:

    dead                  network error or HTTP 4xx/5xx other than the blocked codes
    blocked               401, 402, 403, 429 or a login/subscription wall in the markup: you have not read this page
    redirect_domain       final host differs from the requested host
    redirect_homepage     the request had a path but landed on the site root: the cited page is gone
    not_html              binary or non-HTML content; title and dates are not extracted
    undated               no date hint found; weaker for time-sensitive claims
    truncated             page larger than --max-bytes; dates deep in the page may be missed

Exit code 0 when no URL is dead or blocked, 1 otherwise. Fetching only; nothing is written.
"""

import argparse
import gzip
import html
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36 research-verifier-linkcheck/1.0"
)
BLOCKED_CODES = {401, 402, 403, 429}
WALL_PATTERNS = re.compile(
    r"(subscribe to continue|subscription required|to continue reading|sign in to read|"
    r"log in to continue|paywall|are you a robot|enable javascript and cookies|"
    r"access denied|please verify you are a human|checking your browser)",
    re.IGNORECASE,
)
DATE_META_KEYS = {
    "article:published_time", "article:modified_time", "og:updated_time",
    "datepublished", "datemodified", "date", "dc.date", "dc.date.issued",
    "dcterms.date", "dcterms.created", "dcterms.modified", "pubdate",
    "publishdate", "publish_date", "publication_date", "last-modified",
    "lastmod", "revised", "created", "sailthru.date", "parsely-pub-date",
}
JSONLD_DATE_RE = re.compile(r'"(datePublished|dateModified|dateCreated|uploadDate)"\s*:\s*"([^"]{4,40})"')
TIME_TAG_RE = re.compile(r"<time[^>]*datetime\s*=\s*[\"']([^\"']{4,40})[\"']", re.IGNORECASE)
COPYRIGHT_RE = re.compile(r"(?:©|&copy;|copyright)\s*(?:\d{4}\s*[-–]\s*)?((?:19|20)\d{2})", re.IGNORECASE)


class _Extractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self._in_title = False
        self.metas = []

    def handle_starttag(self, tag, attrs):
        if tag == "title" and not self.title:
            self._in_title = True
        elif tag == "meta":
            a = dict(attrs)
            key = (a.get("property") or a.get("name") or a.get("itemprop") or "").strip().lower()
            content = (a.get("content") or "").strip()
            if key and content:
                self.metas.append((key, content))

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def _fetch(url, timeout, max_bytes):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en,de;q=0.8",
            "Accept-Encoding": "gzip, identity",
        },
    )
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as e:
        resp = e  # HTTPError carries status, headers, and a readable body
    status = getattr(resp, "status", None) or getattr(resp, "code", None)
    final_url = resp.geturl() if hasattr(resp, "geturl") else url
    headers = {k.lower(): v for k, v in resp.headers.items()} if resp.headers else {}
    raw = resp.read(max_bytes + 1)
    truncated = len(raw) > max_bytes
    raw = raw[:max_bytes]
    if headers.get("content-encoding", "").lower() == "gzip" or raw[:2] == b"\x1f\x8b":
        try:
            raw = gzip.decompress(raw)
        except Exception:
            pass
    return status, final_url, headers, raw, truncated


def _decode(raw, headers):
    ctype = headers.get("content-type", "")
    m = re.search(r"charset=([\w\-]+)", ctype, re.IGNORECASE)
    for enc in ([m.group(1)] if m else []) + ["utf-8", "latin-1"]:
        try:
            return raw.decode(enc, errors="replace")
        except (LookupError, UnicodeDecodeError):
            continue
    return raw.decode("utf-8", errors="replace")


def _date_hints(text, headers):
    hints = []
    if "last-modified" in headers:
        hints.append(("header:last-modified", headers["last-modified"]))
    ex = _Extractor()
    try:
        ex.feed(text)
    except Exception:
        pass
    for key, content in ex.metas:
        if key in DATE_META_KEYS:
            hints.append(("meta:" + key, content))
    for m in JSONLD_DATE_RE.finditer(text):
        hints.append(("jsonld:" + m.group(1), m.group(2)))
    for m in TIME_TAG_RE.finditer(text):
        hints.append(("time-tag", m.group(1)))
    if not hints:
        m = COPYRIGHT_RE.search(text)
        if m:
            hints.append(("copyright-year (weak)", m.group(1)))
    # de-duplicate while keeping order
    seen, out = set(), []
    for h in hints:
        if h not in seen:
            seen.add(h)
            out.append(h)
    return ex.title, out[:8]


def check(url, timeout=15, max_bytes=400_000):
    result = {
        "url": url, "status": None, "final_url": None, "content_type": None,
        "title": None, "date_hints": [], "flags": [], "error": None,
    }
    try:
        status, final_url, headers, raw, truncated = _fetch(url, timeout, max_bytes)
    except Exception as e:  # URLError, socket timeout, SSL, etc.
        result["error"] = f"{type(e).__name__}: {e}"
        result["flags"].append("dead")
        return result

    result["status"] = status
    result["final_url"] = final_url
    ctype = headers.get("content-type", "")
    result["content_type"] = ctype.split(";")[0].strip() or None
    if truncated:
        result["flags"].append("truncated")

    if status in BLOCKED_CODES:
        result["flags"].append("blocked")
    elif status is None or status >= 400:
        result["flags"].append("dead")

    req_p = urllib.parse.urlparse(url)
    fin_p = urllib.parse.urlparse(final_url or url)
    if req_p.netloc.lower().removeprefix("www.") != fin_p.netloc.lower().removeprefix("www."):
        result["flags"].append("redirect_domain")
    if req_p.path.strip("/") and not fin_p.path.strip("/") and not fin_p.query:
        result["flags"].append("redirect_homepage")

    is_html = ("html" in ctype.lower()) or raw[:512].lstrip().lower().startswith((b"<!doctype html", b"<html"))
    if not is_html:
        result["flags"].append("not_html")
        return result

    text = _decode(raw, headers)
    title, hints = _date_hints(text, headers)
    result["title"] = html.unescape(" ".join(title.split()))[:200] or None
    result["date_hints"] = [{"source": s, "value": v} for s, v in hints]
    if not hints:
        result["flags"].append("undated")
    if "blocked" not in result["flags"] and WALL_PATTERNS.search(text[:60_000]):
        result["flags"].append("blocked")
    return result


def _read_url_file(path):
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                yield line


def _print_text(results):
    for r in results:
        print(f"URL:       {r['url']}")
        print(f"Status:    {r['status'] if r['status'] is not None else 'n/a'}"
              + (f"   ({r['error']})" if r["error"] else ""))
        if r["final_url"] and r["final_url"] != r["url"]:
            print(f"Final URL: {r['final_url']}")
        if r["content_type"]:
            print(f"Type:      {r['content_type']}")
        if r["title"]:
            print(f"Title:     {r['title']}")
        if r["date_hints"]:
            print("Dates:     " + "; ".join(f"{d['value']} [{d['source']}]" for d in r["date_hints"]))
        print(f"Flags:     {', '.join(r['flags']) if r['flags'] else 'ok'}")
        print()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("urls", nargs="*", help="URLs to check")
    ap.add_argument("--file", help="file with one URL per line")
    ap.add_argument("--json", action="store_true", help="JSON output")
    ap.add_argument("--timeout", type=float, default=15.0, help="seconds per request (default 15)")
    ap.add_argument("--max-bytes", type=int, default=400_000, help="bytes of body to inspect (default 400000)")
    args = ap.parse_args(argv)

    urls = list(args.urls)
    if args.file:
        urls.extend(_read_url_file(args.file))
    if not urls:
        ap.error("no URLs given")

    results = [check(u, timeout=args.timeout, max_bytes=args.max_bytes) for u in urls]
    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        _print_text(results)
        bad = [r for r in results if "dead" in r["flags"] or "blocked" in r["flags"]]
        print(f"{len(results)} checked, {len(bad)} dead or blocked.")
    return 1 if any("dead" in r["flags"] or "blocked" in r["flags"] for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
