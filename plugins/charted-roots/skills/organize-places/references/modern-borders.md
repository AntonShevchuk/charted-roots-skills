# Mapping historical places to modern borders

Guidance for `organize-places`. It is knowledge to apply with care, not a lookup table: check the town, not the province.

## The rule

A Place sits where the town is **today**. The chain is the modern country, its first-level division, and so on down to the locality. The name the export uses, and the native form, are `aliases:` on the Place. A historical state is never a parent: no `Prussia` country, no `Silesia` under `Germany` for a town now in Poland. The historical context goes in the `reason` line and in the aliases.

## `place_type` per level

| Level | `place_type` |
|---|---|
| Modern country | `country` |
| Voivodeship, oblast, Land, province, state | `state` |
| Powiat, Kreis, raion, county, district | `county` |
| Incorporated city or town | `city` |
| Village, parish, ward, estate, cemetery | `locality` |

`township` is a US civil township only. `town` and `village` map to `locality`. No child ranks above its parent. Use a `customPlaceTypes` value from `data.json` only when the vault defines one.

## Titles and aliases

- **Title**: the English form, per the vault's Language section (`Wrocław`, `Lower Silesian Voivodeship`, `Copenhagen`).
- **Aliases**: the export's form of a name and its native and historical forms (`Breslau`), each on the Place it names. Put a historical region name (`Schlesien`) as an alias only on a modern division it substantially coincides with, never on the city. A region that splits across several divisions or countries goes on none of them: rely on the leaf (`Breslau` on the city) and let `check` confirm the string resolves, adding a disambiguating alias on the leaf if it does not.
- A string must resolve to exactly one Place, and `check` fails when it lands anywhere but its planned Place. Add the alias that disambiguates (a district or county form) rather than dropping one.
- Keep native-script spellings verbatim.

## Common historical jurisdictions

These move town by town. Treat each line as a prompt to look at the town, not as an answer.

- **Prussian provinces** (Preußen, to 1945): Schlesien, Posen and Westpreußen are mostly in Poland today; northern Ostpreußen, with Königsberg, is in Russia and Memelland in Lithuania; Pommern is split between Poland and Germany; Brandenburg, Sachsen, Westfalen and the Rhine Province are mostly in Germany. Elsass-Lothringen is in France; North Schleswig is in Denmark.
- **Austria-Hungary crown lands**: Galizien is split between southern Poland and western Ukraine; Böhmen and Mähren are in Czechia; Bukowina is split between Romania and Ukraine; Krain is mostly Slovenia; Küstenland, Dalmatien and Bosnien fall to Croatia, Slovenia, Italy and Bosnia and Herzegovina; the pre-1920 Hungarian counties run across Hungary, Slovakia, Romania, Serbia, Croatia and Ukraine.
- **Russian Empire governorates**: the Kingdom of Poland governorates (Warsaw, Kalisz, Lublin and others) are in Poland; Vilna, Kovno, Grodno, Minsk, Volhynia, Podolia, Kiev, Kherson, Bessarabia, Courland and Livonia spread across Lithuania, Latvia, Estonia, Belarus, Ukraine and Moldova. A governorate rarely equals a modern division, so go by the uyezd or the town. The `research-ancestry` regional guides cover the former Russian Empire and USSR.
- **Danish and Swedish duchies and provinces**: Slesvig and Holsten (Schleswig-Holstein) are split between Germany and Denmark; Skåne, Halland and Blekinge were Danish until 1658 and are Swedish; Finland was Swedish until 1809.

## When to say `unidentified`

Set `unidentified` on the PLAC entry, with what is uncertain, when:

- the name fits several towns (a `Neudorf` with only a province for context);
- the string names only a village or parish and the region is too broad to settle it;
- the spelling is too corrupt to read as one place.

Never link such a string to the coarser Place, and never invent a Place for it. Put the candidate region in the `unidentified` text so the reviewer can find it, and let the user settle it from the record image. A string that is not a place at all (a note, a ship, "at sea") is `not_place`, not `unidentified`.
