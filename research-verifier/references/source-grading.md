# Source grading

Read this when deciding how much a source counts, whether two sources are really one, and how to turn evidence into a traffic-light label. `scripts/grade_sources.py` implements these rules; use it at Tier 2 and 3 so labels come from the recorded evidence rather than from impression.

## Source hierarchy

Higher rows outrank lower rows for the same claim. When two rows disagree, the higher one wins unless it is stale for a time-sensitive claim.

Same-publisher contradiction: when two primary pages of the same entity disagree (help-center articles naming different payment providers or payout deadlines are common), the hierarchy cannot resolve it. Report both statements with both URLs as unresolved, label YELLOW, and never use either one to declare a third party's statement wrong.

1. Primary, from the entity itself or the authority: official documentation, release notes, the legal text, the regulator's page, the filing, the dataset, the paper, the organiser's statement.
2. Reference works and institutions with editorial control: standards bodies, statistical offices, academic institutions, established encyclopaedias with sourced entries (use them to find the primary, cite the primary where possible).
3. Major outlets with a correction policy and named journalists; recognised trade press.
4. Specialist blogs and company blogs with named authors and verifiable expertise; vendor blogs about their own product are primary for the product's features and promotional for its comparisons.
5. Forums, Q&A sites, social posts, and anonymous pages: leads only. A forum answer can point you to the changelog; it cannot replace it.
6. Content farms, affiliate comparison sites, AI-generated aggregators, pages whose purpose is ranking rather than informing: do not cite, even as corroboration.

## Grading source and claim separately

Borrowing from the Admiralty (NATO) system used in intelligence work, grade the source's reliability with a letter and the claim's credibility with a number, and keep them apart. A reliable publisher can carry an unconfirmed claim; an unknown site can carry a claim that three independent primaries confirm. Mixing the two is how a brand's reputation lends false credibility to a specific statement.

### Reliability of the source (letter)

| Letter | Meaning | Typical publisher class |
|---|---|---|
| A | Reliable, with authority on this subject | The entity itself, official documentation, legislator, regulator, standards body, statistical office, peer-reviewed venue |
| B | Usually reliable, editorial control | Major outlet with correction policy, academic institution, established reference work |
| C | Fairly reliable, partial control | Trade press, specialist blog with named expert author, vendor blog about third parties |
| D | Not usually reliable | Unknown site with an author, forum answer, social post by an identifiable person |
| E | Unreliable | Content farm, affiliate comparison, anonymous aggregator, AI-generated summary site |
| F | Cannot be judged | Page not readable, publisher unidentifiable |

### Credibility of the claim (number)

| Number | Meaning | Condition |
|---|---|---|
| 1 | Confirmed | Two or more independent source groups agree, at least one A-grade primary, no contradiction from a source of equal or higher reliability |
| 2 | Probably true | One A-grade primary read directly, or two independent B/C groups agree, no relevant contradiction |
| 3 | Possibly true | One secondary source, or several sources that all derive from one origin |
| 4 | Doubtful | Only D/E sources, or a contradiction from a source of equal reliability that is unresolved |
| 5 | Improbable | Contradicted by a source more reliable than every supporting source |
| 6 | Cannot be judged | No source found, or the only source could not be read |

### From grades to traffic light

| Tier | GREEN | YELLOW | RED |
|---|---|---|---|
| 1 | Credibility 1-2 and fresh | Credibility 3, or 1-2 but stale | Credibility 4-6 |
| 2 | Credibility 1 (two independent groups, one A primary), contradiction search done for the load-bearing claim, fresh | Credibility 2-3, or 1 but stale, or contradiction search missing on the load-bearing claim | Credibility 4-6 |
| 3 | Credibility 1 with the primary read directly, at least two further independent groups, contradiction search done, verification pass agreed, fresh | Any green condition missing while support exists | Credibility 4-6, or primary unreachable with no readable equivalent |

"Fresh" refers to the windows in `verification-checklists.md`; a time-sensitive claim whose supporting sources all fall outside the window is capped at yellow regardless of credibility.

## Independence test

Two sources are independent when neither derives from the other and both do not derive from a common origin you can identify. Ask, for each pair:

- Does one cite, quote, or link the other as its source?
- Do both report the same press release, announcement, wiki entry, or vendor page, possibly in different words?
- Are both owned by the same publisher or operated by the same team?
- Do both show the same unusual phrasing, the same number to the same rounding, the same error?

If any answer is yes, they form one group. Groups count once. In the evidence file, set `derived_from` on the dependent source (or the same `origin` label on all members of a group); the script collapses them.

Corollary: at Tier 2 and 3, "two sources" means two groups. Ten news articles about one announcement are one group plus the announcement, and the announcement is the one to cite.

## Per-source vertical check

For every primary and every load-bearing secondary source at Tier 3 (and when in doubt at Tier 2), run through these five questions and note anything that lowers the letter:

- Currency: dated? updated? still the current version of the page?
- Relevance: does it address this exact claim, or a neighbouring one (a different version, region, product line)?
- Authority: who wrote or published it, and do they have standing on this subject?
- Accuracy: are the details verifiable, does it cite its own sources, is it consistent with other reliable sources?
- Purpose: to inform, to sell, to advocate? Is a commercial or political interest declared, undeclared, or plausible?

## Lateral check for unfamiliar publishers

Before an unfamiliar publisher's statement counts at Tier 2 or 3, spend one search on the publisher rather than the claim: who operates the site, what else they publish, whether others describe it as reliable or as an affiliate or content operation. Assign the letter from that, not from how professional the page looks.

## Red flags that lower a source to E

- No author, no date, no about page, no contact.
- Text that reads like a rewritten version of another page, with generic transitions and no specifics the original lacks.
- Affiliate links or "best X" rankings as the page's structure.
- Numbers without units, dates, or sources; claims about "experts" or "studies" without naming them.
- Domain that imitates a known brand or authority.
- Pages that exist for many unrelated topics in identical templates.

## Evidence file format for `grade_sources.py`

Record your working notes in this structure (print it any time with `python3 scripts/grade_sources.py --schema`):

```json
{
  "tier": 2,
  "run_date": "2026-09-09",
  "claims": [
    {
      "id": "C1",
      "text": "libfoo 3.4 supports Python 3.13",
      "load_bearing": true,
      "time_sensitive": true,
      "freshness_days": 90,
      "contradiction_search": {"done": true, "query": "libfoo python 3.13 incompatible", "found": false, "note": ""},
      "verification_pass": {"done": false, "agrees": null},
      "resolved_contradictions": []
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
      "read": true,
      "derived_from": null,
      "origin": null,
      "supports": ["C1"],
      "contradicts": []
    }
  ]
}
```

Field notes:

- `kind`: `primary` (the entity or authority itself), `secondary` (reports on a primary), `tertiary` (summarises secondaries).
- `publisher_class`: one of `official`, `reference`, `major_outlet`, `academic`, `trade`, `blog`, `forum`, `content_farm`, `unknown`. Maps to the reliability letter; the script prints the mapping.
- `date`: ISO date the page states; omit or set null when the page is undated.
- `read`: true only if you fetched and read the passage. Unread sources count at half weight and cap at credibility 3.
- `derived_from`: id of the source this one restates, or `origin`: a free label shared by all members of a group ("press release 2026-08-01"). Either collapses the group.
- `supports` / `contradicts`: claim ids. A source may support one claim and contradict another.
- `freshness_days`: window from the table; the script uses a default per `time_sensitive` if omitted (90 days).
- `resolved_contradictions`: ids of contradicting sources you examined and dismissed with a written reason in your notes (for example, the contradiction concerns an older version). Unresolved contradictions cap the label at yellow or force red, depending on the contradicting source's letter.
- `load_bearing`: mark the claim the user will act on; at Tier 2 its contradiction search is required for green.

The script prints, per claim: independent group count, best reliability letter among supporters, credibility number, freshness status, contradiction status, the resulting label, and flags such as "single group", "all supporters derive from S3", "stale for time-sensitive claim", "contradicted by higher-reliability S5", "supporting source not read". Copy the label and the flags into the report; do not edit them to look better.
