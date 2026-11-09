# Tier routing

Read this when the tier choice is not obvious from the table in SKILL.md, or when a request mixes parts of different weight.

## The three tiers in one line each

- Tier 1, Quick check: one low-stakes fact with a canonical answer. Budget 5 tool calls.
- Tier 2, Verified: several related facts or a comparison; a wrong answer costs time or money to undo. Budget 15.
- Tier 3, Deep due diligence: a decision, a contested topic, or a fragmented one; a wrong answer is expensive or hard to reverse. Budget 50, shared across subagent threads.

## Signals in depth

### Stakes

Ask: what happens if the answer is wrong and the user acts on it?

- Nothing much, they notice and move on: Tier 1.
- They lose an afternoon, redo a config, return a product, resend a mail: Tier 2.
- They sign, pay, deploy to production, advise a client, file something with an authority, change medication, make a safety-relevant choice: Tier 3.

Professional context raises stakes. The same version question is Tier 1 for a hobby project and Tier 2 when it goes into a client offer.

### Verifiability

Ask: does one authoritative source settle this?

- Yes, and you know where it lives (official docs, a changelog, a public register, a standards page): Tier 1 is possible.
- Several reputable sources exist and may differ in detail (pricing pages versus reseller pages, two outlets reporting the same event): Tier 2.
- The primary source is hard to reach, the topic is disputed, numbers vary widely between sources, or the field is moving: Tier 3.

### Time sensitivity

Ask: how fast does the true answer change?

- Historical or physical facts, settled definitions: no freshness constraint, tier follows the other signals.
- Yearly change (release cadences, annual reports, most regulations): Tier 2 unless stakes are trivial.
- Monthly or faster (prices, availability, security advisories, office holders in flux, ongoing events, model and API versions in an active field): at least Tier 2; Tier 3 when combined with high stakes.

### Breadth

Count the distinct claims the answer needs (see Step 2 in SKILL.md).

- One claim: Tier 1 or 2 by stakes.
- Two to five claims, or a comparison of two or three options: Tier 2.
- More than five claims, more than three options, or a decision that depends on how the claims interact: Tier 3.

### User wording

Take explicit depth requests at face value. "Quick", "roughly", "just check" mean Tier 1 even if you would have gone deeper; state in the report that a deeper check is available. "Verify", "is it true", "compare", "which one" mean Tier 2. "Thorough", "deep dive", "due diligence", "everything about", "before I decide/sign/buy/deploy" mean Tier 3.

Wording never lowers the tier below what the stakes demand without the user knowing it: if they ask for a quick check on something high-stakes, that is a conflict between signals, and conflicts mean you ask.

## Decision rule

1. Score each of the five signals as 1, 2, or 3, or as "no signal".
2. If all scored signals agree, or the user named a depth and nothing high-stakes contradicts it: pick that tier. Do not ask.
3. Otherwise ask the one question. Common conflict patterns:
   - Casual wording plus high stakes ("quickly, which insurer covers X for my company").
   - A trivial fact bundled with a heavy one ("what does the flag do and is the tool safe for production").
   - No idea what the user does with the answer ("what is the price of X" could be curiosity or a purchase).
   - Time-sensitive topic plus no stakes information.

Asking costs the user one tap or one line. Guessing the tier wrong costs either a shallow answer they act on, or fifty tool calls they did not want.

## The one question

Use the environment's ask-user tool when present, with the three tiers as options and one short line of description each. Otherwise write:

```
Which depth do you want for this?
1. Quick check - one or two sources, seconds.
2. Verified - several independent sources cross-checked, a few minutes.
3. Deep - primary sources, contradiction search, full report, longer.
```

End the turn after asking. Do not pre-search "while waiting". If the user replies with something other than a tier ("just tell me"), take that as Tier 2 for moderate stakes and Tier 3 for high stakes, and say which you chose.

## Mixed requests

When one request contains parts of different weight and the user has not been asked yet, you have two options:

- Split: run the trivial part at Tier 1 and the heavy part at the tier its signals demand, inside one report with a tier line per part. Do this when the parts are independent and the heavy part's tier is clear.
- Ask: when the heavy part's tier is itself unclear. The question then covers the whole request; apply the answer to the heavy part and run the trivial part at Tier 1 regardless.

Do not average the tiers. A request that is half trivial and half high-stakes is not a Tier 2 request.

## Worked examples

| Request | Signals | Tier | Why |
|---|---|---|---|
| "What port does PostgreSQL use by default?" | stable, canonical, one claim, no stakes | 1 | Official docs settle it; nothing changes. |
| "What's the current stable version of Node.js?" | time-sensitive (monthly), canonical, one claim | 1 | One official page answers it; freshness check required (source date within days for a release-cadence question). |
| "Does library X still work with framework Y version Z?" | yearly change, several sources, 2-3 claims, moderate stakes | 2 | Needs the compatibility statement from X's docs plus evidence from Y's changelog; a wrong answer costs a migration afternoon. |
| "Compare the pricing of hosting providers A, B, C for our setup" | monthly change, several sources, comparison, money | 2 or ask | If the user's setup is specified, Tier 2 with one thread per provider's official pricing page. If "our setup" is undefined, that is missing information, but still only one question allowed: ask the tier question and fold in a request for the setup details in the same message. |
| "Is vendor V a safe choice for hosting patient data in Germany?" | high stakes, contested, many claims, regulatory | 3 | Legal and compliance consequences; needs primary sources (vendor contracts, certifications, regulator statements) and contradiction search. |
| "Quick: which of these three CRMs should we buy?" | casual wording versus purchase decision | ask | Wording says 1, stakes say 3. The user decides how much they want. |
| "Who is the CEO of company C?" | time-sensitive, canonical, one claim, low stakes | 1 | Official site or filing; check the date. If the query is for a sales approach to that company, stakes rise to 2 because a wrong name in outreach costs the lead. |
| "Summarise the current state of regulation R for my client memo" | high stakes, changing, many claims, professional | 3 | The memo is advice; primary legal texts and regulator pages required. |

## Restating the tier in the report

The first line of every report names the tier and the reason in one clause, for example: "Tier 2 (verified): compatibility question with moderate stakes, cross-checked against official documentation." At Tier 1, add whether a deeper check would change anything ("A Tier 2 check would add nothing here" or "If this goes into a client document, a Tier 2 check is advisable").
