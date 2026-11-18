"""Date forms: GEDCOM in, Charted Roots out.

Two consumers read a date differently, so a sync writes two forms:

* **Person `born` / `died`** are checked by the plugin's *Validate date
  formats* command (`plugin_error` replicates it). It accepts ISO or
  `D MMM YYYY` dates, a `c.` / `ca.` / `circa` / `~` prefix, and `a to b`
  ranges -- and nothing for "before" or "after". So `ABT 1804` is written
  `c. 1804`, a range `1850 to 1858`, and `BEF` / `AFT` is dropped from the
  Person: the qualifier stays on the Event, which the command does not check.
* **Event `date`** keeps the vault's own forms: bare ISO with
  `date_precision`, `BEF` / `AFT` kept, `YYYY-YYYY` for a range.

`meaning` reads any of these back to one comparable value, so a pure
spelling difference between them is never reported as a conflict.
"""

from __future__ import annotations

import re

#: English, plus the German forms upstream trees carry from transcribed
#: records (`25 Dez 1914`, `15 Okt 1795`). Keyed on the first three letters.
MONTHS = {m: i + 1 for i, m in enumerate(
    "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}
MONTHS.update({"JÄN": 1, "MÄR": 3, "MRZ": 3, "MAI": 5, "OKT": 10, "DEZ": 12})

#: Prefix -> qualifier. Longest first so `CA.` is not read as `C.`.
_PREFIXES = [
    ("CIRCA", "ABT"), ("ABOUT", "ABT"), ("ABT", "ABT"), ("CAL", "ABT"),
    ("EST", "ABT"), ("CIR", "ABT"), ("CA.", "ABT"), ("C.", "ABT"), ("~", "ABT"),
    ("BEFORE", "BEF"), ("BEF", "BEF"), ("AFTER", "AFT"), ("AFT", "AFT"),
]

_ISO_FULL = re.compile(r'^(\d{4})-(\d{1,2})-(\d{1,2})$')
_ISO_MONTH = re.compile(r'^(\d{4})-(\d{1,2})$')
_YEAR = re.compile(r'^(\d{3,4})$')
_DMY_TEXT = re.compile(r'^(\d{1,2})\s*([^\W\d_]{3})[^\W\d_]*\.?\s*(\d{3,4})$')
_MY_TEXT = re.compile(r'^([^\W\d_]{3})[^\W\d_]*\.?\s+(\d{3,4})$')
_DMY_DOTS = re.compile(r'^(\d{1,2})\.(\d{1,2})\.(\d{4})$')
_YEAR_SPAN = re.compile(r'^(\d{4})\s*-\s*(\d{4})$')


def single(text: str) -> tuple | None:
    """One calendar date -> (ISO value, precision), or None."""
    d = (text or "").strip()
    m = _ISO_FULL.match(d)
    if m:
        return "%s-%02d-%02d" % (m.group(1), int(m.group(2)), int(m.group(3))), "exact"
    m = _ISO_MONTH.match(d)
    if m and 1 <= int(m.group(2)) <= 12:
        return "%s-%02d" % (m.group(1), int(m.group(2))), "month"
    m = _YEAR.match(d)
    if m:
        return "%04d" % int(m.group(1)), "year"
    m = _DMY_TEXT.match(d)
    if m and m.group(2).upper() in MONTHS:
        return "%04d-%02d-%02d" % (int(m.group(3)), MONTHS[m.group(2).upper()],
                                   int(m.group(1))), "exact"
    m = _MY_TEXT.match(d)
    if m and m.group(1).upper() in MONTHS:
        return "%04d-%02d" % (int(m.group(2)), MONTHS[m.group(1).upper()]), "month"
    m = _DMY_DOTS.match(d)
    if m and 1 <= int(m.group(2)) <= 12:
        return "%s-%02d-%02d" % (m.group(3), int(m.group(2)), int(m.group(1))), "exact"
    return None


def _strip_prefix(text: str) -> tuple:
    up = text.upper()
    for prefix, qual in _PREFIXES:
        if up.startswith(prefix):
            rest = text[len(prefix):]
            if prefix[-1].isalpha():
                if rest[:1] not in (".", " ", ""):
                    continue      # `CALIF…`, not `CAL`
                rest = rest.lstrip(".")
            return qual, rest.strip()
    return "", text.strip()


def _span(a: str, b: str) -> tuple | None:
    sa, sb = single(a), single(b)
    if not (sa and sb):
        return None
    ya, yb = sa[0][:4], sb[0][:4]
    return (ya, yb) if ya != yb else (ya, "")


def from_gedcom(raw: str) -> tuple:
    """GEDCOM date -> (Event form, date_precision).

    Event forms: ISO, `ABT <iso>`, `BEF <iso>`, `AFT <iso>`, `YYYY-YYYY`.
    Anything unreadable comes back verbatim with precision `unknown`; the
    Person form of such a value is empty, so it is never written there.
    """
    if not raw or not raw.strip():
        return "", "unknown"
    d = raw.strip()
    up = d.upper()
    m = (re.match(r'^BET\.?\s+(.+?)\s+AND\s+(.+)$', up)
         or re.match(r'^FROM\s+(.+?)\s+TO\s+(.+)$', up)
         or _YEAR_SPAN.match(d))
    if m:
        span = _span(m.group(1), m.group(2))
        if span:
            return ("%s-%s" % span if span[1] else span[0]), "range"
        return d, "unknown"
    qual, rest = _strip_prefix(d)
    one = single(rest)
    if one is None:
        return d, "unknown"
    if qual:
        return f"{qual} {one[0]}", "estimated"
    return one


def meaning(value) -> tuple | None:
    """Any vault or GEDCOM date form -> (qualifier, start, end), or None.

    `ABT 1804`, `c. 1804` and `circa 1804` read the same; so do `1850-1858`,
    `1850 to 1858` and `BET 1850 AND 1858`.
    """
    v = str(value or "").strip()
    if not v:
        return None
    up = v.upper()
    m = (re.match(r'^BET\.?\s+(.+?)\s+AND\s+(.+)$', up)
         or re.match(r'^(?:FROM\s+)?(.+?)\s+TO\s+(.+)$', up)
         or _YEAR_SPAN.match(v))
    if m:
        a, b = single(m.group(1)), single(m.group(2))
        return ("", a[0], b[0]) if a and b else None
    qual, rest = _strip_prefix(v)
    one = single(rest)
    return (qual, one[0], "") if one else None


def person_form(value: str) -> str:
    """The `born` / `died` form of a date, clean under the plugin's validator.

    '' when there is nothing safe to write. `BEF` / `AFT` become the bare
    date: the validator has no form for them, and the Event keeps the
    qualifier.
    """
    m = meaning(value)
    if m is None:
        return ""
    qual, start, end = m
    if end:
        return f"{start} to {end}"
    if qual == "ABT":
        return f"c. {start}"
    return start


# -- the plugin's "Validate date formats" command ---------------------------

_CIRCA = ("c.", "ca.", "circa", "~")
_V_ISO = re.compile(r'^(\d{4})-(\d{2})-(\d{2})$')
_V_ISO_LOOSE = re.compile(r'^(\d{4})-(\d{1,2})-(\d{1,2})$')
_V_MONTH = re.compile(r'^(\d{4})-(\d{2})$')
_V_YEAR = re.compile(r'^(\d{4})$')
_MON = "JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC"
_V_GED = re.compile(r'^(\d{1,2})\s+(' + _MON + r')\s+(\d{4})$', re.I)
_V_GED_MONTH = re.compile(r'^(' + _MON + r')\s+(\d{4})$', re.I)


def _plugin_single(a: str, s: dict) -> str:
    partial = s.get("allowPartialDates", True)
    zeros = s.get("requireLeadingZeros", False)
    std = s.get("dateFormatStandard", "flexible")
    if std == "iso8601":
        if zeros:
            ok = _V_ISO.match(a) or partial and (_V_MONTH.match(a) or _V_YEAR.match(a))
            return "" if ok else "ISO 8601 format required with leading zeros (YYYY-MM-DD)"
        ok = _V_ISO.match(a) or _V_ISO_LOOSE.match(a) or partial and (
            _V_MONTH.match(a) or _V_YEAR.match(a))
        return "" if ok else "ISO 8601 format required (YYYY-MM-DD or YYYY-M-D)"
    if std == "gedcom":
        ok = _V_GED.match(a) or partial and (_V_GED_MONTH.match(a) or _V_YEAR.match(a))
        return "" if ok else "GEDCOM format required (DD MMM YYYY, e.g., 15 JAN 1920)"
    if std == "flexible":
        ok = (_V_ISO.match(a) or not zeros and _V_ISO_LOOSE.match(a)
              or partial and (_V_MONTH.match(a) or _V_YEAR.match(a))
              or _V_GED.match(a) or partial and _V_GED_MONTH.match(a))
        return "" if ok else "Unrecognized date format (expected YYYY-MM-DD or DD MMM YYYY)"
    return "Unknown date format standard"


def plugin_error(value: str, settings: dict) -> str:
    """The plugin's verdict on a `born` / `died` value: '' if it passes.

    A line-for-line port of Charted Roots' date validator (`Sse` / `Tse` in
    the vendored `main.js`), driven by the same `data.json` settings. Keep
    it a port: its odd corners (no before/after form, a hyphenated year
    span rejected) are what the command actually reports.
    """
    t = str(value).strip()
    low = t.lower()
    circa = any(low.startswith(p) for p in _CIRCA)
    if circa and not settings.get("allowCircaDates", True):
        return 'Circa dates not allowed (check "Allow circa dates" setting)'
    i = t
    if circa:
        for p in _CIRCA:
            if i.lower().startswith(p):
                i = i[len(p):].strip()
                break
    parts = i.split("-")
    ranged = " to " in i or ("-" in i and len(parts) == 3 and len(parts[2]) == 4)
    if ranged and not settings.get("allowDateRanges", True):
        return 'Date ranges not allowed (check "Allow date ranges" setting)'
    if ranged:
        for piece in (i.split(" to ") if " to " in i else parts[:2]):
            err = _plugin_single(piece.strip(), settings)
            if err:
                return err
        return ""
    return _plugin_single(i, settings)
