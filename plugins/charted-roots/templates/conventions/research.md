# Research notes

All are `cr_type: research_project`, in one flat folder. **Genre lives in the filename prefix** (no matching `cr_type` exists). Every note is a substantial document, never a stub.

| Prefix | What | Typical state |
|---|---|---|
| `Hypothesis - ` | claim, evidence for/against, resolution path | `open`, or `completed` + `positive`/`negative` |
| `Survey - ` | executed sweep of a record set | `completed` |
| `Reference - ` | standing material (finding aids, gazetteers, plots) — consult before citing | `completed`, no `result` |
| `Search Plan - ` | strategy not yet executed | `open` |

- Do not retype to `research_report` / `individual_research_note` — they need fields nothing populates.
- Status lives in frontmatter: open = `status: open`; confirmed = `completed` + `result: positive`; refuted = `completed` + `result: negative` (feeds *Negative Findings*). **Closing is a one-field edit — never move or rename.**
- Properties: only `cr_type`, `cr_id`, `title`, `status`, `result`, `date`, `subject`, `related`, `private`. `subject` = the person the question is *about*; `related` = other People, transcriptions, Sources; `date` = when raised, empty if unknown.
- Keep the `**Status:**` prose line, written `**Status:** <badge> …`, with one badge: 🔍 open · ✅ confirmed · ❌ refuted · 📁 standing reference (`Reference - `) · ⛔ superseded or closed without result. If prose and frontmatter disagree, prose wins.
- Keep `_Migrated from …_` lines; decide which copy is authoritative before substantive edits.
- Prose is English; quoted record text, catalogue titles and fond names stay verbatim so they match the archive's index.
