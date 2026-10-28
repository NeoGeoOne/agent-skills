# agent-skills

[![Validate](https://github.com/NeoGeoOne/agent-skills/actions/workflows/validate.yml/badge.svg)](https://github.com/NeoGeoOne/agent-skills/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Skills for AI coding agents that replace answers from memory with live, verifiable data. Each skill follows the
open [Agent Skills specification](https://agentskills.io/specification): a folder with a `SKILL.md` (when to use
it and how), reference files the agent loads on demand, and helper scripts. The data skills use free public
APIs that need no key; all scripts use the Python standard library only.

## Skills

| Skill | What it gives the agent | Data sources |
|---|---|---|
| [`open-meteo`](open-meteo/) | Weather forecasts and history, air quality and pollen, marine conditions, climate projections, river floods, ensembles, geocoding and elevation | [Open-Meteo](https://open-meteo.com) |
| [`research-verifier`](research-verifier/) | Tiered web research with source grading, a verification pass and a reliability label plus citation for every core claim | the host's own search and fetch tools |
| [`space-weather-astronomy`](space-weather-astronomy/) | Planet, Moon, comet and spacecraft positions, rise and set times, asteroid close approaches, geomagnetic storms and aurora forecasts | NASA JPL Horizons and CNEOS, NOAA SWPC |
| [`usgs-earthquake`](usgs-earthquake/) | Earthquake records for any place and time: magnitude, depth, aftershocks, tsunami flags, felt reports, ShakeMap and PAGER | USGS Earthquake Hazards Program |

## Installation

Copy or symlink a skill folder into your agent's skills directory:

| Agent | Personal (all projects) | Per project |
|---|---|---|
| Claude Code | `~/.claude/skills/<name>/` | `.claude/skills/<name>/` |
| OpenCode | `~/.config/opencode/skills/<name>/` | `.opencode/skills/<name>/` |
| Other Agent Skills hosts | `~/.agents/skills/<name>/` | `.agents/skills/<name>/` |

```bash
git clone https://github.com/NeoGeoOne/agent-skills.git
mkdir -p ~/.claude/skills
ln -s "$PWD/agent-skills/usgs-earthquake" ~/.claude/skills/usgs-earthquake
```

The agent picks a skill up by its description; no further configuration is needed. The helper scripts need
Python 3.9 or newer.

## Validation

```bash
python3 tools/validate.py
```

Checks every skill against the specification (name, description and compatibility limits, name matches the
folder, frontmatter that YAML would misread), that every file named in a `SKILL.md` or reference file exists,
and that every script parses as Python 3.9. CI runs the same check and also runs every script on Python 3.9.

## Contributing

Bug reports and ideas are welcome as [issues](https://github.com/NeoGeoOne/agent-skills/issues/new/choose).
Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request. Security issues: see
[SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE). The data belongs to the respective providers; check their terms before commercial use
(for example, Open-Meteo's free API is for non-commercial use).
