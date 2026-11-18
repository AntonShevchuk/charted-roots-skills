# Upstream tree: Ancestry name convention

Read the `.ged` against Ancestry's surname convention before calling a name difference an error.

| Case | Surname field holds |
|---|---|
| Maiden name known | maiden name only |
| Maiden name unknown | blank |
| Several marriages | birth surname; husbands attach via marriage events |
| Nicknames, married, alternate names | legal maiden name primary; others as **Also Known As** facts |

- Export maiden vs vault married name is the convention working. Choose the display form and keep the other in `aliases:`.
- Alternate forms are extra `1 NAME` blocks (each with its own `2 SOUR`) and `1 FACT` / `2 TYPE AKA`. A reader taking only the first `1 NAME` reports false conflicts.
