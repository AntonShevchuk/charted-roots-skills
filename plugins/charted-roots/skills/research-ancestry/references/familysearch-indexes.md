# FamilySearch: targeted search and local analysis of indexes

Read when searching for a metric-book entry by place or DGS, and when analysing permitted material already in hand. A ready index helps find the right document; read unindexed scans per `field-lessons.md`. Web work only once the user has authorised it for this task (`privacy-and-safety.md`, section 0).

If the FamilySearch MCP is connected, do structured search and reading per `familysearch-mcp.md`. Check the server's actual search schema: not every server supports DGS, collection, dates, parents or viewing scans. For an unavailable operation, use the corresponding browser route; having the MCP does not mean the book is indexed or fully accessible.

## Scope and access

1. Establish the historical place, parish, confession and years from the question. In the normal Search / Images / Catalog interface, find suitable books by place or DGS and check the description of the relevant part.
2. Use the existing lawful browser session and the environment's standard tools for targeted search and viewing. Check candidate entries by names, relatives, witnesses and distinguishing features, keeping a stable link and a minimal fragment only where the source permits.
3. Comply with the [FamilySearch terms](https://www.familysearch.org/en/legal/terms), including the requirement of prior written permission for bulk data retrieval. Handle login, CAPTCHA and access restrictions per `browser-and-captcha.md`.
4. Record the query, the entry viewed and the next useful step in the `Survey -` note (and open steps in the `Search Plan -` note).

Check access to the API and to the ordinary website separately. According to the [developer documentation](https://developers.familysearch.org/main/docs/getting-started), read on 09.11.2026, an issued application key is enabled for Beta, while production requires acceptance into the Compatible Solution Program and a compatibility review. These are conditions for developing an application, not a requirement to build one for private research: use an existing suitable MCP or the ordinary interface per `familysearch-mcp.md`. The author of [#184](https://github.com/DenisSergeevitch/ex-ussr-kinship-research/pull/184) reported that on 04.11.2026 an anonymous request for collection metadata answered 200, while search requests ended in a refusal or a redirect to login; this check was not independently repeated. Successfully reading metadata does not confirm access to search or images.

## Browsing unindexed collections

For a collection without a name index, use the catalogue and the [image browse tree](https://articles.familysearch.org/hc/en-us/articles/41450572688923-Browse-film-images-in-Historical-Records) as the task requires. The author of [#236](https://github.com/DenisSergeevitch/ex-ussr-kinship-research/pull/236) reported on 07–09.11.2026 finding in the tree the years needed, which he had not seen on the parish's catalogue card. On a material gap, check the tree groups relevant to the place. A parish's books may be part of a composite volume or a uezd group, including without the parish named. Check the bounds of the relevant part by the title page, record type and years (`field-lessons.md`, section 1). A collection's overall range does not establish coverage of every uezd and social estate. Check discrepancies between the description and the title pages, reported by the author of [#131](https://github.com/DenisSergeevitch/ex-ussr-kinship-research/pull/131) on 31.10–01.11.2026, per `search-result-validation.md`.

If the list of frames is split into pages, open the next page with the normal control when needed. When a frame repeats, compare the folio and the content, including possible differences in legibility and margins. A confirmed re-photograph of the same folio does not increase the number of entries. Check gaps and number sequences per `field-lessons.md`, section 1.

A mirror of an opis may give the DGS image group number next to the archival reference or in a link to FamilySearch. The author of [#184](https://github.com/DenisSergeevitch/ex-ussr-kinship-research/pull/184) reported this route on 01–02.11.2026. Use the full number as given, including leading zeros, in the catalogue's Film/Fiche/Image Group Number field or in Image Group Number in image search; do not assume a fixed length of number or a constant URL pattern. A mirror's link and the existence of a DGS do not confirm the right or ability to view. The author also observed errors and redirects to login on anonymous deep links; handle a real restriction per `browser-and-captcha.md`. Check the group description, the Information panel and the title pages per `field-lessons.md`, section 1.

For Soviet documents, search by the raion of the relevant period. In Explore Images a raion may be a separate place from the pre-revolutionary uezd. The author of [#204](https://github.com/DenisSergeevitch/ex-ussr-kinship-research/pull/204) reported on 03.10.2026 groups with documents of village councils (сельсоветы), executive committees (исполкомы) and other raion institutions without a name index. If the results are cut off, narrow them by the years the documents were created via [Date](https://www.familysearch.org/en/help/helpcenter/article/how-do-i-use-the-explore-historical-images-feature). Check access to the chosen images separately.

In an indexed collection, individual images may remain without a name index. The author of [#160](https://github.com/DenisSergeevitch/ex-ussr-kinship-research/pull/160) reported on 02.11.2026 the label «Для этого снимка нет индекса» ("There is no index for this image") on some of the images viewed; the author of [#184](https://github.com/DenisSergeevitch/ex-ussr-kinship-research/pull/184) reported the message "Image Index: No indexes are available" in a group viewed on 01–02.11.2026. The message concerns the index shown. Check access to the images and the coverage of [Full-Text Search](https://www.familysearch.org/en/blog/what-is-full-text-search) separately. Per the observation of the author of #236 of 08–09.11.2026, full-text search returned no hits in the handwritten books he viewed. An empty name or full-text result does not establish the state of the index (see "Ambiguous state" below). Check coverage for the specific volume or frame. If the index does not cover the stretch needed, note the limitation and, where available, check the images relevant to the question.

If a volume opens with a list of settlements and folios, use it to jump directly and check what the numbers denote (`field-lessons.md`, section 1). The message Image Restricted means viewing of particular images is restricted: record the actual message and the access terms per `browser-and-captcha.md`, without inferring that the whole collection is unavailable. The absence of a volume, year or social estate from the online collection does not by itself establish whether the corresponding documents survive in the archive. Check the availability of the file for the image needed per "Selective preservation of evidence" in `field-lessons.md`.

## Finding children by both parents

If parents' fields are available, start with a [search by the pair of parents](https://www.familysearch.org/en/help/helpcenter/find-all-children-in-a-family-in-historical-records) and a suitable place and period. Check which names went into the index fields. The author of [#256](https://github.com/DenisSergeevitch/ex-ussr-kinship-research/pull/256) reported on 09.11.2026 that in some records of the [Tver collection](https://www.familysearch.org/ru/search/collection/1921824) the father's surname field could hold his patronymic. Use it as a search variant if that fits the source. Check the parents, place and dates against the available images. The results help find children; check the completeness of the family by the coverage of the books and other information.

A message that Full-Text Search is unavailable for a film does not determine whether the selected image has an index. If the frame is accessible, check the Image Index after it loads. The date given in the index may help find the heading of the entry on the folio or near it. Record material discrepancies with the reading of the original. An already displayed [attachment of a record to a person](https://articles.familysearch.org/hc/en-us/articles/41494205418907-How-do-I-understand-my-search-results-in-historical-records) may be taken as a lead under the rules for assessing user trees in `evidence-protocol.md`. Keep links within the scope of the question and under the privacy rules.

## Permitted fragment

From an entry relevant to the question, keep the original spellings, the observed text, the URL, the time and the actual scope. There is no need to keep the entire result list. Example schema (replace the values with the actual ones):

```json
{
  "url": "https://www.familysearch.org/en/search/record/results",
  "captured_at": "2026-10-26T12:00:00Z",
  "scope": {"description": "One matching entry by place and years", "query": "The actual query"},
  "index_state": "indexed",
  "rows": [{
    "url": "https://www.familysearch.org/ark:/61903/1:1:EXAMPLE",
    "name": "Иван Иванов",
    "text": "Observed entry text mentioning Мария Петрова",
    "image_url": ""
  }]
}
```

If no separate record ARK is visible, use the actual image link `/ark:/61903/3:1:...` and your own stable `observed_id` in the row, e.g. `<DGS>:<frame>:<line number>`. This is a local observation label, not a source RID or proof of identity. The `people` field can hold the observed `name` and `label` of relatives and witnesses; keep the labels without turning them into proven kinship.

Save fragments in the session scratchpad, never inside the skill folder or the vault.

## Ambiguous state

An empty JSON `{}`, an empty panel, an unfinished load or a successful login do not prove access to a frame or the absence of an index. Record `index_state: "unresolved"`, `rows: []`, the URL, the context and the observed message in `state_evidence`. On an access refusal, use `index_state: "blocked"`. `not-indexed` is allowed only on an explicit message from the source, kept in `state_evidence`; it does not mean the scan holds no people. Incomplete fragments always have `coverage.complete: false` and do not close the search of the book.

## Local search

Run from the skill folder or use the absolute path to the script. Inputs and output live in the session scratchpad (`<scratch>`); the script refuses an output path inside the skill folder.

```bash
python scripts/familysearch.py browser-import <scratch>/fs-fragment.json --surnames 'Петрова' --out <scratch>/fs-analysis.json
```

The helper reads only the files given, searches the observed names and text, does not contact FamilySearch and does not drive the browser. For several fragments, pass several files. `--surnames` and `--beacons` take Python regexes; `--config` takes label → expression dictionaries under `surnames` and `beacons`. The search covers all recorded participants and name variants, not only the main person.

## Recording the results

Record the hits and the actual coverage in the `Survey -` note for that record set: query, collection/DGS, frames or entries checked, matching rows (with ARK or `observed_id`) and what is still uncovered. A nil sweep is recorded too (`result: negative`, with its coverage).

The analysis creates no people, claims, relationships or independence assessment. Check the original via the link before relying on a hit. A record worth keeping goes through `add-archive-record` (Source + transcription + scan, Citations, Events); the index entry and the scan of the same entry are **one** archival item → one Source, never independent corroboration. An index-only hit that identifies nobody yet → a Source with `- **People:** none` and its reason, or a line in the Survey. Do not put research files or private examples into the skill.
