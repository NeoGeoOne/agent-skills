---
name: research-verifier
description: Tiered online research with verification instead of answering from memory. Routes each question to one of three depths (quick check, verified, deep due diligence), runs a search-read-verify loop with the host environment's web tools, grades sources, and reports every core claim with a traffic-light reliability label and numbered citations. Use this skill whenever the user asks to research, look up, verify, fact-check, compare, or find the latest on anything, and whenever an answer depends on facts that may have changed or that training data may get wrong - prices, dates, current events, who holds a role, software versions, API and library details, documentation, product specs, legal or regulatory status, company and market information, client-specific data. Trigger even when the user does not say "research" but a wrong or outdated answer would matter. Do not use for creative writing, pure code generation without factual lookups, or math.
compatibility: Needs a web search tool and, ideally, a page-fetch tool in the host environment. Optional - python3 for the bundled helper scripts, a subagent or task-delegation tool for parallel deep research, an ask-user tool for the single clarifying question.
metadata:
  version: "1.0.0"
---

# Research Verifier

## Why this skill exists

Language models answer fluently from training data even when that data is stale or wrong, and the answer looks identical either way. This skill replaces "recall and hope" with "search, read, verify, label". Every factual claim in the final answer is either backed by sources you actually read during this run, or explicitly marked as unverified. Memory is allowed for one thing only: forming hypotheses and search queries.

The skill scales effort to the question. A one-line fact does not need fifty searches; a purchase decision or a compliance question should not rest on one blog post. Three tiers cover that range. You pick the tier when the signals are clear and ask the user once when they are not.

## Core rules

1. Do not state a fact you did not confirm in this run. If the search tools cannot confirm it, say so and label it red.
2. Read what you cite. A search snippet is a lead, not evidence. Fetch the page when a claim rests on it.
3. Use only the search and fetch tools the host environment provides. That includes the host's terminal for machine-readable primary sources: GitHub releases/tree API, raw repository files, `sitemap.xml`, a download hashed in the scratch dir. Do not guess URLs; every URL comes from a page, an API response or official docs you read. If no search tool exists, tell the user plainly that verification is not possible here and stop; do not present a memory answer as checked.
4. Ask the user at most one question per run, and only to settle the tier. Everything else you decide yourself and document in the report.
5. Prefer primary and authoritative sources (official documentation, publisher pages, filings, standards, peer-reviewed work) over aggregators and SEO content. Two articles that copy the same press release are one source.
6. Stay inside the tier's tool budget. When the budget runs out, stop and report what you have, with honest labels.
7. Every core claim in the report carries a traffic-light label and at least one numbered citation. Sources are listed with full URLs at the end.

## Workflow checklist

Copy this into your working notes at the start of a run and tick items off; multi-step research drifts without it.

```
[ ] 1. Triage: read signals, pick tier or ask the one question (references/tier-routing.md)
[ ] 2. Decompose: list the core claims the answer must establish
[ ] 3. Plan queries: broad first, then narrow; primary sources first (references/search-techniques.md)
[ ] 4. Research loop: search -> fetch -> extract claim/evidence -> note gaps -> repeat, within budget
[ ] 5. Verify: apply the tier's checklist, grade sources, detect contradictions (references/verification-checklists.md, references/source-grading.md)
[ ] 6. Tier 3 only: independent verification pass on each core claim
[ ] 7. Report in chat with tier line, traffic lights, numbered citations, unverified list (references/output-templates.md)
```

## Step 1: Triage - choose the tier

Judge the request on five signals. Details and worked examples are in `references/tier-routing.md`.

| Signal | Points to Tier 1 | Points to Tier 2 | Points to Tier 3 |
|---|---|---|---|
| Stakes if wrong | Trivial, easily corrected | Costs time or money to undo | Money, legal, safety, health, reputation, irreversible |
| Verifiability | One canonical source exists | Several reputable sources exist, may differ in detail | Contested, fragmented, or primary source is hard to reach |
| Time sensitivity | Stable fact | Changes yearly | Changes monthly or faster, or currently in flux |
| Breadth | One question | 2-5 related questions or a comparison | Many sub-questions, multiple options, a decision |
| User wording | "quick", "just check", "roughly" | "verify", "is it true", "compare", "which" | "thorough", "deep dive", "due diligence", "before I sign/buy/deploy" |

Decision rule:

- All signals land in one tier, or the user names a depth: choose it, and state the choice in the first line of the report.
- Signals point to different tiers, the request mixes a trivial part with a high-stakes part, or you cannot tell what the user will do with the answer: ask. Exactly one question. Use the environment's ask-user tool if it has one (present the three tiers as options); otherwise ask in plain text and end your turn. Do not start searching before the answer.

Question template:

```
Which depth do you want for this?
1. Quick check - one or two sources, seconds.
2. Verified - several independent sources cross-checked, a few minutes.
3. Deep - primary sources, contradiction search, full report, longer.
```

If the user's reply adds constraints (a date range, a region, a budget), fold them into the plan. Never ask a second question in the same run; if a real blocker appears later, say so in the report instead.

## Step 2: Decompose into core claims

Before searching, write down the specific claims the answer needs, one line each. "Is library X still maintained?" becomes: (a) date of the latest release, (b) date of the latest commit, (c) open maintainer statements about status. Claims, not topics. Each gets a traffic light later, so make them checkable.

Mark claims that are time-sensitive (versions, prices, roles, availability, legal status, anything "current" or "latest"). They get freshness requirements.

## Step 3: Research loop

The loop is the same at every tier: search, read, record, assess gaps, repeat. What changes is the budget, the source requirements, and how much contradiction hunting you do.

Recording format for working notes (keep it in your reasoning or a scratch file, not in the report):

```
Claim C1: <text>
  Evidence: [S1] <what the source says, page section>  date: <source date>  kind: primary/secondary
  Evidence: [S2] ...
  Gaps: <what is still missing for the tier's threshold>
```

### Tier 1 - Quick check (budget: 5 tool calls)

Purpose: a single, low-stakes, canonically answerable fact.

- Search once with the most specific query. Fetch the top authoritative result.
- Green threshold: one primary source (the entity or authority itself, read directly), or two independent secondary sources agreeing; date acceptable if time-sensitive.
- Do not spend the remaining calls polishing a green claim. Spend them only if the first result is not authoritative or is stale.
- Output: the answer in one to three sentences, label, one or two citations.

### Tier 2 - Verified (budget: 15 tool calls)

Purpose: moderate stakes, several related facts, or a comparison where being wrong wastes real time or money.

- Start broad to map the space (one or two searches), then one targeted search per core claim.
- For each core claim, find at least two independent sources, at least one of them a primary source (the entity or authority itself). Read them.
- Run one contradiction search for the load-bearing claim: query the opposite ("X deprecated", "X not supported", "X problems", "X wrong").
- For the load-bearing claim only, do the independent verification pass described under Tier 3 if budget remains.
- Output: structured answer, label per core claim, numbered citations, a short "not verified" section.

### Tier 3 - Deep due diligence (budget: 50 tool calls, shared across all threads)

Purpose: high stakes, contested or fragmented topics, decisions with cost.

- Map the topic first (two to four broad searches) and refine the claim list; the initial decomposition is usually incomplete.
- For every material claim: locate and read the primary source (original document, official page, filing, changelog, standard, paper). Add at least two independent corroborations. Run a dedicated contradiction search per claim.
- Parallelise when the environment offers subagents or task delegation: split into two to five threads with non-overlapping briefs, such as primary-source hunt, counter-evidence, recency and status check, one thread per option in a comparison. Give each thread a budget slice so the total stays within 50, a clear output format (claim, evidence, source, date, kind), and the instruction to report what it could not find. Reconcile the threads yourself; do not let a thread's conclusion pass through unread.
- Independent verification pass (required at this tier): after drafting the answer, write one verification question per core claim without looking at the draft's wording, search each question fresh, and compare. Where the fresh answer disagrees with the draft, the draft loses. This catches errors that the original search path baked in.
- Output: full report in chat with sections, a claim table with labels, sources with dates, an explicit list of unverified or disputed points and what would settle them.

### Working with internal or client data

When the question concerns the user's own systems, customers, or documents, the "source" is an internal connector (mail, drive, database, ticketing) rather than the web. Use whichever such tools the environment exposes, treat their output as primary evidence, and label the claim red if no tool gives access. Do not fill the gap from memory or from generic web results.

## Step 4: Verify and label

Apply the checklist for the tier from `references/verification-checklists.md`. Grade sources with `references/source-grading.md` (source hierarchy, Admiralty-style separation of source reliability from claim credibility, independence test, freshness rules).

Traffic-light labels, applied per core claim:

- GREEN: meets the tier's threshold; no unresolved contradiction; fresh enough if time-sensitive.
- YELLOW: some support but below threshold; only secondary or derived sources; stale for a time-sensitive claim; sources agree on substance but disagree on detail.
- RED: no confirming source found; contradicted by a more reliable source; only low-reliability sources (forums, content farms, unknown sites); the only source could not be read (paywall, blocked) and nothing else confirms it.

Red claims are still reported, phrased as "could not be verified" with what was checked. Never upgrade a label because the claim sounds right.

Helper scripts (need python3; if unavailable, do the same by hand following the references):

```
python3 scripts/check_links.py URL [URL ...]          # status, final URL, title, date hints, paywall/dead flags
python3 scripts/check_links.py --file urls.txt --json
python3 scripts/grade_sources.py evidence.json --tier 2 --markdown   # independence groups, reliability, per-claim label
python3 scripts/grade_sources.py --schema             # prints the evidence.json format
```

Run `check_links.py` on every URL you intend to cite at Tier 2 and 3; a dead or redirected link in the sources list undermines the whole report. Run `grade_sources.py` at Tier 2 and 3 to compute labels deterministically from your evidence notes rather than from impression.

## Step 5: Report

Follow the template for the tier in `references/output-templates.md`. The report is always delivered in the chat, in the language of the user's request. Fixed elements at every tier:

- First line: the tier used and, in one clause, why.
- Labels written as words in the answer's language inside square brackets, for example `[GREEN]`, `[GELB]`, `[ROT]`, placed at the end of the claim's sentence.
- Citations as bracketed numbers inline, `[1]`, `[2]`, matching a numbered source list at the end with title, publisher, source date, and the full URL in plain text.
- A "Not verified" section listing red and yellow items with what was tried, at Tier 2 and 3. At Tier 1 a single sentence suffices.
- No filler: no restating the question, no closing summary, no offers of further help. End on the source list.

## Stopping criteria

Stop when every core claim has reached the tier's target label, or when the budget is exhausted. Do not keep searching to turn a yellow into a green if the remaining budget is small and the claim is not load-bearing; label it and move on. Do not stop early because the first result "looks right" - at Tier 2 and 3 the second independent source is the whole point.

Keep a running count of tool calls. Searches and fetches both count. Subagent calls count against the shared Tier 3 budget.

## Failure modes to avoid

- Answering from memory and citing a source you did not read to make it look verified.
- Treating a search snippet as evidence. Snippets truncate and mislead.
- Counting two pages that repeat one press release, wiki article, or vendor claim as two sources.
- Choosing SEO-optimised pages over the official documentation that ranks lower.
- Citing a paywalled or blocked page as if you read it.
- Repeating near-identical queries. Change the angle, the terms, or the source type instead.
- Asking the user more than once, or asking when the signals were clear.
- Continuing to search after the threshold is met, or stopping at the first plausible page.
- Inventing URLs, dates, version numbers, or attributions to fill gaps. A gap is a red label, not a guess.

## Environment notes

This skill is written to run unchanged in different agent environments. It never names a specific assistant or vendor tool. Read "web search tool", "fetch tool", "ask-user tool", and "subagent tool" as whatever the current host provides under those functions. If a capability is absent, degrade as described: no ask-user tool means a plain-text question; no subagents means a sequential Tier 3; no python3 means manual grading. Only the absence of a search tool stops the run.

## Reference files

- `references/tier-routing.md` - routing signals in depth, worked examples, mixed-request handling, the question template.
- `references/search-techniques.md` - query design, finding primary sources, contradiction searches, freshness-aware searching, software releases/downloads/hashes and docs sites, bot-protected pages, internal-data lookups.
- `references/verification-checklists.md` - minimum, standard, and maximum checklists; freshness table; paywall handling; the independent verification pass.
- `references/source-grading.md` - source hierarchy, reliability letters and credibility numbers, independence test, red flags, and the `evidence.json` schema for `grade_sources.py`.
- `references/output-templates.md` - report templates per tier, label and citation conventions, verdict table for evaluating a user-supplied document, language handling.
