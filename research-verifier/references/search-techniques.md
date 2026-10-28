# Search techniques

Read this before planning queries at Tier 2 and 3, or when a Tier 1 search returns nothing authoritative.

## Query design

- Short queries work better than long ones. Two to six words: the entity plus the attribute you need. "libfoo release notes 3.x" beats "what is the latest version of libfoo and when was it released".
- Start broad, then narrow. The first search maps who publishes on the topic; the following searches target the publisher you trust. Anthropic's own research agents were tuned toward this "wide, then narrow" pattern because narrow first queries miss the authoritative source when its wording differs from the user's.
- Use the entity's own name as written by its owner (product name, legal company name, standard number). Marketing names and nicknames pull in low-quality pages.
- Change the angle when a query fails; do not paraphrase it. Swap the attribute ("pricing" to "plans"), the source type ("docs" to "changelog" to "github releases"), or the language (search in the entity's home-market language for company facts).
- Do not use search operators (quotes, site:, minus) unless the environment's search tool documents that it supports them. Many agent search tools ignore or mangle them. Put the site name in the query as a word instead ("libfoo documentation").
- Add the current year for anything that changes yearly; add the current month for anything faster. Take the current date from the environment, never from memory.

## Where primary sources live

Pick the row that matches the claim type and go there first.

| Claim type | Primary or authoritative source |
|---|---|
| Software version, feature, compatibility | Official docs, release notes, changelog, tagged releases in the source repository, package registry page |
| API behaviour, parameters, limits | Official API reference, OpenAPI spec, official SDK source |
| Price, plan, quota | Vendor pricing page (check the date and region), order form, official announcement |
| Company facts (CEO, address, ownership, revenue) | Company register, annual report or filing, investor relations page, official press release |
| Who holds a public office | The institution's own site, official gazette |
| Law, regulation, standard | Official legal text on the legislator's or regulator's site, the standards body's page, official guidance documents |
| Security issue | The vendor advisory, the CVE record, the national CERT |
| Scientific or medical claim | The peer-reviewed paper, a systematic review, a regulator's assessment; press coverage only as a lead to the paper |
| Event (date, outcome) | The organiser's or authority's statement, then two independent outlets |
| Statistic | The statistical office or organisation that produced the number, with the table or dataset, not a page that quotes it |

If the primary source cannot be found within two targeted searches, fall back to the most authoritative secondary source you can read, and note in the report that the primary was not reachable.

## Reading the page

- Fetch the page. Snippets cut sentences, drop negations, and merge unrelated text.
- Find the date. Look for a publication date, a "last updated" line, a version tag, a copyright year at worst. `scripts/check_links.py` extracts common date hints. A page without any date is a weaker source for time-sensitive claims; say so.
- Read the exact statement, not the heading. Headings promise; body text qualifies.
- Note what the page does not say. Absence of a claim on the official page is not confirmation that the claim is false, but it is a reason to search for a contradiction.
- Headings followed by empty bodies ("Was kostet X?" with nothing under it, filter headings without links) mean collapsed accordion or JS-rendered content that the extractor did not capture, not a page without the fact. Get it from a sibling article of the same vendor, the help center's other pages, or a rendered browser view before concluding anything from the gap.

## Contradiction searches

Every load-bearing claim at Tier 2 and every core claim at Tier 3 gets a search that tries to prove it wrong. Query patterns:

- "X deprecated", "X discontinued", "X end of life", "X removed"
- "X not supported", "X incompatible", "X breaking change"
- "X problems", "X issues", "X criticism", "X complaint", "X lawsuit"
- "X price increase", "X price change"
- "X correction", "X retracted", "X debunked"
- The claim's opposite in plain words ("X is free" becomes "X paid plan required")

A contradiction search that returns nothing relevant is itself evidence; record it in the working notes as "contradiction search: none found (query: ...)". A hit from a more reliable source than your supporting sources turns the claim red; a hit from a weaker source turns it yellow until resolved.

## Freshness-aware searching

For time-sensitive claims:

- Sort mentally by date. When the search tool shows dates, prefer the newest authoritative page. When it does not, fetch and read the date.
- Confirm "current" with a source dated inside the freshness window from `references/verification-checklists.md`. A 2023 page cannot establish what is current now, however authoritative it was then.
- Search for the successor explicitly: "X successor", "X replaced by", "X new version". Fields with fast release cycles rename things; the old name still ranks well.
- Where a status could have changed recently (role holder, availability, legal status), search news from the last weeks with the entity name plus "announces", "appointed", "resigns", "acquired", "shut down".

## Comparisons

- One thread or query set per option, same attribute list for each, official sources only for the attribute values. Fill the table before judging.
- Record the date and region for every price or plan cell; comparisons across different dates or regions are invalid.
- Search for head-to-head coverage last, not first. Comparison articles are secondary and often affiliate-driven; use them to discover attributes you forgot, never as the source of the values.

## Software releases, downloads and docs sites

- Release state comes from the source repository, not from blogs or videos. `curl -s https://api.github.com/repos/OWNER/REPO/releases?per_page=5 | jq -r '.[] | "\(.tag_name) \(.published_at)"'` gives tag and date. `/releases/tags/TAG` lists assets with `size` and `digest` (`sha256:...`). The digest is the primary hash. Older uploads show `null`: record the first-seen hash, dated, and label it TOFU.
- Hash lists on guide or wiki pages lag behind releases. Download the current file into the scratch dir, hash it, and compare. A mismatch means either a stale list or a changed file. Settle it with the upstream digest before labelling anything.
- Some download pages assemble the archive in the browser. Read the page's HTML for `/api/...` endpoints and its JS bundle for the package manifest and file-rename rules. That recovers the exact upstream URLs, sizes and digests, which a script can then reproduce.
- Claims about what an archive or binary contains are verified the same way as text: fetch it to scratch and read it (`unzip -l`, `sha256sum`).
- For numeric facts defined in code (file sizes, limits, constants), the defining source file or header is the primary source. Search it through the repo tree API (`/git/trees/HEAD?recursive=1`), then read the raw file.
- For software the user runs (self-hosted apps, the agent's own install), verify behaviour and config against the source at the exact deployed version: `/git/trees/<tag>?recursive=1` plus `raw.githubusercontent.com/OWNER/REPO/<tag>/path`, or the local install tree. Docs sites describe latest and gate features by version, so an unpinned doc page can describe options the running version lacks or has changed. Get the running version first (`<app> --version`, image tag), then read config classes, defaults and auth code at that tag. Corroborate with the live instance's unauthenticated discovery surface (`/.well-known/*`, the `WWW-Authenticate` header of a 401, health endpoints).
- Security status of a deployed version: `api.github.com/repos/OWNER/REPO/security-advisories` lists `vulnerable_version_range` and `patched_versions` per supported minor line. If the running minor line has no patched entry while newer lines do, treat it as unpatched; don't read the absence of a line as "not affected".
- Docs sites (VitePress, Docusaurus, MkDocs): enumerate pages via `/sitemap.xml`. When extraction returns only navigation and headings, fetch the raw markdown from the repository behind the site.
- Bot-protected pages ("Just a moment..." challenge): the headings, tables or snippets that do come through are usable fragments. Corroborate them from another source and label YELLOW. Don't spend budget on repeated retries.

## Internal and client data

When the claim concerns the user's own environment (their tenant, their customers, their tickets, their documents), the web cannot verify it. Use whatever internal tools the host exposes: mail search, drive search, database query, ticket lookup, calendar. Treat the result as primary evidence and cite it with the tool name and the record identifier instead of a URL ("[3] Drive: 'Angebot_2026-03.pdf', p. 2"). If no internal tool is available, the claim is red: report that it needs a lookup the current environment cannot perform, and do not substitute a generic web answer.

## Budget discipline

Count every search and every fetch. Typical spend at Tier 2: two mapping searches, one targeted search plus one fetch per core claim, one contradiction search, one link check. That is around twelve calls for three claims, leaving three for surprises. At Tier 3 with subagents, hand each thread a fixed slice (for example four threads with ten calls each) and keep ten for your own reconciliation and verification pass.
