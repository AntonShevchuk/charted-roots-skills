# CLAUDE.md

An Obsidian vault of genealogy notes managed by the **Charted Roots** plugin, worked with the `charted-roots` Claude Code plugin.

## Core rules

The entity model, invariants, evidence chain, vocabularies, place and GEDCOM rules ship with the plugin (`skills/verify-vault/references/charted-roots-model.md`); its session-start hook loads them into every session in this vault. This file and the modules below override them where they differ.

## Language

English is the working language for headings, labels, analysis, research prose and commits. Source material is **never translated in place** — the original stays verbatim and a translation is added beside it. Proper nouns, native-script names, archival designations, quoted record text and `aliases:` keep their original form; where a name has both, use the English form in prose and keep the native one in `aliases:` or parentheses.


## House conventions (opt-in modules)

`/charted-roots:init-vault` copies the chosen modules into `.claude/conventions/` and keeps only their lines here.

@.claude/conventions/source-collections.md
@.claude/conventions/archive.md
@.claude/conventions/research.md
@.claude/conventions/letters.md
@.claude/conventions/history.md
@.claude/conventions/upstream-ancestry.md

## Git

One branch; commit a document and its transcription together.

## Keeping this file reusable

Method, not inventory. The same holds for skills and conventions: no vault-specific paths, names or figures — folders by `data.json` key, modules by name. Never commit counts, dates, named notes or per-item tables here — record them in `History/` (or the report, without that module). Assert settings conditionally. Prefer the reason to the instance.
