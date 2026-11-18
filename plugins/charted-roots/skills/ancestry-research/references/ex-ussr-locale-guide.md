# Locale guide: former USSR, USSR and the Russian Empire

Read this file when working with historical borders, multilingual names, script changes, calendars and archival jurisdiction.

## 1. Jurisdiction on the event date

The modern country does not determine where an old record is held. For each event, establish:

1. the date or known range of the event;
2. the historical state;
3. the administrative chain on that date;
4. the confessional or civil registering institution;
5. the modern territory and the likely successor archive.

Look for variants of the levels: «губерния» (guberniya), «область» (oblast), «край» (krai), «уезд» (uyezd), «округ» (okrug), «волость» (volost), «район» (raion), «сельсовет» (selsoviet, village council), «приход» (parish), «благочиние» (deanery), «воеводство» (voivodeship), «повет» (povet), uyezd/city ZAGS (civil registry office). If a named raion is not on the modern map, check a gazetteer for the record's date: the raion may have been renamed or abolished. Modern absence does not establish a scribal error; keep a possible corruption as a hypothesis.

While the place, period or parish is still ambiguous, build several reasoned routes through catalogues and neighbouring settlements. Refine the jurisdiction from the records you find; do not postpone the whole search until this chain is filled in.

Do not confuse same-named villages. Use neighbouring settlements, parish, river, railway station, uyezd and coordinates together as a set of distinguishing features. Neighbouring settlements may share one second name marked «тож» ("also called"). In that case compare the available information on the population size, its composition and when the settlements arose. Compare the estate (soslovie) as it is given in the documents of the relevant period.

**In the vault.** Once a place is identified, its hierarchy goes into Place notes (`parent_place` + `parent_place_id`, `place_type` from the closed list in the core model; a village or town is `locality`; former and alternative names go in `aliases:`). Historic chains may be anachronistic — that is a schema decision, not a fix. A toponym that is not yet resolved stays unidentified: record it in the Hypothesis or Survey note, and never invent a parent chain for it. A place missing from the gazetteer is a stop-and-ask point (`SKILL.md` § Rules that win).

### Place and parish on the event date

When a family birthplace conflicts with the documents, check when the settlement arose and its former names in historical lists of populated places, administrative-division handbooks and local publications of clear provenance. A late official founding date may refer to a renaming or a new status; absence of a name from one list does not prove the settlement did not exist. Distinguish the claims "was born" and "lived".

Choose neighbouring parishes from historical maps and the catalogues of the relevant confession. Modern coordinates and a radius, for example 20–30 km, help pick candidates but do not determine the historical parish and do not bound the search. Check the neighbouring uyezd and other archives: an empty index in one archive does not close the books of another.

[GeoNames](https://www.geonames.org/about.html) holds coordinates and name variants, draws on several sources including NGA, and accepts community edits. It is a class-C geographic lead: check the provenance of the entry and the existence of the place in the relevant year against a historical source. For hard-to-read places in military documents, you can pick suitable records from the same military commissariat (voenkomat) and compare their spellings with a historical list; there is no need to download everyone conscripted.

### Corrupted or unidentified place name

If a name from a document is not in gazetteers, on maps or in inventories, do not pick a similar village on sound alone. Decode it from several records:

1. **Keep the string as written** and open the image of the document. Distinguish a scribe's error from an error of a later index or OCR. A "sic" note changes the further search: the scribe may have written the name by ear, while the index may have misread the handwriting.
2. **Compare suitable records of the same unit.** Pick available cards, lists or metric-book entries with the same guberniya and uyezd and, if given, the same volost: for example, namesakes or fellow servicemen. Record the useful place spellings and links to the records; collecting the entire result set for the volost is not required. For GWAR cards, `scripts/gwar.py places` does this (`ww1-search.md`, "Compare spellings of a locality").
3. **Compare against the list of places of that unit.** The inventory of metric books (parishes and attached villages), the guberniya list of populated places, the volost list, a historical map. The candidate must exist in the relevant unit on the date of the document.
4. **Explain the discrepancy by specific scribal habits:** writing by ear (voiced vs voiceless consonants, dropped or inserted vowels), confusion of similar handwritten letters (т/п/н, и/н, ш/щ, abbreviation with a full stop), Russifying the stem (a Romanian or Polish form of a saint's name in the place name → the Russian one), a change of suffix (-овка/-евка/-ицы/-ены/-ешты/-ауцы), a dropped prefix (Слобода-, Ново-, Старо-), abbreviation. Explain which changes support the chosen candidate; do not invent a chain of substitutions to reach a similar-sounding name.
5. **Look for converging spellings.** A strong sign is several independently written forms from one volost that differ in different ways yet converge on one name from the list. One form resembling several villages is a weak sign: record all candidates.
6. **Assess independence by `evidence-protocol.md`.** Several cards from one list may repeat one reading even if they concern different people. The number of people or URLs does not by itself establish independence.
7. **Test the candidate with a document.** The identification remains a hypothesis until the person or family is found in the candidate's own source: the metric book of its parish, a revision list, a family list. A negative result for one candidate does not carry over to the others.

Keep the document's spelling verbatim in the transcription and Source; keep the interpretation, with its reasoning and status, separately in the Hypothesis note. Keep the table of variants and tested candidates in the Survey note. Illustrative example: a card reads «Новоберезицы», and no such place is in the gazetteers. Cards of other people from the same volost give «Новобережка», «Новоберезка» and «Ново-Березовка». They converge on the village «Новоберёзовка» in the uyezd parish inventory. The candidate is tested against the metric books of its parish, while the similar-sounding village of another volost stays on the list of alternatives.

## 2. Geographic scope

"Ex-USSR" means all former Union republics and territories that, in the period studied, may have belonged to the Russian Empire, the USSR, neighbouring states or occupation administrations:

- Russia;
- Ukraine;
- Belarus;
- Moldova;
- Estonia, Latvia, Lithuania;
- Georgia, Armenia, Azerbaijan;
- Kazakhstan, Kyrgyzstan, Tajikistan, Turkmenistan, Uzbekistan.

For border families also check Poland, Finland, Romania, Germany/Prussia, Austria-Hungary, the Ottoman Empire and other historical jurisdictions, but do not widen the search without an actual connection. For cases involving Galicia or Bukovina read `references/habsburg-galicia-bukovina.md`. For Bessarabia, Moldova, the MASSR and the Dniester uyezds of Podolia and Kherson guberniyas read `references/bessarabia-moldova.md`. For Chechen families and the 1944 deportation (renamed villages, names, special settlement) read `references/chechnya-deportation.md`.

## 3. Names: keep the original, build variants separately

For each name form keep:

- as written — the exact string of the source (verbatim in the transcription and Source);
- the normalised research form (the Person's display name; other forms in `aliases:`, labelled as research forms);
- language and script;
- the rule or reason for the variant;
- the degree of confidence.

Language, rule and confidence for a non-obvious variant go in the Hypothesis or Survey note, not in Person frontmatter.

### Typical sources of variation

- pre-reform Russian orthography and the final hard sign;
- Russian, Ukrainian, Belarusian and Polish forms of one Christian name;
- German, Yiddish/Hebrew, Armenian, Georgian, Romanian, Baltic or Turkic forms;
- Russification or reverse localisation of a name;
- a patronymic in full, short, colloquial or absent form;
- the gendered surname ending; with reason also check the variants «-ских» / «-ский/-ская», reported by the author of [#92](https://github.com/DenisSergeevitch/ex-ussr-kinship-research/pull/92) on 30.10.2026. A shared stem does not establish identity of persons or the direction of migration;
- a double surname, maiden name, surname after a stepfather/husband;
- an everyday name, diminutive, pseudonym;
- errors of the scribe, the OCR and a later index;
- the transition between Arabic, Latin and Cyrillic script in some republics;
- for records without a stable surname, check whether the father's name has landed in the index's surname field, and whether the form «Имя Имя-отца» ("Name Father's-name") or «Имя-отца-оглу» ("Father's-name-oglu") is used. This route may be useful, for example, in Crimean Tatar documents; establish the presence of this form from the record, not from presumed ethnicity. Link a later surname and different renderings of the name only as hypotheses;
- when matching 19th-century revision lists to the 1920 census for Bashkir settlements of Ufa and Orenburg guberniyas, a contributor used the stem of the later surname as a variant of the personal name for the earlier search. Match candidates by household composition, dates and place, keeping the surname's origin as a hypothesis until checked. The same spelling may denote a surname, a patronymic or a settlement name; establish the word's role from the column and the context of the record. [Observation of the author of #162](https://github.com/DenisSergeevitch/ex-ussr-kinship-research/pull/162);
- different systems of Latin transliteration.

Do not declare two forms equivalent merely because they are often rendered into each other. Use the date, place and family cluster.

### Case-insensitivity, transliteration and mixed spellings

In local comparison keep the original spelling, and build search keys separately, taking into account what the tool in use can do.

- **Case.** In standard SQLite the built-in `lower()` converts only ASCII, and `LIKE` by default is case-sensitive for characters outside ASCII. For Cyrillic use an available comparison method with Unicode support — for example, Python `str.casefold()` applied to both strings compared. The search key serves to match variants; the original record keeps its spelling. [SQLite `lower()`](https://sqlite.org/lang_corefunc.html#lower), [SQLite `LIKE`](https://sqlite.org/lang_expr.html#like), [Python `casefold()`](https://docs.python.org/3/library/stdtypes.html#str.casefold).
- **Transliteration and word order.** Choose useful variants from the known spellings and how the search works, for example Evgeniy/Evgeny or Dmitriy/Dmitry. Check the orders `First Last` and `Last First` when word order affects searching in the chosen field. The general variant matrix is in section 4.
- **Mixed scripts.** When parsing names and pseudonyms, choose a pattern that supports the letters of the languages in use, diacritics, and the spaces, hyphens and apostrophes occurring in the record. Bear in mind that ASCII mode restricts Unicode matching. Check look-alike Cyrillic and Latin characters against the original string, keeping the variants separate. [Python Unicode matching rules](https://docs.python.org/3/library/re.html#regular-expression-syntax).

### Name dictionary

For Russian personal names consider N. A. Petrovsky, «Словарь русских личных имён» (Dictionary of Russian Personal Names): [the publisher's description of the edition and its indexes](https://slovari.ru/default.aspx?p=312&s=0). Check the specific entry and the labels of the form, keeping the edition or the link; the dictionary helps choose search variants but does not replace the record. Historically related forms may be used as independent names: do not change the source's spelling and patronymic, and do not merge people on a dictionary link alone. For other languages and traditions use dictionaries suited to them.

## 4. Practical query matrix

For a key person, choose suitable combinations from this list according to the known data and how the search works. It is not required to try every combination in every database:

1. surname + first name + full patronymic;
2. surname + initials;
3. first name without patronymic;
4. maiden/previous surname;
5. masculine/feminine surname ending, where applicable;
6. pre-reform and modern form;
7. Cyrillic and several reasoned Latin transliterations;
8. the local-language form;
9. a year range allowing for approximate age, rounding and collection coverage;
10. name + spouse/parent/child;
11. name + old and new toponym;
12. name + occupation, estate (soslovie), military unit, place of conscription or evacuation.

Record the variants actually used in the `Survey -` note, not only the final successful queries.

If an index shows a result count, comparing substantive variants under identical filters may suggest an additional check. The count depends on collection coverage, duplicates, OCR and search mode, not only on how common the surname is. A frequent form or its regional cluster does not automatically get priority: choose the variant by place, time and other features of the family. Do not infer the original surname, origin or kinship from the number of rows. If the comparison influenced the plan, record the database, filters and date in the Survey note.

### Databases with exact field matching

Choose name forms by section 3, `SKILL.md` (Workflow step 2) and the "name traps" in `field-lessons.md`, section 2. If a database (OBD «Мемориал», GWAR, memory books) searches only by exact field match, additionally:

1. **Test useful combinations of forms, not just each part separately.** In a mode where all filled fields must match, single substitutions may miss a record with several variants. Choose combinations by language, period and documents already found, widening them as needed. For example, Георгиевич, Егорович and Юрьевич may be search hypotheses about the father's name, but they do not prove that this is one person or that the names were interchangeable official names. A full enumeration of all combinations is not required.
2. **Keep commonly confused names as a separate hypothesis.** Mark them in the Survey: a hit on such a name needs checking that it is the same person.
3. **If the surname may have been corrupted beyond recognition,** search by first name and patronymic without the surname in the relevant year or place. Filter the results locally by year, place and surname similarity.

## 5. Dates and calendars

- Record the date as written in the transcription; put the ISO value on the Event and note the calendar in the Source body.
- State the calendar: Julian, Gregorian, unknown or other.
- Do not convert silently, and do not correct a birthday to the modern calendar without explanation.
- Bear in mind that different institutions and territories may have used different calendars in transitional periods. For Galicia and Bukovina, do not infer the calendar of a metric book from Austrian rule alone: check the confession, period and practice of the specific book; a 12–13-day discrepancy is a hypothesis to test, not a ready explanation (`habsburg-galicia-bukovina.md`, section 3).
- The difference between the Julian and Gregorian calendars, by Julian dates: 11 days from 29 February 1700 to 28 February 1800, 12 days from 29 February 1800 to 28 February 1900, 13 days from 29 February 1900 to 28 February 2100 ([calendar rules](https://aa.usno.navy.mil/faq/calendars), USNO). Under the [decree introducing the Western European calendar](https://projects.rusarchives.ru/statehood/08-34-dekret-kalendar-1918.shtml), civil usage in Russia went from 31 January 1918 straight to 14 February. If a later document, register or inscription differs from the metric book by exactly the number of days for its period, that is a reason to check for a style conversion; such a difference does not by itself prove the records are the same. Keep both dates with their calendar stated.
- For Russia in the transition period, check the style from the book's heading, any statement of the calendar, and events with independent dating. Church and civil books may have continued in parallel. A match between the name and the church calendar of saints («святцы») is a weak pointer and needs a separate check of the record's calendar.
- If a one-day difference remains after conversion, check whether the shift for the relevant period was applied and whether both records relate to the same event. Keep the dates of birth, baptism and later celebration separate.
- A family date may refer to a name day. If that version fits the name, the parish calendar and the family's practice, check the corresponding saint's commemoration day and the available birth records near it, including for several preceding days. Treat the calendar and year of the celebration itself separately from the calendar of the metric book. The explanation of the discrepancy remains a hypothesis, checked against the parents, godparents and other records.
- An age in a census, military card or death record may be rounded. Record a computed birth date as a range, not an exact date (on the Event: `date_precision: estimated` or `range`).

## 6. Record types by period

### Russian Empire and neighbouring jurisdictions

- metric books and civil acts;
- confession lists («исповедные ведомости»);
- revision lists («ревизские сказки»);
- family and household lists («посемейные и подворные списки»);
- censuses;
- recruitment and military documents;
- Austro-Hungarian conscription books and service records (Musterungslisten, Grundbuchblätter) for natives of Galicia and Bukovina;
- land cadastres (the Josephine survey 1785–1789, the Franciscan 1819–1820; later cadastral series separately);
- noble, merchant, meshchane and other estate (soslovie) files;
- address calendars, memorial books («памятные книжки»), staff lists;
- school, court, notarial and inheritance files;
- resettlement and emigration documents;
- periodicals, obituaries, announcements.

### USSR

- ZAGS acts and repeat certificates;
- house registers and household books («домовые и похозяйственные книги»);
- passportisation and population registration;
- personnel questionnaires and personal files;
- military registration, awards, losses, captivity, demobilisation;
- motherhood awards from 1944 and related questionnaires as a route to information about children; conditions and limits of inference — `field-lessons.md`, section 9;
- evacuation, special settlement, deportation, filtration;
- files of the repressed and of rehabilitation;
- Party/Komsomol materials;
- censuses and voter lists;
- cemetery books and memory books;
- address directories and the local press, including notices of the opening of divorce proceedings. Publication in the local newspaper was required by art. 24 of the [decree of 8 July 1944](https://sun.tsu.ru/mminfo/2020/000462771/1944/1944_037.pdf). The requirement was removed by [decree No. 4238-VI of 10 December 1965](https://meganorm.ru/mega_doc/dop1/75/ukaz_prezidiuma_vs_sssr_ot_08_07_1944_red_ot_07_05_1986_ob/0/ukaz_prezidiuma_vs_sssr_ot_10_12_1965_N_4238-VI_o_nekotorom.html), item 3. Establish whether notices exist from the specific issues. The checking route is `source-strategy.md`, section 12, "ZAGS records after 1918". A notice is a Source, never an Event (`CLAUDE.md`).

### Post-Soviet period

Rules of access to acts and archival files vary by country and by age of record. Do not assume availability. Check the current requirements of the official body at the time of research, and record which proof-of-kinship documents may be required.

## 7. Confession and community

Before civil registration existed, a record could depend on the parish or community: Orthodox, Catholic, Lutheran, Reformed, Jewish, Muslim, Armenian Apostolic, etc. Use confession only as an archival feature and only with a source reference; do not infer a person's modern religious or ethnic identity from an old record.

Where to look for records by confession (check coverage and custodian against the opisi):

- **Old Believers and Edinovertsy (единоверцы).** In the Russian Empire, under the rules of 1874, the registers of marriages, births and deaths of Old Believers were kept by the police ([collection of laws, §§ 21–25](https://azbyka.ru/otechnik/sekty/sbornik-zakonov/)). Look for them in the fonds of the police and guberniya boards, for example in the [opisi of the uyezd police administrations of Tula guberniya](https://guides.rusarchives.ru/funds/128/uezdnye-policeyskie-upravleniya). Check the metric books of Edinoverie parishes also in the [collections of parish registers](https://guides.rusarchives.ru/node/77489).
- **Muslims of the Orenburg Mohammedan Spiritual Assembly (Оренбургское магометанское духовное собрание).** The Assembly's documents are described in the [guide of the National Archive of the Republic of Bashkortostan](https://guides.rusarchives.ru/funds/94/orenburgskoe-magometanskoe-duhovnoe-sobranie-1788-1917-gg), ф. И-295. Look for metric books by mosque, settlement and period in the suitable opisi. Establish the language and script before reading.
- **Civil-status acts of the Kingdom of Poland** (from 1826): the witnesses to the drawing up of the act (`świadkowie`) are not the same as the godparents (`rodzice chrzestni`), although the same people could act in both roles ([State Archive in Kalisz](https://www.kalisz.ap.gov.pl/wystawy-on-line/nadaje-ci-imie)). Do not record a witness as a godparent without a direct statement in the text.

## 8. Special migration scenarios

Check the chain of places, not a single point:

- resettlement within the empire;
- Stolypin-era and earlier resettlements;
- First World War refugees;
- revolution and civil war;
- collectivisation, dekulakisation and special settlement;
- deportations of peoples;
- the evacuation of 1941–1945;
- prisoners of war and forced labour;
- post-war repatriation;
- labour migration and job assignment («распределение»);
- late Soviet and post-Soviet emigration.

For a move, check the points of departure and arrival; add transit points when documents or a specific hypothesis point to them.

## 9. Archival reference

For an archival document keep, where possible:

`Archive, fond, opis, delo, list/verso or frame, file title, date range, act number, catalogue URL, access date.`

In the vault this chain goes into the Source and the Citation `page:` locator (quoted verbatim, never rewritten). Without it, a screenshot or a retelling is hard to re-check.
