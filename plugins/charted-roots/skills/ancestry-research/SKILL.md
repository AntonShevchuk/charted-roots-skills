---
name: ancestry-research
description: Use when researching a person, family line or kinship question in an Obsidian + Charted Roots vault — planning a search, reading church/metric books, civil registers, revision lists, censuses, military, migration, deportation or repression records, disambiguating namesakes, deciding whether two records are the same person, or drafting an archive request. Strongest for the former USSR, the Russian Empire, Habsburg Galicia/Bukovina and Bessarabia; the evidence method applies anywhere. Writes results into the vault's own notes. Not for tracking living people.
---

# Ancestry research

Prove or refute kinship through reproducible research. Every record is an **artefact, not a fact** until assessed; keep the record separate from its interpretation, respect historical borders and name variants, rank conclusions by strength of evidence.

Reading a supplied metric-book page or searching one book: scope by the request — an extract or hit list with locators and caveats is enough for a point task (`references/metric-books-scans.md`).

Adapted (MIT, see `LICENSE`) from `DenisSergeevitch/ex-ussr-kinship-research`. Last synced with upstream v1.45.0 (commit 64b032a). The upstream case-folder workflow (CSV registers, HTML/PDF reports, GEDCOM export) is replaced by the vault's own stores. **Do not re-install or auto-update from upstream**; port useful upstream changes by hand.

## Rules that win

The core model (`<vault-verify>/references/charted-roots-model.md`, where `<vault-verify>` is `${CLAUDE_SKILL_DIR}/../vault-verify`), the vault's `CLAUDE.md` and its `.claude/conventions/*` override anything in this skill or its references. In particular:

- **Language** — the vault's working language (its `CLAUDE.md`; English if unstated) for prose, headings, labels. Quoted record text, archival designations and native-script names stay verbatim, with a translation beside them. Search queries are written in the *source's* language.
- **Privacy** — the vault holds living people. **No web search, portal lookup, upload or e-mail without the user's explicit instruction for this task.** Reading local scans and notes needs none.
- **Stop and ask** — on an uncertain identification, two vault people who both fit, a place missing from the gazetteer, or any write to an existing fact. Otherwise work through the plan without asking "continue?" after each step.
- **Never** create a Citation without new evidence, invent a `cr_type`, edit the vault's `.ged`, or push structure upstream by round-trip.

## Vault terms

Resolve these once per session — from `.obsidian/plugins/charted-roots/data.json` and `.claude/conventions/` — and use them below. A module that is absent means its row falls back as stated.

| Term | Resolves to | If absent |
|---|---|---|
| **research folder** | where `cr_type: research_project` notes live (search by `cr_type`) | ask where to create the first one |
| **archive folder** | the `mediaFolders` entry holding scans + transcriptions (`archive.md`) | first `mediaFolders` entry |
| **media folder** | the `mediaFolders` entry for other media (photos) | archive folder |
| **letters folder / letters index** | `Letters/` + `Letters Index.md` (`letters.md`) | give the draft to the user in the conversation; create nothing |
| **upstream tree** | the hosted master and its `.ged` export (core model § GEDCOM, any upstream-tree convention) | the vault is its own master; no sync |
| **history** | `History/` method + run-record pairs (`history.md`) | skip |

## Where things live

| Research object | Vault store | How |
|---|---|---|
| Research question, scope, constraints | research folder: `Search Plan - <topic>.md` | `research.md` |
| Competing identification or kinship claim | `Hypothesis - <claim>.md` — evidence for/against, resolution path | `research.md` |
| Executed sweep of a record set (incl. nil results) | `Survey - <record set>.md`, `completed`; nil sweep → `result: negative` | `research.md` |
| Finding aid, gazetteer, fond/opis list | `Reference - <topic>.md` | `research.md` |
| A record (scan, register entry, index hit) | Source + transcription + scan in the archive folder | `add-archive-record` |
| One fact about one person from one record | Citation (`fact`, `page`) + Event | `add-archive-record` |
| Established person / relationship | Person note, relationship wikilink + `_id` | core model § Invariants |
| Unidentified candidate | stays inside the Hypothesis note — **no Person note** until identified | — |
| Request to an archive or registry | letters folder note + row in the letters index | `letters.md` |
| Photo of a person | media folder, `.jpg`/`.pdf` | `archive.md` § Scan files |
| Upstream tree | its `.ged` — lead, not evidence; synced only via `gedcom-sync` | core model § GEDCOM |

Without `research.md` the filename prefixes are a suggestion: keep the same split (plan / claim / sweep / reference) in `research_project` notes.

Reading the upstream tree: a tree entry without a cited image is a lead. Never treat two trees that copy each other as independent.

## Evidence rules (non-negotiable)

1. Copies, mirrors, indexes and retellings of one record are **one** archival item → one Source (`archive.md`); they never corroborate each other.
2. A relationship is established only by independent evidence chains. One strong primary record is still a single source — say so in the Hypothesis.
3. Never merge two namesakes on name, age or place alone. Keep candidates apart until a distinguishing feature appears; record the reason for every merge or split.
4. Keep original spelling of names, dates and places; a normalised form is a research form, labelled as such (`aliases:`).
5. Never hide contradictions; keep alternative hypotheses open beside the conclusion.
6. A nil search is not proof of absence — record it as a Survey with its coverage.
7. Never invent missing data or promote family memory to documentary fact.
8. Do not bypass access limits. One CAPTCHA attempt through the normal browser UI at most; login is the user's (`references/browser-and-captcha.md`).
9. Living people: minimum data; no current addresses, phones, accounts, ID numbers or data on minors (`references/privacy-and-safety.md`).

**Assessment vocabulary.** On the Source, `confidence` (`high` / `medium` / `low`) rates the *reading*, not the document's authority (core model); primary vs derivative goes in the Source body. On a Hypothesis, use these words in prose: *hypothesis* · *single-source* · *corroborated* (≥ 2 independent chains, no unresolved material conflict) · *strongly corroborated* (several chains incl. one direct record of known provenance) · *contradicted* · *unresolved*. Frontmatter stays `status` / `result` per `research.md`. Full assessment scheme (originality, informant, directness, independence, identity resolution, DNA, which relationships count as established): `references/evidence-protocol.md`.

## Workflow

1. **Frame.** Restate the question; list known names, spellings, approximate dates, places, confession, occupation, relatives, migrations. Mark who may be alive. Before an action that depends on someone being alive (interview, DNA test, request on their behalf), check what the Person note and the vault say; if unknown, keep it unknown and plan the action conditionally (`references/privacy-and-safety.md` § 2). Ask one targeted question only if the answer decides the action; meanwhile continue the other work. Family memory: `references/relatives-interview.md`. Search the vault first (every folder, the letters folder, history, existing Hypotheses) — by name variants and `cr_id`. Open or extend a `Search Plan -` note.
2. **Historical model.** Jurisdiction *on the event date*; successor archive; old and new toponyms; original calendar — never convert silently (`references/ex-ussr-locale-guide.md`). Build a name-variant matrix: as written, pre-reform spelling, local language, Cyrillic/Latin, patronymic, surname ending, Russification, church vs everyday form; for women, maiden and every married surname. Regional guides: Galicia/Bukovina → `habsburg-galicia-bukovina.md`; Bessarabia/Moldova/MASSR → `bessarabia-moldova.md`; Chechen 1944 deportation → `chechnya-deportation.md`; Ostarbeiter / Soviet citizens in Germany 1941–45 → `germany-forced-labour.md`; Mari El, Pavlodar, Uzbekistan → `regional-routes-mari-pavlodar-uzbekistan.md`.
3. **Plan.** Start from the latest securely known event and walk back one link at a time. Pick the record type per gap (ZAGS act, metric book, confession list, revision list, family list, census, military, evacuation, repression, migration, address calendar, obituary, cemetery). Go from an index to the original it names. Tactics: `references/source-strategy.md`; catalogue: `references/seed-sources.md` (read its full structure, not just the top); field techniques for unindexed scans, repression files, vanished hamlets, occupied territory: `references/field-lessons.md`; Russian ZAGS certificates with «Иные сведения», repression and rehabilitation files and access, dekulakisation and disenfranchisement, cemetery records: `references/russia-records-access.md`.
4. **Search** — only once the user has authorised web work for this task. Sequential, no bulk requests. Record each query (exact string, language, filters, URL, date, result) in the Survey note. For scans, look at the page itself, not the OCR or snippet; check the viewer has loaded it (`browser-and-captcha.md` § 2, "Loading frames and indexes"). Reading an entry or searching a metric book: `references/metric-books-scans.md`; other handwritten tables and disputed readings: `field-lessons.md` § 1, "Checking a visual reading". Browser: reuse working pages, close your own unneeded tabs after a check or batch; before the final answer and on an early stop run the `browser-and-captcha.md` § 9 "Working tabs" check. Memorial and family sites: use their own search. FamilySearch indexes: `references/familysearch-indexes.md`; FamilySearch MCP: `references/familysearch-mcp.md`; WWI cards on GWAR: `references/ww1-search.md`; photos: `references/photo-search.md`; validating a hit, catalogue conflicts, reused searches: `references/search-result-validation.md`.
5. **Record.** Each relevant record → `add-archive-record` (transcription with `## Uncertain readings` for doubtful text, Source, Citations, Events). Index-only hits that identify nobody yet → Source with `- **People:** none` and its reason, or a line in the Survey.
6. **Identify.** Match on the whole cluster — dates, places, relatives, occupation, estate, confession, witnesses, godparents, unit, migration route. A shared household is not kinship; a patronymic alone does not prove paternity. Build compound links edge by edge (grandparent = two parent–child edges). Distinguish biological, legal, adoptive, step and household relationships.
7. **Conclude.** Update the Hypothesis: evidence for/against per edge, status word, next distinguishing check. Close it per `research.md` (one-field edit). Sensitive findings (adoption, paternity, repression, ethnicity, religion) — neutral wording, only what the question needs, cited.
8. **Request.** When the answer needs an unpublished record: choose the current custodian and its official channel (`references/correspondence.md`, `references/government-portals.md`), draft in the letters folder in the recipient's language. **Never send**; the user sends.
9. **Verify and report.** `vault-verify` over the changed notes. Report to the user in the working language: what is established, what is not, search coverage, open routes (who must act, cost/access if known). For a pass, show the new checks and results; say up front when only a title or description was available, giving the designation if known; separately list records/pages read, what was compared, what stays open. Resuming: take prior coverage from the Survey note and justify significant repeats. Editing a biography (Research Notes prose, a narrative for the family): keep each claim's source, locator and caveats per `research-coordination.md`, "Keep the grounds when editing a biography". Commit only when asked. Resuming after a break, or several agents on one question: `references/research-coordination.md`.

## Scripts

Standard library unless noted. Outputs go to the session scratchpad, never into the skill folder (the scripts refuse that).

| Script | Use |
|---|---|
| `scripts/familysearch.py browser-import <files…> --surnames … --beacons …` | name search inside saved FamilySearch page fragments (`familysearch-indexes.md`) |
| `scripts/gwar.py search\|volost\|places\|page` | WWI card lookups on GWAR / Pamyat Naroda; bundled Russian CA certs are scoped to this one connection (`ww1-search.md`) |
| `scripts/gwar.py surnames --input <saved.json…> --target "<surname>"` | offline: group surname spellings across saved GWAR results, ranked against the family's form (`ww1-search.md`) |
| `scripts/scan_montage.py <dir> --out … --box x0,y0,x1,y1` | strips of the same column across hundreds of frames for fast reading (needs Pillow) |

## Errors

- Unreadable document → keep it, describe the defect, ask for a better copy; continue elsewhere.
- Source vanished → official catalogue, web archive within its rules, mirrors (not independent).
- Unclear jurisdiction → check plausible places, parishes, archives in parallel; do not merge candidates meanwhile.
- Several namesakes → widen the family cluster; never pick by intuition.
- Document vs family memory → keep both as separate claims with their sources; "born" ≠ "grew up".
- Living person without a family-history basis → narrow to the user's own materials or stop the intrusive part.
- Routes exhausted → list established / not established / coverage once; routes waiting on the user are not exhausted. Leave the Search Plan current so work resumes from it.
