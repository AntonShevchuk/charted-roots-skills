# Deported to Germany: Arolsen Archives and German civil registers

Read this when searching for a person deported from the USSR to Germany during the Second World War, a camp prisoner, or a displaced person after the war. Examples of personal data are fictitious. The observations of the author of [#69](https://github.com/DenisSergeevitch/ex-ussr-kinship-research/pull/69) describe individual searches; check the interface, access and coverage for the material chosen. Online collections and portals below are used only on the user's explicit instruction for the task (`SKILL.md` § Rules that win).

## 1. Names, indexes and dates

- In individual cards and indexes the PR author observed transposition of first name and surname, truncation and rendering by ear. For example, Анна Сидоренко can be searched as `Sidorenko, Anna`, and where there are signs of transposition also check `Anna, Sidor`. If such a recording pattern is confirmed, the first-name letter in the index is useful; this is not a universal arrangement of German lists.
- Choose reasoned forms of the first name, surname and maiden name by `ex-ussr-locale-guide.md`, sections 3–4. German endings `-ow`/`-owa`, the variants `tsch`/`sch` and forms like `Anna`/`Anja` are search hypotheses, not proven equivalents. A table of every possible form and a full enumeration are not required.
- Match a corrupted place against the dates, relatives and circumstances of the record: transport, camp, employer. A similar sound or proximity in a list alone is not enough; the decoding route — `ex-ussr-locale-guide.md`, section 1.
- The date order in an interface and in a document may differ. `03/04/1925` means 4 March only where the MM/DD/YYYY format is established; otherwise keep the ambiguity until the locale and the scan are checked. Record the original as written in the transcription, and put the ISO value on the Event only once the reading is justified, stating the reasoning in the Source body.
- Record the forms and index letters actually checked in the `Survey -` note: this describes coverage, not the closing of all search variants.

## 2. Arolsen Archives

The [online collections](https://collections.arolsen-archives.org/en/search) contain registration cards, camp and labour documents, name lists and post-war lists. Use the tools available; an empty HTML shell alone confirms neither that results loaded nor that there are no records.

- On an ambiguous empty result, check the actual loading by `search-result-validation.md`. A control query is useful where there are signs of failure, but not mandatory before every negative result. Do not attribute an empty result to overload without checking.
- According to the PR author's observations, combining the first name with the surname or its root helped find transposed forms; a very broad query might yield nothing useful. Check the current behaviour of the fields and choose the narrowing from what is known.
- A person may have several documents and copies of lists with different annotations. Add the useful documents through `add-archive-record` and note the differences between them in the Source bodies; copies do not become independent confirmations (`evidence-protocol.md`).
- [The full database is wider than the online collections](https://arolsen-archives.org/en/archive/research/). For missing documents there is an [official inquiry form](https://arolsen-archives.org/en/archive/inquiry/). As of 28.10.2026 the service describes its services as free, with rare exceptions agreed in advance; check the timeline and terms of a specific inquiry on the site, and do not promise a quick answer. Drafting on the user's instruction — by `correspondence.md`, in the letters folder; the user sends. Waiting for the answer does not block other checks.

## 3. German civil registers (Personenstandsregister)

- Look for the Standesamt at the place of the event, then the present custodian of the relevant volume: a municipal or Land archive. Transfer, survival and access depend on the place, year and specific book; absence of an online copy does not mean loss.
- A death entry may give the date, place, cause of death, place of birth and information on the parents. Do not assume compulsory registration, complete fields or accuracy of the reported information; assess the document itself and the informant.
- For Hesse, start with the [official Personenstandsunterlagen page](https://landesarchiv.hessen.de/personenstandsunterlagen) and the [archive's instructions](https://landesarchiv.hessen.de/ueber-uns/personenstandsarchiv-hessen/recherche-digitalisierte-personenstandsnebenregister): the [Arcinsys Hessen](https://arcinsys.hessen.de) catalogue leads to digital second copies in LAGIS. A missing thumbnail may mean no digitisation or no permission for online publication; establish coverage for the chosen volume. As of 28.10.2026 the official descriptions were read; a direct link into the new module `lagis.hessen.de` gave HTTP 500, image viewing not confirmed. Check the catalogues of other Länder on their official sites.
- In a suitable volume, find the alphabetical index and its coverage. Open entries by number; check the first-name letter where there are signs of transposition. An incomplete or missing index may call for targeted reading of entries, but not a mandatory walk through every page.
- According to the PR author's observations, there are separate volumes for those killed in air raids (`Fliegerangriff`) and special books of institutions. If the main series does not cover the event, check the description of the corresponding series; such volumes are not guaranteed to exist.
- Limit a negative result to the city, period, volume and the part actually viewed, by `evidence-protocol.md`, and record it as a `Survey -` note (`result: negative`).

## 4. Local German sources

By the place of work, detention or death, choose suitable materials:

- Stadtarchiv and the Land archive: lists of foreign workers by enterprise, post-war registration lists, hospital records and thematic inventories on forced labour. Later compensation correspondence may contain private data; apply the existing access and privacy rules.
- The memorial of a former camp or institution: transport and admission lists, reference materials.
- The archive of the employer or its successor organisation: check the existence of a fond, the custodian, the search terms and possible cost, without assuming survival.
- A local historical publication or initiative: leads and archival reference codes, which are then checked against the documents; burials — by the existing route in `source-strategy.md` and the catalogue in `seed-sources.md`.

Order of correspondence, choice of channel and language of the letter — by `correspondence.md`. Do not promise a reply time or free service without the specific institution's terms.

## 5. Documents at the place of deportation and testing identity

- Look for lists of those deported and those who returned in the ЧГК (ChGK, Extraordinary State Commission) materials in ГАРФ (GARF) and in regional archives at the place of deportation; check the specific composition and access against the inventory.
- Consider also the fonds of the occupation administration, including ф. 3206 of ЦДАВО (TsDAVO, Central State Archive of the Supreme Bodies of Power and Government of Ukraine) and the fonds of raion or city administrations («управы») in oblast archives (`seed-sources.md`). In them a contributor found name lists of people who left or were sent to Germany. Check the purpose of the list, the nature of the departure and the territory covered against the document and its context. Limit a negative result to the part of the population actually checked.
- Filtration files of repatriates — by the existing section "Captivity, deportation to Germany, Ostarbeiter, filtration" in `source-strategy.md`; do not replace the custodian's access rights and requirements with a general promise of release.
- A German document and a Soviet list may support a test of identity, but the country of custody does not determine independence: establish the provenance of the specific information by `evidence-protocol.md`.
- Distinguish candidates by the whole set of dates, places, relatives and circumstances, keeping contradictions. Transposition of first name and surname is a search hypothesis; the number of matching fields does not replace the canonical order of identity resolution. Keep excluded records, with the reason, in the `Hypothesis -` note so the check is not repeated without new grounds.
