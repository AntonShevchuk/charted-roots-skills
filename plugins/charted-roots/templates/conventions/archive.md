# Archive documents

A document = a transcription note, plus (if downloaded) a scan beside it with the **same filename**. Archive-coded scans keep the archival code verbatim, prepended to the slug. A transcription without a scan is normal — the Source records where the image lives.

## Transcription template

```markdown
# <Type>: <Name(s)> (<Year>)

## Document Details
* **Document Type**: <native term (English gloss)>
* **Registry Number**: <NNN>
* **Place of Registration**: <Place>
* **Date of Registration**: <Date>
* **Source**: <Title>
* **URL**: <URL>
* **Archive**: <Archive Name>
* **Collection**: <Archive Collection>
* **Entry**: <Archive Entry>
* **Page**: <Page>

## Original Text (<Language>)
<verbatim>

## English Translation
<translation>
```

- **H1 `<Type>`** — short English genre from a small closed list (Birth Certificate, Death Certificate, Marriage Record, Baptismal Record, Burial Record, Census Entry, Press Notice, Obituary, Military Record, Passport, Naturalization Record, Probate, Directory Entry, Passenger List, …); extend deliberately. Marriage names joined by `×`; undated `(n.d.)`.
- **`Document Type`** is always present and carries the register's own term. Every other bullet is optional — **omit, never placeholder**. Values come from the body, not the filename.
- **`## Original Text (<Language>)`** — language first, then an optional bare script word (`(German Kurrent)`) or comma qualifier (`(Russian, pre-reform orthography)`). Wrong: script alone, comma before a script, a language's default script. Keep the label set small; check it before inventing one.
- Every non-English original gets a **complete** `## English Translation` (boilerplate and marginalia included); both sections stay. English originals get none.
- Optional trailing sections, only these, in this order: `## Uncertain readings` (evidentiary — must survive reformatting), then `## Notes` (physical-artefact remarks only; no research, no cross-references).
- No frontmatter, no `---` rules, no links out. **A transcription is linked to, never from.**
- A note with Document Details but no `## Original Text` needs transcribing, not translating. A paraphrase under `## Original Text` is not a transcription — say so.
- Text flagged as handwritten and not fully legible is paraphrase; check the scan before relying on wording.

## What the Source carries

- **`## Linked records`**, with ` · ` between entries:
  - `- **Events:**`, `- **People:**` first (the document → record edges), then `- **Places:**`.
  - Cross-references: `- **Related document:**`, `- **Companion source:**`, `- **Catalogue:**`, `- **Continued in:**`.
  - `- **Scan (<purpose>):**` — plain link, only for a scan the gallery does not convey.
  - `- **Note:**` — which copy, what was captured.
- `- **Events (<occasion>):**` is allowed when one document evidences two clusters; never alongside a generic `Events` bullet.
- `- **People:**` puts `(fact_type)` after each person matching the Citation `fact`; prose about a person goes outside the parentheses.
- Several transcriptions on one Source: group bullets under `**From [[<transcription>]]:**`.
- **Embed each transcription once**, at the foot, in a collapsed callout whose title copies the H1. Add a qualifier (`— copy`, `— p. 2`, `— scan <code>`) only to disambiguate identical titles. Re-sync titles when H1s change.

  ```markdown
  > [!quote]- <H1 text>
  > ![[<transcription filename>]]
  ```

- **One Source per archival item.** Multiple scans/readings of one entry share a Source. A church and a civil register entry for the same event are two items — keep both.
- No `repository` unless the document names one.
- **`- **People:** none` is a decision.** State the reason: subject unidentifiable · identification under open hypothesis · tested and refuted / family excluded · finding aid, not evidence. Never add a Citation without new evidence.

## Scan files

- Rasters are `.jpg` or `.pdf` only; convert PNG to JPEG quality 95 (`sips` on macOS, or ImageMagick).
- Multi-page → one consolidated PDF; delete the page files in the same commit.
- A JPG the user prepared themselves (e.g. a stitched register opening) stays a JPG; if it replaces a scan it takes that filename, and pages it lacks stay as separate labelled files.
- `_pN` means page of this document on split scans, page in the source on books/registers. Never renumber one into the other.
- **A same-named PDF does not make a JPG redundant** — compare embedded-image hashes before deleting. A cropped entry and the full archive download are complementary.
