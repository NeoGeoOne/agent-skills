#!/usr/bin/env python3
"""Turn recorded evidence into per-claim labels, deterministically.

Standard library only. Usage:

    python3 grade_sources.py evidence.json                 # text report
    python3 grade_sources.py evidence.json --markdown      # table for pasting into the chat report
    python3 grade_sources.py evidence.json --json
    python3 grade_sources.py evidence.json --tier 3        # override the tier stored in the file
    python3 grade_sources.py --schema                      # print an example evidence.json and field notes

The rules implemented here are the ones written out in references/source-grading.md:
source reliability (letter A-F) from publisher class, claim credibility (1-6) from independent
supporting groups and contradictions, freshness windows for time-sensitive claims, and the tier
thresholds that map credibility to GREEN / YELLOW / RED. Edit the reference and this file together.
"""

import argparse
import datetime as dt
import json
import sys

CLASS_TO_LETTER = {
    "official": "A",
    "academic": "B",
    "reference": "B",
    "major_outlet": "B",
    "trade": "C",
    "blog": "C",
    "forum": "D",
    "unknown": "D",
    "content_farm": "E",
}
LETTER_RANK = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4, "F": 5}
DEFAULT_FRESHNESS_DAYS = 90

SCHEMA_EXAMPLE = {
    "tier": 2,
    "run_date": "2026-09-09",
    "claims": [
        {
            "id": "C1",
            "text": "libfoo 3.4 supports Python 3.13",
            "load_bearing": True,
            "time_sensitive": True,
            "freshness_days": 90,
            "contradiction_search": {"done": True, "query": "libfoo python 3.13 incompatible", "found": False, "note": ""},
            "verification_pass": {"done": False, "agrees": None},
            "resolved_contradictions": [],
        }
    ],
    "sources": [
        {
            "id": "S1",
            "url": "https://example.org/libfoo/changelog",
            "title": "libfoo changelog",
            "publisher": "libfoo project",
            "kind": "primary",
            "publisher_class": "official",
            "date": "2026-08-14",
            "read": True,
            "derived_from": None,
            "origin": None,
            "supports": ["C1"],
            "contradicts": [],
        }
    ],
}

FIELD_NOTES = """
Field notes
  tier                 1, 2 or 3. --tier on the command line overrides it.
  run_date             ISO date of the research run; defaults to today when missing.
  claims[].load_bearing        the claim the user will act on; Tier 2 green requires its contradiction search.
  claims[].time_sensitive      applies the freshness window (freshness_days, default 90).
  claims[].contradiction_search.done / .found / .query / .note
  claims[].verification_pass.done / .agrees   Tier 3 green requires done and agrees.
  claims[].resolved_contradictions            ids of contradicting sources you examined and dismissed with a reason in your notes.
  sources[].kind               primary | secondary | tertiary
  sources[].publisher_class    """ + " | ".join(CLASS_TO_LETTER) + """
  sources[].date               ISO date stated on the page, or null when undated.
  sources[].read               true only if you fetched and read the passage.
  sources[].derived_from       id of the source this one restates; or origin: shared label for a group.
  sources[].supports / contradicts   claim ids.

Letter mapping: """ + ", ".join(f"{k}={v}" for k, v in CLASS_TO_LETTER.items()) + """; unread or unidentifiable -> F.
"""


def _parse_date(s):
    if not s:
        return None
    try:
        return dt.date.fromisoformat(str(s)[:10])
    except ValueError:
        return None


def _letter(source):
    if not source.get("read", False):
        return "F"
    return CLASS_TO_LETTER.get(str(source.get("publisher_class", "unknown")).lower(), "D")


class _Groups:
    """Union-find over sources: derived_from, shared origin, and same publisher collapse into one group."""

    def __init__(self, sources):
        self.parent = {s["id"]: s["id"] for s in sources}
        by_id = {s["id"]: s for s in sources}
        by_origin, by_publisher = {}, {}
        for s in sources:
            if s.get("derived_from") and s["derived_from"] in by_id:
                self.union(s["id"], s["derived_from"])
            if s.get("origin"):
                by_origin.setdefault(str(s["origin"]).strip().lower(), []).append(s["id"])
            if s.get("publisher"):
                by_publisher.setdefault(str(s["publisher"]).strip().lower(), []).append(s["id"])
        for ids in list(by_origin.values()) + list(by_publisher.values()):
            for other in ids[1:]:
                self.union(ids[0], other)

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def _validate(data):
    errors = []
    if not isinstance(data, dict):
        return ["top level must be an object"]
    for key in ("claims", "sources"):
        if not isinstance(data.get(key), list):
            errors.append(f"'{key}' must be a list")
    if errors:
        return errors
    claim_ids = {c.get("id") for c in data["claims"]}
    if None in claim_ids:
        errors.append("every claim needs an 'id'")
    source_ids = [s.get("id") for s in data["sources"]]
    if None in source_ids:
        errors.append("every source needs an 'id'")
    if len(set(source_ids)) != len(source_ids):
        errors.append("source ids must be unique")
    for s in data["sources"]:
        for key in ("supports", "contradicts"):
            for cid in s.get(key, []) or []:
                if cid not in claim_ids:
                    errors.append(f"source {s.get('id')} {key} unknown claim '{cid}'")
        pc = str(s.get("publisher_class", "unknown")).lower()
        if pc not in CLASS_TO_LETTER:
            errors.append(f"source {s.get('id')}: publisher_class '{pc}' not in {sorted(CLASS_TO_LETTER)}")
        if s.get("kind") not in (None, "primary", "secondary", "tertiary"):
            errors.append(f"source {s.get('id')}: kind must be primary, secondary or tertiary")
        if s.get("date") and _parse_date(s["date"]) is None:
            errors.append(f"source {s.get('id')}: date '{s['date']}' is not ISO (YYYY-MM-DD)")
    return errors


def grade_claim(claim, sources, groups, tier, run_date):
    cid = claim["id"]
    supporters = [s for s in sources if cid in (s.get("supports") or [])]
    contradictors = [s for s in sources if cid in (s.get("contradicts") or [])]
    resolved = set(claim.get("resolved_contradictions") or [])
    contradictors = [s for s in contradictors if s["id"] not in resolved]
    flags = []

    read_supp = [s for s in supporters if s.get("read", False)]
    unread_supp = [s for s in supporters if not s.get("read", False)]
    if unread_supp:
        flags.append("supporting source not read: " + ", ".join(s["id"] for s in unread_supp))

    group_ids = {groups.find(s["id"]) for s in read_supp}
    n_groups = len(group_ids)
    if read_supp and n_groups == 1 and len(read_supp) > 1:
        flags.append("all read supporters form one group (" + ", ".join(s["id"] for s in read_supp) + ")")
    elif n_groups == 1:
        flags.append("single independent group")

    letters = [_letter(s) for s in read_supp]
    best_letter = min(letters, key=LETTER_RANK.get) if letters else None
    primary_read = [s for s in read_supp if s.get("kind") == "primary" and _letter(s) == "A"]
    has_primary_A = bool(primary_read)

    # freshness
    time_sensitive = bool(claim.get("time_sensitive"))
    window = int(claim.get("freshness_days") or DEFAULT_FRESHNESS_DAYS)
    fresh = True
    if time_sensitive:
        fresh = False
        dated = False
        for s in read_supp:
            d = _parse_date(s.get("date"))
            if d is not None:
                dated = True
                if (run_date - d).days <= window:
                    fresh = True
        if read_supp and not dated:
            flags.append("no dated supporting source for a time-sensitive claim")
        elif read_supp and not fresh:
            flags.append(f"stale: no supporting source within {window} days")

    # contradictions
    unresolved_equal_or_higher = False
    unresolved_weaker = False
    for c in contradictors:
        cl = _letter(c)
        if best_letter is None or LETTER_RANK[cl] < LETTER_RANK[best_letter]:
            flags.append(f"contradicted by higher-reliability {c['id']} ({cl})")
            unresolved_equal_or_higher = "higher"
        elif LETTER_RANK[cl] == LETTER_RANK[best_letter]:
            flags.append(f"contradicted by equal-reliability {c['id']} ({cl})")
            unresolved_equal_or_higher = unresolved_equal_or_higher or "equal"
        else:
            flags.append(f"weaker contradiction unresolved: {c['id']} ({cl})")
            unresolved_weaker = True

    # credibility number
    if not supporters:
        cred = 6
    elif not read_supp:
        cred = 3
    elif unresolved_equal_or_higher == "higher":
        cred = 5
    elif unresolved_equal_or_higher == "equal":
        cred = 4
    elif all(LETTER_RANK[l] >= LETTER_RANK["D"] for l in letters):
        cred = 4
        flags.append("only D/E/F sources")
    elif n_groups >= 2 and has_primary_A:
        cred = 1
    elif has_primary_A or (n_groups >= 2 and LETTER_RANK[best_letter] <= LETTER_RANK["C"]):
        cred = 2
    else:
        cred = 3
    if unresolved_weaker and cred < 2:
        cred = 2

    # tier thresholds
    cs = claim.get("contradiction_search") or {}
    cs_done = bool(cs.get("done"))
    vp = claim.get("verification_pass") or {}
    vp_ok = bool(vp.get("done")) and vp.get("agrees") is True
    load_bearing = bool(claim.get("load_bearing"))
    any_unresolved = bool(unresolved_equal_or_higher or unresolved_weaker)

    if cred >= 4:
        label = "RED"
    elif tier == 1:
        label = "GREEN" if (cred <= 2 and fresh and not any_unresolved) else "YELLOW"
    elif tier == 2:
        ok = cred == 1 and fresh and not any_unresolved and (cs_done or not load_bearing)
        label = "GREEN" if ok else "YELLOW"
        if load_bearing and not cs_done:
            flags.append("load-bearing claim without contradiction search")
    else:
        ok = (cred == 1 and has_primary_A and n_groups >= 3 and cs_done and vp_ok and fresh and not any_unresolved)
        label = "GREEN" if ok else "YELLOW"
        if not has_primary_A:
            flags.append("no primary source read directly")
        if n_groups < 3 and has_primary_A:
            flags.append("fewer than two corroborating groups beyond the primary")
        if not cs_done:
            flags.append("contradiction search not done")
        if not vp_ok:
            flags.append("verification pass missing or disagreed")
    if cred >= 4 and not supporters:
        flags.append("no supporting source")

    return {
        "claim_id": cid,
        "text": claim.get("text", ""),
        "label": label,
        "credibility": cred,
        "independent_groups": n_groups,
        "best_source_letter": best_letter,
        "primary_read": has_primary_A,
        "fresh": fresh if time_sensitive else None,
        "supporters": [s["id"] for s in supporters],
        "contradictors": [s["id"] for s in contradictors],
        "flags": flags,
    }


def grade(data, tier=None, today=None):
    errors = _validate(data)
    if errors:
        return {"errors": errors}
    tier = int(tier or data.get("tier") or 2)
    if tier not in (1, 2, 3):
        return {"errors": [f"tier must be 1, 2 or 3 (got {tier})"]}
    run_date = _parse_date(data.get("run_date")) or today or dt.date.today()
    groups = _Groups(data["sources"])
    src_report = []
    for s in data["sources"]:
        src_report.append({
            "id": s["id"], "letter": _letter(s), "kind": s.get("kind"),
            "publisher": s.get("publisher"), "date": s.get("date"),
            "read": bool(s.get("read")), "group": groups.find(s["id"]), "url": s.get("url"),
        })
    claims = [grade_claim(c, data["sources"], groups, tier, run_date) for c in data["claims"]]
    return {"tier": tier, "run_date": run_date.isoformat(), "sources": src_report, "claims": claims}


def _print_text(rep):
    print(f"Tier {rep['tier']}  run date {rep['run_date']}\n")
    print("Sources")
    for s in rep["sources"]:
        print(f"  {s['id']:<5} {s['letter']}  {s['kind'] or '-':<9} {s['publisher'] or '-'}"
              f"  {s['date'] or 'undated'}  {'read' if s['read'] else 'NOT READ'}  group={s['group']}")
    print("\nClaims")
    for c in rep["claims"]:
        fresh = "" if c["fresh"] is None else ("  fresh" if c["fresh"] else "  STALE")
        print(f"  {c['claim_id']:<5} [{c['label']}]  credibility {c['credibility']}  groups {c['independent_groups']}"
              f"  best {c['best_source_letter'] or '-'}{fresh}")
        print(f"        {c['text']}")
        if c["supporters"]:
            print(f"        supports: {', '.join(c['supporters'])}")
        if c["contradictors"]:
            print(f"        contradicts: {', '.join(c['contradictors'])}")
        for f in c["flags"]:
            print(f"        flag: {f}")
    print()


def _print_markdown(rep):
    print(f"| # | Claim | Label | Credibility | Groups | Sources | Flags |")
    print(f"|---|---|---|---|---|---|---|")
    for c in rep["claims"]:
        srcs = "".join(f"[{s}]" for s in c["supporters"]) or "-"
        flags = "; ".join(c["flags"]) or "-"
        text = c["text"].replace("|", "/")
        print(f"| {c['claim_id']} | {text} | [{c['label']}] | {c['credibility']} | {c['independent_groups']} | {srcs} | {flags} |")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("evidence", nargs="?", help="path to evidence.json")
    ap.add_argument("--tier", type=int, choices=(1, 2, 3), help="override the tier stored in the file")
    ap.add_argument("--today", help="ISO date to use as run date when the file has none")
    ap.add_argument("--markdown", action="store_true", help="print a markdown claims table")
    ap.add_argument("--json", action="store_true", help="print the full report as JSON")
    ap.add_argument("--schema", action="store_true", help="print an example evidence.json and field notes")
    args = ap.parse_args(argv)

    if args.schema:
        print(json.dumps(SCHEMA_EXAMPLE, indent=2))
        print(FIELD_NOTES)
        return 0
    if not args.evidence:
        ap.error("evidence.json path required (or --schema)")
    with open(args.evidence, encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except json.JSONDecodeError as e:
            print(f"invalid JSON: {e}", file=sys.stderr)
            return 2
    rep = grade(data, tier=args.tier, today=_parse_date(args.today))
    if "errors" in rep:
        print("evidence file has problems:", file=sys.stderr)
        for e in rep["errors"]:
            print("  - " + e, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(rep, indent=2, ensure_ascii=False))
    elif args.markdown:
        _print_markdown(rep)
    else:
        _print_text(rep)
    return 0


if __name__ == "__main__":
    sys.exit(main())
