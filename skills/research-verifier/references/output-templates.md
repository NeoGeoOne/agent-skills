# Output templates

Read this before writing the report. The report always goes into the chat, in the language of the user's request. Structure stays as below; wording adapts to the language.

## Conventions at every tier

Tier line. First line of the report, one sentence: tier name and the reason in one clause. Examples:

- "Tier 1 (quick check): default port, official documentation, stable fact."
- "Stufe 2 (verifiziert): Kompatibilitätsfrage mit mittlerem Risiko, gegen offizielle Dokumentation und Changelog geprüft."

Labels. Written as a word in square brackets in the answer's language, at the end of the sentence that states the claim, before the citation numbers: English `[GREEN]`, `[YELLOW]`, `[RED]`; German `[GRÜN]`, `[GELB]`, `[ROT]`. Other languages use the everyday colour words. Do not use coloured symbols or emoji; text labels survive every terminal, chat client, and copy-paste.

Citations. Bracketed numbers inline, `[1]`, `[2]`, after the label. Numbers are assigned in order of first appearance and never reused. Every number resolves to one entry in the source list.

Source list. Titled "Sources" (or the language's equivalent), numbered to match, one line per source:

```
[1] Title of the page or document - Publisher, source date (or "undated"). URL in plain text
```

Full URL, no link markup, no shortener, no tracking parameters. Source date is the date the page states; if you had to infer it from a version tag or copyright line, say "date inferred from ...". For internal tools, replace the URL with the tool and record identifier: `[4] Angebot_2026-03.pdf, p. 2 - Drive search, dated 2026-03-11`.

Red and yellow claims. Stated as findings, not omitted. Wording: "Could not be verified: ..." followed by what was tried. Never soften a red into a hedge like "it seems" or "reportedly"; the label carries the uncertainty.

What the report does not contain: a restatement of the question, an introduction about how research was done, a closing summary, offers of further help, or apologies for budget limits. The tier line covers the method; the "Not verified" section covers the limits; the report ends on the source list.

## Tier 1 template

```
<Tier line>

<Answer in one to three sentences, each factual sentence ending with its label and citation.> [GREEN] [1]

<One sentence on freshness if the claim is time-sensitive: "Source dated 2026-09-02; this changes with each release.">
<One sentence on whether a deeper check would add anything, when the stakes might be higher than assumed.>

Sources
[1] ...
```

Example (English):

```
Tier 1 (quick check): default configuration value, official documentation, stable fact.

PostgreSQL listens on TCP port 5432 by default; the value is set by the `port` parameter in postgresql.conf. [GREEN] [1]

A deeper check would add nothing here.

Sources
[1] PostgreSQL 17 Documentation, 19.3 Connections and Authentication - PostgreSQL Global Development Group, 2024-11-21. https://www.postgresql.org/docs/current/runtime-config-connection.html
```

(The URL, version, and date above are illustrative of the format; take real values from the run.)

## Tier 2 template

```
<Tier line>

Answer
<The direct answer to the user's question in two to five sentences, labels and citations inline. Lead with the load-bearing claim.>

Findings
<One short paragraph or line per core claim, each with label and citations. Where sources disagreed on detail, state which value you adopted and why. Include the source date for time-sensitive claims.>

Not verified
<Yellow and red items: the claim, what was searched, what was found or not found, what would settle it. If everything is green: "All core claims verified at this tier.">

Sources
[1] ...
[2] ...
```

Keep "Findings" as prose lines rather than a table unless the question is a comparison; comparisons get one table with options as columns, attributes as rows, and a label plus citation in each cell.

## Tier 3 template

```
<Tier line>

Summary
<The answer and the recommendation or conclusion, five to eight sentences, labels and citations inline. Say plainly what is established, what is disputed, and what could not be verified.>

Claims
| # | Claim | Label | Sources | Note |
|---|---|---|---|---|
| C1 | ... | [GREEN] | [1][4] | primary read; verification pass agreed |
| C2 | ... | [YELLOW] | [2] | single group; primary unreachable |
| C3 | ... | [RED] | - | contradicted by [5]; see Not verified |

Detail
<One subsection per core claim or per option. What the primary source says, with date. Corroboration. Contradiction search result. For disputed points: the positions, who holds them, and their sources; do not resolve silently.>

Not verified
<Per yellow or red claim: what was tried, what was found, what evidence would change the label.>

Method notes
<Two to four lines: tool calls used of the budget, whether subagents were used and how the work was split, whether the verification pass changed anything. No narrative.>

Sources
[1] ...
```

For comparisons at Tier 3, the "Detail" section gets one subsection per option with the same attribute order, and "Claims" becomes the comparison table with a label and citation per cell.

## Evaluating a user-supplied document

When the user hands over a guide, PDF, plan or article and asks for evaluation (or for a plan based on it), put a verdict table before any recommendation. One row per substantive claim of the document:

```
| # | Document claim | Verdict |
|---|---|---|
| 1 | <claim, paraphrased> | **Correct.** <one-line evidence> [GREEN] [1] |
| 2 | <claim> | **Partly.** <what holds, what doesn't, the corrected value> [GREEN] [2] |
| 3 | <claim> | **Disagree as default.** <why: risk, missing evidence, better option> [YELLOW] [3] |
| — | **Missing in the document** | (a) ... (b) ... <facts the document omits that change the outcome> |
```

Verdict words: Correct / Partly / Disagree / Not verifiable. Every verdict carries a label and a citation. The "Missing" row is mandatory; omissions usually matter more than errors. The rest of the answer or plan follows the verdicts, not the document.

## Language handling

Write the whole report, including section titles and labels, in the language of the user's request. Keep source titles in their original language. Do not translate quotations; paraphrase in the report language and cite. If the user writes in German, "Sources" becomes "Quellen", "Not verified" becomes "Nicht verifiziert", "Findings" becomes "Befunde", "Claims" becomes "Aussagen", "Detail" stays "Detail", "Method notes" becomes "Methodik".

## Length

Tier 1: under 120 words plus sources. Tier 2: 150 to 400 words plus sources. Tier 3: as long as the claims require, and no longer; a long report earns its length with sourced findings, not with connective prose. Cut every sentence that carries no claim, no label, no source, and no caveat.
