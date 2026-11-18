# charted-roots-skills

Claude Code skills for an [Obsidian](https://obsidian.md) genealogy vault managed by the **Charted Roots** plugin.

| Skill | Use |
|---|---|
| `add-archive-record` | One archival document → transcription, Source, Events, Citations, Person updates |
| `research-ancestry` | Plan and run a kinship investigation; regional guides (former USSR, Russian Empire, Galicia/Bukovina, Bessarabia); draft archive requests |
| `verify-vault` | Read-only consistency audit. Runs the shared toolkit in `lib/` (`crsync`, standard-library Python), which the other skills call too |
| `sync-gedcom` | Reconcile an upstream GEDCOM export without the duplicates the plugin's import wizard creates |
| `organize-places` | Map a GEDCOM's historical place names to Place notes under modern borders, with the old names as aliases; reviewed in batches |
| `init-vault` | One-time vault setup: `CLAUDE.md`, convention modules, project-scope plugin settings (run it as `/charted-roots:init-vault`) |

## Install

Install per vault (project scope), so the plugin is active only where it is needed. In the vault folder:

```
claude plugin marketplace add AntonShevchuk/charted-roots-skills
claude plugin install charted-roots@charted-roots-skills --scope project
```

Then start Claude Code in the vault and run `/charted-roots:init-vault`. It:

- writes the vault's `CLAUDE.md` from `templates/CLAUDE.md` (or merges into an existing one, showing the diff);
- suggests convention modules from what the vault already contains and copies the ones you pick into `.claude/conventions/`;
- adds the marketplace and `enabledPlugins` entry to the vault's `.claude/settings.json`, so collaborators who clone the vault are pointed at the plugin. Each of them runs the `claude plugin install … --scope project` line once.

Nothing is written before you approve the plan.

Requires Python 3.10+ for the scripts. Pillow is optional (`scan_montage.py` only).

## How the rules load

- **Core rules** — `skills/verify-vault/references/charted-roots-model.md`: entity model, invariants, evidence chain, vocabularies, places, GEDCOM, date forms. A session-start hook loads it into every session started in a Charted Roots vault (detected by `.obsidian/plugins/charted-roots/data.json`) and outputs nothing elsewhere. It stays current with plugin updates; nothing is copied into the vault.
- **Your `CLAUDE.md`** — house rules: working language, git habits, module imports. It overrides the core rules where they differ.
- **Convention modules** — `.claude/conventions/*.md`, copied from `templates/conventions/`. `init-vault` always installs `archive.md` and `source-collections.md`; the rest are opt-in. Each skill degrades when one is absent.

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
- **Tests.** `cd plugins/charted-roots/lib && python3 -m unittest discover -s tests -t .` All fixture names are fictional.

## License

MIT — see `LICENSE`. `research-ancestry` is adapted from [ex-ussr-kinship-research](https://github.com/DenisSergeevitch/ex-ussr-kinship-research) and keeps its upstream MIT notice in its own `LICENSE`.
