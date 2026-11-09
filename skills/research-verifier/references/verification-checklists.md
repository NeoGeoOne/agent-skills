# Verification checklists

Three checklists, one per tier. The minimum list is drawn from editorial fact-checking practice (one primary source or two independent secondary sources per fact); the maximum list adds the OSINT habit of grading source and claim separately, the journalistic independence test, and an independent re-verification pass. Apply the list to each core claim, not to the report as a whole.

## Freshness windows for time-sensitive claims

A source can only establish a current state if it is recent enough for how fast that state changes. Use these windows; a source outside the window caps the claim at yellow.

| Claim type | Source must be dated within |
|---|---|
| Price, availability, stock, exchange rate | 30 days |
| Software version, model version, API surface in an active field | 90 days |
| Office holder, executive, company ownership | 90 days, plus a news search for changes in the last 30 |
| Regulation in force, legal status | 6 months, plus a check for pending amendments |
| Product specifications of a shipping product | 12 months |
| Statistics that are published on a schedule | Latest scheduled release |
| Stable facts (history, physics, definitions, closed events) | No window |

"Dated" means the page itself states a publication or update date that you read. Undated pages count as half a source for time-sensitive claims.

## Minimum checklist - Tier 1

Every item must hold for green.

1. The claim was searched for in this run; the answer is not from memory.
2. The page that supports it was fetched and the relevant passage read, not inferred from a snippet.
3. Support is one primary or authoritative source, or two independent secondary sources that agree.
4. If time-sensitive: the source date lies inside the freshness window.
5. The source is what it appears to be: the domain belongs to the entity or a recognised publisher, not a look-alike or an aggregator restating it.
6. The report states the label and cites the source with a full URL.

If item 3 fails because only one secondary source exists, label yellow and say so. If nothing supports the claim, label red.

## Standard checklist - Tier 2

All Tier 1 items, plus:

7. At least two independent sources per core claim, at least one primary or authoritative. Independence means different origin, not different domain: two outlets rewriting one press release are one source (see `source-grading.md`).
8. The load-bearing claim (the one the user will act on) has a contradiction search on record, with the query noted and the result summarised.
9. Sources that disagree on detail are reconciled in the report: which value you adopt and why (newer, more authoritative, primary).
10. Each cited URL was checked to resolve to the page you read (`scripts/check_links.py`), so the source list does not point at dead pages or redirects to a homepage.
11. Unfamiliar publishers received a lateral check: one search about the publisher itself (who runs it, what else it publishes) before their statement counts.
12. The report contains a "Not verified" section listing yellow and red items with what was attempted.

## Maximum checklist - Tier 3

All Tier 1 and Tier 2 items, plus:

13. Every material claim is traced to its first point of publication: the original document, page, filing, dataset, or statement, read directly. Secondary reporting is used only to find the primary or to corroborate it.
14. Every material claim has a dedicated contradiction search, and the absence or presence of counter-evidence is recorded per claim.
15. Source reliability and claim credibility are graded separately (`source-grading.md`). A claim from an A-grade publisher that no one else confirms is still credibility 3 at best, not 1.
16. Independence is tested explicitly: for each pair of supporting sources, ask whether one derives from the other or both from a common origin. Group derived sources; count each group once.
17. Per-source vertical check on every primary and every load-bearing secondary source: currency (dated, current), relevance (addresses this exact claim, not a neighbouring one), authority (who wrote it, what standing), accuracy (verifiable details, references, consistent with other reliable sources), purpose (commercial, advocacy, informational; declared or undeclared interest).
18. Established fact is separated from disputed or evolving matters in the report; disputed points name the positions and their sources instead of picking one silently.
19. Paywalled or blocked sources are handled per the rule below; none is cited as if read.
20. The independent verification pass (below) was run and its disagreements resolved in favour of the fresh result.
21. The report states, per red or yellow claim, what evidence would change the label.

## Paywalled, blocked, and unreadable sources

- If a fetch returns a login wall, a 402/403, a cookie wall that hides the text, or a truncated preview: you have not read it. Record it as a lead.
- Look for an accessible equivalent: the publisher's press release, the underlying document the article reports on, a syndicated copy on the outlet's partner site, an official summary. Cite the equivalent.
- If no equivalent exists, the claim's label is capped at yellow when other readable sources support it, and red when the paywalled page is the only support. Say in the report that the source exists but could not be read.
- Never reconstruct a paywalled article's content from its headline, its snippet, or your memory of similar coverage.

## The independent verification pass

Required at Tier 3; applied to the load-bearing claim at Tier 2 when budget allows. The point is to check the draft with searches that did not grow out of the draft's own path, which is how the Chain-of-Verification technique reduces error carry-over.

1. Finish the draft answer with labels.
2. For each core claim, write a plain verification question that does not reuse the draft's phrasing or assume its answer. Draft says "X supports Y since version 4.2"; question is "Which versions of X support Y, according to the official documentation?"
3. Search each question fresh, preferably through a different query angle or source type than the one the draft used. Fetch and read.
4. Compare. Agreement confirms the label. Disagreement means the fresh result wins unless it comes from a clearly weaker source, in which case both are reported and the claim goes yellow.
5. Update the labels and the "Not verified" section before writing the final report.

Budget the pass at roughly one to two calls per core claim; reserve them when planning the run.

## Definition of done per tier

- Tier 1: the minimum checklist holds for the single claim, or the claim is labelled yellow or red with the reason.
- Tier 2: every core claim has reached green or carries a yellow or red label with an explanation, the load-bearing claim survived its contradiction search, links resolve, the "Not verified" section is complete.
- Tier 3: every material claim is traced to a primary source or explicitly marked as not traceable, all contradiction searches are on record, the independent verification pass has run, disputed points are presented as disputed, and each non-green claim names what would settle it.

Done does not mean every claim is green. It means every claim is labelled honestly and the reader needs no further research to act at the level of confidence the tier provides.
