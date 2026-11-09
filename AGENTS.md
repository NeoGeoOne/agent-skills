# AGENTS.md

Conventions for everyone changing this repository, contributors and coding agents alike. README.md lists the
skills and how to install them; this file holds only what is easy to get wrong.

## Commands

```bash
python3 tools/validate.py                                # spec limits, referenced files, Python 3.10 syntax (CI runs it)
python3 skills/usgs-earthquake/scripts/usgs_quake.py -h  # every script documents its options with -h
claude plugin validate . --strict                        # marketplace file (CI runs it)
```

## Where to edit

- Each skill is a folder in `skills/`: `skills/<name>/SKILL.md`, `references/`, `scripts/`. `tools/validate.py`
  checks every folder there. This is the layout the [skills CLI](https://github.com/vercel-labs/skills) and
  Claude Code plugin marketplaces discover.
- `.claude-plugin/marketplace.json` makes the repository the Claude Code marketplace `starsoules` (the name
  `agent-skills` is reserved by Claude Code). Every skill is its own plugin entry with `"source": "./"` and
  `"skills": ["./skills/<name>"]`, so it loads only that skill. A plugin's `name` is permanent: users install by
  `name@starsoules`. Leave `version` out so installs follow the commits; there is no `plugin.json`.
- Keep file references one level deep from `SKILL.md`, as relative paths (`references/…`, `scripts/…`).
- A new skill also gets a plugin entry in `marketplace.json`, a row in the README table and a `/plugin install`
  line in the README. Skills that drive a larger tool stay in that tool's repository and get a README row only.

## Constraints

- Follow the [Agent Skills specification](https://agentskills.io/specification); `tools/validate.py` enforces
  its limits. The `description` says what the skill does and when to use it. Keep `SKILL.md` under 500 lines
  and move detail into `references/`.
- Skills stay host-neutral: describe capabilities ("the host's web search tool"), never a vendor's tool name.
- Scripts run on Python 3.10 or newer and use the standard library only. They print errors to stderr, exit
  non-zero on failure and work without an API key on the default path. If a paid tier needs a key, read it from
  an argument at run time; never store it.
- The validator only parses scripts; CI also compiles them and runs `-h` on Python 3.10. After changing a
  script, run the examples from its `SKILL.md` (against the live API where the script calls one) and include
  the command and its output in the pull request.
- Keep each `SKILL.md` in step with its script: every flag in an example exists in the script.
  `skills/research-verifier/scripts/grade_sources.py` and `references/source-grading.md` implement the same rules;
  change them together.
- Facts about an API (endpoint, parameter, limit) come from the provider's documentation; link it in the
  reference file. Note a provider's usage terms (for example non-commercial use only) in the README.
- Repository files are English. A skill may tell the agent to answer in the user's language.
- Do not add evaluation runs, test transcripts or personal data.

## Pull requests

- Open a pull request only for an issue the maintainer has replied to, and link it (`Closes #N`).
- One topic per pull request. Run `python3 tools/validate.py` and `claude plugin validate . --strict` before pushing. Only the maintainer merges.
