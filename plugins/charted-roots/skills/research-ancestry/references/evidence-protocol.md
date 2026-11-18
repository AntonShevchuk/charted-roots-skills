# Evidence protocol

Read this file when assessing sources, resolving people of the same name, corroborating, and preparing a conclusion.

## Terms

- **Artefact** — a preserved research object: document, page, scan, database entry, photograph, letter, interview, extract or search result. In the vault: a Source (plus transcription and scan in the archive folder, via `add-archive-record`); a search result that identifies nobody yet is a line in the Survey or a Source with `- **People:** none` and its reason.
- **Claim** — one testable proposition drawn from one or more artefacts. In the vault: a Citation (one source → one `fact` about one person, locator in `page`) plus the Event it evidences; identification and kinship claims are argued in a `Hypothesis -` note.
- **Evidence chain** — the path from the underlying source to the claim. Copies and indexes of one original belong to one chain — one archival item, one Source (`archive.md`).
- **Independence** — absence of a shared underlying document, a shared informant or evident copying.
- **Identity candidate** — a separate candidate that cannot yet safely be merged with another. In the vault it stays inside the Hypothesis note; it gets no Person note until identified.
- **Kinship edge** — a specific relationship between two people, with its type and evidence. In the vault: a relationship wikilink + `_id` between two Person notes, written only once established; until then, an edge argued in a Hypothesis.

## Basic principle

Assess not "how good the site is" but the specific record for the specific claim. One and the same source may be strong for the date a document was issued and weak for a date of birth reported decades later.

## Assessing an artefact

Record the assessment in the Source body (primary vs derivative, provenance, readability); `confidence` on the Source rates the reading only (core model).

### 1. Provenance

Record what is available; mark the unknown explicitly and refine it as the search proceeds:

- the institution or owner of the original;
- fond, opis, delo, leaf/frame, act number;
- a stable identifier of the record;
- the path from the original to the accessible copy;
- the access date, and a checksum if a local copy is kept.

Where numbering differs, give separately the archival leaf and verso, the printed page, the PDF page, the viewer frame and the filename. Mapping between them must rest on verification: a file `2515.jpg` does not by itself establish leaf 2515. For part of an opening, state the side or area; the start of another book on the right-hand half does not change what the left-hand half belongs to.

Several frames may be different photographs of one leaf. Keep the provenance of each file obtained, but do not add re-photographed acts to the research coverage again. Different hashes mean different bytes, not different historical records; establish that a record is the same from its content and address. In doubt, leave a presumed repeat unresolved. Several scans or readings of one entry share one Source (`archive.md`).

Unknown provenance sharply reduces an artefact's usefulness, even if the image looks convincing.

### 2. Originality

Use the categories (in the Source body; they feed the primary/derivative statement there):

- `original` — the physical original;
- `image-of-original` — scan/photograph of the original;
- `official-extract` — an official extract;
- `index` — an index or card;
- `transcription` — a transcription;
- `derivative` — retelling, tree, article, forum;
- `unknown` — provenance not established.

An index helps find the original but does not replace it if the image is accessible.

**Material from family pages.** Assess each item separately. The story and dates on the page are family testimony; the informant is the page's author (a relative). A scan of a document on the same page is `image-of-original` with the provenance "family archive, published on <site>"; its evidential weight is determined by the document itself. If the page merely retells a document you already have, it is the same archival item — not a second chain; note it on the existing Source rather than counting it as corroboration.

### 3. Contemporaneity and informant

Record when the entry was made and who supplied the information. A death record may be primary for the date of death but secondary for the place of birth. An autobiography may be direct for self-identification but motivated and inaccurate.

**Numbers and order in family reports.** Keep the informant's exact words and distinguish the total number of children, the child's birth order and the completeness of the memory. "Five in all" does not mean "the fifth child"; "I remember three" does not establish how many children there were in total or survived. That a relative is not remembered does not on its own imply that they died earlier. Keep the informant's clarification together with the earlier statement and revise the dependent conclusions; do not remove contradictions by guesswork.

### 4. Directness

- `direct` — the record names the relationship or event being tested outright;
- `indirect` — the relationship is inferred from a combination of features;
- `negative` — an expected record is absent where full coverage is proven;
- `lead-only` — the material only gives a direction for searching.

### 5. Readability

Use `clear`, `partial`, `poor`, `unreadable`. Do not turn a doubtful reading into an exact name. Keep the fragment, the page and the alternative readings — the alternatives go into the transcription's `## Uncertain readings` section (`archive.md`), not as inline markers in the original text. Readability is what the Source's `confidence` (`high` / `medium` / `low`) expresses.

### 6. Independence

Check dependence when you use several records as independent confirmations of one claim. Start from the available content and provenance of the documents: where the information came from, who supplied it, whether it was carried over from an earlier record. A shared parish, archive or clerk does not by itself establish dependence; different institutions or forms do not guarantee independence. If provenance remains unclear, record that and continue the research, without claiming an additional independent chain merely because copying was not detected. Further tracing of where information came from is needed when it could change a material conclusion; do not turn it into a mandatory audit of every document.

For example, a marriage entry may take a date of birth from an attached metric record and at the same time report that the marriage took place. The borrowed date does not become a second confirmation of the birth; the provenance of the information about the marriage is considered separately. A mixed document need not be declared wholly independent or wholly discounted. Do not treat a match of birth and baptism dates as self-evident: first establish which event each column speaks of.

In the vault the unit of independence is the archival item: **one Source per archival item** (`archive.md`). The Source is the chain; its index, scan, mirror and repeat download belong to it and never corroborate it. A summary that combines different underlying lines (a compiled certificate, an abstract of several registers) is split per line: cite each underlying record it names through its own Source, with the locator of that record. Copies of one record stay on one Source. For a mixed case, explain the dependence in the Hypothesis and keep a conservative status word if an additional chain is not justified. Several chains may each support a different part of a compound claim without forming two complete independent chains for the whole claim. Do not create a second Source for the same item to make a claim look corroborated. A clean `verify-vault` run does not prove historical independence.

Group chains by their underlying line, for example:

- RGIA f. 1343, d. 56, l. 12 — the original file and all its copies → one Source;
- stories going back to one informant → one oral-history Source (or one per recorded interview of that informant, never counted as separate chains);
- an OBD card and its mirrors → one Source;
- a metric entry of 1902, act 17, its index and a family tree that copied the index → one chain; the tree is a derivative of the Source, not new evidence.

Two URLs do not mean two independent chains.

Several readings of one image by people, models or OCR remain one documentary chain. Checking a reading can refine the transcription, but does not create a new chain and does not by itself raise the status to *corroborated*. In the note on a disputed reading (`## Uncertain readings`) record the hints and additional context used; repeating an answer in the same chat is not an independent check. The practical procedure: `field-lessons.md`, section 1, "Checking a visual reading".

Index hits and cards found by search are `originality: index`, `directness: lead-only` until the original is read and its provenance checked; record them in the Survey (or as a Source with `- **People:** none` and its reason). Before using one in a claim, attach it to the Source of the underlying document; its index, scan, mirror and repeat download belong to the same chain. An ID of a person inside an index is not a vault `cr_id`. A lead noted by the researcher from another resource (e.g. "page 12, row 3 of an address calendar") goes into the Survey with the resource, the query and what was seen; its type and originality stay unknown and it stays a lead until assessed. Missing coverage means *partial*: describe the volume actually checked and its bounds; that is not a claim about the completeness of the whole resource. An empty result with unknown coverage does not mean the record is absent.

## Claim statuses

These are prose words in the Hypothesis note (`SKILL.md` § Assessment vocabulary); frontmatter stays `status` / `result` per `research.md`.

### *hypothesis*

There is a research supposition but no usable evidence.

### *single-source*

There is one evidence chain. It may be strong and direct, but not yet corroborated.

### *corroborated*

Requirements:

1. at least two independent chains;
2. both genuinely relate to the same person/event;
3. no unresolved material contradiction;
4. the Hypothesis explains why the sources are independent.

### *strongly corroborated*

In addition to *corroborated*:

- at least one direct record of established provenance;
- the body of evidence covers the key identifiers rather than repeating one name;
- alternative candidates have been checked and reasonably excluded.

### *contradicted*

Strong evidence is incompatible with the claim. Do not remove the supporting material; describe why the contradicting evidence weighs more, or why the question remains disputed.

### *unresolved*

The data are insufficient, the sources are dependent, or the conflict cannot be resolved.

A status describes the result of checking, not permission to continue work. Keep useful findings and interim conclusions as *single-source* or *unresolved* while you look for distinguishing information and explore other branches.

## The confidence field

In the vault, `confidence` lives on the Source and rates the **reading** of the document, not its authority or the strength of a claim (core model). Use only `high`, `medium` or `low` on non-import Sources (never `unknown`), and explain the basis in the Source body. `confidence` does not replace the Hypothesis status word and is not a probability. Do not use percentages, and do not raise confidence merely because of the number of dependent copies.

## Resolving identity

Do not merge records on one feature. Compare the matrix (in the Hypothesis note):

| Feature | Content |
|---|---|
| Name and variants | Original and normalised forms |
| Date/age | Exact, approximate, calculated |
| Place | Settlement and historical jurisdiction |
| Parents | Names, patronymics, status |
| Spouse/children | Names and sequence of events |
| Occupation/estate | Stability or change |
| Address/household | House, street, yard, neighbours |
| Military service | Unit, rank, place of conscription |
| Witnesses/godparents | Recurring social cluster |
| Signature/handwriting | Only as a supplementary feature |

If two people remain possible, keep both candidates in the Hypothesis and check them in parallel by distinguishing records, without waiting for a final choice to continue the other searches. If two existing Person notes both fit, stop and ask (`SKILL.md` § Rules that win).

If an early death could distinguish namesakes, start with the available death records for the year of birth and the following year. Allow for separate books, sections and actual coverage. Match the record to a candidate by parents, age, place and other distinguishing features. A confirmed death before an established later event excludes that candidate; the identity of the others still needs checking. When searching later births, allow for a name being reused in the family. Assess a match with a family date together with the other evidence, allowing for the calendar and possible name days (`ex-ussr-locale-guide.md`, section 5). Age and an approximate birth year help choose the search range. If an exclusion so far rests only on family memory, keep that ground and the uncertainty in the Hypothesis.

That a record belongs to a particular person and that a kinship edge is proven are separate conclusions with their own sources. An established identity does not make all its relationships *corroborated*; a direct statement of kinship in a document does not remove the question of a namesake. A patronymic helps propose a candidate father but does not by itself prove paternity. Keep *single-source* or *unresolved* until the edge in question has sufficient support under the general status rules.

## Testing kinship types

### Parent — child

Strong basis: a birth/baptism/adoption record or civil act naming both parties directly. For corroboration, look for an independent record: marriage, house register, census, military questionnaire, probate file, death, or another family document.

### Spouses

Strong basis: a marriage record. Supplement with the children's births, household lists, addresses and death. Cohabitation by itself does not prove marriage.

### Siblings

Confirm common parents for each person. A shared surname, household or patronymic is insufficient.

### Grandparent — grandchild

Do not infer in one jump. Prove two separate parent–child edges and show each in the Hypothesis.

### Adoptive, guardianship, step and household relationships

Keep the exact category of the source. Do not rename a legal or household relationship as a biological one.

### DNA

Use only data provided and authorised by the user. A DNA match is an independent class of evidence, but on its own usually does not establish the exact relationship path. Do not upload data to third-party databases without separate consent.

**Independence.** Apply the "Independence" section to the specific claim. A repeat download of the same test, or display of the same match on another platform, does not create independent confirmation. Do not lump all results of one tester into one chain: assess different matches and segments by origin and inheritance path. Matches with a relative and their descendants may depend on one inherited segment; several matches do not by themselves confirm a shared segment or a particular ancestor. The match's tree is not automatically independent either: check whether it retells a document already counted or another tree. Treat each specific observation (one match as shown by one service) as one item, with its copies; explain related segments and the limits of the grouping in the Hypothesis, per the rule for mixed artefacts.

**Observation and inference.** Keep the available identifiers of the test and match, the service, the date, the analysis version if known, and the metrics shown: shared cM, longest segment, number and coordinates of segments. Leave the unknown unknown. The observation "the service reports such a match with so many cM" may be *single-source*; it does not establish the exact relationship path. Keep a path suggested by someone else's tree as a hypothesis until it is grounded. Determine the status of each claim and kinship edge per "Claim statuses": DNA and document must support precisely the relationship being tested, with independence and contradictions assessed; a match of names or of two classes of source is not enough for *corroborated*.

**Narrowing the common ancestor.** Compare the match's question-relevant lines, places and periods, noting gaps and the provenance of their tree. A shared locality and surname are leads, not a proven line or the user's place of origin. Tests of parents and established relatives can help determine the side of inheritance. Shared matches, their geography or surname are not enough on their own to assign a distant match to the paternal or maternal side; compare them with verified kinship lines, parents' tests and available segments ([FamilyTreeDNA explanation](https://blog.familytreedna.com/interpreting-family-finder-matches/)). The absence of a match in a full sibling does not by itself establish the side or refute the presumed distant relationship: siblings inherit different stretches of DNA ([Ancestry explanation](https://help.ancestry.com/hc/en-us/articles/53933347951507-Should-Other-Family-Members-Test-with-AncestryDNA)). The absence of a shared X segment does not by itself establish the side either. Keep an unfounded link between the match's surname and a particular line of the user's as a *hypothesis*. Shared matches help select candidates but do not replace comparison of available segments and checking of pedigrees; overlapping coordinates do not by themselves prove a single inheritance path ([FamilyTreeDNA explanation](https://blog.familytreedna.com/family-finder-matrix-update/)). Y-DNA and mtDNA concern only the direct paternal and direct maternal lines; a shared haplogroup does not by itself name a recent common ancestor.

**Ethnicity estimates** depend on the reference panels and the method version; they do not establish a particular ancestor ([FamilyTreeDNA method description](https://blog.familytreedna.com/recent-and-ancient-origin-results/)). Many short matches may reflect distant common origin, endogamy or chance similarity; their number by itself does not prove the cause and does not exclude close kinship. Consider shared cM, segment lengths, quality of the available data and possible multiple paths together, without a universal threshold or automatic status upgrade ([FamilyTreeDNA matching white paper](https://blog.familytreedna.com/wp-content/uploads/2021/08/Family_Finder_Matching_WhitePaper.pdf), sections Relationship Estimation and Summary and Limitations).

**Working in DNA service accounts.** Only on the user's explicit instruction for this task (`SKILL.md` § Rules that win). Use access within the task and the rights of the connection, without changing other people's records. Ordinary actions in the user's own chosen tree or notes are done within the scope the user has already authorised. For living matches, keep in the vault only the information needed for the check, where possible under neutral labels rather than names; do not copy unrelated profiles. `privacy-and-safety.md`, sections 2, 4–6, apply. Purchases and changes to account settings only within the scope the user has already authorised. A request to a person for access to a private tree or membership is an external message per `correspondence.md` — drafted in the letters folder, never sent by the agent; access to an account does not by itself authorise correspondence.

**Terms of access in DNA service accounts.** For automated work, take into account the terms of the chosen service and the permission already given for the specific method. For example, the [GEDmatch terms](https://www.gedmatch.com/terms-of-service-november-22-2024/), read on 13.11.2026, prohibit crawling pages to collect data and allow access to be terminated for a violation. The author of [#258](https://github.com/DenisSergeevitch/ex-ussr-kinship-research/pull/258) reported their account being disabled after automated reading. Where the terms prohibit it or are unclear, leave that method unavailable and continue with the material already authorised. If needed, the user can pass on the relevant information obtained in the normal way. On refusal, do not switch to another account. Record the restriction and the resume point per `browser-and-captcha.md`, section 8. A request to support goes per `correspondence.md`.

**Match list filters.** The author of [#235](https://github.com/DenisSergeevitch/ex-ussr-kinship-research/pull/235) reported on 11.11.2026 that in the Genotek account examined a combination of tags narrowed the list, and after changing the «Общие родственники» (shared relatives) filter the list updated with a delay. Before concluding that the result is empty, check the active tags and the match selected in the filter header. If the list is still updating or the selected filter is unclear, record the state as unchecked. Check the actual sample per `search-result-validation.md`.

**"Possible common ancestor" fields on a match card.** Per the observation of the author of [#128](https://github.com/DenisSergeevitch/ex-ussr-kinship-research/pull/128) of 30.10.2026, in the Genotek cards examined, the lists of possible surnames and places repeated information from the match's tree; for large trees the list was broad. This observation does not establish the service's algorithm. Check the origin of the specific field: treat a retelling of a tree as another user's tree, `derivative`; with unknown origin keep the uncertainty. The field name and a match of surname or place do not by themselves establish a common ancestor or that all matches found belong to one branch. Use them as leads per "Narrowing the common ancestor"; rules of access and actions in the account — in "Working in DNA service accounts" and `browser-and-captcha.md`.

**Describing artefacts.** Distinguish a match list, a test analysis, an admixture estimate and another user's tree in the Source body. Charted Roots has no built-in DNA or compiled-tree `source_type`: use a matching id from `customSourceTypes` if the vault registers one; otherwise ask the user before a custom type is added (through the plugin UI) — never fall back to `document`. Set originality by actual provenance: an analytical retelling or a user tree is `derivative`; keep the primary observation separate from the retelling. `directness` applies to the claim: a displayed measurement may be direct for the fact of measurement and indirect for the relationship path. Assess a document scan inside a tree by the existing rule "Material from family pages".

## Handling conflicts

1. Write the conflict out as a separate claim (in the Hypothesis).
2. Check whether the records relate to different people.
3. Compare time of creation, informant, provenance and directness.
4. Check the calendar, age rounding, index errors and changes of toponym.
5. Look for an independent record with a feature that distinguishes the hypotheses.
6. Do not average dates and do not choose the "nicer" version.

When correcting a reading, keep the earlier and the new variant, the line/frame address and the grounds for the change (`## Uncertain readings`; git keeps the prior text). Separately reassess the identities, relationships and events that depended on it; a corrected name must not come back from an older note as a new person. Useful targeted repeat searches — per `search-result-validation.md`; checking the image — per `field-lessons.md`, section 1.

Distinguish the reading of a record, its attribution to a person, a kinship edge and a separate biographical event. For example, a later mention of a son with the same name does not yet establish that an infant found earlier survived: there may be different children and reused names.

## Negative results

A negative search becomes evidential only with a clear expectation and full coverage: the fond, period, territory, survival and search method are known. Otherwise record "not found in the volume viewed", listing the volume and the limitations (Survey, `result: negative`).

Account for actual coverage — including unviewed sections, gaps and the difference between downloading, overview and reading — per `research-coordination.md`, section "Extended scan reading", and `search-result-validation.md`. A wrong range or parish requires limiting or withdrawing the negative conclusion that depended on it.

If a conclusion depends on selecting among namesakes, keep the material candidates, or links to them, in the Hypothesis. For each candidate considered, give the record and the observed feature that distinguishes them from the person sought — for example the father, the household or the age. Leave a missing feature unknown. Limit the argument that only one candidate fits to the series and years actually checked. Revisit it if distinguishing information or a fitting candidate appears.

## Which relationships count as established

Only established people and relationships enter the tree: a Person note and relationship wikilinks + `_id` are written once the edge is supported, and charts read those. Keep research candidates in Hypothesis notes, separate from the tree connected to the starting people. Documented internal relationships of another family do not prove a bridge to the user's family. Do not fill in intermediate generations for the sake of connectedness. Hypotheses may be discussed beside the tree in their Hypothesis notes, with explicit qualification.

The inclusion rule follows the task: it may admit documentary or explicitly attributed family relationships. A family report keeps its provenance and evidential weight (an oral-history Source); the absence of a document does not by itself remove such an accepted relationship, nor make it documentary. The upstream tree (the vault's `.ged`) is a lead, not evidence; it is reconciled only through the `sync-gedcom` skill and read per the vault's upstream-tree convention, if any. The agent never edits the vault's `.ged` or exports GEDCOM.

Compute a kinship label relative to the chosen reader (or the starting person) from both parent–child chains to the common ancestor and the number of steps in each. Age and position on a chart page do not determine kinship. For people of one generation, a common ancestor four steps from each gives English `third cousins` (Russian «четвероюродные брат или сестра»). For example, if a woman is a first cousin of the reader's grandmother, her grandson is linked to the reader through a common ancestor four steps away on each side. For different generations prefer an explicit chain such as "first cousin of the grandmother" if the everyday label is ambiguous. On finding an error, recheck the affected calculations, keeping the evidential weight of each underlying edge separate. [FamilySearch relationship chart](https://www.familysearch.org/en/blog/cousin-chart).

A new relative who meets the inclusion rule gets a Person note and relationship links with their grounds, after checking for duplicates (search the vault by name variants and `cr_id`); do not leave them only in a comment on another person. Every link shown must have a target note. Distinguish a correction from a new confirmation in the Hypothesis and the commit message; rebuilding a note does not make an earlier finding new.

## Minimum conclusion matrix

For each material conclusion state, in the Hypothesis note:

- the text of the claim;
- the status word;
- the supporting Sources and Citations (wikilinks);
- the independent chains (distinct archival items);
- contradicting Sources;
- the reasoning for the identification;
- alternatives;
- the next step that could change the conclusion.
