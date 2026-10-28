# AGENTS.md

Conventions for everyone changing this repository, contributors and coding agents alike. README.md lists the
skills and how to install them; this file holds only what is easy to get wrong.

## Commands

```bash
python3 tools/validate.py                         # spec limits, referenced files, Python 3.9 syntax (CI runs it)
python3 usgs-earthquake/scripts/usgs_quake.py -h  # every script documents its options with -h
```

## Where to edit

- Each skill is a folder at the repository root: `<name>/SKILL.md`, `<name>/references/`, `<name>/scripts/`.
  There is no `skills/` folder; `tools/validate.py` only finds skills at the root. Instructions written for
  other skill collections do not apply here.
- Keep file references one level deep from `SKILL.md`, as relative paths (`references/…`, `scripts/…`).
- A new or renamed skill also gets a row in the README table.

## Constraints

- Follow the [Agent Skills specification](https://agentskills.io/specification); `tools/validate.py` enforces
  its limits. The `description` says what the skill does and when to use it. Keep `SKILL.md` under 500 lines
  and move detail into `references/`.
- Skills stay host-neutral: describe capabilities ("the host's web search tool"), never a vendor's tool name.
- Scripts run on Python 3.9 or newer and use the standard library only. They print errors to stderr, exit
  non-zero on failure and work without an API key on the default path. If a paid tier needs a key, read it from
  an argument at run time; never store it.
- The validator only parses scripts; CI also compiles them and runs `-h` on Python 3.9. After changing a
  script, run the examples from its `SKILL.md` (against the live API where the script calls one) and include
  the command and its output in the pull request.
- Keep each `SKILL.md` in step with its script: every flag in an example exists in the script.
  `research-verifier/scripts/grade_sources.py` and `references/source-grading.md` implement the same rules;
  change them together.
- Facts about an API (endpoint, parameter, limit) come from the provider's documentation; link it in the
  reference file. Note a provider's usage terms (for example non-commercial use only) in the README.
- Repository files are English. A skill may tell the agent to answer in the user's language.
- Do not add evaluation runs, test transcripts or personal data.

## Pull requests

- Open a pull request only for an issue the maintainer has replied to, and link it (`Closes #N`).
- One topic per pull request. Run `python3 tools/validate.py` before pushing. Only the maintainer merges.
