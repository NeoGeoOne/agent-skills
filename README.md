# agent-skills

[![Validate](https://github.com/starsoules/agent-skills/actions/workflows/validate.yml/badge.svg)](https://github.com/starsoules/agent-skills/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Skills for AI coding agents that replace answers from memory with live, verifiable data. Each skill follows the
open [Agent Skills specification](https://agentskills.io/specification): a folder with a `SKILL.md` (when to use
it and how), reference files the agent loads on demand, and helper scripts. The data skills use free public
APIs that need no key; all scripts use the Python standard library only.

## Skills

| Skill | What it gives the agent | Data sources |
|---|---|---|
| [`open-meteo`](skills/open-meteo/) | Weather forecasts and history, air quality and pollen, marine conditions, climate projections, river floods, ensembles, geocoding and elevation | [Open-Meteo](https://open-meteo.com) |
| [`research-verifier`](skills/research-verifier/) | Tiered web research with source grading, a verification pass and a reliability label plus citation for every core claim | the host's own search and fetch tools |
| [`space-weather-astronomy`](skills/space-weather-astronomy/) | Planet, Moon, comet and spacecraft positions, rise and set times, asteroid close approaches, geomagnetic storms and aurora forecasts | NASA JPL Horizons and CNEOS, NOAA SWPC |
| [`usgs-earthquake`](skills/usgs-earthquake/) | Earthquake records for any place and time: magnitude, depth, aftershocks, tsunami flags, felt reports, ShakeMap and PAGER | USGS Earthquake Hazards Program |

Skills that drive a larger tool live in that tool's repository, so the skill and the code it runs change
together:

| Skill | Repository | What it gives the agent |
|---|---|---|
| [`flarum2-design-ops`](https://github.com/starsoules/flarum2-ops/tree/main/skills/flarum2-design-ops) | [flarum2-ops](https://github.com/starsoules/flarum2-ops) | Flarum 2 forum design-sets and admin API through a bundled engine and MCP server. Needs the repository's setup; see its README |

## Installation

### Claude Code

This repository is a plugin marketplace named `starsoules`; every skill is its own plugin. Install one in a
session (Claude Code 2.1.275 or later):

```text
/plugin install open-meteo --marketplace starsoules/agent-skills
/plugin install research-verifier --marketplace starsoules/agent-skills
/plugin install space-weather-astronomy --marketplace starsoules/agent-skills
/plugin install usgs-earthquake --marketplace starsoules/agent-skills
```

Or add the marketplace once and pick from the list: `/plugin marketplace add starsoules/agent-skills`, then
`/plugin`. Plugin skills are named `<plugin>:<skill>`, for example `usgs-earthquake:usgs-earthquake`. Updates
follow this repository's commits: `/plugin marketplace update starsoules`, or turn on auto-update for the
marketplace in `/plugin`.

### Other agents

With the [skills CLI](https://github.com/vercel-labs/skills) (Node.js 22.20 or later), which supports OpenCode,
Codex, Cursor, Claude Code and many more:

```bash
npx skills add starsoules/agent-skills                          # choose skills and agents interactively
npx skills add starsoules/agent-skills --skill usgs-earthquake  # one skill
```

### Manually

Copy or symlink a folder from `skills/` into your agent's skills directory:

| Agent | Personal (all projects) | Per project |
|---|---|---|
| Claude Code | `~/.claude/skills/<name>/` | `.claude/skills/<name>/` |
| OpenCode | `~/.config/opencode/skills/<name>/` | `.opencode/skills/<name>/` |
| Other Agent Skills hosts | `~/.agents/skills/<name>/` | `.agents/skills/<name>/` |

```bash
git clone https://github.com/starsoules/agent-skills.git
mkdir -p ~/.claude/skills
ln -s "$PWD/agent-skills/skills/usgs-earthquake" ~/.claude/skills/usgs-earthquake
```

The agent picks a skill up by its description; no further configuration is needed. The helper scripts need
Python 3.10 or newer.

## Validation

```bash
python3 tools/validate.py
```

Checks every skill in `skills/` against the specification (name, description and compatibility limits, name
matches the folder, frontmatter that YAML would misread), that every file named in a `SKILL.md` or reference
file exists, and that every script parses as Python 3.10. CI runs the same check, runs every script on Python
3.10 and validates the marketplace with `claude plugin validate . --strict`.

## Contributing

Bug reports and ideas are welcome as [issues](https://github.com/starsoules/agent-skills/issues/new/choose).
Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request. Security issues: see
[SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE). The data belongs to the respective providers; check their terms before commercial use
(for example, Open-Meteo's free API is for non-commercial use).
