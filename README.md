# charted-roots-skills

Claude Code skills for an [Obsidian](https://obsidian.md) genealogy vault managed by the **Charted Roots** plugin.

| Skill | Use |
|---|---|
| `add-archive-record` | One archival document → transcription, Source, Events, Citations, Person updates |
| `ancestry-research` | Plan and run a kinship investigation; regional guides (former USSR, Russian Empire, Galicia/Bukovina, Bessarabia); draft archive requests |
| `vault-verify` | Read-only consistency audit. Its `scripts/` (`crsync`, standard-library Python) is the toolkit the other skills call |
| `gedcom-sync` | Reconcile an upstream GEDCOM export without the duplicates the plugin's import wizard creates |

## Install

```
/plugin marketplace add AntonShevchuk/charted-roots-skills
/plugin install charted-roots@charted-roots-skills
```

Or copy `plugins/charted-roots/skills/*` into your vault's `.claude/skills/`. The skills locate each other as sibling folders, so both layouts work.

Requires Python 3.10+ for the scripts. Pillow is optional (`scan_montage.py` only).

## Set up your vault

The skills read every folder and setting from `.obsidian/plugins/charted-roots/data.json`; nothing is assumed.

- **Core rules** — `skills/vault-verify/references/charted-roots-model.md`: entity model, invariants, evidence chain, vocabularies, places, GEDCOM, date forms. Every skill reads it.
- **Your `CLAUDE.md`** — start from `templates/CLAUDE.md`. It overrides the core rules where they differ, sets the working language, and imports the optional modules. To have the core rules in sessions where no skill runs, copy the model file to `.claude/conventions/` as the template describes.
- **Optional modules** — `templates/conventions/`. Copy the ones you use into `.claude/conventions/`; each skill degrades when one is absent.

| Module | Adds |
|---|---|
| `archive.md` | transcription template, scan files, the Source's `## Linked records` |
| `source-collections.md` | `Collection - <Group>` parent Sources |
| `research.md` | `Hypothesis` / `Survey` / `Reference` / `Search Plan` research notes |
| `letters.md` | outgoing archive requests and their index |
| `history.md` | method + run-record pairs for bulk maintenance |
| `upstream-ancestry.md` | reading an Ancestry export's name convention |

## Notes

- **Privacy.** A genealogy vault holds data on living people. The skills do no web search, upload or e-mail without your explicit instruction, and never send letters.
- **GEDCOM.** `gedcom_sync.py` was written against Ancestry GEDCOM 5.5.1 exports. Other hosts may need adjustments; start with the dry run.
- **Tests.** `cd plugins/charted-roots/skills/vault-verify/scripts && python3 -m unittest discover -s tests -t .` All fixture names are fictional.

## License

MIT — see `LICENSE`. `ancestry-research` is adapted from [ex-ussr-kinship-research](https://github.com/DenisSergeevitch/ex-ussr-kinship-research) and keeps its upstream MIT notice in its own `LICENSE`.
