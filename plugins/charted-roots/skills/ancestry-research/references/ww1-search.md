# First World War: document search and collection by locality

Read when searching «Память героев Великой войны 1914–1918» ("Memory of the Heroes of the Great War 1914–1918", GWAR). The helper `scripts/gwar.py` searches casualty reports (донесения), hospital and award records; use the cards to reach the document and to tell candidates apart by the stated locality, unit and event. The evidence protocol (`evidence-protocol.md`) applies as for any record; results go into the vault's own notes. Web work only once the user has authorised it for this task (`privacy-and-safety.md`, section 0).

## Choose the query

Start from the person's distinguishing features. If the surname is distorted or the family circle needs checking, run a bounded search by historical locality, within the source's rules. Allow for homonymous volosts and clerks' errors: the server-side filter does not guarantee that every result belongs where it seems to.

```bash
python scripts/gwar.py search --surname "Иванов" --given "Пётр" --gubernia "Название губернии" --out <scratch>/gwar-person.json
python scripts/gwar.py search --birth-place "Название села" --gubernia "Название губернии" --out <scratch>/gwar-village.json
python scripts/gwar.py volost --volost "Название волости" --gubernia "Название губернии" --max-records 5000 --out <scratch>/gwar-volost.json
```

Run the commands from the skill folder; otherwise use the absolute path to the script. `<scratch>` is the session scratchpad — outputs never go inside the skill folder (the script refuses that) or the vault. Needs Python 3, standard library only; no account is required, but check availability from the site's response. Lack of access does not mean the person is absent.

`search` also accepts `--patronymic`, `--event-place`, `--regiment`. `--event-place` refers to the place of the event. `--birth-place` passes `birth_place` (settlement), `--gubernia` passes `birth_place_gubernia`, and `volost --volost` a separate `birth_place_volost`. The API field names do not establish the meaning of the historical record: in the public `/heroes/` form, checked 26.10.2026, these three fields sit in the group «Место жительства / место призыва на военную службу» ("Place of residence / place of conscription"). Establish the birthplace from the document itself.

By default all four card types are checked. `--kind reports hospitals awards pows` selects the ones needed; `pows` is the prisoner-of-war card index (`chelovek_plen`: camp, place of capture); one may be given alone. The `volost` mode sets the volost and gubernia from that same form group, not a settlement or a place of service. The collection is not a complete census of servicemen, residents or families: one person may have several cards, and many are not represented at all.

To resume a search saved before `pows` was added, give the earlier set `--kind reports hospitals awards`; for the extended set use a new checkpoint file. Changing the set of card types changes the query; the old file is kept.

If a surname search discriminates poorly between candidates, or the father's name may have landed in the surname field, consider a bounded search by historical volost and gubernia, then pick out the matching variants of given name and father's name (`ex-ussr-locale-guide.md`, section 3). Check useful spellings of the volost against the records found, keeping the actual coverage and card IDs. A full volost download and running through every form are not required.

## Coverage and resuming

`--out` is mandatory and doubles as a checkpoint. The file holds the raw `hits`, the query, the record types, the source's exact count, the next-page position and `coverage`. The default cap is 1000 cards; size it to the question. If the total count exceeds the cap, the result is marked incomplete (exit code 1). Repeat the command with the same file and raise `--max-records` if needed. Changing the query or the card types needs another file. Results are saved after every page and on error; two processes cannot write to one file.

Consecutive pages hold at most 1000 records each, with pauses. A repeated/empty page before the total count is reached is not a complete result. If the count or a card's content changes, re-check the result in another file. On `401`, `403`, `429`, a CAPTCHA or a block, save the state and stop requests; do not circumvent the protection and do not carry this method over to the Second World War portals.

## Compare spellings of a locality

If the village name on a card cannot be identified, compare it with the spellings in other saved results (by surname, by volost, by neighbouring villages). This command works on local files only and does not contact the site:

```bash
python scripts/gwar.py places --input <scratch>/gwar-person.json <scratch>/gwar-volost.json --target "Название как в карточке" --out <scratch>/gwar-places.json
```

Cards are grouped by gubernia, uezd and volost. For each spelling, the number of cards, their IDs and full keys (`_index|_type|_id`) are given, distinguishing identical IDs in different record types. Conflicting versions of one card require comparing the source files; the original result is not replaced by the output file. With `--target`, spellings are ranked by similarity to the unidentified name (letters and consonant skeleton). Similarity only orders the checking: it does not establish that places are identical. Strings are split on commas, and the settlement-type word («с.», «д.», «селение» — village abbreviations) is dropped in comparison. If the field has another format, check against the original card. Incomplete input gives exit code 1 and `coverage.complete: false`. Method for deciphering and checking a candidate — `ex-ussr-locale-guide.md`, section 1, "Corrupted or unidentified place name".

## Compare surname spellings

When the spelling of a surname is disputed, you can group results already saved by locality. The command reads local results of `search` and `volost`.

```bash
python scripts/gwar.py surnames --input <scratch>/gwar-volost.json <scratch>/gwar-village.json --target "Surname as in the family's documents" --out <scratch>/gwar-surnames.json
```

For each spelling the number of cards is given. The given name, patronymic and locality fields stay beside the full key of the card they were taken from. Check the meaning of the `birth_place*` fields against the document, as when searching by place. An empty surname forms a separate group. `--target` orders the variants for checking by similarity of letters and consonants. Check identity and kinship per `evidence-protocol.md` and the original document. Repeated cards with the same source fields are counted once. If the fields change, compare the saved versions. Incomplete input keeps the useful result with exit code 1 and `coverage.complete: false`. Keep this working list in the session scratchpad; record the spellings that matter in the Survey note.

## Find the image

On the card, look for `documents_pages.pages_id`, then:

```bash
python scripts/gwar.py page --pages 10063712 10063713 --out <scratch>/gwar-pages.json
```

The command returns `image_url`, the `zones` coordinates and the raw `obraz_s_oblastyami`. The coordinates refer to the source scan; having the URL does not mean the image has been downloaded or read. Where keeping it is permitted, use the normal browser route, record the archival reference and check the line, the neighbouring lines and the verso. If the source requires page context, open the page normally; do not tamper with protection measures.

Check that `image_url` returned an image, not HTML (`field-lessons.md`, section 7, "Checking the copy obtained"). Per the observation of the author of [#50](https://github.com/DenisSergeevitch/ex-ussr-kinship-research/pull/50) of 27.10.2026, a direct request to it returned a protection page with HTTP 503, while the same image opened in the site's viewer at `https://gwar.mil.ru/heroes/document/<documents_id>/?page_id=<pages_id>`. For casualty-report and hospital cards, the author gave the address `https://gwar.mil.ru/heroes/<_type><_id>/` (e.g. `/heroes/chelovek_donesenie<ID>/`); record that locator in the Survey note and on the Source. An address of the form `/heroes/?ids=<_id>`, per the same observation, gave an empty result. During a maintenance check on 27.10.2026 the web tool got a GWAR timeout; these routes have not been independently confirmed. A recorded locator does not prove the card is accessible or has been read.

## Prisoners of war

GWAR has a separate «Картотека военнопленных» ("Prisoner-of-war card index") of RGVIA (РГВИА) (addresses `/heroes/chelovek_plen…/`). `scripts/gwar.py search --kind pows` and the `volost --kind pows` mode search this index; use the site's form if it suits the question better. The card's locator is built from `_type` and the numeric `_id`; per the author of [#64](https://github.com/DenisSergeevitch/ex-ussr-kinship-research/pull/64), that route returned HTTP 200 on 28.10.2026. This proves neither the accessibility of every document nor the completeness of the result. Establish the provenance of a specific card and its link to the original list from the document.

- **Distortions.** Surnames and places can be distorted in transfer between languages and in copying. Keep the card's spelling; choose transliteration and reading variants by context and `ex-ussr-locale-guide.md`, without mechanical letter substitution.
- **Fields.** Keep the stated unit, place of origin, place and date of capture, camp and list numbers, which may lead to the original entry. Check the meaning of abbreviations such as «род.» (rodom — "native of", or "born"), the meaning of the date and the calendar against the specific form; leave the unknown unknown and record discrepancies.
- **Two cards for one name.** Matching given name, surname, place and date of capture, or neighbouring camps, help select candidates but do not resolve identity automatically. Weigh a differing unit and a missing patronymic or gubernia per `evidence-protocol.md`; keep candidates apart (in the Hypothesis note) until identity is resolved. A link between cards shown by the site is a lead.
- **Danish Red Cross.** Lists of Russian POWs in Germany went through the prisoner-of-war department of the Danish Red Cross in Copenhagen; the International Committee of the Red Cross archive holds little on Russian prisoners in Germany ([ICRC note](https://grandeguerre.icrc.org/Content/help/FAQ_en.pdf); ICRC entry — `seed-sources.md`, section "Military sources"). The department's archive is held in Rigsarkivet; direct links to series, dates and the restrictions of the surviving sampled material — in `seed-sources.md`, section "Military sources". Absence of a name in this incomplete material does not exclude captivity. A Danish record may help refine the reading of a name or place, but check its details and dependence on other records against the specific document. A search can be ordered if needed (`correspondence.md`, section 1) — the agent drafts the order, the user sends and pays. In the draft, give the known surname variants, unit, date and place of capture, camp and card numbers; do not invent unknown fields.

## Record the finds

Record each search in the `Survey -` note for GWAR: the exact command/query, card types, the source's total count, `coverage` (complete or not), the card IDs found and their locators. Cards are index entries — leads only. The number of cards does not become the number of people; identical full names are not merged. Establish identities, relationships, informant and independence after reading the documents (`SKILL.md` § Workflow, steps 6–7). A card or document worth keeping goes through `add-archive-record`; a card and the scan of the report page it indexes are **one** archival item → one Source. A card that identifies nobody yet → a Source with `- **People:** none` and its reason, or a line in the Survey.

The service `_score` and the sort order depend on the query and do not create a new version of the document. The same card appearing in a surname search and a locality search with the same raw fields is one card; note both searches in the Survey. A change in the raw fields themselves is recorded separately. Re-reading a local cache that is already complete does not change the cards' retrieval date.

## Technical details

The public session begins at `GET /heroes/`, search is `POST /gt_data/?builder=Heroes` with the site's advanced-search fields; scans are `builder=HeroesStranitsa` by `linkedPages`. Both POST operations only read the source. The response format is checked; changes to the internal API are not fixed by guesswork.

The Russian Trusted Root/Sub CA certificates are in `scripts/ca/`; distribution points: `nuc-cdp.digital.gov.ru/cdp/rootca_ssl_rsa2022.crt` and `subca_ssl_rsa2024.crt`. They are attached only to the GWAR HTTPS client; the system trust store is not changed, TLS verification is not disabled, and new certificates are not downloaded automatically. On a chain error, check the source and the certificates' validity by ordinary means.

The search part is adapted from `russian-archives/scripts/gwar.mjs` and ported to Python.
