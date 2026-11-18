# Source and web-search strategy

Read this file when planning a search and when choosing between an official archive, an index, a family tree, a forum or a secondary database.

## 1. Default hierarchy

Search in this order unless the task calls for something else:

1. **The original or an image of the original** in an official archive, library, ZAGS/registration office, military or departmental resource.
2. **An official extract, catalogue entry or card** with a stable identifier.
3. **A reputable index/transcription** that leads to the original.
4. **Printed directories, newspapers, address calendars, memorial books** with an identifiable publisher.
5. **Genealogy databases, family trees and community projects** — as leads.
6. **Forums and social networks** only for hypotheses, local hints and contact with a published source; posts do not prove kinship by themselves.

## 2. Plan from the question to the record

For each key gap, determine which document could answer it, where it is held, and by which name, place and period to search for it. Choose the next check by its value for the question; record the result and its limits as you go — in the `Survey -` note for an executed sweep, in the `Search Plan -` note for what is still queued.

Build the search outward from a documented person: a child's record can help find the parents' marriage; a marriage can suggest an age and a maiden name for the birth search. The first known child is not necessarily the first in the family, and its birth date is a pointer for the marriage search, not proof of the marriage date. For each step, distinguish confirmed from assumed and choose the next piece of evidence by the link being tested (`evidence-protocol.md`).

## 3. Search templates

Adapt the language and toponym (queries stay in the source's language):

```text
"Фамилия Имя Отчество" место
"Фамилия Имя" год супруг
site:официальный-домен "Фамилия" населённый-пункт
"архивный шифр" OR "номер акта"
"старое название места" метрическая книга
"фамилия" "место призыва"
"фамилия" репрессирован OR спецпоселенец OR эвакуация
```

(Placeholders: surname, given name, patronymic, place; year, spouse; official domain, settlement; archival designation, act number; old place name + "metric book"; place of conscription; repressed / special settler / evacuation.)

Do not run every variant mechanically. Start with the most distinguishing features, then widen.

## 4. Working with catalogues

- Look first for the fonds creator (фондообразователь) and the administrative affiliation.
- Check the date span of the file and its actual state of preservation.
- Keep not only the direct view but also the catalogue card of the storage unit.
- Without full-text search, search by parish, volost, uezd, institution and document type.
- If the catalogue uses session links, keep the stable identifier and the textual archival reference.
- If a web catalogue or a third-party index covers only part of the years, check the relevant inventories and indexes in the archive's own files. In the XLS, XLSX or PDF, find the needed parish or fonds by matching the designations and years in the rows. Cite the file and the row or page used. If the file is unavailable, record this as a gap in coverage.

The author of [#96](https://github.com/DenisSergeevitch/ex-ussr-kinship-research/pull/96) describes searching files of TsGA Moscow (Central State Archive of Moscow) in [E-poisk](https://epoisk.ru/) by words in the title, period, fonds or opis, and its [PDF inventories](https://epoisk.ru/opisi_pdf/). Per that description, the default form has the filter «Сканы онлайн: Да» (scans online: yes) switched on; for a wider search, check its value. Current filters, availability of PDFs and access to scans were not independently checked: on the check of 04.11.2026 the web tool was refused access by robots.txt. This is a limitation of the check, not evidence that the service has closed. The service is also suggested for searching settlements of present-day Moscow oblast, but it does not cover all the region's archives: check the historical jurisdiction and the custodian. A file description does not confirm the person's presence or access to scans: check designation, parish and dates against the inventory and the book.

For searching RGADA inventories, also use [РГАДА Поиск SovaDev](https://rgada.sovadev.pro/). The «По описям» (by inventories) mode searches fonds and opis titles and annotations; «По содержимому PDF» (by PDF content) searches the text layer of indexed inventories, including recognised text. Search variants of the historical place name, the fonds creator or the document kind; narrow by fonds number and years where needed. Quotation marks give an exact phrase; «+ Уточнить» (refine) narrows the current results. Record the query, mode and filters: an empty result in one mode does not close the other and does not prove the file is absent from the archive.

For a hit, record fonds, opis, file number, description and dates, and the link to the card and the PDF page if given. Match the hit against the page of the published inventory; do not treat the PDF page number and the archival folio as the same thing. Establish the provenance of the inventory from its title page and metadata: a published PDF may be a modern transcription, not an image of the archival original. Then check the content of the file itself and its availability in the archive. If the inventory or file is unavailable, record the restriction and plan a check. A text index and the inventory it was derived from are not independent confirmations; assess the dependence between inventory and file for each claim. Matching words on a page may belong to different files; use `search-result-validation.md` when checking results.

In the [«Великія описи»](https://inv.velikie.org/) system, search volunteer-typed inventories and individual projects by relevant archive, place, surname and document type. In the [configurable search](https://inv.velikie.org/search/), mind the scope and result type: the tabs «Фонды» (fonds), «Дела» (files), «Проекты» (projects), «Документы» (documents) and «Записи» (entries) answer different questions. Narrow by archive, fonds, opis, file, project and dates as the task requires; record the filters and search settings applied. With a date range set, consider the option «Дела без датировки» (undated files); with an archive or designation filter, «Непривязанные документы» (unattached documents) for documents and entries; word forms and match mode also change the results. With an unknown designation or dates, do not restrict the search by them without reason. Selecting an archive in the form does not mean the needed inventory or document has already been typed.

For a lead, record the URL, archival designation, title and dates, and the name of the project and source document where given. Compare the typed set with the archival inventory and, if the question requires, with the file itself; the site states that it does not publish scans or photocopies of documents. Confirm access to the file with the archive. A typed inventory and its copy on another site may come from the same work: check provenance and do not count copies as independent confirmations. A successful empty result means no match only in the part checked and under the filters chosen; use `search-result-validation.md` when checking coverage. Observe the [site terms](https://inv.velikie.org/agreement/), including citing the source and archive and the limits on automated bulk harvesting.

For Belarus, also use [СОДД НАФ](https://sodd.by/): search for the fonds creator, the historical place name and the record type, then go from fonds to opis, file and document through the levels available. The [quick-search help](https://sodd.by/info/15b4aa12-8f49-4c21-b2ea-b0900442eee8) allows partial words and is case-insensitive. A catalogue card does not imply an open scan or a name index. Record the archive, fonds/opis/file, date span, card ID and URL; check the presence of images, login and viewing conditions separately per file. An empty surname search in the descriptions does not rule out an entry inside a file.

### RSL electronic catalogue and searching inside publications

Use the [RSL catalogue](https://search.rsl.ru/) (Russian State Library) to find relevant printed publications, including periodicals, directories and indexes. Search the known variants of surname and place; where needed, the series title and the relevant years. The advanced-search help describes quotation marks for a phrase, `*` after the start of a word, and fields including `title:`; check the index's accuracy and whether filters apply against the results. If the previous rows are still visible after submitting, wait for the counter and results to refresh before recording the result.

Results may contain a publication card and «Цитаты из текста» (quotations from the text) with links to OCR pages. Open the relevant card, check year, book, part and access; verify the quotation and page against the image. Record the viewer page number and the printed page separately: one frame may show a two-page spread. Where there is text, the in-viewer search can be used; its empty result, or an empty surname search in the catalogue, does not prove the name is absent from the scan. Try justified variants and a short stem, allowing for OCR noise and errors; choose publications by the question and read the available alphabetical index or the relevant part of the book. Record the coverage and access of each issue in the Survey note; do not present a catalogue card or OCR as a reading of the whole publication.

If court publications are relevant to the case, consider «Ведомость справок о судимости» (register of criminal-record certificates) and the available alphabetical indexes. When the year of the entry is unknown, start from the person's lifespan and other documented dates, without treating them as exact bounds of the event. Find the series indexes, years and parts separately in the catalogue, then selectively read the relevant alphabetical section and the surname variants on the scan. For a candidate, record the index, its part and year of coverage, the line and entry number; use the number to identify the matching issue of the same part, check its card and the line on the image. [Указатель за 1886 год, часть 2](https://search.rsl.ru/ru/record/01005499993) (index for 1886, part 2) and [книга 8, часть 2 за 1886 год](https://search.rsl.ru/ru/record/01005426156) (book 8, part 2 for 1886) are an example of this step, reported as viewed by the author of [#141](https://github.com/DenisSergeevitch/ex-ussr-kinship-research/pull/141) on 02.11.2026; the bibliographic titles of the cards were re-confirmed, the matching of the line to the scan was not independently checked. Choosing the right year for a new person needs grounds. An index and a book may have different publication dates; the index's publication year does not replace its year of coverage, and an entry number is not a page or book number.

Check access and actual coverage of every index and issue; a surname absent from one index or part is not ruled out in another year, and unavailable issues are not counted as read. An index and the entry it reproduces do not become independent confirmations; a matching surname and number do not yet establish the person's identity. Keep the original reading and the distinguishing features; report criminal-record information neutrally, with cautious identification and per `privacy-and-safety.md`. Do not assert kinship or the guilt of relatives on a surname match.

## 5. Scan, index and OCR

1. Use the index as a pointer to the frame.
2. Verify name, act number, date and fields on the image.
3. Record material discrepancies between index and original in the Source and transcription (`## Uncertain readings`); ordinary spelling variants go beside the original reading.
4. Use OCR for navigation, but not as the sole basis for difficult handwriting or old orthography.
5. When citing, give the page/frame and the minimum fragment needed.

For FamilySearch, first establish whether the relevant book has a ready index, then run a targeted search for the question through the normal interface or a connected MCP with suitable filters (`familysearch-mcp.md`). Unindexed scans need separate browsing, and the limits of a particular MCP should not be taken for absence of the record. Permitted fragments and lawfully obtained materials already on hand can be analysed locally per `familysearch-indexes.md`, including relatives and witnesses named. Do not download a whole book. An ambiguous empty answer does not confirm the absence of an index or record. Leads go into the Survey note (or a Source with `- **People:** none` per `archive.md`), then the originals and independence are checked by the usual protocol.

### Inventories of the Vilna Commission

Volumes XXV, XXXV and XXXVIII contain published inventories of individual estates, including on the territory of present-day Belarus and Lithuania: these are historical economic descriptions (инвентари), not archival file inventories (описи дел). Choose the volume by locality and by the dates of the documents, which differ from the publication dates; links and the limits of the check are in `seed-sources.md`.

- Start with the relevant table of contents, geographical or name index. The table of contents may name an estate without its villages; where needed, widen the check to related names and other relevant volumes. There is no need to OCR all three volumes to start the search.
- If the machine text is unusable, use available local OCR on the pages needed or read the images; checking the text layer — `field-lessons.md`, section 7. For Tesseract, start at about 300 dpi and choose Russian and/or Polish according to the text. Where columns are mixed, recognise them separately; keep the resulting text in the session scratchpad (or as a transcription via `add-archive-record` when it is evidence) for reuse with the same copy. Lack of OCR does not block reading the scans.
- Check the title, act number and page from the index against the image; take the errata list and the column order into account. Establish the correspondence between printed and PDF numbering at the chosen place, without carrying one offset over the whole volume or another copy unchecked.
- Open the target document and as many neighbouring pages as needed for its heading, beginning, continuation and the meaning of the extract. If the link leads to a different heading, check numbering and index first. Check names, dates and kinship terms against the images; keep sources and uncertainty per the general rules of this chapter and `evidence-protocol.md`.

Do not assume a complete enumeration of inhabitants: the content depends on the specific inventory. An empty OCR search does not prove the entry is absent; limits of negative conclusions and dependence of copies — per `evidence-protocol.md`.

### Жніво / Zhnivo

Use the [internal search](https://db.zhnivo.com/by/belarus-genealogical-databases/) for the historical Belarusian lands, including territories beyond Belarus's present borders and places of resettlement. Per the help, start with the surname in Russian, then narrow by given name/patronymic, settlement, uezd and guberniya, and choose document types by the question. `|` separates variants within one field, `*` replaces any number of characters; where there are gaps, check the original language forms and close OCR/HTR readings. Do not carry these rules over automatically to other sites.

Open the details of the row found: document title, folio, link/designation, author of the index and comments where available. Check the material fields against the scan; without an accessible original, keep the index as a lead and plan a check. A missing row does not close the search of an uncovered document. The project's terms forbid automated download of the whole database or parts of it without agreement; regular automated and commercial access also requires the project's consent. For targeted searching and viewing individual results, use the normal interface elements and observe these terms.

### Geneteka

1. In the [search form](https://geneteka.genealodzy.pl/), choose the territory (`Teren`), parish (`Parafia`), act type — births, marriages or deaths — and year range (`Zakres lat`). For the historical eastern territories, check the relevant sections `Białoruś`, `Litwa`, `Ukraina`, rather than restricting yourself to present-day Poland. Establish the coverage of parish and years separately for each act type.
2. Check Polish and other material variants of surname and given name; for women, maiden and married surnames. `Wyszukiwanie dokładne` (exact search) requires the exact surname; on a gap, relax this restriction and check variants. The filter for recent index additions does not replace the event year range; in a normal search, do not restrict results to new indexes only.
3. To find mentions of a person in their children's records, do not enable `Nie wyszukuj w rodzicach` ("do not search in parents"). Distinguish the principal of the act from a parent: a child's birth row found is not the parent's own birth record. If the surname may have been distorted in indexing, narrow parish, act type and years and check the given name without a surname. Per the observation of the author of [#160](https://github.com/DenisSergeevitch/ex-ussr-kinship-research/pull/160) of 02.11.2026, such results included both the principal's given name and the father's given name. Establish the role from the row and the image.
4. If both spouses or parents are known, fill in the second person (`oraz`) and, where needed, enable `Wyszukaj jako para` (search as a pair): the two persons must be the couple or the parents in the same act. Use the neighbouring-parish search (15 km) as an additional check; it does not establish historical parish affiliation and does not close all possible places of registration.
5. Record parish, confession, year, type and number of the act, original names, URL and the available details of the source and index author. Follow the link to the scan if there is one; check act and folio, without equating act number with page number. According to the [PTG description](https://geneteka.genealodzy.pl/ogenetece.php), some indexes have no accessible scans: then keep the lead and search for the original by the source given. An empty result does not rule out an event outside the coverage checked.

### hryc.by

Use the [page search](https://hryc.by/) for relevant archival collections, newspapers and books; choose the collections by place and period, and do not take the `.by` domain as the limit of coverage. Per the site help: a query in quotation marks respects word order and distance, without quotation marks it requires all words on the page. For a single search word the masks `?` (one letter) and `*` (any sequence of letters) are available. Check OCR variants and old orthography; a surname and a place on the same page are not yet linked to one entry.

Open the document page and check the context; record the title, archival designation, folio/page and URL where available. Search and access to the document/designation may differ, and the link to the original may be missing or outdated. Check access conditions and the availability of filters on the current plan; a blocked view is not absence of the document. If the image is unavailable, keep the lead and continue via the official archival catalogue. OCR, index and scan of one entry are not independent confirmations.

### Metric books with machine handwriting recognition

Applies to services where scans of handwritten books carry machine text (e.g. Yandex «Поиск по архивам», search in archives). Full-text search finds only what was recognised. Choose the relevant years and parish sections by the question; where useful, read their machine text sequentially, up to a whole chosen volume, within the service's terms. A full pass is not required; verify hits against the image.

1. **Old orthography in machine text.** Recognition may keep «ѳ», «і», «ѣ» and final «ъ». Choose useful forms from the actual text: e.g. Ѳома/Фома, Ѳеодоръ/Фёдор, Тимоѳей/Тимофей; general order of variants — `ex-ussr-locale-guide.md`, sections 3–4. A modern form may miss the entry. Allow for observed handwriting-recognition errors (К/Н, ц/щ/д, а/о), checking relevant matches against the image.
2. **Full title of the file.** Long titles may be truncated in the inventory list. A composite volume of several churches may name the needed church at the end of the title; open the full title before excluding a file.
3. **Section of the right parish.** If one file binds the books of several churches, determine the pages of the needed parish (e.g. by the church and village names on each page) before assigning a found line to it.
4. **Negative result.** Record volumes, years, parish sections and pages without machine text; absence of text does not mean an empty page. Limits of the conclusion — per `evidence-protocol.md`, section "Negative results". Check relevant near-matches against the image; a badly distorted surname may match no pattern.
5. **Entries without a surname.** In peasant metric books the parents' surname may be missing. For example, the father may be named only by given name, patronymic and estate, with the surname appearing in later entries. A surname search will not find such entries: search by the father's given name with patronymic and the village, or browse the section.
6. **A snippet is not the whole entry.** A result fragment may cut the entry short. Open the available page text and the image; for a revision list («ревизская сказка»), check the neighbouring folio if the household continues there. Machine text may scramble table columns (age, «умре в … году» (died in … year), notes on marrying out), so check family composition, age and the meaning of notes by the layout of rows and columns on the image. An unavailable image leaves the reading provisional and does not stop other checks.
7. **Morphology and exact form.** The [Yandex help](https://ya.ru/archive/help) describes searching different word forms. The author of [#90](https://github.com/DenisSergeevitch/ex-ussr-kinship-research/pull/90) reported on 30.10.2026 that quotation marks narrow the results; check the exact semantics of operators and the conditions applied against the current help and the text found. The genitive plural of a surname in "-ский" (illustrative example: «вотчина графинь Ивановских», the estate of the Countesses Ivanovsky) looks like a surname in "-ских"; distinguish such uses by grammar and context.
8. **Composition of collections.** Take the archive and file designation from the document description or the breadcrumb trail. Absence of the needed archive from the results does not establish that its collections are absent from the service. Check the catalogue, years, document types and presence of recognised text as of the search date; leave unconfirmed coverage as unknown. A full-text search limitation is not a negative result about the person — see item 4. Besides the «Текст документа» (document text) panel, some scans, per a contributor's observation of 29–30.10.2026, have a «Список персон» (list of persons) tab with names from the same recognised text; this is the same recognition derivative, not a separate index: check against the image.
9. **Saving images.** If the service does not serve the original file and the preview is too small to read, save the needed fragment or a viewer screenshot per the source's rules, with the scan URL, and describe it as a screenshot, not the archival original (scan files go beside the transcription as `.jpg`/`.pdf`, `archive.md` § Scan files). Do not bypass access restrictions.
10. **Disagreement with the machine text.** If a proposed reading disagrees with the OCR, apply "Checking a visual reading" from `field-lessons.md`, section 1. Keep the machine form and the proposed reading, and ground the conclusion in the image. If there are too few distinguishable strokes, leave the reading open. An expected name or a presumed scribal slip is a reason to check against the image.
11. **Re-running after an update.** The author of [#221](https://github.com/DenisSergeevitch/ex-ussr-kinship-research/issues/221) reported the filter «Обновлено после» (updated after) in [Yandex «Поиск по архивам»](https://ya.ru/archive/search). If the filter is available and applied, use it to re-check a saved query, and record the date of the previous pass, the date chosen and the filters actually applied in the Survey note. The update date refers to the service's results, not to the date of the entry in the document. An empty result describes only this query with the filter; if the coverage, name variants or place have changed, repeat the relevant check without it.

### Address books «Весь …», address calendars and commemorative books

For an urban family, consider address books («Весь …», "All [city]"), address calendars (адрес-календари) and commemorative books (памятные книжки) for the relevant years. Content and periodicity depend on the city and the publication: a directory may include residents, house owners, institutions or officials, but not the whole population. Before a negative conclusion, check through the table of contents and the relevant section whether the issue includes the category of officials sought and whether its alphabetical index covers it; a surname absent outside the established coverage does not refute the service. Look for scans in the NEB, the Presidential and regional libraries or the Internet Archive (`seed-sources.md`); check for a text layer per issue.

1. Choose issues by the research question and establish their sections. Comparing neighbouring years can help trace a historical address, initials, rank or occupation; going through all years is not required.
2. Search the OCR for justified surname variants, old orthography and likely recognition errors (`ex-ussr-locale-guide.md`, sections 3–4). On an empty result, browse the relevant alphabetical section: OCR may miss a line. Neighbouring surnames constrain the possible reading of a damaged line but do not restore the surname unambiguously.
3. Until checked against the page, record the result as an OCR lead in the Survey note, with publication, year, section, page/column and URL. On viewing, check the line and abbreviations against the directory's legend. Apply the usual assessment and dependence evaluation per `evidence-protocol.md`: neighbouring issues may repeat a single count; they cannot automatically be treated as dependent or independent.
4. Match surname and initials against the historical address, occupation and neighbouring years; keep namesakes apart per the general identity-resolution protocol. Restrictions for living people stay in `privacy-and-safety.md`.

To refine historical geography, also use the lists of volosts and populated places in regional directories: e.g. the electronic library of the A. S. Pushkin OGONB (Omsk State Regional Scientific Library) holds commemorative books of Akmolinsk oblast (`seed-sources.md`). Find the section from the table of contents; if the PDF yields no text, OCR the needed pages with available local OCR where needed and apply the checking rules above. Printed pagination may restart in different sections; handle numbers per `evidence-protocol.md`, "Provenance". A mention of a place or an official's address helps choose the next archival route but by itself does not establish the identity of same-named places, the ancestor's residence or a kinship link.

## 6. Military, repression and memorial databases

- Distinguish a loss card, an award sheet, a report, a burial list and a late memorial entry.
- Identical cards on several portals may derive from one document.
- Check place of birth, of conscription, relative and address — a full name alone is not enough.
- Political repression, captivity, deportation and filtration are sensitive topics; report only relevant information and exact provenance.

### Burial search and checking candidates

If a burial helps answer the question, choose local and international sources from `seed-sources.md` by what is known of the place, period and possible relocation. The place of residence or death does not by itself establish the place of burial; where migration is justified, consider another locality or country. Check the necessary variants and filters, actual coverage and the limits of an empty result per `search-result-validation.md`; an unavailable route does not stop other checks (`browser-and-captcha.md`).

Assess the inscription, its transcription, a relative's information and the cemetery register separately. Working with monuments, neighbouring graves and private fragments — `field-lessons.md`, section 5; the origin and dependence of specific information, including copies of one index on different sites — `evidence-protocol.md`.

For the First World War, GWAR allows searching by person, by the locality from the source form and by military unit, and limited browsing of records found for a chosen volost. Do not take the technical name `birth_place` as proof of place of birth: establish the meaning from the form and the document. Distinguish reports, hospital and award records; procedure, result limits and getting to the scan — `ww1-search.md`. The number of cards is not the number of people, and a volost search is not a complete military or household census.

## 7. Family trees and user databases

Treat them as leads only until sources are found. Check:

- whether images are attached;
- whether an archival designation is given;
- who entered the data and when;
- whether the trees copy each other;
- whether there is impossible chronology or a mix-up of namesakes.

**A ready-made tree (GEDCOM, JSON and other exports).** If the vault has an upstream master, never edit its `.ged` export and bring it into the vault only through the `sync-gedcom` skill; read its names per the vault's upstream-tree convention (e.g. `upstream-ancestry.md`), if any, before calling a difference an error. Any other tree file the user supplies stays unchanged where the user put it; it is a lead, not evidence — the relationships it contains are leads. Check the links to primary documents separately; the same tree repeated in another format does not create independent confirmation.

Use the available reading tools; no dedicated mandatory converter is needed. When drawing on a third-party tree, keep the original names, dates and places and the export's person identifiers, and note their correspondence to vault People (by `cr_id`) in the relevant `Hypothesis -` note. Do not overwrite existing candidates and do not merge same-named people automatically; keep unresolved references and unsupported fields for review. A relationship taken from a tree enters the Hypothesis as *hypothesis*, with its origin explained, not raised to *single-source* just because it was imported. Assess living status conservatively from the available information: absence of a death date or an arbitrary year threshold does not prove death. For probably living people, `privacy-and-safety.md`, section 2, applies. An incomplete reading does not prevent researching the part already reviewed; record the actual coverage and the remainder in the `Search Plan -` note.

**Reconciling research versions.** On a material discrepancy between a tree, its export and the vault, compare the specific claim and the identifiers of the people involved with the existing notes; keep the versions with provenance and date, if known. An unconfirmed link is not a refuted one; assessment of documents and dependence — per `evidence-protocol.md`. Choose an available check that can distinguish the versions. A re-import by itself does not change previously assessed links: do not restore a rejected version as established; keep the reason for its rejection and the history of any justified revision (in the Hypothesis). Never overwrite the source file; record material unresolved discrepancies in the Search Plan and the report to the user. Differences against the upstream tree are resolved upstream by the user and synced via `sync-gedcom`, never by editing the `.ged`.

**Pages kept by the family** are checked in the first pass: trees on FamilySearch, Geni and MyHeritage, threads on the VGD forum, and memorial databases by type of case — «Бессмертный полк» (Immortal Regiment) and «Дорога памяти» (Road of Memory) for war participants, «Бессмертный барак» (Immortal Barrack) and «Последний адрес» (Last Address) for the repressed, Yad Vashem Pages of Testimony for Holocaust victims. These often hold scans of documents and photos from the family archive that are not in state databases. Assessment of individual materials and their independence — `evidence-protocol.md`, section "Originality"; identifying and describing photos — `photo-search.md`.

## 8. Unstable or doubtful resources

- Do not use databases of current addresses/phones, leaks, dumped registers or personal-data aggregators.
- Do not bypass regional restrictions via VPN/proxy to gain access.
- Do not join closed groups or accounts under a false pretext.
- Do not bulk-download collections of unclear legal status.
- If it is unclear where a scan came from, use it only as a lead until an archival reference is found.
- Mark politicised or propagandistic editorial framing with a specific reason and separate it from the archival documents. A doubtful source is acceptable as a clearly labelled lead, but its claims do not become facts without independent verification.

## 9. Recording a web record

A web hit that matters becomes a Source via `add-archive-record` (or, if it identifies nobody yet, a Source with `- **People:** none` and its reason, or a line in the Survey). Record at minimum:

- the Source note (one Source per archival item — mirrors and copies of the same item share it);
- site title and owner;
- full URL and access date;
- search query and filters (in the Survey note);
- record ID/archival designation;
- type: original, image, index, retelling (primary vs derivative in the Source body);
- a brief extract without excess copying;
- which other Sources, if any, derive from the same archival item (they are not independent);
- access restrictions and link stability.

If a field is missing from the source, mark it as unknown and continue checking with the data available.

## 10. A broken source

1. Check the official new domain or catalogue.
2. Search for the same archival designation and title.
3. Check library/archive copies and a permissible web archive.
4. Do not count a mirror as an independent source.
5. Record the failure and the alternative route.

## 11. Request to an archive

If there is no digital image, establish the archive and designation and draft a request in the letters folder (in the recipient's language, plus a row in the letters index, per `letters.md`). Choosing the addressee and the channel — in [correspondence.md](correspondence.md); the agent never sends — the user does — and waiting for a reply does not hold up other sources. State:

- the exact question;
- full name and variants;
- period and place;
- the presumed fonds/file;
- proof of kinship, if the official body requires it;
- the desired type of answer: archival certificate (архивная справка), copy, search of a specific file.

Always check requirements and deadlines on the current official website.

## 12. Coverage checklists by task type

Choose the items that fit the place, period and research question. Use them to find gaps and the next strong checks. Record the searches done and their extent in the Survey note; related query variants may be combined. Mark unavailable and inapplicable items with the reason. Interim results may be reported as work proceeds; the final account must honestly describe coverage and remaining limits.

Addresses and search formats marked "not checked" must be checked on the site before use. Archive access procedures change: check them on the official websites.

### General items for any task

- [ ] The user's materials reviewed completely, including reverses, stamps, annotations and photos inside documents.
- [ ] The materials on hand taken into account; if their extent is still unclear, one general question about materials asked (SKILL.md, Workflow step 1). The answer, or the wait for it, recorded; the search continues without waiting.
- [ ] Relevant family pages, trees and memorial databases checked with their internal search by the family's details (once web work is authorised); the absence of a page needs no answer from the user.
- [ ] Search by the maiden surname of mother, wife, grandmother: female lines often lead to new documents.
- [ ] Cemeteries and obituaries: cemetery books, gravestones (relevant sources from `seed-sources.md`, chosen per section 6), open funeral-agency reports on the funerals of recently deceased relatives (`field-lessons.md`, section 5), obituaries in the local press. `field-lessons.md`, section 4, helps link a surname from a gravestone to a candidate in a military record; neighbouring graves do not prove kinship.
- [ ] Photo search (`photo-search.md`).
- [ ] The key relevant collections from `seed-sources.md` checked; choices and omissions explained by question, coverage and access.
- [ ] For an aggregator search, the coverage of archive, place, period and record type established. Absence of the needed collection gives no negative result for it; mentions of natives may appear in documents of other regions.
- [ ] For a 20th-century civil biography, documents on work, awards and evacuation considered per `field-lessons.md`, section 9. Choose archives by the place of the event across the whole former USSR; a Russian regional example does not replace a local search.

### Metric books and confession lists (before 1918–1920s)

- [ ] Jurisdiction on the event date: guberniya, uezd, volost, parish (SKILL.md, Workflow step 2; `ex-ussr-locale-guide.md`).
- [ ] Archive catalogues and scans: Glavarkhiv of Moscow, regional archives, FamilySearch (unindexed films), Duck Inspector for Ukraine — per section 1 and `field-lessons.md`, sections 1–2.
- [ ] Indexes (FamilySearch, Geneteka, regional projects) checked for material surname variants. If the confession is unknown, cover the relevant confessions of the place and period: the books were kept separately.
- [ ] For metric books of the historical Belarusian lands, consider Zhnivo and Geneteka → `Białoruś` when choosing indexes (techniques — section 5); check parish, year and act-type coverage separately. Do not use Geneteka as an index of the 1926 census.
- [ ] An empty index result is a reason to check parish and year coverage, not a conclusion of absence.
- [ ] On a material gap in the parish books, consider the relevant second copies, including the summary copies of the благочиние (deanery), деканат (Catholic deanery) or консистория (consistory) (`field-lessons.md`, section 8); for a marriage, also the bride's parish and the separate series of брачные обыски (premarital inquiries) or premarital examinations (same file, section 1). Latgalian routes via Raduraksti and NIAB ф. 1781 — in `seed-sources.md`.
- [ ] Confession lists (исповедные росписи) — for family composition and checking neighbouring years. Establish the columns and age coverage from the document. Composition of the file and reading the household formulas — `field-lessons.md`, section 1, "Confession lists". Clergy registers (клировые ведомости) describe the clergy and their families. The description of a parish may list the villages and hamlets attached to it. Check the attachment as of the event date, especially for same-named places. Example — the [клировая книжка Полтавской епархии за 1902 год](https://histpol.pl.ua/ru/sbornik-svedenij-o-prikhodakh-poltavskoj-eparkhii?id=13311) (clergy book of the Poltava eparchy for 1902), a partial transcription of the publication with links to scans.

### Sverdlovsk oblast and the mining-and-metallurgical Urals: searching beyond metric books

On a gap in the metric books or when searching for family composition, consider the [GASO recommendations](https://gaso-ural.ru/uslugi/rekomendatsii-po-provedeniyu-issledovaniy/) (State Archive of Sverdlovsk Oblast) and the cross-fonds indexes from `seed-sources.md`. Choose relevant fonds by historical place, estate (сословие) and occupation: besides the consistory, these may be individual churches, works administrations (заводоуправления), local bodies and employers. An index gives a route to the fonds and file; check the presence of the needed document type, its years and content against the inventory and the accessible file per `search-result-validation.md`. For act books, the catalogue gives a separate list of ZAGS fonds.

In the recommendations read on 09.11.2026 (page revision of 08.04.2025), GASO states that population censuses were not transferred to it. Do not carry this statement over to revision lists, family lists and works lists; for a specific census, check preservation and the custodian in the relevant catalogue. The same page directs inquiries about the repressed to the State Archive of Administrative Bodies of Sverdlovsk Oblast (Государственный архив административных органов Свердловской области), and party and nomenklatura files to the Documentation Centre of Public Organisations of Sverdlovsk Oblast (Центр документации общественных организаций Свердловской области). These are routes by document type, not confirmation that every personal file is held there; check an already known exact designation in another archive separately. Access and requests — per `government-portals.md` and `correspondence.md`.

### Revision lists, censuses, family and household lists

- [ ] Revision lists («ревизские сказки», 1719–1858) — family composition in the male line with ages; link between revisions by household number.
- [ ] When searching a revision by settlement, also check the inventories for relevant separate lists by estate (сословие), department or owner: in one place, families might fall into different files. Do not assume such a list survived or that the family's category is known; note the files checked and their coverage.
- [ ] First General Census of 1897: to choose the archive and fonds, use the relevant preservation catalogues — Dmitry Kudinov's catalogue or the AltGU project «Архивные фонды Первой всеобщей переписи населения 1897 г.» (`seed-sources.md`). Check the information against the inventory of the census commission's fonds or another custodian; on discrepancies between descriptions, clarify the content with the archive. A uezd missing from the catalogue does not prove the sheets are lost; an inaccessible inventory leaves preservation unchecked. For information on populated places and population, also consider the summary materials of RGIA, ф. 1290 оп. 11 (link and limits of the check — in the source catalogue). Summaries do not replace the name sheets: establish the presence of names per specific file.
- [ ] Soviet-era censuses: preservation of census sheets varies greatly by region — check the archive's inventory.
- [ ] All-Russian Agricultural Census of 1917: check preservation by region; the questionnaires can reveal household composition, ages and the origin of settlers. For Altai (Tomsk) guberniya, use the GAAK index (`seed-sources.md`), then check the relevant questionnaire through an accessible file or a request. Consider neighbouring households of the same surname when this helps distinguish people or test a link; ordering all questionnaires for the surname is not required. Payment and external requests — per `correspondence.md`, only on the user's instruction (the agent drafts, the user sends); other available routes continue.
- [ ] Family lists (посемейные списки, from the 1870s) and village-soviet household books (похозяйственные книги, from the 1930s, in municipal and district archives) — household composition, years of birth, departures.
- [ ] Compare the columns of specific census cards, staff lists and household books: one document may name only the head and the number of household members, another their names and relationships. Absence of a name in a form without such a column is not evidence of the person's absence.

### ZAGS records after 1918

- [ ] Where they are held: records of recent decades remain with ZAGS offices (in Ukraine — DRATsS), older ones have been transferred to state archives. Transfer period and issuing procedure — on the official website. The boundary differs by region. The author of [#114](https://github.com/DenisSergeevitch/ex-ussr-kinship-research/pull/114) reported the following from official pages read on 31.10.2026: in Samara oblast, metric and act books up to 1920 have been transferred to TsGASO ([Комитет ЗАГС](https://zags.samregion.ru/category/gosuslugi/archive/)); in Udmurtia, ZAGS offices hold act records from 1925, while metric books of 1845–1937 and records of volost executive committees of 1918–1924 have been transferred to TsGA UR ([Комитет по делам ЗАГС](https://zagskom.udmurt.ru/about/info/news/2422/)); in Chelyabinsk oblast, ZAGS offices hold records from 1920, earlier metric records are in OGAChO ([ГУ ЗАГС](https://zags.gov74.ru/zags/other/voprosotvet/vydachapovtornyxdokumentov.htm)). On independent checking, the pages could not be read; confirm the current custody of a specific book with the archive and the ZAGS office. Do not carry one region's year over to another.
- [ ] When choosing a specific collection, check its date span and composition. For example, the author of [#146](https://github.com/DenisSergeevitch/ex-ussr-kinship-research/pull/146) reported GAIO (Ivanovo) ф. Р-2252 with dates 1890–1929 (`seed-sources.md`); the bounds of one fond do not establish the custodian of the other acts, their loss or the absence of other collections.
- [ ] For Ivanovo oblast, the [page of a branch of the ZAGS committee](https://zags.ivanovoobl.ru/departament/kontakty/filialy/lezhnevskiy-rayonnyy-filial-komiteta-ivanovskoy-oblasti-zags/), read 03.11.2026, states that applications by e-mail are not considered. This does not exclude a separate supported electronic form. Choice of channel, means of receipt and payment — per `government-portals.md`; do not carry one office's conditions over to others.
- [ ] Repeat certificates and archival certificates are usually issued to relatives on proof of kinship: prepare the chain of kinship documents for the user.
- [ ] Draft requests: full name and variants, date and place of the event, what is needed (copy of the act record or a certificate), the applicant's relationship.
- [ ] Russia: ZAGS certificates with the line «Иные сведения» (other information) and checking against the paper record — `russia-records-access.md`, section 1.
- [ ] If the question concerns a divorce in the USSR, consider notices in the local press and court files for the place and period. A notice may give the spouses' names and a lead to the court. Check the outcome of the case and registration of the event against the court decision and the ZAGS act. Check the coverage of newspaper issues and verify material matches on the image. Keep information on places to the extent needed for the research, per `privacy-and-safety.md`. See `ex-ussr-locale-guide.md`, section 6, and `field-lessons.md`, section 10, for changes to the father's entry.

### Probate cases and death searches in Russia

The [FNP probate case register](https://notariat.ru/ru-ru/help/probate-cases/) (Federal Notary Chamber) is an auxiliary official index, not an act record and not proof of kinship. Under [Article 34.4 of the Fundamentals of Legislation on Notaries](https://minjust.gov.ru/ru/documents/7900/), the public result includes the case number, the notary and the notarial district. Record these details, the URL, the query and the dates actually given; the index does not replace information on heirs or the content of the case itself. Access to documents and requests to a notary — per `correspondence.md`.

The form describes an exact full-name match: a query without a patronymic finds cases where the patronymic is absent. Dates allow partial entry. If a doubtful filter yields zero, repeat without it; a control search is needed only when the filter's behaviour is unclear. Choose justified name and period variants by the question, within the query limit, without mandatory iteration over every year. The year in the case number does not stand in for the date of death; completeness of historical coverage is not established. A nil result applies only to the query checked, and the candidate's identity is assessed per `evidence-protocol.md`.

Per a contributor's observation of 30.10.2026, the form did not distinguish «е» and «ё». Do not collect incidental current addresses of living people; keep historical information only to the extent needed for the family research, per `privacy-and-safety.md`.

The notarial district helps choose a geographical direction but does not prove the last place of residence: when that is unknown or abroad, the place where the estate is opened may be determined by the location of property. This exception of Article 1115 of the Civil Code of the Russian Federation is explained in [Constitutional Court of the RF ruling No. 12-П of 26.03.2024](https://www.ksrf.ru/doc/KSRFDecision745336.pdf). Do not infer the region from the notary code in the URL; check the notary's card and the details of the specific case.

Limits of the check of 29.10.2026: the FNP form and help were read on its [«нотариат.рф» domain](https://xn--80aaxsfnme.xn--p1ai/ru-ru/help/probate-cases/), including partial dates, exact full name and the query limit; opening `notariat.ru` directly gave HTTP 502. Name search and case results were not checked. Old death dates, missing birth dates and late opening of cases are described by the author of [issue #84](https://github.com/DenisSergeevitch/ex-ussr-kinship-research/issues/84); these observations do not establish the completeness of the register or mandatory behaviour of every filter.

### Repression, dekulakisation, deportations

- [ ] Indexes of the repressed: «Открытый список» (Open List; Russian and Ukrainian versions), the database «Жертвы политического террора в СССР» (Victims of Political Terror in the USSR; Memorial, address not checked), «Возвращённые имена» (Returned Names), regional memorial books — `field-lessons.md`, section 3.
- [ ] Family memorial databases: «Бессмертный барак», «Последний адрес».
- [ ] Publications of documents from departmental archives: lists of the evicted, books of the rehabilitated (e.g. «Нескорена Буковина»).
- [ ] Special settlements and labour settlements: registration files of special settlers in MVD archives at the place of exile.
- [ ] Chechen families and the 1944 deportation: certificate of eviction, certificate of rehabilitation, special-settler files in Kazakhstan and Kyrgyzstan, the Book of Memory of the Chechen Republic — `chechnya-deportation.md`.
- [ ] Draft requests for copies of criminal and registration files, certificates of rehabilitation.
- [ ] Russia: requests for rehabilitation, access to files and information on the fate of the repressed — `russia-records-access.md`, sections 2–3.
- [ ] Deportations: for the place of residence and property left behind before eviction, check the inventories of the state archive of the region of origin (acts, lists of residents, household books); registration files and movements — also archives at the place of special settlement. Establish the custodian and preservation per specific series; these are search routes, not a guarantee that a file exists.

### Evacuation 1941–1945

- [ ] Lists of evacuees in the archives of places of arrival (oblast and district archives, executive committees).
- [ ] Card index of the Central Information Bureau for the Registration of the Evacuated Population (Buguruslan) — check its location and access procedure.

### Captivity, deportation to Germany, Ostarbeiter, filtration

- [ ] Route via Arolsen and German civil-registry (Standesamt) books, name forms and the order for reading indexes — `germany-forced-labour.md`.
- [ ] Arolsen Archives (online collections) — registration cards, camp lists, forced-labour documents.
- [ ] POW cards in OBD «Мемориал» and memorial projects for camps (e.g. Zeithain from `seed-sources.md`).
- [ ] Filtration files — in oblast archives and security-service archives; draft requests only.
- [ ] Documents of the occupation period in the Russian database «Без срока давности» (No Statute of Limitations) — choosing the card and checking the reading per `field-lessons.md`, section 5.
- [ ] **Camps and places of forced detention on occupied Soviet territory.** Establish the place, period and kind of detention. By these, choose the acts of local ChGK (Extraordinary State Commission) commissions, lists of prisoners and of the liberated, published collections and the district chronicles «Памяць» (Memory), where available. The [Rosarkhiv reference list](https://portal.rusarchives.ru/demands/sp/fl.shtml) gives for Ozarichi incomplete lists of prisoners and interview records in GARF, and documents on prisoners in NARB (National Archive of the Republic of Belarus). Confirm the current custodian, designation and access against the inventory. When searching a suitable database, allow for historical spellings of the place. Absence of a name from the lists viewed limits only that search. Routes to Belarusian archives and publications — in `seed-sources.md`.

### Townspeople, officials and students (Russian Empire — 1920s)

- [ ] For the Moscow мещанство (petty townspeople), consider the family and alphabetical books of the Moscow мещанская управа (townspeople's board), TsGA Moscow, ф. 5 оп. 1. Per [Igor Yakovlev's analysis](https://yakovlev.family/2024/10/31/posemejnye-spiski-moskovskih-meshhan/), first establish the слобода (settlement) of registration from metric, revision or confession records; the actual address and the слобода of registration may differ. Look for the family number in the relevant alphabet or another document, then choose the book by слобода and number range from the [fonds inventory](https://cgamos.ru/upload/iblock/dbd/tzpz949v532lvwnxb98iwfz3d5plgy48/5.1.pdf). Check the men's and women's books according to the task and the inventory's content; a file card alone does not establish the person's membership of the слобода or the presence of the family in the book. The author's description and example were read on the check of 04.11.2026; access to the inventory and a specific file was not confirmed — check separately.

- [ ] Address books «Весь …», address calendars and commemorative books for the years chosen by the question: initials, address, rank or occupation, namesakes in the same house (`source-strategy.md`, section 5).
- [ ] Lists of departmental ranks, court and educational calendars — by the rank or service named in the directory.
- [ ] Формулярные (послужные) списки (service records) of officials — in the fonds of the institution where the person served. Per a [study of service records](https://elar.urfu.ru/bitstream/10995/116446/1/qr_3_2022_17.pdf) («Quaestio Rossica», 2022, No. 3), by the mid-19th century they recorded marital status and children, and from 1905 the children's confession; children's birth dates in the first half of the century can be inaccurate. Check dates against the metric records.
- [ ] If family memory speaks of education (institute, gymnasium, courses), lists of pupils and graduates (`seed-sources.md`, personalhistory.ru) and the fonds of the institution itself in the regional archive. Establish each list's coverage by year before assessing an empty result.
- [ ] When choosing surname variants, allow for the limits of result counters per `ex-ussr-locale-guide.md`, section 4.

### Emigration and resettlement

- [ ] Departure: foreign passports and files in the guberniya boards (губернские правления); lists of settlers.
- [ ] Internal resettlement: check documents at the place of departure and of arrival, including petitions, family lists, permits, village-society documents and registration records. A petition or resettlement plan does not prove the family moved: compare the outcome of the file and subsequent records at both places. For a landowner's transfer of serfs, use the owner and his estates as search pointers, checking the link against documents.
- [ ] Arrival: ship passenger lists (e.g. Ellis Island for the USA, Hamburg lists), naturalisation, censuses of the country of arrival — in the order customary in that country.
- [ ] Return (re-emigration) and consular registration — draft requests.
- [ ] Russian emigration: look for materials of the Russian Foreign Historical Archive in Prague (Русский заграничный исторический архив) in [GARF](https://statearchive.ru/2044). Documents of BREM (Bureau for Russian Émigrés in Manchuria), including émigrés' personal files, are described in the [guide to the State Archive of Khabarovsk Krai](https://guides.rusarchives.ru/node/19980), ф. Р-830, date span 1932–1947. Check the presence of a file against the inventory and with the custodian.
- [ ] For a move to the Baltic states after 1944, choose records by the place and time of the event: pre-revolutionary books and the 1897 census in Raduraksti do not establish later resettlement. Search for birth and earlier events at the documented former place, and for later acts with the established custodian in the country of arrival; check present access and transfer to an archive per `government-portals.md`, and do not treat the whole Soviet period as automatically closed or unpublished.

### Jewish communities

- [ ] Metric books of crown rabbis (separate Jewish books in the same archives and FamilySearch films; in Geneteka marked «mojż.»).
- [ ] JewishGen: unified database search and Family Finder; Yizkor books by shtetl.
- [ ] Yad Vashem: Central Database of Shoah Victims' Names and Pages of Testimony (often filled in by relatives — check who submitted them).
- [ ] Revision lists and family lists of Jewish communities.

### Military service (optional block — if the person served)

**Great Patriotic War / career soldier 1939–1945**

- [ ] «Память народа» (Memory of the People, `pamyat-naroda.ru`): general search by full name, then every document in the group — service record card index, award card index, award sheets and orders (always the reverse of the sheet with the resolutions of higher commanders), long-service decrees, officers' database, «Дорога памяти». On an actual CAPTCHA, follow `browser-and-captcha.md`, section 5: one permissible attempt in the internal browser, then if needed a tab and a ready request to the user; continue with the available sources.
  - Search: `https://pamyat-naroda.ru/heroes/?adv_search=y&last_name=<Фамилия>&first_name=<Имя>&middle_name=<Отчество>&group=all`
  - Unit information: `https://pamyat-naroda.ru/warunit/id<N>/` — commanders, subordination, combat path.
  - Checking strong matches against the full card and comparing documents from different groups — `field-lessons.md`, section 4.
- [ ] «Бессмертный полк» (`moypolk.ru`): site search `https://www.moypolk.ru/search/soldiers?s=<Фамилия Имя Отчество>`. An empty external result does not replace a search of the internal database. On the page found, open the sections «Документы» (documents), «Фотографии» (photos), «Семья солдата» (the soldier's family).
- [ ] «Дорога памяти» (`1418museum.ru`) — card and photo, if the family uploaded them.
- [ ] Regional electronic memorial books, e.g. Moscow's `polk.mos.ru` (search format not checked).
- [ ] OBD «Мемориал»: choose the sections on losses, Memorial Books and personnel by the question, including searching for those who returned from service. Section composition, settings and limits of a negative result — `field-lessons.md`, section 4; record the filters actually enabled.
- [ ] The history of a unit or educational institution, if it helps the question. Check formation, deployment, renamings and evacuation against documents, military-history publications and graduates' books. Check an abbreviation, a disputed regiment number and dates of front-line service against the composition and subordination of the formation on the dates relevant to the question.
  - From a letter, certificate or commendation, keep the original designation of the postal address and the date. Choose a historical reference by the type of number and the period. Field post stations (полевые почтовые станции), conventional unit numbers (условные номера частей) and military-unit numbers (войсковые части) — field post numbers are described in different indexes. The 1943 change of system is reflected in [order No. 0105](https://docs.historyrussia.org/ru/nodes/332991). A reference correspondence gives a lead. With an unclear digit, keep the variants and check them against dated documents of the unit and of personnel records.
- [ ] War diaries (журналы боевых действий) of units for the dates of the deeds in the award sheets.
- [ ] Post-war service (MVD, MGB, military commissariats) — draft requests to departmental archives only.
- [ ] For navy service during the Great Patriotic War, check the [Navy Archive in Gatchina](https://archives.gov.ru/faq/war.Shtml) (Архив ВМФ); for earlier service, RGAVMF. The [Reference and Information Centre of the Federal Archives](https://sic.rgantd.ru/news/sic/o-mestakh-khraneniya-dokumentov/) names the Central Border Archive of the FSB (Центральный пограничный архив ФСБ) for certificates of service in the border troops, and RGVA for a number of documents of the border and internal troops of the USSR. For the command staff of partisan detachments there is [RGASPI, ф. 69, оп. 4](https://rgaspi-site.dlibrary.org/ru/nodes/322-opis-4-lichnye-dela-komandnogo-sostava-partizanskih-otryadov). Check the custodian of a specific series by department, period and inventory.

**First World War and Civil War, service in the Russian Imperial Army**

- [ ] «Памяти героев Великой войны 1914–1918» (In Memory of the Heroes of the Great War, `gwar.mil.ru`) — loss lists, award documents, hospitals.
- [ ] For Galicia and Bukovina — Austro-Hungarian loss lists (`field-lessons.md`, section 4).
- [ ] RGVIA (army before 1918) and RGVA (Red Army 1918–1940s) — draft requests; officers' service records, unit lists.
- [ ] Per the [Rosarkhiv page on genealogical research in RGVIA](https://rusarchives.ru/uslugi/pomoshh-issledovatelu/o-vozmozhnosti-provedeniya-genealogicheskih-issledovaniy-rgvia): service records (послужные списки) of command staff of 1881–1917 — ф. 409 (for officers' lists of this period the archive has an alphabetical index); формулярные списки of generals, officers, soldiers and officials of the military department of 1720–1900 — ф. 489; seniority lists (списки по старшинству) of 1737–1917 — ф. 407 and 408. Such documents are also found in other fonds of the archive.
